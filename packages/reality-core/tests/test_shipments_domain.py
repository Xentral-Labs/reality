from __future__ import annotations

import pytest

from reality.db.core import (
    Movement,
    Shipment,
    ShipmentEvent,
    ShipmentEventSupersession,
    ShipmentPackage,
)
from reality.domain.shipments import (
    ShipmentCompatibilityError,
    current_observations,
    validate_movement_compatibility,
    validate_shipment_direction,
)


@pytest.mark.parametrize(
    ("purpose", "direction", "movement_type"),
    [
        ("customer_delivery", "outbound", "shipment"),
        ("supplier_delivery", "inbound", "receipt"),
        ("customer_return", "inbound", "return"),
        ("supplier_return", "outbound", "supplier_return"),
    ],
)
def test_each_shipment_purpose_has_one_direction_and_movement(
    purpose, direction, movement_type
):
    validate_shipment_direction(purpose, direction)
    validate_movement_compatibility(purpose, direction, movement_type)


def test_wrong_direction_and_movement_are_rejected():
    with pytest.raises(ShipmentCompatibilityError):
        validate_shipment_direction("customer_delivery", "inbound")
    with pytest.raises(ShipmentCompatibilityError):
        validate_movement_compatibility("supplier_delivery", "inbound", "shipment")


def test_observations_keep_warehouse_and_external_delivery_distinct():
    result = current_observations(
        direction="outbound",
        package_ids=("pkg_1", "pkg_2"),
        effective_movements=(
            {"package_id": "pkg_1", "occurred_at": "2026-09-11T08:00:00+00:00"},
        ),
        current_events=(
            {
                "package_id": "pkg_1",
                "event_type": "delivered",
                "occurred_at": "2026-09-12T08:00:00+00:00",
            },
        ),
    )
    assert result["dispatched"] is True
    assert result["externally_delivered"] is False
    assert result["received"] is False


def test_shipment_schema_keeps_identity_tenant_scope_and_derivations_separate():
    for model in (Shipment, ShipmentPackage, ShipmentEvent, ShipmentEventSupersession):
        assert model.__table__.c.tenant_id.nullable is False
        assert model.__table__.c.id.primary_key
    assert "status" not in Shipment.__table__.c
    assert "delivered_at" not in Shipment.__table__.c
    assert Movement.__table__.c.shipment_package_id.nullable is True
    assert "shipment_id" not in Movement.__table__.c
    assert "tracking_number" not in Movement.__table__.c
