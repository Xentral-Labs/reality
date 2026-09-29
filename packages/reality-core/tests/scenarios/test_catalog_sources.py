"""Catalog scenarios P04, P07 and the spec 296 shop changes (A09, A16, A17, F12, L04, L05): what a source says after the fact, and when it goes quiet.

Each story feeds stored Shopify payloads through the same intake the connector
uses, and closes what a person must decide through the reviewed tool.
"""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from conftest import record_by_id
from sqlalchemy import func, select

from reality.db import core as db_core
from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    LedgerEntry,
    ReturnAnnouncement,
    SourceRecord,
)
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    propose_tool,
)


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


# --- Spec 296: shop order changes and refunds (A16, L05, A09, L04, F12, A17) ----


def _shop_order(order_id, *, updated_at="2026-09-10T10:00:00Z", lines=None, **changes):
    return {
        "id": order_id,
        "name": f"#{order_id}",
        "currency": "EUR",
        "total_price": "80.00",
        "created_at": "2026-09-10T10:00:00Z",
        "updated_at": updated_at,
        "line_items": lines
        if lines is not None
        else [
            {
                "id": order_id * 10 + 1,
                "sku": "BIKE-LIGHT",
                "quantity": 5,
                "price": "10.00",
            },
            {
                "id": order_id * 10 + 2,
                "sku": "BIKE-LIGHT",
                "quantity": 3,
                "price": "10.00",
            },
        ],
        **changes,
    }


def _stocked(session, business, quantity="20"):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def _ship_line(session, business, commitment, quantity):
    core.reserve(session, business.tenant.id, commitment.id)
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )


def _latest_outcome(session, business, source):
    return core.interpretation_coverage(session, business.tenant.id, source.id)[0][
        "outcomes"
    ][-1]


def test_a_new_shop_version_revises_the_promise_and_keeps_the_old_version(
    session, business
):
    """A16: a second version lowers a line; the first stays as evidence."""
    _stocked(session, business)
    first, interpreted = _intake(session, business, _shop_order(9601))
    order, (line_a, line_b) = interpreted[1], interpreted[3]
    core.reserve(session, business.tenant.id, line_a.id)

    second, applied = _intake(
        session,
        business,
        _shop_order(
            9601,
            updated_at="2026-09-11T10:00:00Z",
            lines=[
                {
                    "id": 96011,
                    "sku": "BIKE-LIGHT",
                    "quantity": 5,
                    "current_quantity": 3,
                    "price": "10.00",
                },
                {"id": 96012, "sku": "BIKE-LIGHT", "quantity": 3, "price": "10.00"},
            ],
        ),
    )

    assert applied is not None and applied[1].id == order.id
    assert second.supersedes_source_record_id == first.id
    assert json.loads(first.payload)["line_items"][0]["quantity"] == 5
    assert core.commitment_quantity(session, business.tenant.id, line_a.id) == 3
    assert core.commitment_quantity(session, business.tenant.id, line_b.id) == 3
    assert core.active_reserved(session, business.tenant.id, business.item.id) == 3
    revised = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.event_type == "commitment.revised",
            BusinessEvent.subject_id == line_a.id,
        )
    ).one()
    assert revised.source_record_id == second.id
    assert _count(session, business, Document, Document.type == "sales_order") == 1


def test_an_edited_shopify_order_applies_a_removed_line_and_holds_an_added_one(
    session, business
):
    """L05: an edit removing a line applies; an edit adding one waits for a person."""
    _stocked(session, business)
    _, interpreted = _intake(session, business, _shop_order(9602))
    line_a, line_b = interpreted[3]

    _, applied = _intake(
        session,
        business,
        _shop_order(
            9602,
            updated_at="2026-09-11T10:00:00Z",
            lines=[{"id": 96021, "sku": "BIKE-LIGHT", "quantity": 5, "price": "10.00"}],
        ),
    )
    assert applied is not None
    assert record_by_id(session, Commitment, line_b.id).status == "cancelled"

    # Positive control for the other direction: an added line is held, nothing changes.
    added, held = _intake(
        session,
        business,
        _shop_order(
            9602,
            updated_at="2026-09-12T10:00:00Z",
            lines=[
                {"id": 96021, "sku": "BIKE-LIGHT", "quantity": 5, "price": "10.00"},
                {"id": 96023, "sku": "BIKE-LIGHT", "quantity": 2, "price": "10.00"},
            ],
        ),
    )
    assert held is None
    assert _latest_outcome(session, business, added)["reason_code"] == "line_added"
    assert record_by_id(session, Commitment, line_a.id).status == "open"
    assert core.commitment_quantity(session, business.tenant.id, line_a.id) == 5


def test_a_cancellation_after_shipment_becomes_an_expected_return(session, business):
    """A09: the shop cancels shipped goods; they are expected back, nothing is cancelled."""
    tenant = business.tenant.id
    _stocked(session, business)
    _, interpreted = _intake(session, business, _shop_order(9603))
    line_a, line_b = interpreted[3]
    _ship_line(session, business, line_a, "5")
    _ship_line(session, business, line_b, "3")

    cancellation, held = _intake(
        session,
        business,
        _shop_order(
            9603,
            updated_at="2026-09-12T10:00:00Z",
            cancelled_at="2026-09-12T10:00:00Z",
            cancel_reason="customer",
        ),
    )

    assert held is None
    outcome = _latest_outcome(session, business, cancellation)
    assert outcome["reason_code"] == "cancelled_after_shipment"
    assert "return_announce" in outcome["summary"]
    assert {
        record_by_id(session, Commitment, line.id).status for line in (line_a, line_b)
    } == {"fulfilled"}

    proposal = propose_tool(
        session,
        tenant,
        "return_announce",
        {
            "commitment_id": line_a.id,
            "quantity": "5",
            "reference": f"Shopify cancellation {cancellation.external_id}",
            "reason": "Cancelled in the shop after shipment",
        },
    )
    confirm_tool(session, tenant, proposal.id)

    (announcement,) = session.scalars(
        select(ReturnAnnouncement).where(ReturnAnnouncement.commitment_id == line_a.id)
    ).all()
    assert announcement.quantity == 5
    assert record_by_id(session, Commitment, line_a.id).status == "fulfilled"


def _refund(refund_id, order_id, line_id, quantity, amount, restock):
    return {
        "id": refund_id,
        "order_id": order_id,
        "created_at": "2026-09-13T10:00:00Z",
        "refund_line_items": [
            {
                "id": refund_id * 10,
                "line_item_id": line_id,
                "quantity": quantity,
                "restock_type": restock,
                "subtotal": amount,
            }
        ],
        "transactions": [
            {
                "id": refund_id * 100,
                "kind": "refund",
                "status": "success",
                "amount": amount,
                "currency": "EUR",
            }
        ],
    }


def test_a_partial_shopify_refund_is_recorded_from_its_source(session, business):
    """L04: a partial refund becomes evidence on the order, with no posting."""
    tenant = business.tenant.id
    _stocked(session, business)
    _, interpreted = _intake(session, business, _shop_order(9604))
    order, (line_a, _) = interpreted[1], interpreted[3]
    _ship_line(session, business, line_a, "5")

    version, _ = _intake(
        session,
        business,
        _shop_order(
            9604,
            updated_at="2026-09-13T10:00:00Z",
            refunds=[_refund(9641, 9604, 96041, 1, "10.00", "no_restock")],
        ),
    )
    core.process_pending_import_jobs(session, tenant)

    (refund,) = session.scalars(
        select(Document).where(
            Document.tenant_id == tenant, Document.type == "sales_refund"
        )
    ).all()
    assert (refund.gross_amount, refund.party_id) == (Decimal("10.00"), order.party_id)
    source = record_by_id(session, SourceRecord, refund.source_record_id)
    assert (source.source_system, source.source_type, source.external_id) == (
        "shopify",
        "refund",
        "9641",
    )
    assert json.loads(source.payload)["order_id"] == 9604
    assert (
        _count(session, business, LedgerEntry, LedgerEntry.document_id == refund.id)
        == 0
    )
    # The order version carrying it changed nothing else.
    assert (
        _latest_outcome(session, business, version)["classification"] == "interpreted"
    )
    assert _count(session, business, ReturnAnnouncement) == 0


def test_a_refund_before_the_goods_come_back_keeps_the_return_expected(
    session, business
):
    """F12: refund and return are independent; the goods stay expected until they arrive."""
    tenant = business.tenant.id
    _stocked(session, business)
    _, interpreted = _intake(session, business, _shop_order(9605))
    line_a, _ = interpreted[3]
    _ship_line(session, business, line_a, "5")

    _intake(
        session,
        business,
        _shop_order(
            9605,
            updated_at="2026-09-13T10:00:00Z",
            refunds=[_refund(9651, 9605, 96051, 2, "20.00", "return")],
        ),
    )
    core.process_pending_import_jobs(session, tenant)

    (announcement,) = session.scalars(
        select(ReturnAnnouncement).where(ReturnAnnouncement.commitment_id == line_a.id)
    ).all()
    assert (announcement.quantity, announcement.reference) == (2, "Refund 9651")
    assert core.announcement_outstanding(session, tenant, announcement) == 2
    # No credit exists, so the refund raises no credit finding of its own.
    classes = {row.class_id for row in operational_exceptions(session, tenant)}
    assert "credited_not_returned" not in classes

    core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "2",
        to_location_id=business.location.id,
        commitment_id=line_a.id,
        return_announcement_id=announcement.id,
    )

    assert core.announcement_outstanding(session, tenant, announcement) == 0


def test_a_shop_order_with_an_unknown_item_keeps_the_known_lines(session, business):
    """A17: the known line is promised; the unknown one is kept and visible until assigned."""
    tenant = business.tenant.id
    _stocked(session, business)
    _, result = _intake(
        session,
        business,
        _shop_order(
            9606,
            lines=[
                {"id": 96061, "sku": "BIKE-LIGHT", "quantity": 2, "price": "10.00"},
                {"id": 96062, "sku": "HELMET-M", "quantity": 1, "price": "40.00"},
            ],
        ),
    )
    order, lines, promises = result[1], result[2], result[3]
    assert len(lines) == 2 and len(promises) == 1
    unknown = next(line for line in lines if line.sku == "HELMET-M")
    findings = [
        row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "order_line_item_unknown"
    ]
    assert [row.record_id for row in findings] == [unknown.id]

    helmet = core.create_item(session, tenant, "HELMET-M-01", "Helmet M")
    proposal = prepare_delivery_action(
        session,
        tenant,
        "order_line_item_assign",
        {"document_line_id": unknown.id, "item_id": helmet.id},
        request_id="a17-assign",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True
    )

    promise = session.scalars(
        select(Commitment).where(Commitment.document_line_id == unknown.id)
    ).one()
    assert (promise.item_id, promise.quantity) == (helmet.id, 1)
    assert promise.to_party_id == order.party_id
    assert "order_line_item_unknown" not in {
        row.class_id for row in operational_exceptions(session, tenant)
    }
