from datetime import timedelta

import pytest
from sqlalchemy import event

from reality.services.core import InvalidOperation, NotFound, record_movement
from reality.services.shipments import (
    record_shipment_event,
    record_shipment_notice,
    shipment_explain,
    shipments_list,
    supersede_shipment_event,
)


def test_notice_is_searchable_without_creating_physical_contents(session, business):
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
        carrier="DHL",
        tracking_number="TRACK-123",
    )

    result = shipments_list(session, business.tenant.id, query="track-123")
    assert result["page"]["total"] == 1
    assert result["items"][0]["id"] == shipment.id
    assert result["items"][0]["packages"][0]["id"] == package.id
    assert result["items"][0]["movements"] == []
    assert result["items"][0]["observations"]["received"] is False
    assert (
        shipment_explain(session, business.tenant.id, package.id)["id"] == shipment.id
    )
    assert (
        shipments_list(
            session,
            business.tenant.id,
            tracking="ack-12",
            created_from=shipment.created_at - timedelta(seconds=1),
            created_to=shipment.created_at + timedelta(seconds=1),
            observation="announced",
        )["page"]["total"]
        == 1
    )
    assert (
        shipments_list(
            session,
            business.tenant.id,
            created_from=shipment.created_at + timedelta(seconds=1),
        )["page"]["total"]
        == 0
    )
    with pytest.raises(InvalidOperation, match="observation"):
        shipments_list(session, business.tenant.id, observation="invented")


def test_superseded_delivery_event_does_not_claim_current_delivery(session, business):
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
    )
    delivered = record_shipment_event(
        session,
        business.tenant.id,
        shipment.id,
        shipment_package_id=package.id,
        event_type="delivered",
        reporter_type="carrier",
        location_text="Bologna hub",
    )
    detail = shipment_explain(session, business.tenant.id, shipment.id)
    assert detail["observations"]["externally_delivered"]
    rendered = next(event for event in detail["events"] if event["id"] == delivered.id)
    assert rendered["event_type"] == "delivered"
    assert rendered["reporter_type"] == "carrier"
    assert rendered["location_text"] == "Bologna hub"
    assert (
        shipments_list(session, business.tenant.id, observation="externally_delivered")[
            "page"
        ]["total"]
        == 1
    )

    supersession = supersede_shipment_event(
        session, business.tenant.id, delivered.id, reason="Carrier correction"
    )
    corrected = shipment_explain(session, business.tenant.id, shipment.id)
    assert not corrected["observations"]["externally_delivered"]
    historical = next(
        event for event in corrected["event_history"] if event["id"] == delivered.id
    )
    assert historical["superseded"] is True
    assert historical["supersession_id"] == supersession.id
    assert historical["supersession_reason"] == "Carrier correction"
    assert (
        shipments_list(session, business.tenant.id, observation="externally_delivered")[
            "page"
        ]["total"]
        == 0
    )


def test_foreign_shipment_is_not_found(session, business):
    shipment, _, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
    )
    try:
        shipment_explain(session, "tenant_elsewhere", shipment.id)
    except NotFound:
        pass
    else:
        raise AssertionError("foreign shipment was disclosed")


def test_package_accepts_only_its_purpose_movement(session, business):
    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
    )
    with pytest.raises(InvalidOperation, match="does not match"):
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            1,
            from_location_id=business.location.id,
            shipment_package_id=package.id,
        )
    assert shipment.id


def test_paged_shipment_register_has_bounded_query_cost(session, business):
    for index in range(80):
        record_shipment_notice(
            session,
            business.tenant.id,
            direction="outbound",
            purpose="customer_delivery",
            counterparty_id=business.customer.id,
            carrier="DHL",
            tracking_number=f"PERF-{index:03d}",
            commit=False,
        )
    session.commit()
    count = 0

    def counted(*_):
        nonlocal count
        count += 1

    bind = session.get_bind()
    event.listen(bind, "before_cursor_execute", counted)
    try:
        result = shipments_list(
            session,
            business.tenant.id,
            page=1,
            size=50,
            direction="outbound",
        )
    finally:
        event.remove(bind, "before_cursor_execute", counted)
    assert len(result["items"]) == 50
    assert result["page"]["total"] == 80
    assert count <= 6, f"Shipment register issued {count} queries for one page"
