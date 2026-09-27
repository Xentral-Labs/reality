"""Spec 283: one invoice over several orders of one party and one currency."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from conftest import record_by_id
from sqlalchemy import func, select
from test_unified_invoice_entry import confirm

from reality.db.core import Document, DocumentLine, LedgerEntry, SourceRecord
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.services.exceptions import operational_exceptions


def order(session, b, direction="sales", *, party=None, currency="EUR", lines=1):
    counterparty = party or (b.customer if direction == "sales" else b.supplier)
    return core.create_manual_order(
        session,
        b.tenant.id,
        direction,
        "ORDER-280-" + uuid4().hex[:8],
        b.company.id,
        counterparty.id,
        b.location.id,
        [
            {
                "item_id": b.item.id,
                "quantity": "3",
                "unit_price": "10",
                "gross_amount": "30",
            }
            for _ in range(lines)
        ],
        gross_amount=str(30 * lines),
        currency=currency,
    )[2]


def position(line, quantity="2", gross_amount="20"):
    return {
        "order_line_id": line.id,
        "quantity": quantity,
        "gross_amount": gross_amount,
    }


def prepare(session, b, lines, direction="sales", *, total="61.07", request=None):
    return prepare_delivery_action(
        session,
        b.tenant.id,
        "sales_invoice_record" if direction == "sales" else "supplier_invoice_record",
        {"lines": lines, "gross_amount": total, "number": "INV-280"},
        request_id=request or "consolidated-" + uuid4().hex[:8],
    )


def nothing_recorded(session):
    return (
        session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
        and session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.type.in_(("sales_invoice", "supplier_invoice")))
        )
        == 0
    )


@pytest.mark.parametrize(("direction", "orders"), [("sales", 3), ("purchase", 2)])
def test_one_invoice_bills_positions_of_several_orders(
    session, business, direction, orders
):
    """FR-001/FR-002: one source, one invoice, one line per position, one posting."""
    lines = [order(session, business, direction)[0] for _ in range(orders)]
    selected = [
        position(line, gross_amount=str(20 + index)) for index, line in enumerate(lines)
    ]
    proposal = prepare(session, business, selected, direction)
    assert nothing_recorded(session)

    confirm(session, business, proposal)

    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    records = detail["receipt"]["records"]
    invoice = record_by_id(
        session, Document, next(r["id"] for r in records if r["family"] == "document")
    )
    assert invoice.gross_amount == Decimal("61.07")
    invoice_lines = [
        record_by_id(session, DocumentLine, r["id"])
        for r in records
        if r["family"] == "document_line"
    ]
    assert [
        (row.billed_document_line_id, row.quantity, row.gross_amount)
        for row in invoice_lines
    ] == [
        (line.id, Decimal(2), Decimal(20 + index)) for index, line in enumerate(lines)
    ]
    assert len({line.document_id for line in lines}) == orders
    entries = [
        record_by_id(session, LedgerEntry, r["id"])
        for r in records
        if r["family"] == "ledger_entry"
    ]
    assert len({entry.posting_group_id for entry in entries}) == 1
    assert all(entry.amount == Decimal("61.07") for entry in entries)
    assert (
        json.loads(
            record_by_id(session, SourceRecord, invoice.source_record_id).payload
        )["lines"]
        == selected
    )


@pytest.mark.parametrize("mismatch", ["party", "currency", "direction"])
def test_positions_of_another_party_currency_or_direction_are_refused(
    session, business, mismatch
):
    """FR-001: grouping is one direction, one party and one currency; nothing is written."""
    first = order(session, business)[0]
    if mismatch == "party":
        other_party = core.create_party(
            session, business.tenant.id, "Other Customer KG", "customer"
        )
        other = order(session, business, party=other_party)[0]
    elif mismatch == "currency":
        other = order(session, business, currency="CHF")[0]
    else:
        other = order(session, business, "purchase")[0]
    same = order(session, business)[0]

    expected = {
        "party": "one party",
        "currency": "one currency",
        "direction": "requires a sales order line",
    }[mismatch]
    with pytest.raises(core.InvalidOperation, match=expected):
        prepare(session, business, [position(first), position(other)])
    assert nothing_recorded(session)

    # Positive control: the same two orders of one party and currency are accepted.
    prepare(session, business, [position(first), position(same)])


def test_a_failing_later_position_leaves_no_invoice(session, business):
    """FR-002: one refused position refuses the whole consolidated invoice."""
    first = order(session, business)[0]
    second = order(session, business)[0]
    with pytest.raises(core.InvalidOperation, match="remaining"):
        prepare(session, business, [position(first), position(second, quantity="4")])
    assert nothing_recorded(session)


def test_an_invoice_carries_at_most_two_hundred_positions(session, business):
    """FR-010: the position bound is refused before any write; 200 still fit."""
    lines = order(session, business, lines=201)
    selected = [position(line, quantity="1", gross_amount="10") for line in lines]

    with pytest.raises(core.InvalidOperation, match="at most 200"):
        prepare(session, business, selected, total="2010")
    assert nothing_recorded(session)

    prepare(session, business, selected[:200], total="2000")


# --- FR-003: billing stays per order line ------------------------------------

AS_OF = datetime(2026, 12, 31, tzinfo=UTC)


def placed(session, b, direction="sales"):
    _, _, lines, commitments = core.create_manual_order(
        session,
        b.tenant.id,
        direction,
        "ORDER-280-" + uuid4().hex[:8],
        b.company.id,
        (b.customer if direction == "sales" else b.supplier).id,
        b.location.id,
        [
            {
                "item_id": b.item.id,
                "quantity": "3",
                "unit_price": "10",
                "gross_amount": "30",
            }
        ],
        gross_amount="30",
    )
    return lines[0], commitments[0]


def billing(session, b, line):
    row = core._order_line_billing(session, b.tenant.id, line.id)
    assert row["invoiced"] + row["remaining"] == row["ordered"]
    return row["invoiced"], row["remaining"]


def findings(session, b, class_id, quantity):
    return {
        row.record_id: row.causal_values[quantity]
        for row in operational_exceptions(session, b.tenant.id, as_of=AS_OF)
        if row.class_id == class_id
    }


def invoice_group(session, b, proposal):
    receipt = delivery_proposal_detail(session, b.tenant.id, proposal.id)["receipt"]
    return next(
        record_by_id(session, LedgerEntry, r["id"]).posting_group_id
        for r in receipt["records"]
        if r["family"] == "ledger_entry"
    )


def test_a_consolidated_sales_invoice_bills_each_order_line_by_its_own_quantity(
    session, business
):
    """FR-003: billed + remaining = ordered per line, before, after and after reversal."""
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    (a, a_promise), (b, b_promise) = (
        placed(session, business),
        placed(session, business),
    )
    for promise in (a_promise, b_promise):
        core.record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            3,
            from_location_id=business.location.id,
            commitment_id=promise.id,
        )
    unbilled = "unbilled_quantity"
    assert findings(session, business, "shipped_not_billed", unbilled) == {
        a.id: Decimal(3),
        b.id: Decimal(3),
    }

    proposal = prepare(
        session,
        business,
        [position(a, "2", "20"), position(b, "3", "30")],
        total="50",
    )
    confirm(session, business, proposal)

    assert billing(session, business, a) == (Decimal(2), Decimal(1))
    assert billing(session, business, b) == (Decimal(3), Decimal(0))
    assert findings(session, business, "shipped_not_billed", unbilled) == {
        a.id: Decimal(1)
    }

    core.reverse_ledger_posting_group(
        session,
        business.tenant.id,
        invoice_group(session, business, proposal),
        reason="Wrong customer reference",
    )
    assert billing(session, business, a) == (Decimal(0), Decimal(3))
    assert billing(session, business, b) == (Decimal(0), Decimal(3))
    # A reversed invoice bills nothing any more, so both deliveries are unbilled.
    assert findings(session, business, "shipped_not_billed", unbilled) == {
        a.id: Decimal(3),
        b.id: Decimal(3),
    }


def test_a_consolidated_supplier_invoice_is_received_against_each_purchase(
    session, business
):
    """FR-003: billed_not_received is judged per purchase order line."""
    (a, a_promise), (b, _) = (
        placed(session, business, "purchase"),
        placed(session, business, "purchase"),
    )
    proposal = prepare(
        session,
        business,
        [position(a, "2", "20"), position(b, "3", "30")],
        "purchase",
        total="50",
    )
    confirm(session, business, proposal)
    unreceived = "unreceived_quantity"
    assert findings(session, business, "billed_not_received", unreceived) == {
        a.id: Decimal(2),
        b.id: Decimal(3),
    }

    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        2,
        to_location_id=business.location.id,
        commitment_id=a_promise.id,
    )
    assert findings(session, business, "billed_not_received", unreceived) == {
        b.id: Decimal(3)
    }


@pytest.mark.anyio
async def test_the_mcp_schema_declares_the_position_bound():
    """FR-010: agents see the same bound before calling the tool."""
    from reality.mcp import server as mcp_module

    tools = {tool.name: tool for tool in await mcp_module.build_server().list_tools()}
    for name in ("sales_invoice_record_propose", "supplier_invoice_record_propose"):
        lines = tools[name].input_schema["properties"]["lines"]
        assert (lines["minItems"], lines["maxItems"]) == (1, 200)


# --- FR-007/FR-009: review, stale detection, recovery -------------------------


def review_of(session, b, proposal):
    return delivery_proposal_detail(session, b.tenant.id, proposal.id)["review"]


def test_the_review_lists_every_order_and_names_none_as_the_order(session, business):
    """FR-007, SC-003: a consolidated review has orders, not one order."""
    a, b = order(session, business)[0], order(session, business)[0]
    proposal = prepare(session, business, [position(a), position(b)])

    state = review_of(session, business, proposal)["state"]
    assert [row["id"] for row in state["orders"]] == [a.document_id, b.document_id]
    assert all(row["number"].startswith("ORDER-280-") for row in state["orders"])
    assert "order" not in state and "line" not in state and "item" not in state
    assert state["party"] == {
        "id": business.customer.id,
        "name": business.customer.name,
    }
    assert [row["line"]["id"] for row in state["positions"]] == [a.id, b.id]
    assert "orders" not in state["creation"]


def test_a_change_to_the_second_order_makes_the_review_stale(session, business):
    """FR-007: billing a selected position elsewhere invalidates the review."""
    a, b = order(session, business)[0], order(session, business)[0]
    proposal = prepare(session, business, [position(a), position(b)])
    core.record_sales_invoice(session, business.tenant.id, b.id, "1", "10", "INV-ELSE")
    before = session.scalar(select(func.count()).select_from(LedgerEntry))

    with pytest.raises(core.InvalidOperation, match="fresh review"):
        confirm(session, business, proposal)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before


def test_a_consolidated_receipt_is_recovered_exactly(session, business):
    """FR-007: an unknown outcome is recovered from the recorded N-line proof."""
    a, b = order(session, business)[0], order(session, business)[0]
    proposal = prepare(session, business, [position(a), position(b)])
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert len(detail["receipt"]["records"]) == 2 + 4

    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["receipt"]
        == detail["receipt"]
    )


def test_a_single_order_review_keeps_its_shape(session, business):
    """FR-009: a one-order proposal has the review it had before spec 283."""
    lines = order(session, business, lines=2)
    proposal = prepare(session, business, [position(lines[0]), position(lines[1])])
    state = review_of(session, business, proposal)["state"]
    assert set(state) == {
        "creation",
        "order",
        "line",
        "party",
        "item",
        "positions",
        "billing",
    }
    assert state["order"]["id"] == lines[0].document_id
    assert "orders" not in state["creation"]


def cancelled_line(session, b, number):
    _, _, lines, promises = core.create_manual_order(
        session,
        b.tenant.id,
        "sales",
        number,
        b.company.id,
        b.customer.id,
        b.location.id,
        [
            {
                "item_id": b.item.id,
                "quantity": "3",
                "unit_price": "10",
                "gross_amount": "30",
            }
        ],
        gross_amount="30",
    )
    return lines[0], promises[0]


def test_a_cancelled_promise_changes_nothing_as_for_a_single_order_invoice(
    session, business
):
    """Spec 283 edge case: billing is order-line based; cancellation does not block it."""
    first, first_promise = cancelled_line(session, business, "ORDER-280-CANCEL")
    single_line, single_promise = cancelled_line(session, business, "ORDER-280-SINGLE")
    second = order(session, business)[0]
    consolidated = prepare(session, business, [position(first), position(second)])
    single = prepare(
        session,
        business,
        [position(single_line, quantity="1", gross_amount="10")],
        total="10",
        request="single-after-cancel",
    )
    for promise in (first_promise, single_promise):
        core.cancel_commitment(
            session,
            business.tenant.id,
            promise.id,
            reason="Customer cancelled the rest",
        )

    confirm(session, business, consolidated)
    confirm(session, business, single)
    assert core._order_line_billing(session, business.tenant.id, first.id)[
        "invoiced"
    ] == Decimal(2)
    assert core._order_line_billing(session, business.tenant.id, single_line.id)[
        "invoiced"
    ] == Decimal(1)
