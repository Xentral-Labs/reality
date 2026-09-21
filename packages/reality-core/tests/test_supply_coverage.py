from decimal import Decimal

from reality.db.core import Reservation
from reality.services import core
from reality.services.delivery_reads import delivery_case
from reality.services.supply_assignments import assign_supply, supply_coverage
from sqlalchemy import func, select


def _commitments(session, business):
    customer = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-COVERAGE-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "8",
                "unit_price": "20",
                "gross_amount": "160",
            }
        ],
        "160",
        document_date="2026-09-21",
    )[3][0]
    supplier = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        "PO-COVERAGE-001",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "12",
                "unit_price": "10",
                "gross_amount": "120",
            }
        ],
        "120",
        document_date="2026-09-21",
    )[3][0]
    return customer, supplier


def test_purchasing_sales_and_inventory_views_reconcile_without_double_counting(
    session, business
):
    customer, supplier = _commitments(session, business)
    assign_supply(
        session,
        business.tenant.id,
        supplier.id,
        "6",
        purpose="customer_demand",
        customer_commitment_id=customer.id,
        request_id="coverage-customer",
    )
    assign_supply(
        session,
        business.tenant.id,
        supplier.id,
        "2",
        purpose="stock_replenishment",
        request_id="coverage-stock",
    )
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "4",
        to_location_id=business.location.id,
        commitment_id=supplier.id,
    )

    purchasing = supply_coverage(
        session, business.tenant.id, supplier_commitment_id=supplier.id
    )["supplier"]
    sales = delivery_case(session, business.tenant.id, customer.id)
    receiving = delivery_case(session, business.tenant.id, supplier.id)

    assert purchasing == receiving["supply_coverage"]["supplier"]
    assert sales["supply_coverage"]["customer"]["protecting_supply"] == Decimal(6)
    assert purchasing["customer_assigned"] == Decimal(6)
    assert purchasing["stock_replenishment"] == Decimal(2)
    assert purchasing["unassigned"] == Decimal(4)
    assert purchasing["received"] == Decimal(4)
    assert purchasing["open"] == Decimal(8)
    assert receiving["inventory"]["physical"] == "4.0000"
    assert receiving["inventory"]["reserved"] == "0"
    assert (
        session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(Reservation.tenant_id == business.tenant.id)
        )
        == 0
    )
