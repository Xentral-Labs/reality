import pytest
from conftest import record_by_id
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import BusinessEvent, HandlingUnit, Movement
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_handling_unit,
    create_tenant,
    handling_units,
    record_movement,
)
from reality.web import api as api_module
from reality.web import app as web_module


def test_pallet_nve_is_optional_and_tenant_unique(session, business):
    anonymous = create_handling_unit(session, business.tenant.id)
    pallet = create_handling_unit(session, business.tenant.id, " 003400599999999999 ")

    assert anonymous.nve is None
    assert pallet.nve == "003400599999999999"
    assert {row.id for row in handling_units(session, business.tenant.id)} == {
        pallet.id,
        anonymous.id,
    }
    with pytest.raises(InvalidOperation, match="NVE already exists"):
        create_handling_unit(session, business.tenant.id, pallet.nve)


def test_movement_may_reference_a_pallet_but_does_not_require_one(session, business):
    pallet = create_handling_unit(session, business.tenant.id, "003400599999999999")

    on_pallet = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        12,
        to_location_id=business.location.id,
        handling_unit_id=pallet.id,
    )
    without_pallet = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        3,
        to_location_id=business.location.id,
    )

    assert on_pallet.handling_unit_id == pallet.id
    assert without_pallet.handling_unit_id is None
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.subject_type == "movement",
            BusinessEvent.subject_id == on_pallet.id,
        )
    )
    assert pallet.id in event.payload


def test_movement_rejects_pallet_from_another_tenant(session, business):
    other = create_tenant(session, "Other company")
    foreign_pallet = create_handling_unit(session, other.id, "003400500000000001")

    with pytest.raises(NotFound):
        record_movement(
            session,
            business.tenant.id,
            "receipt",
            business.item.id,
            1,
            to_location_id=business.location.id,
            handling_unit_id=foreign_pallet.id,
        )

    assert (
        session.scalar(select(Movement).where(Movement.tenant_id == other.id)) is None
    )
    assert record_by_id(session, HandlingUnit, foreign_pallet.id) is foreign_pallet


def test_api_records_optional_pallet_and_movement(session, business, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(api_module, "Session", factory)
    client = TestClient(web_module.app)

    pallet_response = client.post(
        f"/api/tenants/{business.tenant.id}/handling-units",
        json={"nve": "003400599999999999"},
    )
    assert pallet_response.status_code == 201
    pallet_id = pallet_response.json()["id"]

    movement_response = client.post(
        f"/api/tenants/{business.tenant.id}/movements",
        json={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "7",
            "to_location_id": business.location.id,
            "handling_unit_id": pallet_id,
        },
    )
    assert movement_response.status_code == 201
    assert movement_response.json()["handling_unit_id"] == pallet_id
