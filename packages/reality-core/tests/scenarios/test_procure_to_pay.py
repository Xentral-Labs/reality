from decimal import Decimal

from reality.services.core import (
    create_commitment,
    create_document,
    fulfilled_quantity,
    open_invoice_amount,
    post_supplier_invoice,
    post_supplier_payment,
    record_movement,
    stock_at,
)


def test_procure_to_pay_business_story(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        20,
        "2026-09-10",
        amount=600,
    )
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        8,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        12,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    invoice = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "ER-2201",
        business.supplier.id,
        600,
        document_date="2026-09-22",
    )
    post_supplier_invoice(session, business.tenant.id, invoice.id)
    post_supplier_payment(session, business.tenant.id, invoice.id, 250)

    assert fulfilled_quantity(session, business.tenant.id, commitment.id) == Decimal(
        "20.0000"
    )
    assert stock_at(session, business.tenant.id, business.item.id) == Decimal("20.0000")
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(
        "350.0000"
    )
