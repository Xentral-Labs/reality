import json
from decimal import Decimal
from pathlib import Path

from reality.services.core import (
    allocate_credit_note,
    create_document,
    explain_commitment,
    ingest_shopify_order,
    open_invoice_amount,
    open_quantity,
    post_customer_payment,
    post_sales_credit_note,
    post_sales_invoice,
    record_movement,
    reserve,
)


def test_order_to_cash_business_story(session, business):
    payload = json.loads(
        (Path(__file__).parents[2] / "fixtures/shopify/order_10473.json").read_text()
    )
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        30,
        to_location_id=business.location.id,
    )
    _, _, _, commitments = ingest_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    commitment = commitments[0]
    assert reserve(session, business.tenant.id, commitment.id).shortage == 0
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        10,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        20,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-10473",
        business.customer.id,
        "1470.00",
        document_date="2026-09-22",
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    post_customer_payment(session, business.tenant.id, invoice.id, "500")
    credit = create_document(
        session,
        business.tenant.id,
        "credit_note",
        "GS-10473",
        business.customer.id,
        "100",
        document_date="2026-09-27",
    )
    post_sales_credit_note(session, business.tenant.id, credit.id)
    allocate_credit_note(session, business.tenant.id, credit.id, invoice.id, "100")

    assert open_quantity(session, business.tenant.id, commitment.id) == 0
    assert (
        explain_commitment(session, business.tenant.id, commitment.id)["raw_source"]
        == payload
    )
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(
        "870.0000"
    )
