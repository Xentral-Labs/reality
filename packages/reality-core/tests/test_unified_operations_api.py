from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from unified_fixtures import delivery_fixture

from reality.db.core import ChangeProposal, Movement, Reservation
from reality.services.core import (
    correct_movement,
    create_item,
    create_tenant,
    record_movement,
    reserve,
)
from reality.services.projections import EXCEPTIONS, rebuild_projections
from reality.web.api import database_session
from reality.web.app import app


def test_warehouse_reads_filter_exact_item_before_paging_without_effects(
    session, business
):
    fixture = delivery_fixture(session, business)
    tid = business.tenant.id
    reserve(session, tid, fixture.commitment.id, "12")
    other_item = create_item(session, tid, "OTHER", business.item.name, unit="kg")
    record_movement(
        session,
        tid,
        "receipt",
        other_item.id,
        "99",
        to_location_id=business.location.id,
    )
    other_tenant = create_tenant(session, "Foreign operations")
    # The attention reads consume the stored generation the worker publishes.
    rebuild_projections(session, tid, [EXCEPTIONS], force=True)
    session.commit()
    models = (Movement, Reservation, ChangeProposal)
    before = [
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tid)
        )
        for model in models
    ]
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tid}"
            stock = client.get(
                f"{base}/warehouse/stock?item_id={business.item.id}&size=1"
            ).json()
            assert stock["page"]["total"] == 1
            assert Decimal(stock["items"][0]["available"]) == 8
            reservations = client.get(
                f"{base}/warehouse/reservations?item_id={business.item.id}"
            ).json()
            assert reservations["items"][0]["delivery_id"] == fixture.commitment.id
            movements = client.get(
                f"{base}/warehouse/movements?item_id={business.item.id}"
            ).json()
            assert movements["page"]["total"] == 1
            assert movements["items"][0]["item"] == business.item.name
            assert (
                client.get(f"{base}/warehouse/stock?state=invented").status_code == 422
            )
            assert client.get(f"{base}/warehouse/movements?size=101").status_code == 422
            assert (
                client.get(
                    f"/api/tenants/{other_tenant.id}/warehouse/stock?item_id={business.item.id}"
                ).status_code
                == 404
            )
            register = client.get(f"{base}/attention")
            assert register.status_code == 200
            assert register.json()["metadata"]["state"] == "ready"
            assert register.json()["metadata"]["calculation_mode"] == "stored"
            summary = client.get(f"{base}/attention/summary")
            assert summary.status_code == 200
            assert summary.json()["metadata"] == register.json()["metadata"]
            assert (
                summary.json()["total"]
                == client.get(f"{base}/attention").json()["page"]["total"]
            )
            open_class = next(row for row in summary.json()["classes"] if row["open"])[
                "class_id"
            ]
            by_class = client.get(f"{base}/attention?class_id={open_class}").json()
            assert {row["class_id"] for row in by_class["items"]} == {open_class}
            assert client.get(f"{base}/attention?class_id=invented").status_code == 422
            assert client.get(f"{base}/attention/foreign").status_code == 404
    finally:
        app.dependency_overrides.clear()
    assert before == [
        session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tid)
        )
        for model in models
    ]


def test_warehouse_movement_history_keeps_correction_roles(session, business):
    from reality.web.warehouse_reads import warehouse_register

    delivery_fixture(session, business)
    original = record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
    )
    correction = correct_movement(
        session,
        business.tenant.id,
        original.id,
        reason="Wrong count",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "from_location_id": business.location.id,
            "quantity": "3",
        },
    )
    result = warehouse_register(
        session, business.tenant.id, "movements", item_id=business.item.id, size=100
    )
    roles = {row["id"]: row["correction_role"] for row in result["items"]}
    assert roles[original.id] == "corrected"
    assert roles[correction.compensating_movement_id] == "compensation"
    assert roles[correction.replacement_movement_id] == "replacement"
    assert len(result["items"]) == 4


def test_warehouse_state_filters_and_non_customer_targets(session, business):
    from decimal import Decimal

    from reality.services.core import create_commitment, release_reservation
    from reality.web.warehouse_reads import warehouse_register

    fixture = delivery_fixture(session, business)
    tid = business.tenant.id
    reserve(session, tid, fixture.commitment.id, "12")
    extra = create_item(session, tid, "EMPTY", "Empty item")
    result = warehouse_register(session, tid, "stock", state="fully_allocated", size=1)
    assert result["page"]["total"] == 1 and result["items"][0]["id"] == extra.id
    active = warehouse_register(session, tid, "reservations", state="active")
    release_reservation(session, tid, active["items"][0]["id"])
    assert (
        warehouse_register(session, tid, "reservations", state="active")["page"][
            "total"
        ]
        == 0
    )
    assert (
        warehouse_register(session, tid, "reservations", state="released")["page"][
            "total"
        ]
        == 1
    )
    supplier = create_commitment(
        session,
        tid,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "7",
        None,
    )
    record_movement(
        session,
        tid,
        "receipt",
        business.item.id,
        "3",
        to_location_id=business.location.id,
        commitment_id=supplier.id,
    )
    movements = warehouse_register(
        session, tid, "movements", item_id=business.item.id, state="receipt", size=1
    )
    assert movements["page"]["total"] == 2
    assert movements["items"][0]["commitment_id"] == supplier.id
    assert movements["items"][0]["delivery_id"] is None
    assert (
        Decimal(
            warehouse_register(session, tid, "stock", item_id=business.item.id)[
                "items"
            ][0]["physical"]
        )
        == 23
    )


def test_attention_detail_classifies_a_cleared_finding_over_http(session, business):
    fixture = delivery_fixture(session, business)
    tid = business.tenant.id
    rebuild_projections(session, tid, [EXCEPTIONS], force=True)
    session.commit()
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tid}"
            register = client.get(f"{base}/attention").json()
            finding = next(
                row
                for row in register["items"]
                if row["record_id"] == fixture.commitment.id
            )
            assert client.get(f"{base}/attention/{finding['id']}").status_code == 200
            reserve(session, tid, fixture.commitment.id, "12")
            cleared = client.get(f"{base}/attention/{finding['id']}")
            assert cleared.status_code == 404
            assert cleared.json()["code"] == "finding_cleared"
            assert (
                cleared.json()["completed_at"] == register["metadata"]["completed_at"]
            )
            assert "cleared" in cleared.json()["detail"]
            assert client.get(f"{base}/attention/exc__invented__x").status_code == 404
            assert "code" not in client.get(f"{base}/attention/exc__invented__x").json()
    finally:
        app.dependency_overrides.clear()
