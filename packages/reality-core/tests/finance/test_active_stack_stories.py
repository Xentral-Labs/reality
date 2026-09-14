"""Spec 148 active-stack cutover: symmetric, source-backed settlement stories."""

from decimal import Decimal

import pytest

from reality.services import core


def run_story(session, tenant_id, party_id, item_id, side, prefix):
    customer = side == "customer"
    invoice_kind = "sales_invoice" if customer else "supplier_invoice"
    credit_kind = "credit_note" if customer else "supplier_credit_note"
    post_invoice = core.post_sales_invoice if customer else core.post_supplier_invoice
    pay = core.post_customer_payment if customer else core.post_supplier_payment
    post_credit = (
        core.post_sales_credit_note if customer else core.post_supplier_credit_note
    )
    refund = core.post_customer_refund if customer else core.post_supplier_refund
    allocate = (
        core.allocate_credit_note if customer else core.allocate_supplier_credit_note
    )

    def document(kind, suffix, amount):
        number = f"{prefix}-{suffix}"
        source, _, _ = core.store_source_record(
            session,
            tenant_id,
            "finance_cutover_fixture",
            kind,
            number,
            {
                "number": number,
                "gross_amount": amount,
                "currency": "EUR",
                "synthetic": True,
            },
        )
        doc, _ = core.create_manual_document_with_lines(
            session,
            tenant_id,
            kind,
            number,
            party_id,
            [
                {
                    "item_id": item_id,
                    "quantity": "1",
                    "unit": "pcs",
                    "gross_amount": amount,
                }
            ],
            amount,
            source_record_id=source.id,
        )
        return doc

    invoice = document(invoice_kind, "INV-100", "100")
    invoice_entries = post_invoice(session, tenant_id, invoice.id)
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == Decimal(100)
    first = pay(session, tenant_id, invoice.id, "40", payment_number=f"{prefix}-PAY-40")
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == Decimal(60)
    pay(session, tenant_id, invoice.id, "60", payment_number=f"{prefix}-PAY-60")
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == 0
    core.reverse_ledger_posting_group(
        session,
        tenant_id,
        first[0].posting_group_id,
        reason="Synthetic cutover reversal",
    )
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == Decimal(40)
    pay(
        session, tenant_id, invoice.id, "40", payment_number=f"{prefix}-PAY-REPLACEMENT"
    )
    assert core.open_invoice_amount(session, tenant_id, invoice.id) == 0

    credit = document(credit_kind, "CREDIT-20", "20")
    post_credit(session, tenant_id, credit.id)
    refund(session, tenant_id, credit.id, "8", refund_number=f"{prefix}-REFUND-8")
    assert core.open_invoice_amount(session, tenant_id, credit.id) == Decimal(12)
    second = document(invoice_kind, "INV-50", "50")
    post_invoice(session, tenant_id, second.id)
    allocate(session, tenant_id, credit.id, second.id, "12")
    assert core.open_invoice_amount(session, tenant_id, credit.id) == 0
    assert core.open_invoice_amount(session, tenant_id, second.id) == Decimal(38)
    assert all(entry.account_id for entry in core.journal_rows(session, tenant_id))
    assert all(
        entry.source_record_id == invoice.source_record_id for entry in invoice_entries
    )
    return {
        "side": side,
        "settled_invoice": invoice.id,
        "open_invoice": second.id,
        "open_amount": "38",
        "credit": credit.id,
    }


@pytest.mark.parametrize("side", ["customer", "supplier"])
def test_active_stack_settlement_story(session, business, side):
    party = business.customer if side == "customer" else business.supplier
    run_story(
        session, business.tenant.id, party.id, business.item.id, side, side.upper()
    )
