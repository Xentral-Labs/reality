from decimal import Decimal

import pytest
from sqlalchemy import event

from reality.mcp.catalog import MCP_TOOL_REGISTRY, dispatch_tool
from reality.services.core import (
    InvalidOperation,
    NotFound,
    cancel_commitment,
    create_document,
    create_item,
    create_location,
    create_manual_order,
    create_party,
    create_tenant,
    post_ledger,
    record_movement,
    reserve,
    revise_commitment,
)
from reality.tools.application import run_read_tool


def read(session, business, name, **arguments):
    return dispatch_tool(session, business.tenant.id, name, arguments)


def order(session, business, number="READ-1"):
    return create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit": "pcs",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )


def test_currency_balances_and_ledger_direction(session, business):
    for currency, receivable, payable in [
        ("EUR", "100.25", "40"),
        ("USD", "200", "70.5"),
    ]:
        doc = create_document(
            session,
            business.tenant.id,
            "sales_invoice",
            currency,
            business.customer.id,
            receivable,
            currency=currency,
        )
        post_ledger(
            session,
            business.tenant.id,
            doc.id,
            business.customer.id,
            [
                ("accounts_receivable", "debit", receivable),
                ("sales_revenue", "credit", receivable),
            ],
            currency=currency,
        )
        post_ledger(
            session,
            business.tenant.id,
            doc.id,
            business.customer.id,
            [("inventory", "debit", payable), ("accounts_payable", "credit", payable)],
            currency=currency,
        )
    result = read(session, business, "finance_balances")
    assert result["balances"] == [
        {"currency": "EUR", "receivables": "100.2500", "payables": "40.0000"},
        {"currency": "USD", "receivables": "200.0000", "payables": "70.5000"},
    ]
    assert "currency" not in result
    entries = read(
        session, business, "business_records_discover", family="ledger_entry"
    )
    assert len(entries["records"]) == 8
    assert {r["debit_credit"] for r in entries["records"]} == {"debit", "credit"}
    assert all(r["side"] == r["debit_credit"] for r in entries["records"])
    foreign = create_tenant(session, "Empty foreign")
    assert dispatch_tool(session, foreign.id, "finance_balances")["balances"] == []


def test_discovery_traverses_over_one_hundred_and_binds_cursor(session, business):
    for index in range(104):
        create_item(session, business.tenant.id, f"PAGE-{index:03}", f"Paged {index}")
    args = {"family": "item", "query": "PAGE-", "limit": 17}
    result = read(session, business, "business_records_discover", **args)
    first_cursor = result["next_cursor"]
    ids = []
    while True:
        ids.extend(r["id"] for r in result["records"])
        assert len(result["records"]) <= 17
        if not result["has_more"]:
            assert result["next_cursor"] is None
            break
        result = read(
            session,
            business,
            "business_records_discover",
            **args,
            cursor=result["next_cursor"],
        )
    assert len(ids) == len(set(ids)) == 104
    assert ids == sorted(ids)
    for overrides in [{"query": "other"}, {"family": "party"}]:
        with pytest.raises(InvalidOperation, match="cursor"):
            read(
                session,
                business,
                "business_records_discover",
                **(args | overrides),
                cursor=first_cursor,
            )
    foreign = create_tenant(session, "Cursor foreign")
    with pytest.raises(InvalidOperation, match="cursor"):
        dispatch_tool(
            session,
            foreign.id,
            "business_records_discover",
            args | {"cursor": first_cursor},
        )
    empty = read(
        session,
        business,
        "business_records_discover",
        family="item",
        query="not-present",
    )
    assert empty["records"] == [] and empty["has_more"] is False
    assert empty["next_cursor"] is None


@pytest.mark.parametrize(
    "arguments",
    [
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"cursor": "not-a-cursor"},
        {"response_format": "bad"},
    ],
)
def test_invalid_page_arguments_refused(session, business, arguments):
    with pytest.raises(InvalidOperation):
        read(session, business, "business_records_discover", family="item", **arguments)


def test_inventory_location_and_aggregate_use_same_stock(session, business):
    other = create_location(session, business.tenant.id, "Other")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=other.id,
    )
    aggregate = read(session, business, "inventory_read")["records"]
    assert aggregate[0]["aggregation"] == "item_all_locations"
    assert Decimal(aggregate[0]["available"]) == 10
    local = read(
        session,
        business,
        "inventory_read",
        item_id=business.item.id,
        location_id=business.location.id,
    )
    assert len(local["records"]) == 1
    assert local["records"][0]["location_id"] == business.location.id
    assert Decimal(local["records"][0]["available"]) == 0
    all_locations = read(
        session, business, "inventory_read", view="location", item_id=business.item.id
    )
    assert {r["location_id"] for r in all_locations["records"]} == {
        other.id,
        business.location.id,
    }
    assert all(r["unit"] == "pcs" for r in all_locations["records"])
    foreign = create_tenant(session, "Other location owner")
    foreign_location = create_location(session, foreign.id, "Foreign")
    with pytest.raises(NotFound):
        read(session, business, "inventory_read", location_id=foreign_location.id)


def test_units_and_effective_promise_context(session, business):
    _, _, _, commitments = order(session, business)
    commitment = next(c for c in commitments if c.type == "customer_delivery")
    revise_commitment(session, business.tenant.id, commitment.id, quantity="3")
    for tool in [
        "commitments_list",
        "item_supply_demand",
        "fulfillment_queue",
        "fulfillment_blockers",
    ]:
        records = read(session, business, tool)["records"]
        if tool == "fulfillment_queue":
            records = records[0]["lines"]
        assert records
        assert all(r["unit"] == "pcs" for r in records if r.get("item_id"))
    row = next(
        r
        for r in read(session, business, "commitments_list")["records"]
        if r["commitment_id"] == commitment.id
    )
    assert Decimal(row["original_quantity"]) == 2
    assert Decimal(row["quantity"]) == 3
    assert row["quantity_basis"] == "item_unit"


@pytest.mark.parametrize("closed", ["fulfilled", "cancelled"])
def test_retained_order_explanation_preserves_source_and_effects(
    session, business, closed
):
    source, document, lines, commitments = order(session, business)
    commitment = next(c for c in commitments if c.type == "customer_delivery")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    reservation = reserve(session, business.tenant.id, commitment.id).reservation
    if closed == "fulfilled":
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            "2",
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )
    else:
        cancel_commitment(session, business.tenant.id, commitment.id)
    result = read(session, business, "order_explain", order_reference=document.id)
    assert result["source"]["source_record_id"] == source.id
    assert result["document_lines"][0]["id"] == lines[0].id
    assert result["reservations"][0]["id"] == reservation.id
    assert result["fulfillment"]["lines"][0]["status"] == closed
    assert result["fulfillment"]["ship_ready"] is False
    assert Decimal(result["fulfillment"]["lines"][0]["open_quantity"]) == 0
    assert result["metadata"]["tenant_id"] == business.tenant.id
    by_commitment = read(
        session, business, "order_explain", order_reference=commitment.id
    )
    assert by_commitment["fulfillment"]["document_id"] == document.id
    foreign = create_tenant(session, "Foreign explanation")
    with pytest.raises(NotFound):
        dispatch_tool(
            session, foreign.id, "order_explain", {"order_reference": document.id}
        )


def test_ambiguous_order_numbers_require_identity(session, business):
    _, first, _, _ = order(session, business, "DUPLICATE")
    create_document(
        session,
        business.tenant.id,
        "sales_order",
        "DUPLICATE",
        business.customer.id,
        "30",
    )
    with pytest.raises(InvalidOperation, match="ambiguous"):
        read(session, business, "order_explain", order_reference="DUPLICATE")
    assert (
        read(session, business, "order_explain", order_reference=first.id)["document"][
            "id"
        ]
        == first.id
    )


def test_new_diagnostics_do_not_write_or_commit_and_metadata_is_honest(
    session, business, monkeypatch
):
    _, document, _, _ = order(session, business)
    connection = session.connection()

    def forbid_write(conn, cursor, statement, parameters, context, executemany):
        assert statement.lstrip().split()[0].upper() in {"SELECT", "WITH"}, statement

    def forbid_commit():
        pytest.fail("Diagnostic committed")

    monkeypatch.setattr(session, "commit", forbid_commit)
    event.listen(connection, "before_cursor_execute", forbid_write)
    try:
        for tool, args in [
            ("business_records_discover", {"family": "item"}),
            ("inventory_read", {}),
            ("inventory_read", {"view": "location"}),
            ("commitments_list", {}),
            ("fulfillment_queue", {}),
            ("fulfillment_blockers", {}),
            ("item_supply_demand", {}),
            ("finance_balances", {}),
            ("order_explain", {"order_reference": document.id}),
        ]:
            meta = read(session, business, tool, **args)["metadata"]
            assert meta["tenant_id"] == business.tenant.id and meta["observed_at"]
            assert meta["upstream_freshness"] == "unknown"
            assert meta["persistence"]["projection_writes"] is False
            assert meta["persistence"]["business_writes"] is False
    finally:
        event.remove(connection, "before_cursor_execute", forbid_write)


def test_mcp_page_default_and_legacy_internal_compatibility(session, business):
    schema = MCP_TOOL_REGISTRY["inventory_read"].input_schema
    assert schema["properties"]["response_format"]["default"] == "page"
    assert isinstance(read(session, business, "inventory_read"), dict)
    assert isinstance(
        read(session, business, "inventory_read", response_format="legacy"), list
    )
    assert isinstance(run_read_tool(session, business.tenant.id, "inventory"), list)
    assert isinstance(
        read(
            session,
            business,
            "business_records_discover",
            family="item",
            response_format="legacy",
        ),
        list,
    )


def test_reserved_local_stock_and_cursor_filter_scope(session, business):
    from reality.services.core import create_commitment

    other = create_location(session, business.tenant.id, "Stocked")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=other.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        other.id,
        "3",
        None,
    )
    reserve(session, business.tenant.id, commitment.id, "1")
    result = read(session, business, "inventory_read", view="location", limit=1)
    cursor = result["next_cursor"]
    assert cursor and result["has_more"]
    with pytest.raises(InvalidOperation, match="cursor"):
        read(session, business, "inventory_read", view="aggregate", cursor=cursor)
    local = read(session, business, "inventory_read", location_id=other.id)["records"][
        0
    ]
    assert {k: Decimal(local[k]) for k in ("physical", "reserved", "available")} == {
        "physical": 10,
        "reserved": 1,
        "available": 9,
    }
    discovered = read(
        session,
        business,
        "business_records_discover",
        family="commitment",
        record_id=commitment.id,
    )["records"][0]
    assert discovered["unit"] == "pcs"


def test_unit_mismatch_and_missing_unit_are_not_converted(session, business):
    from types import SimpleNamespace

    from reality.services.projections import quantity_unit

    assert quantity_unit(SimpleNamespace(unit=""))["unit_status"] == "unknown"
    assert quantity_unit(None)["unit"] is None
    _source, document, _lines, _ = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "UNIT",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit": "box",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )
    explained = read(session, business, "order_explain", order_reference=document.id)
    assert explained["document_lines"][0]["unit"] == "box"
    assert explained["document_lines"][0]["item_unit"] == "pcs"
    assert explained["document_lines"][0]["unit_mismatch"] is True
    queue = read(session, business, "fulfillment_queue")["records"][0]["lines"][0]
    assert queue["unit"] == "pcs" and queue["document_line_unit"] == "box"
    assert queue["unit_mismatch"] is True
    assert Decimal(queue["quantity"]) == 2


def test_exact_page_end_and_live_insert_contract(session, business):
    for i in range(3):
        create_item(session, business.tenant.id, f"EXACT-{i}", f"Exact {i}")
    args = {"family": "item", "query": "EXACT", "limit": 3}
    end = read(session, business, "business_records_discover", **args)
    assert (
        len(end["records"]) == 3 and not end["has_more"] and end["next_cursor"] is None
    )
    first = read(
        session, business, "business_records_discover", **(args | {"limit": 1})
    )
    created = create_item(session, business.tenant.id, "EXACT-NEW", "Exact new")
    second = read(
        session,
        business,
        "business_records_discover",
        **args,
        cursor=first["next_cursor"],
    )
    assert all(r["id"] > first["records"][0]["id"] for r in second["records"])
    assert (created.id in {r["id"] for r in second["records"]}) == (
        created.id > first["records"][0]["id"]
    )
    assert second["metadata"]["consistency"] == "live_keyset"


def test_currency_balances_preserve_zero_and_credit_positions(session, business):
    document = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "CREDIT-POSITION",
        business.customer.id,
        "10",
        currency="USD",
    )
    for entries in (
        [("accounts_receivable", "debit", "10"), ("sales_revenue", "credit", "10")],
        [("accounts_receivable", "credit", "10"), ("cash", "debit", "10")],
        [("accounts_payable", "debit", "5"), ("cash", "credit", "5")],
    ):
        post_ledger(
            session,
            business.tenant.id,
            document.id,
            business.customer.id,
            entries,
            currency="USD",
        )
    balance = read(session, business, "finance_balances")["balances"]
    assert len(balance) == 1 and balance[0]["currency"] == "USD"
    assert Decimal(balance[0]["receivables"]) == 0
    assert Decimal(balance[0]["payables"]) == -5


def test_diagnostic_services_exclude_foreign_reality(session, business):
    from reality.services.read_contracts import (
        discovery_page,
        finance_balances,
        operational_page,
        read_metadata,
    )

    foreign = create_tenant(session, "Foreign diagnostic records")
    foreign_party = create_party(
        session, foreign.id, "Foreign customer", "customer"
    )
    foreign_item = create_item(session, foreign.id, "FOREIGN", "Foreign item")
    foreign_location = create_location(session, foreign.id, "Foreign warehouse")
    record_movement(
        session,
        foreign.id,
        "opening_stock",
        foreign_item.id,
        "99",
        to_location_id=foreign_location.id,
    )
    doc = create_document(
        session,
        foreign.id,
        "sales_invoice",
        "FOREIGN",
        foreign_party.id,
        "999",
        currency="USD",
    )
    post_ledger(
        session,
        foreign.id,
        doc.id,
        foreign_party.id,
        [("accounts_receivable", "debit", "999"), ("sales_revenue", "credit", "999")],
        currency="USD",
    )
    tenant_id = business.tenant.id
    assert {
        r["id"]
        for r in discovery_page(session, tenant_id, {"family": "item"})["records"]
    } == {business.item.id}
    for args in ({}, {"view": "location"}):
        rows = operational_page(session, tenant_id, "inventory", args)["records"]
        assert {r["item_id"] for r in rows} == {business.item.id}
        assert all(Decimal(r["physical"]) == 0 for r in rows)
        assert foreign_location.id not in {r.get("location_id") for r in rows}
    assert finance_balances(session, tenant_id)["balances"] == []
    assert read_metadata(session, tenant_id, {})["tenant_id"] == tenant_id


def test_order_explanation_keeps_closed_and_open_lines_together(session, business):
    _, document, _, commitments = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "MIXED-LIFECYCLE",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "10",
                "gross_amount": "10",
            }
            for _ in range(2)
        ],
        "20",
    )
    deliveries = [c for c in commitments if c.type == "customer_delivery"]
    cancel_commitment(session, business.tenant.id, deliveries[0].id)
    explained = read(session, business, "order_explain", order_reference=document.id)
    lines = {line["commitment_id"]: line for line in explained["fulfillment"]["lines"]}
    assert set(lines) == {c.id for c in deliveries}
    assert Decimal(lines[deliveries[0].id]["open_quantity"]) == 0
    assert Decimal(lines[deliveries[1].id]["open_quantity"]) == 1
    assert explained["fulfillment"]["readiness"] == "blocked"
    assert len(explained["document_lines"]) == 2
