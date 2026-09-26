from decimal import Decimal

import pytest
from conftest import record_by_id

from reality.db.core import Document, DocumentLine, uid
from reality.services.core import (
    InvalidOperation,
    create_commitment,
    create_manual_document_with_lines,
    create_party,
    create_payment_term,
    create_tenant,
    hold_commitment,
    post_customer_payment,
    record_movement,
    record_sales_invoice,
    reserve,
    reverse_ledger_posting_group,
)
from reality.services.fulfillment_readiness import fulfillment_readiness


def _prepayment_order(session, business):
    tenant_id = business.tenant.id
    create_payment_term(
        session,
        tenant_id,
        "PREPAY",
        "Prepayment",
        0,
        requires_prepayment=True,
    )
    order, lines = create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        "SO-PREPAY",
        business.customer.id,
        [
            {
                "sku": business.item.sku,
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
        payment_term_code="PREPAY",
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "10",
        None,
        amount="100",
        document_id=order.id,
        document_line_id=lines[0].id,
    )
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    reserve(session, tenant_id, commitment.id)
    return order, lines[0], commitment


def test_prepayment_readiness_uses_stated_order_and_active_allocation(
    session, business
):
    tenant_id = business.tenant.id
    _order, line, commitment = _prepayment_order(session, business)

    before_invoice = fulfillment_readiness(session, tenant_id, commitment.id)
    assert before_invoice.ship_ready is False
    assert before_invoice.blocker_codes == (
        "prepayment_invoice_missing",
        "prepayment_required",
    )
    assert before_invoice.required_amount == Decimal(100)
    assert before_invoice.received_amount == 0
    assert before_invoice.remaining_amount == Decimal(100)

    receipt = record_sales_invoice(
        session, tenant_id, line.id, "10", "100", "INV-PREPAY"
    )
    invoice = record_by_id(
        session,
        Document,
        next(row["id"] for row in receipt["records"] if row["family"] == "document"),
    )
    invoiced = fulfillment_readiness(session, tenant_id, commitment.id)
    assert invoiced.blocker_codes == ("prepayment_required",)
    assert invoiced.invoice_ids == (invoice.id,)

    post_customer_payment(session, tenant_id, invoice.id, "100")
    paid = fulfillment_readiness(session, tenant_id, commitment.id)
    assert paid.ship_ready is True
    assert paid.blocker_codes == ()
    assert paid.received_amount == Decimal(100)
    assert paid.remaining_amount == 0
    assert len(paid.allocation_ids) == 1


def test_reversed_and_foreign_payment_evidence_does_not_satisfy_prepayment(
    session, business
):
    tenant_id = business.tenant.id
    _order, line, commitment = _prepayment_order(session, business)
    receipt = record_sales_invoice(
        session, tenant_id, line.id, "10", "100", "INV-EVIDENCE"
    )
    invoice = record_by_id(
        session,
        Document,
        next(row["id"] for row in receipt["records"] if row["family"] == "document"),
    )
    payment_entries = post_customer_payment(session, tenant_id, invoice.id, "100")
    assert fulfillment_readiness(session, tenant_id, commitment.id).ship_ready is True

    other_customer = create_party(session, tenant_id, "Other customer", "customer")
    payment_control = next(
        row for row in payment_entries if row.account == "accounts_receivable"
    )
    payment_control.party_id = other_customer.id
    session.flush()
    foreign_party = fulfillment_readiness(session, tenant_id, commitment.id)
    assert foreign_party.received_amount == 0
    assert foreign_party.ship_ready is False

    payment_control.party_id = business.customer.id
    payment_control.currency = "USD"
    session.flush()
    foreign_currency = fulfillment_readiness(session, tenant_id, commitment.id)
    assert foreign_currency.received_amount == 0
    assert foreign_currency.ship_ready is False

    payment_control.currency = "EUR"
    session.commit()
    reverse_ledger_posting_group(
        session,
        tenant_id,
        payment_control.posting_group_id,
        reason="Payment was assigned in error",
    )
    reversed_payment = fulfillment_readiness(session, tenant_id, commitment.id)
    assert reversed_payment.received_amount == 0
    assert reversed_payment.ship_ready is False


def test_invoice_line_of_another_partys_order_blocks_without_guessing(
    session, business
):
    """An invoice line billing another party's order cannot be attributed."""
    tenant_id = business.tenant.id
    _order, line, commitment = _prepayment_order(session, business)
    receipt = record_sales_invoice(
        session, tenant_id, line.id, "10", "100", "INV-FOREIGN-LINE"
    )
    invoice = record_by_id(
        session,
        Document,
        next(row["id"] for row in receipt["records"] if row["family"] == "document"),
    )
    other_customer = create_party(session, tenant_id, "Other customer", "customer")
    other_order, other_lines = create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        "SO-OTHER",
        other_customer.id,
        [{"item_id": business.item.id, "quantity": "1", "gross_amount": "10"}],
        "10",
    )
    session.add(
        DocumentLine(
            id=uid("dln"),
            tenant_id=tenant_id,
            document_id=invoice.id,
            source_line_id="ambiguous-line",
            item_id=business.item.id,
            sku=business.item.sku,
            quantity=Decimal(1),
            gross_amount=Decimal(10),
            billed_document_line_id=other_lines[0].id,
        )
    )
    session.commit()

    result = fulfillment_readiness(session, tenant_id, commitment.id)
    assert other_order.id != result.order_id
    assert "prepayment_attribution_ambiguous" in result.blocker_codes
    assert result.received_amount == 0
    assert result.ship_ready is False


def test_a_consolidated_invoice_releases_prepayment_only_when_settled_in_full(
    session, business
):
    """Spec 280 FR-004: no split of a payment; the whole invoice must be settled."""
    tenant_id = business.tenant.id
    _order, line, commitment = _prepayment_order(session, business)
    _other, other_lines = create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        "SO-SAME-CUSTOMER",
        business.customer.id,
        [{"item_id": business.item.id, "quantity": "1", "gross_amount": "10"}],
        "10",
    )
    receipt = record_sales_invoice(
        session,
        tenant_id,
        lines=[
            {"order_line_id": line.id, "quantity": "10", "gross_amount": "100"},
            {"order_line_id": other_lines[0].id, "quantity": "1", "gross_amount": "10"},
        ],
        gross_amount="110",
        number="INV-COLLECTIVE",
    )
    invoice = record_by_id(
        session,
        Document,
        next(row["id"] for row in receipt["records"] if row["family"] == "document"),
    )

    open_invoice = fulfillment_readiness(session, tenant_id, commitment.id)
    assert open_invoice.blocker_codes == (
        "prepayment_consolidated_invoice_open",
        "prepayment_required",
    )
    assert open_invoice.invoice_ids == (invoice.id,)
    blocker = next(
        row
        for row in open_invoice.as_dict()["blockers"]
        if row["code"] == "prepayment_consolidated_invoice_open"
    )
    assert "INV-COLLECTIVE" in blocker["detail"]
    assert "110" in blocker["detail"]
    assert {"kind": "invoice", "id": invoice.id} in blocker["links"]

    post_customer_payment(session, tenant_id, invoice.id, "50")
    part_paid = fulfillment_readiness(session, tenant_id, commitment.id)
    assert part_paid.ship_ready is False
    assert "prepayment_consolidated_invoice_open" in part_paid.blocker_codes
    assert part_paid.received_amount == 0

    post_customer_payment(session, tenant_id, invoice.id, "60")
    settled = fulfillment_readiness(session, tenant_id, commitment.id)
    assert settled.blocker_codes == ()
    assert settled.ship_ready is True
    assert settled.received_amount == Decimal(100)
    assert settled.remaining_amount == 0


def test_unpaid_net_term_is_not_blocked_by_prepayment(session, business):
    tenant_id = business.tenant.id
    order, lines = create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        "SO-NET",
        business.customer.id,
        [
            {
                "sku": business.item.sku,
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "10",
                "gross_amount": "10",
            }
        ],
        "10",
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        None,
        document_id=order.id,
        document_line_id=lines[0].id,
    )
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    reserve(session, tenant_id, commitment.id)
    assert fulfillment_readiness(session, tenant_id, commitment.id).ship_ready is True


def test_readiness_combines_stock_reservation_and_active_hold(session, business):
    tenant_id = business.tenant.id
    order, lines = create_manual_document_with_lines(
        session,
        tenant_id,
        "sales_order",
        "SO-OPS",
        business.customer.id,
        [{"item_id": business.item.id, "quantity": "2", "gross_amount": "20"}],
        "20",
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        None,
        document_id=order.id,
        document_line_id=lines[0].id,
    )

    unavailable = fulfillment_readiness(session, tenant_id, commitment.id)
    assert unavailable.blocker_codes == (
        "insufficient_reservation",
        "insufficient_stock",
    )

    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    reserve(session, tenant_id, commitment.id)
    hold = hold_commitment(
        session, tenant_id, commitment.id, "manual_review", "Check delivery"
    )
    held = fulfillment_readiness(session, tenant_id, commitment.id)
    assert held.blocker_codes == ("commitment_hold",)
    assert held.commitment_hold_ids == (hold.id,)
    assert held.as_dict()["blockers"][0]["links"] == [
        {"kind": "commitment_hold", "id": hold.id}
    ]


def test_fulfillment_readiness_refuses_foreign_and_unknown_commitments_equally(
    session, business
):
    other = create_tenant(session, "Other readiness tenant")
    _order, _line, commitment = _prepayment_order(session, business)

    with pytest.raises(InvalidOperation) as foreign:
        fulfillment_readiness(session, other.id, commitment.id)
    with pytest.raises(InvalidOperation) as unknown:
        fulfillment_readiness(session, other.id, "com_unknown")

    assert str(foreign.value) == str(unknown.value)
