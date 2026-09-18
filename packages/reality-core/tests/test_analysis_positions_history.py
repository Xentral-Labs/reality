"""Balances, exact stock dimensions and effective-date snapshots share canonical readers."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import LedgerEntry
from reality.domain.traversal import Traversal
from reality.services import core
from reality.services.analytics.traversal import TraversalRefused, run_traversal


def ask(session, tenant, **query):
    return run_traversal(session, tenant, Traversal.model_validate(query))


def invoice(session, business, number="HISTORY"):
    doc = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        business.customer.id,
        "100",
        document_date="2026-01-01",
    )
    core.post_sales_invoice(session, business.tenant.id, doc.id)
    for entry in session.scalars(
        select(LedgerEntry).where(LedgerEntry.document_id == doc.id)
    ):
        entry.effective_at = datetime(2026, 1, 2, tzinfo=UTC)
    session.flush()
    return doc


def test_unpaged_balances_match_existing_finance_and_include_unused_credit(
    session, business
):
    from reality.services.finance.balances import party_balance_rows, party_balances

    tenant = business.tenant.id
    invoice(session, business)
    core.record_customer_payment(session, tenant, business.customer.id, "130")
    expected = party_balances(session, tenant, side="customer")["items"][0]
    row = party_balance_rows(session, tenant, side="customer")[0]
    assert row["balance"] == Decimal(expected["balance"]) == -30
    result = ask(
        session,
        tenant,
        **{
            "from": "customer_balance",
            "as": "b",
            "group_by": [{"field": "b.position_id"}, {"field": "b.currency"}],
            "measures": ["customer_net_balance", "customer_unused_credit"],
        },
    )
    assert Decimal(result.rows[0]["customer_net_balance"]) == -30
    assert Decimal(result.rows[0]["customer_unused_credit"]) == 130


def test_historical_settlements_do_not_use_later_payments_or_allocations(
    session, business
):
    from reality.services.finance.balances import party_balance_rows

    tenant = business.tenant.id
    doc = invoice(session, business)
    entries = core.record_customer_payment(session, tenant, business.customer.id, "30")
    for entry in entries:
        entry.effective_at = datetime(2026, 1, 10, tzinfo=UTC)
    payment = next(e for e in entries if e.account == "accounts_receivable")
    allocation = core.allocate_settlement(
        session,
        tenant,
        payment.id,
        core._settlement_control_entry(session, tenant, doc.id).id,
        "30",
    )
    allocation.allocated_at = datetime(2026, 1, 11, tzinfo=UTC)
    session.flush()

    def at(day):
        return party_balance_rows(
            session,
            tenant,
            side="customer",
            effective_before=datetime(2026, 1, day, tzinfo=UTC),
        )[0]

    assert (at(9)["open"], at(9)["credit"], at(9)["balance"]) == (100, 0, 100)
    assert (at(11)["open"], at(11)["credit"], at(11)["balance"]) == (100, 30, 70)
    assert (at(12)["open"], at(12)["credit"], at(12)["balance"]) == (70, 0, 70)


def test_detail_inventory_conserves_locations_and_unknown_tracking(session, business):
    from reality.services.inventory_positions import inventory_detail_rows

    tenant = business.tenant.id
    second = core.create_location(session, tenant, "Other location")
    receipt = core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    receipt.occurred_at = datetime(2026, 1, 1, tzinfo=UTC)
    transfer = core.record_movement(
        session,
        tenant,
        "transfer",
        business.item.id,
        3,
        from_location_id=business.location.id,
        to_location_id=second.id,
    )
    transfer.occurred_at = datetime(2026, 1, 10, tzinfo=UTC)
    session.flush()
    current = inventory_detail_rows(session, tenant)
    assert {r["location_id"]: r["physical"] for r in current} == {
        business.location.id: 7,
        second.id: 3,
    }
    assert all(r["lot_id"] is None and r["serial_unit_id"] is None for r in current)
    old = inventory_detail_rows(
        session, tenant, effective_before=datetime(2026, 1, 5, tzinfo=UTC)
    )
    assert {r["location_id"]: r["physical"] for r in old} == {business.location.id: 10}
    assert all("reserved" not in r for r in old)
    result = ask(
        session,
        tenant,
        **{
            "from": "stock_detail",
            "as": "s",
            "group_by": [{"field": "s.position_id"}, {"field": "s.unit"}],
            "measures": ["detail_physical"],
        },
    )
    assert sum(Decimal(r["detail_physical"]) for r in result.rows) == 10


def test_snapshot_requires_one_explicit_date_and_keeps_history_measures_separate(
    session, business
):
    tenant = business.tenant.id
    q = {
        "from": "stock_history",
        "as": "s",
        "group_by": [{"field": "s.unit"}],
        "measures": ["historical_physical"],
    }
    with pytest.raises(TraversalRefused) as failure:
        ask(session, tenant, **q)
    assert failure.value.code == "snapshot_date_required"
    q["filter"] = [{"field": "s.snapshot_date", "op": "eq", "value": "2026-01-05"}]
    assert ask(session, tenant, **q).rows
    q["filter"][0]["value"] = "2999-01-01"
    with pytest.raises(TraversalRefused) as failure:
        ask(session, tenant, **q)
    assert failure.value.code == "invalid_snapshot_date"


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_balance_currency_grain_and_both_join_directions(session, business, side):
    from reality.services.finance.balances import party_balance_rows

    tenant = business.tenant.id
    party = getattr(business, side)
    pay = getattr(core, f"record_{side}_payment")
    pay(session, tenant, party.id, "12", currency="EUR")
    pay(session, tenant, party.id, "7", currency="USD")
    rows = party_balance_rows(session, tenant, side=side)
    assert {(r["currency"], r["balance"]) for r in rows} == {
        ("EUR", Decimal(-12)),
        ("USD", Decimal(-7)),
    }
    forward = ask(
        session,
        tenant,
        **{
            "from": f"{side}_balance",
            "as": "b",
            "follow": [{"edge": f"{side}_balance_party", "as": "p"}],
            "group_by": [
                {"field": "b.position_id"},
                {"field": "b.currency"},
                {"field": "p.id"},
            ],
            "measures": [f"{side}_net_balance"],
        },
    )
    reverse = ask(
        session,
        tenant,
        **{
            "from": "party",
            "as": "p",
            "follow": [{"edge": f"{side}_balance_party", "direction": "in", "as": "b"}],
            "group_by": [
                {"field": "b.position_id"},
                {"field": "b.currency"},
                {"field": "p.id"},
            ],
            "measures": [f"{side}_net_balance"],
        },
    )
    assert len(forward.rows) == len(reverse.rows) == 2
    assert {r["b.position_id"] for r in forward.rows} == {
        r["b.position_id"] for r in reverse.rows
    }
    assert {r["p.id"] for r in forward.rows} == {party.id}


def test_balances_are_not_truncated_at_register_page_size(session, business):
    from reality.services.finance.balances import party_balance_rows, party_balances

    tenant = business.tenant.id
    for i in range(101):
        party = core.create_party(session, tenant, f"Customer {i}", "customer")
        core.record_customer_payment(session, tenant, party.id, "1")
    assert len(party_balance_rows(session, tenant, side="customer")) == 101
    assert (
        len(party_balances(session, tenant, side="customer", size=100)["items"]) == 100
    )
    result = ask(
        session,
        tenant,
        **{
            "from": "customer_balance",
            "as": "b",
            "group_by": [{"field": "b.currency"}],
            "measures": ["customer_unused_credit"],
        },
    )
    assert Decimal(result.rows[0]["customer_unused_credit"]) == 101


def test_reversal_changes_only_snapshots_on_or_after_reversal(session, business):
    from reality.db.core import LedgerReversal
    from reality.services.finance.balances import party_balance_rows

    tenant = business.tenant.id
    invoice(session, business)
    payment = core.record_customer_payment(session, tenant, business.customer.id, "40")
    for entry in payment:
        entry.effective_at = datetime(2026, 1, 3, tzinfo=UTC)
    reversal = core.reverse_ledger_posting_group(
        session, tenant, payment[0].posting_group_id, reason="Wrong payment"
    )
    session.get(LedgerReversal, reversal.reversal_id).reversed_at = datetime(
        2026, 1, 10, tzinfo=UTC
    )
    session.flush()
    assert (
        party_balance_rows(
            session,
            tenant,
            side="customer",
            effective_before=datetime(2026, 1, 9, tzinfo=UTC),
        )[0]["balance"]
        == 60
    )
    assert (
        party_balance_rows(
            session,
            tenant,
            side="customer",
            effective_before=datetime(2026, 1, 11, tzinfo=UTC),
        )[0]["balance"]
        == 100
    )


def test_lot_null_tracking_and_reservations_conserve_canonical_stock(session, business):
    from reality.services.inventory_positions import inventory_detail_rows

    tenant = business.tenant.id
    item = core.create_item(
        session, tenant, "BATCH", "Tracked article", tracking_type="lot"
    )
    lot = core.create_lot(session, tenant, item.id, "L-1")
    movement = core.record_movement(
        session,
        tenant,
        "receipt",
        item.id,
        10,
        to_location_id=business.location.id,
        lot_id=lot.id,
    )
    # Imported retained stock may lack tracking; it must not become a wildcard.
    unknown = core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        4,
        to_location_id=business.location.id,
    )
    unknown.item_id = item.id
    promise = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        item.id,
        business.location.id,
        3,
        "2026-09-01",
    )
    reservation = core.reserve(session, tenant, promise.id, lot_id=lot.id).reservation
    session.flush()
    rows = [
        r for r in inventory_detail_rows(session, tenant) if r["item_id"] == item.id
    ]
    assert {
        (r["lot_id"], r["physical"], r["reserved"], r["available"]) for r in rows
    } == {(lot.id, 10, 3, 7), (None, 4, 0, 4)}
    canonical = next(
        r for r in core.inventory_rows(session, tenant) if r["item"].id == item.id
    )
    for field in ("physical", "reserved", "available"):
        assert sum(r[field] for r in rows) == canonical[field]
    core.release_reservation(session, tenant, reservation.id)
    core.correct_movement(session, tenant, movement.id, reason="Wrong receipt")
    assert (
        sum(
            r["physical"]
            for r in inventory_detail_rows(session, tenant)
            if r["item_id"] == item.id
        )
        == 4
    )


def test_history_roundtrip_and_chat_require_explicit_cutoff(session, business):
    from reality.services.analytics.cypher_surface import format_query, parse
    from reality.services.analytics.graph_model import reporting_graph
    from reality.services.analytics.interpretation import checked_interpretation

    query = {
        **reporting_graph().templates["stock_history_location"].question,
        "filter": [{"field": "s.snapshot_date", "op": "eq", "value": "2026-01-05"}],
    }
    traversal = Traversal.model_validate(query)
    formatted = format_query(traversal)
    parsed = parse(formatted["path"], formatted["parameters"])
    assert parsed.filter == traversal.filter
    assert (
        checked_interpretation({"status": "ready", "question": query})["status"]
        == "ready"
    )
    assert ask(session, business.tenant.id, **query).rows
    with pytest.raises(TraversalRefused) as failure:
        checked_interpretation({"status": "ready", "question": {**query, "filter": []}})
    assert failure.value.code == "snapshot_date_required"
    historical = reporting_graph().nodes["stock_history"]
    assert historical.coverage == ("as_of_effective",)
    assert not {"reserved", "available"} & historical.properties.keys()
    assert (
        not {"overdue", "due_date"}
        & reporting_graph().nodes["customer_balance_history"].properties.keys()
    )


def test_history_opening_boundaries_and_tenant_isolation(session, business):
    from reality.db.opening import OpeningScope

    tenant = business.tenant.id
    session.add(
        OpeningScope(
            id="scope_history_test",
            tenant_id=tenant,
            source_namespace="test",
            snapshot_key="opening",
            cutover_date=datetime(2026, 2, 1, tzinfo=UTC).date(),
            coverage_kind="summary",
            party_id=business.customer.id,
            direction="customer_debt",
            currency="EUR",
        )
    )
    session.flush()
    query = {
        "from": "customer_balance_history",
        "as": "b",
        "group_by": [{"field": "b.currency"}],
        "measures": ["customer_historical_net_balance"],
        "filter": [{"field": "b.snapshot_date", "op": "eq", "value": "2026-01-05"}],
    }
    with pytest.raises(TraversalRefused) as failure:
        ask(session, tenant, **query)
    assert failure.value.code == "history_unavailable"
    other = core.create_tenant(session, "Other company")
    assert not ask(session, other.id, **query).rows
    stock = core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    stock.occurred_at = datetime(2026, 2, 1, tzinfo=UTC)
    session.flush()
    with pytest.raises(TraversalRefused) as failure:
        ask(
            session,
            tenant,
            **{
                "from": "stock_history",
                "as": "s",
                "group_by": [{"field": "s.unit"}],
                "measures": ["historical_physical"],
                "filter": [
                    {"field": "s.snapshot_date", "op": "eq", "value": "2026-01-05"}
                ],
            },
        )
    assert failure.value.code == "history_unavailable"


def test_derived_positions_keep_units_fanout_and_input_bounds(
    session, business, monkeypatch
):
    from reality.services.analytics import position_relations

    q = {"from": "customer_balance", "as": "b", "measures": ["customer_net_balance"]}
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **q)
    assert failure.value.code == "unit_mismatch"
    q["group_by"] = [{"field": "b.currency"}]
    monkeypatch.setattr(position_relations, "MAX_ROWS", 0)
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **q)
    assert failure.value.code == "position_limit"


@pytest.mark.parametrize(
    "condition",
    [
        {"op": "gte", "value": "2026-01-05"},
        {"op": "eq", "value": "not-a-date"},
        {"op": "eq", "value": "2026-01-05T00:00:00Z"},
    ],
)
def test_invalid_snapshot_forms_are_refused(session, business, condition):
    with pytest.raises(TraversalRefused) as failure:
        ask(
            session,
            business.tenant.id,
            **{
                "from": "stock_history",
                "as": "s",
                "group_by": [{"field": "s.unit"}],
                "measures": ["historical_physical"],
                "filter": [{"field": "s.snapshot_date", **condition}],
            },
        )
    assert failure.value.code == "invalid_snapshot_date"


def test_conflicting_dates_and_historical_fanout_are_refused(session, business):
    q = {
        "from": "stock_history",
        "as": "s",
        "group_by": [{"field": "s.unit"}],
        "measures": ["historical_physical"],
        "filter": [
            {"field": "s.snapshot_date", "op": "eq", "value": d}
            for d in ["2026-01-05", "2026-01-06"]
        ],
    }
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **q)
    assert failure.value.code == "invalid_snapshot_date"
    q["filter"].pop()
    q["follow"] = [
        {"edge": "stock_history_item", "as": "i"},
        {"edge": "moved_item", "direction": "in", "as": "m"},
    ]
    q["group_by"].append({"field": "m.id"})
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **q)
    assert failure.value.code == "fan_out"


def test_cutoff_excludes_next_midnight_and_late_allocation_endpoint(session, business):
    tenant = business.tenant.id
    doc = invoice(session, business)
    entries = core.record_customer_payment(session, tenant, business.customer.id, "30")
    for entry in entries:
        entry.effective_at = datetime(2026, 1, 6, tzinfo=UTC)
    allocation = core.allocate_settlement(
        session,
        tenant,
        next(e.id for e in entries if e.account == "accounts_receivable"),
        core._settlement_control_entry(session, tenant, doc.id).id,
        "30",
    )
    allocation.allocated_at = datetime(2026, 1, 4, tzinfo=UTC)
    session.flush()
    result = ask(
        session,
        tenant,
        **{
            "from": "customer_balance_history",
            "as": "b",
            "group_by": [{"field": "b.currency"}],
            "measures": [
                "customer_historical_net_balance",
                "customer_historical_balance_open",
            ],
            "filter": [{"field": "b.snapshot_date", "op": "eq", "value": "2026-01-05"}],
        },
    )
    assert Decimal(result.rows[0]["customer_historical_net_balance"]) == 100
    assert Decimal(result.rows[0]["customer_historical_balance_open"]) == 100


def test_serial_stock_keeps_each_identity_and_current_labels(session, business):
    from reality.services.inventory_positions import inventory_detail_rows

    tenant = business.tenant.id
    item = core.create_item(
        session, tenant, "SERIAL", "Tracked serial article", tracking_type="serial"
    )
    ids = set()
    for number in ["SN-1", "SN-2"]:
        serial = core.create_serial_unit(session, tenant, item.id, number)
        ids.add(serial.id)
        core.record_movement(
            session,
            tenant,
            "receipt",
            item.id,
            1,
            to_location_id=business.location.id,
            serial_unit_id=serial.id,
        )
    rows = [
        r for r in inventory_detail_rows(session, tenant) if r["item_id"] == item.id
    ]
    assert {r["serial_unit_id"] for r in rows} == ids
    assert {r["serial_unit_name"] for r in rows} == {"SN-1", "SN-2"}
    assert len({r["position_id"] for r in rows}) == 2
    assert sum(r["physical"] for r in rows) == 2


def test_later_stock_compensation_does_not_rewrite_earlier_snapshot(session, business):
    from reality.db.core import Movement
    from reality.services.inventory_positions import inventory_detail_rows

    tenant = business.tenant.id
    receipt = core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    receipt.occurred_at = datetime(2026, 1, 1, tzinfo=UTC)
    core.correct_movement(session, tenant, receipt.id, reason="Wrong original quantity")
    for inverse in session.scalars(
        select(Movement).where(Movement.tenant_id == tenant, Movement.id != receipt.id)
    ):
        inverse.occurred_at = datetime(2026, 1, 10, tzinfo=UTC)
    session.flush()
    assert (
        sum(
            r["physical"]
            for r in inventory_detail_rows(
                session, tenant, effective_before=datetime(2026, 1, 5, tzinfo=UTC)
            )
        )
        == 10
    )
    assert (
        sum(
            r["physical"]
            for r in inventory_detail_rows(
                session, tenant, effective_before=datetime(2026, 1, 11, tzinfo=UTC)
            )
        )
        == 0
    )
