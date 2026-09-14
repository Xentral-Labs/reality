from decimal import Decimal

from reality.services.core import (
    create_commitment,
    fulfilled_quantity,
    record_movement,
    stock_at,
)
from reality.services.shipments import record_packaged_execution, shipment_explain


def test_packaged_customer_and_supplier_returns_preserve_original_fulfillment(
    session, business
):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
    )
    customer_commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        5,
        None,
    )
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        5,
        from_location_id=business.location.id,
        commitment_id=customer_commitment.id,
    )
    customer_return = record_packaged_execution(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="customer_return",
        counterparty_id=business.customer.id,
        movements=[
            {
                "commitment_id": customer_commitment.id,
                "item_id": business.item.id,
                "to_location_id": business.location.id,
                "quantity": "2",
            }
        ],
    )
    assert fulfilled_quantity(
        session, business.tenant.id, customer_commitment.id
    ) == Decimal(5)
    assert shipment_explain(
        session, business.tenant.id, customer_return["shipment_id"]
    )["purpose"] == "customer_return"

    supplier_commitment = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        5,
        None,
    )
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        5,
        to_location_id=business.location.id,
        commitment_id=supplier_commitment.id,
    )
    before_return = stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    )
    supplier_return = record_packaged_execution(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="supplier_return",
        counterparty_id=business.supplier.id,
        movements=[
            {
                "commitment_id": supplier_commitment.id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "2",
            }
        ],
    )
    assert fulfilled_quantity(
        session, business.tenant.id, supplier_commitment.id
    ) == Decimal(5)
    assert stock_at(
        session, business.tenant.id, business.item.id, business.location.id
    ) == before_return - 2
    assert shipment_explain(
        session, business.tenant.id, supplier_return["shipment_id"]
    )["purpose"] == "supplier_return"
