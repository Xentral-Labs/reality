"""Current stock analysis reuses warehouse observations and safe starting questions."""

from decimal import Decimal

import pytest

from reality.domain.traversal import Traversal
from reality.services import core
from reality.services.analytics.graph_model import reporting_graph, reporting_templates
from reality.services.analytics.traversal import TraversalRefused, run_traversal
from reality.web.warehouse_reads import warehouse_register


def ask(session, tenant, **query):
    return run_traversal(session, tenant, Traversal.model_validate(query))


def stock_question():
    return {
        "from": "stock_position",
        "as": "s",
        "group_by": [{"field": "s.id"}, {"field": "s.unit"}],
        "measures": ["stock_physical", "stock_reserved", "stock_available"],
    }


def test_stock_matches_canonical_and_warehouse_through_reservation_lifecycle(
    session, business
):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
    )
    promise = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        8,
        "2026-09-01",
    )
    reservation = core.reserve(session, tenant, promise.id).reservation
    second = core.create_location(session, tenant, "Second")
    core.record_movement(
        session,
        tenant,
        "transfer",
        business.item.id,
        3,
        from_location_id=business.location.id,
        to_location_id=second.id,
    )

    def verify():
        expected = next(
            r
            for r in core.inventory_rows(session, tenant)
            if r["item"].id == business.item.id
        )
        warehouse = next(
            r
            for r in warehouse_register(session, tenant, "stock")["items"]
            if r["id"] == business.item.id
        )
        result = ask(session, tenant, **stock_question())
        row = next(r for r in result.rows if r["s.id"] == business.item.id)
        for key in ("physical", "reserved", "available"):
            assert (
                Decimal(row[f"stock_{key}"]) == expected[key] == Decimal(warehouse[key])
            )
        assert result.statements > 1
        return row

    assert Decimal(verify()["stock_available"]) == 12
    core.release_reservation(session, tenant, reservation.id)
    assert Decimal(verify()["stock_reserved"]) == 0
    reservation = core.reserve(session, tenant, promise.id).reservation
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=promise.id,
    )
    assert Decimal(verify()["stock_physical"]) == 18


def test_zero_stock_and_tenant_isolation(session, business):
    result = ask(session, business.tenant.id, **stock_question())
    row = next(r for r in result.rows if r["s.id"] == business.item.id)
    assert all(
        Decimal(row[f"stock_{key}"]) == 0
        for key in ("physical", "reserved", "available")
    )
    other = core.create_tenant(session, "Foreign inventory")
    assert not ask(session, other.id, **stock_question()).rows


def test_stock_requires_units_and_rejects_time_trends(session, business):
    q = stock_question()
    q["group_by"] = [{"field": "s.id"}]
    with pytest.raises(TraversalRefused, match="unit"):
        ask(session, business.tenant.id, **q)
    q = stock_question()
    q["group_by"].append({"field": "s.name", "bucket": "month"})
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **q)
    assert failure.value.code == "not_additive"


def test_stock_derivation_bound_refuses_without_partial_answer(
    session, business, monkeypatch
):
    from reality.services.analytics import inventory_relation

    monkeypatch.setattr(inventory_relation, "MAX_INVENTORY_ITEMS", 0)
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **stock_question())
    assert failure.value.code == "inventory_limit"


def test_new_templates_are_localized_and_executable(session, business):
    keys = {
        "stock_by_article",
        "reserved_stock",
        "stock_shortages",
        "customer_outstanding",
        "supplier_outstanding",
        "customer_overdue",
    }
    templates = {t["key"]: t for t in reporting_templates("de")}
    assert keys <= templates.keys()
    for key in keys:
        entry = templates[key]
        assert entry["label"] != reporting_graph().templates[key].label.en
        ask(session, business.tenant.id, **entry["question"])


def test_shortage_template_and_movement_corrections_preserve_observations(
    session, business
):
    tenant = business.tenant.id
    receipt = core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    promise = core.create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        8,
        "2026-09-01",
    )
    reserved = core.reserve(session, tenant, promise.id).reservation
    # Retained imported reservations can exceed stock: do not clamp the observation.
    reserved.quantity = Decimal(12)
    session.flush()
    q = reporting_graph().templates["stock_shortages"].question
    row = ask(session, tenant, **q).rows[0]
    assert Decimal(row["stock_available"]) == -2
    reserved.quantity = Decimal(8)
    session.flush()
    core.release_reservation(session, tenant, reserved.id)
    core.correct_movement(session, tenant, receipt.id, reason="Wrong receipt")
    row = next(
        r
        for r in ask(session, tenant, **stock_question()).rows
        if r["s.id"] == business.item.id
    )
    assert Decimal(row["stock_physical"]) == 0


def test_stock_units_and_cost_do_not_depend_on_item_count(session, business):
    tenant = business.tenant.id
    before = ask(session, tenant, **stock_question())
    core.create_item(session, tenant, "KG-1", "Bulk", unit="kg")
    for n in range(8):
        core.create_item(session, tenant, f"EA-{n}", f"Article {n}")
    after = ask(session, tenant, **stock_question())
    assert len(after.rows) == len(before.rows) + 9
    assert after.statements == before.statements
    assert {r["s.unit"] for r in after.rows} == {"kg", business.item.unit}


def test_stock_cannot_multiply_across_movement_history(session, business):
    q = stock_question()
    q["follow"] = [
        {"edge": "stock_position_item", "as": "i"},
        {"edge": "moved_item", "direction": "in", "as": "m"},
    ]
    q["group_by"].append({"field": "m.id"})
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **q)
    assert failure.value.code == "fan_out"


def test_movement_input_bound_is_independent_of_item_bound(
    session, business, monkeypatch
):
    from reality.services.analytics import inventory_relation

    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        1,
        to_location_id=business.location.id,
    )
    monkeypatch.setattr(inventory_relation, "MAX_INVENTORY_INPUTS", 0)
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **stock_question())
    assert failure.value.code == "inventory_limit"


def test_chat_can_compile_stock_templates_without_reading_business_data():
    from reality.services.analytics.interpretation import checked_interpretation

    value = checked_interpretation(
        {
            "status": "ready",
            "question": reporting_graph().templates["stock_by_article"].question,
        }
    )
    assert value["status"] == "ready"


def test_supplier_commitment_bound_keeps_bulk_bind_parameters_bounded(
    session, business, monkeypatch
):
    from reality.services.analytics import inventory_relation

    core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        10,
        "2026-09-01",
    )
    monkeypatch.setattr(inventory_relation, "MAX_INVENTORY_COMMITMENTS", 0)
    with pytest.raises(TraversalRefused) as failure:
        ask(session, business.tenant.id, **stock_question())
    assert failure.value.code == "inventory_limit"
