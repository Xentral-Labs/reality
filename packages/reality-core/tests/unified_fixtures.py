"""Shared service-created delivery fixtures; never seed operational state via ORM."""

from dataclasses import dataclass
from decimal import Decimal

from reality.db.core import Commitment
from reality.services.core import create_commitment, record_movement


@dataclass
class DeliveryFixture:
    commitment: Commitment
    initial_stock: Decimal = Decimal(20)


def delivery_fixture(session, business, *, quantity="12") -> DeliveryFixture:
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "receipt",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        tenant_id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        None,
    )
    return DeliveryFixture(commitment)
