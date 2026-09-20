"""Current read-only contribution candidates follow exact existing evidence links."""

import json

import pytest
import test_costing_services as costs
import test_inventory_costing_services as stock
from sqlalchemy import event

from reality.db.core import Item
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.costing import contribution_preview, receipt_cost
from reality.tools.application import run_read_tool

cost_owner = costs.cost_owner


def prepared(session, business, owner, *, reviewed=True):
    t = business.tenant.id
    order, lines = core.create_manual_document_with_lines(
        session,
        t,
        "sales_order",
        "SO",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "60",
                "unit": business.item.unit,
                "unit_price": "999",
                "gross_amount": "1200",
            }
        ],
        "1200",
    )
    agreed = lines[0]
    commitment = core.create_commitment(
        session,
        t,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "60",
        None,
        document_id=order.id,
        document_line_id=agreed.id,
    )
    invoice, lines = core.create_manual_document_with_lines(
        session,
        t,
        "sales_invoice",
        "INV",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "60",
                "unit": business.item.unit,
                "unit_price": "999",
                "gross_amount": "1428",
                "billed_document_line_id": agreed.id,
            }
        ],
        "1428",
    )
    billed = lines[0]
    # Retain received fixture detail, independent of deliberately different unit price.
    billed.payload = json.dumps({"reality_finance_v1": {"net": "1200", "tax": "228"}})
    session.flush()
    args, receipt, issue = stock.prepared(session, business, owner)
    issue.commitment_id = commitment.id  # fixture relation for the recorded shipment
    session.flush()
    args["effective_at"] = core.now().isoformat()
    args["expected_event_sequence"] = receipt_cost(session, t, receipt.id)[
        "event_sequence"
    ]
    review = None
    if reviewed:
        _, review = stock.commit_review(session, business, owner, args)
    return billed, agreed, invoice, commitment, issue, review


def test_preview_actual_trace_and_no_writes(session, business, cost_owner):
    billed, agreed, _invoice, _commitment, issue, review = prepared(
        session, business, cost_owner
    )
    writes = []

    def observe(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)

    connection = session.connection()
    event.listen(connection, "before_cursor_execute", observe)
    try:
        result = contribution_preview(session, business.tenant.id, billed.id)
    finally:
        event.remove(connection, "before_cursor_execute", observe)
    assert not writes
    assert result["state"] == "candidate"
    assert result["known_db1"] == "570.0000"
    assert result["db1"] is result["db2"] is result["db1_rate"] is None
    assert result["trace"]["order_line_id"] == agreed.id
    assert result["trace"]["movement_id"] == issue.id
    assert result["trace"]["inventory_review_id"] == review["review_id"]
    assert result["trace"]["revenue"]["amounts"]["net"] == "1200"
    assert "commercial_match_not_reviewed" in result["missing_basis"]
    assert "selling_costs_unknown" in result["missing_basis"]
    assert result["persistence"] == {
        "business_writes": False,
        "projection_writes": False,
    }


def test_preview_foreign_scope_and_dispatch(session, business, cost_owner):
    billed, *_ = prepared(session, business, cost_owner)
    args = {"document_line_id": billed.id}
    expected = contribution_preview(session, business.tenant.id, billed.id)
    assert (
        run_read_tool(session, business.tenant.id, "cost.contribution.preview", args)
        == expected
    )
    assert (
        MCP_TOOL_REGISTRY["cost_contribution_preview"].handler(
            session, business.tenant.id, args
        )
        == expected
    )
    other = core.create_tenant(session, "Other")
    for read in [
        lambda: contribution_preview(session, other.id, billed.id),
        lambda: run_read_tool(session, other.id, "cost.contribution.preview", args),
        lambda: MCP_TOOL_REGISTRY["cost_contribution_preview"].handler(
            session, other.id, args
        ),
    ]:
        with pytest.raises(core.NotFound):
            read()


@pytest.mark.parametrize(
    "change,gap",
    [
        ("missing_net", "received_net_missing"),
        ("missing_link", "billed_order_line_missing"),
        ("quantity", "quantity_scope_mismatch"),
        ("unit", "unit_scope_mismatch"),
        ("currency", "currency_scope_mismatch"),
        ("customer", "customer_scope_mismatch"),
        ("shipment_quantity", "quantity_scope_mismatch"),
        ("owner", "owner_scope_mismatch"),
        ("type", "unsupported_revenue_type"),
    ],
)
def test_preview_gaps_never_make_margin(session, business, cost_owner, change, gap):
    billed, _agreed, invoice, commitment, issue, _ = prepared(
        session, business, cost_owner
    )
    if change == "missing_net":
        billed.payload = "{}"
    elif change == "missing_link":
        billed.billed_document_line_id = None
    elif change == "quantity":
        billed.quantity = 59
    elif change == "unit":
        billed.unit = "kg"
    elif change == "currency":
        invoice.currency = "USD"
    elif change == "customer":
        invoice.party_id = business.supplier.id
    elif change == "shipment_quantity":
        issue.quantity = 59
    elif change == "owner":
        commitment.from_party_id = business.supplier.id
    elif change == "type":
        invoice.type = "credit_note"
    session.flush()  # corrupt/unsupported fixture input, not a business mutation path
    result = contribution_preview(session, business.tenant.id, billed.id)
    assert gap in result["missing_basis"]
    assert result["known_db1"] is result["db1"] is result["db2"] is None


def test_preview_stale_review_and_multiple_billing(session, business, cost_owner):
    billed, agreed, _invoice, _commitment, _issue, _review = prepared(
        session, business, cost_owner
    )
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    result = contribution_preview(session, business.tenant.id, billed.id)
    assert "inventory_review_stale" in result["missing_basis"]
    core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-2",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": business.item.unit,
                "gross_amount": "1",
                "billed_document_line_id": agreed.id,
            }
        ],
        "1",
    )
    assert (
        "ambiguous_billing"
        in contribution_preview(session, business.tenant.id, billed.id)["missing_basis"]
    )


def test_preview_does_not_flush_pending_objects(session, business, cost_owner):
    billed, *_ = prepared(session, business, cost_owner)
    pending = Item(
        id="pending",
        tenant_id=business.tenant.id,
        sku="pending",
        name="Pending",
        unit="pcs",
    )
    session.add(pending)
    contribution_preview(session, business.tenant.id, billed.id)
    assert pending in session.new


def test_preview_concurrent_change_refuses(session, business, cost_owner, monkeypatch):
    from reality.services import contribution

    billed, *_ = prepared(session, business, cost_owner)
    real_sequence = contribution._sequence
    calls = 0

    def changed(db, tenant):
        nonlocal calls
        calls += 1
        return real_sequence(db, tenant) + int(calls > 1)

    monkeypatch.setattr(contribution, "_sequence", changed)
    with pytest.raises(core.Conflict, match="changed during preview"):
        contribution_preview(session, business.tenant.id, billed.id)


def test_preview_multiple_shipments_and_no_history_parameter(
    session, business, cost_owner
):
    billed, _, _, commitment, issue, _ = prepared(session, business, cost_owner)
    issue.quantity = 59  # split the fixture before appending the second shipment
    session.flush()
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    assert (
        "ambiguous_fulfilment"
        in contribution_preview(session, business.tenant.id, billed.id)["missing_basis"]
    )
    with pytest.raises(core.InvalidOperation):
        run_read_tool(
            session,
            business.tenant.id,
            "cost.contribution.preview",
            {"document_line_id": billed.id, "review_id": "invented-history"},
        )


def test_preview_refuses_old_snapshot_isolation(
    session, business, cost_owner, monkeypatch
):
    billed, *_ = prepared(session, business, cost_owner)
    monkeypatch.setattr(
        session.connection(), "get_isolation_level", lambda: "REPEATABLE READ"
    )
    with pytest.raises(core.InvalidOperation, match="READ COMMITTED"):
        contribution_preview(session, business.tenant.id, billed.id)


def test_preview_unknown_inventory_and_negative_revenue(session, business, cost_owner):
    billed, *_ = prepared(session, business, cost_owner)
    billed.payload = json.dumps({"reality_finance_v1": {"net": "-1"}})
    session.flush()
    assert (
        "negative_revenue_requires_match"
        in contribution_preview(session, business.tenant.id, billed.id)["missing_basis"]
    )


def test_preview_foreign_customer_link_is_not_disclosed(session, business, cost_owner):
    from reality.db.core import Document

    billed, agreed, invoice, commitment, _, _ = prepared(session, business, cost_owner)
    other = core.create_tenant(session, "Other")
    foreign = core.create_party(session, other.id, "Private", "customer")
    invoice.party_id = foreign.id
    session.get(Document, agreed.document_id).party_id = foreign.id
    commitment.to_party_id = foreign.id
    session.flush()
    with pytest.raises(core.NotFound):
        contribution_preview(session, business.tenant.id, billed.id)


def test_preview_unreviewed_stock_is_unknown(session, business, cost_owner):
    billed, *_ = prepared(session, business, cost_owner, reviewed=False)
    result = contribution_preview(session, business.tenant.id, billed.id)
    assert result["known_db1"] is None
    assert result["missing_basis"] == ["inventory_scope_not_reviewed"]
