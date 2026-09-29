"""Catalog scenarios P04 and P07: what a source says after the fact, and when it goes quiet.

Each story feeds stored Shopify payloads through the same intake the connector
uses, and closes what a person must decide through the reviewed tool.
"""

import json
from datetime import UTC, datetime, timedelta

from conftest import record_by_id
from sqlalchemy import func, select

from reality.db import core as db_core
from reality.db.core import BusinessEvent, Commitment, Document, SourceRecord
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.tools.application import approve_and_execute_proposal


def _order_payload(order_id, *, updated_at="2026-09-01T10:00:00Z", **changes):
    return {
        "id": order_id,
        "name": f"#{order_id}",
        "currency": "EUR",
        "total_price": "20.00",
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": updated_at,
        "line_items": [
            {"id": order_id * 10, "sku": "BIKE-LIGHT", "quantity": 2, "price": "10.00"}
        ],
        **changes,
    }


def _intake(session, business, payload):
    source, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    return source, core.process_import_job(session, business.tenant.id, job.id)


def _count(session, business, model, *conditions):
    return session.scalar(
        select(func.count())
        .select_from(model)
        .where(model.tenant_id == business.tenant.id, *conditions)
    )


# --- P04 ---------------------------------------------------------------------


def test_a_source_cancellation_closes_the_line_with_the_source_as_its_reason(
    session, business
):
    """P04: the shop cancels afterwards; the line closes citing that source record.

    Before anything shipped the cancellation applies itself (spec 296). After a
    partial shipment it waits, and a person closes the open rest through the
    reviewed tool, citing the same record.
    """
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    _, interpreted = _intake(session, business, _order_payload(6101))
    commitment = interpreted[3][0]
    core.reserve(session, tenant, commitment.id)

    cancellation, applied = _intake(
        session,
        business,
        _order_payload(
            6101,
            updated_at="2026-09-02T09:00:00Z",
            cancelled_at="2026-09-02T09:00:00Z",
            cancel_reason="customer",
        ),
    )
    assert applied is not None
    assert record_by_id(session, Commitment, commitment.id).status == "cancelled"
    assert core.active_reserved(session, tenant, business.item.id) == 0
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "commitment.cancelled",
            BusinessEvent.subject_id == commitment.id,
        )
    ).one()
    assert event.source_record_id == cancellation.id
    assert json.loads(event.payload)["reason"] == "Cancelled in Shopify (customer)"

    # A second order ships one of two before the shop cancels it.
    _, interpreted = _intake(session, business, _order_payload(6102))
    shipped = interpreted[3][0]
    core.reserve(session, tenant, shipped.id)
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=shipped.id,
    )
    late, held = _intake(
        session,
        business,
        _order_payload(
            6102,
            updated_at="2026-09-03T09:00:00Z",
            cancelled_at="2026-09-03T09:00:00Z",
            cancel_reason="customer",
        ),
    )
    assert held is None
    coverage = core.interpretation_coverage(session, tenant, late.id)[0]
    assert coverage["current_classification"] == "needs_review"
    assert coverage["outcomes"][-1]["reason_code"] == "cancelled_after_shipment"
    assert record_by_id(session, Commitment, shipped.id).status == "open"

    proposal = prepare_delivery_action(
        session,
        tenant,
        "commitment_cancel",
        {
            "commitment_id": shipped.id,
            "reason": "Cancelled in the shop after one unit shipped",
            "source_record_id": late.id,
        },
        request_id="cancel-p04",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    assert record_by_id(session, Commitment, shipped.id).status == "cancelled"
    assert core.fulfilled_quantity(session, tenant, shipped.id) == 1
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "commitment.cancelled",
            BusinessEvent.subject_id == shipped.id,
        )
    ).one()
    assert event.source_record_id == late.id
    assert event.action_id == proposal.id


# --- P07 ---------------------------------------------------------------------


class _Clock:
    """Stands in for the wall clock `db.core.now()` reads when a source arrives."""

    def __init__(self, instant):
        self.instant = instant

    def now(self, tz=None):
        return self.instant


def test_a_day_long_outage_is_reported_and_its_backlog_arrives_without_duplicates(
    session, business, monkeypatch
):
    """P07: the shop goes quiet, then catches up, repeating what it already sent."""
    tenant = business.tenant.id
    system = core.create_source_system(session, tenant, "shopify", "Shopify")
    capability = core.create_source_capability(
        session, tenant, system.id, "order", "document"
    )
    clock = _Clock(datetime(2026, 9, 1, 9, tzinfo=UTC))
    monkeypatch.setattr(db_core, "datetime", clock)

    for day in range(7):
        clock.instant = datetime(2026, 9, 1, 9, tzinfo=UTC) + timedelta(days=day)
        _intake(session, business, _order_payload(7000 + day))
    last_arrival = clock.instant

    # Nothing for four days: the source is reported silent.
    silent = {
        row.record_id: row
        for row in operational_exceptions(
            session, tenant, as_of=last_arrival + timedelta(days=4)
        )
        if row.class_id == "silent_source"
    }
    assert silent[capability.id].causal_values["silent_hours"] == 96

    # It catches up: three new orders, and two it had already sent, twice over.
    clock.instant = last_arrival + timedelta(days=4, hours=1)
    for order_id in (7005, 7006, 7007, 7008, 7006, 7009):
        _intake(session, business, _order_payload(order_id))

    distinct = 10
    assert _count(session, business, SourceRecord) == distinct
    assert _count(session, business, Document, Document.type == "sales_order") == (
        distinct
    )
    assert (
        _count(session, business, Commitment, Commitment.type == "customer_delivery")
        == distinct
    )
    assert "silent_source" not in {
        row.class_id
        for row in operational_exceptions(
            session, tenant, as_of=clock.instant + timedelta(hours=1)
        )
    }
