import pytest

from reality.services.core import (
    NotFound,
    create_commitment,
    create_item,
    create_location,
    create_party,
    create_tenant,
)


def test_cross_tenant_records_cannot_be_linked(session, business):
    other = create_tenant(session, "Other GmbH")
    foreign_item = create_item(session, other.id, "BIKE-LIGHT", "Same human SKU")

    with pytest.raises(NotFound):
        create_commitment(
            session,
            business.tenant.id,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            foreign_item.id,
            business.location.id,
            1,
            "2026-09-03",
        )


def test_human_values_may_repeat_across_tenants(session, business):
    other = create_tenant(session, "Other GmbH")
    party = create_party(session, other.id, business.customer.name, "customer")
    location = create_location(session, other.id, business.location.name)
    item = create_item(session, other.id, business.item.sku, business.item.name)

    assert party.id != business.customer.id
    assert location.id != business.location.id
    assert item.id != business.item.id
