"""Catalog scenarios P04, P07 and the spec 296 shop changes (A09, A16, A17, F12, L04, L05): what a source says after the fact, and when it goes quiet.

Each story feeds stored Shopify payloads through the same intake the connector
uses, and closes what a person must decide through the reviewed tool.
"""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from conftest import record_by_id
from intake_review_support import (
    accept_import_job,
    accept_normalized_payment,
    accept_pending_import_jobs,
)
from sqlalchemy import func, select

from reality.db import core as db_core
from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    DocumentLine,
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
    return source, accept_import_job(session, business.tenant.id, job.id)


def _count(session, business, model, *conditions):
    return session.scalar(
        select(func.count())
        .select_from(model)
        .where(model.tenant_id == business.tenant.id, *conditions)
    )


# --- P04 ---------------------------------------------------------------------


def test_a_source_cancellation_closes_the_line_with_the_source_as_its_reason(
    session, business, scheduled_owner
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
    from reality.services.memberships import Principal

    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session, tenant, proposal.id, review_token=token, confirmed=True
        )
    assert refused.value.code == "case_source_unresolved"
    approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=token, confirmed=True,
        confirming_principal=Principal(scheduled_owner.id),
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
    accept_pending_import_jobs(session, tenant)

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
    accept_pending_import_jobs(session, tenant)

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


# --- Spec 314: out of order (P02), incomplete (P05), go-live (P08) -------------


def _classes(session, business, class_id):
    return {
        row.record_id
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def test_records_arriving_before_their_order_are_linked_once_it_is_in(
    session, business, monkeypatch
):
    """P02: a refund links itself on retry; a payment is offered by its reference."""
    from reality.db.core import ImportJob
    from reality.services import payment_intake
    from reality.services.finance.accounts import list_accounts
    from reality.services.payment_intake import NormalisedPayment, Reference
    from reality.tools.application import create_change_proposal

    tenant = business.tenant.id
    _stocked(session, business)
    clock = _Clock(datetime(2026, 9, 10, 9, tzinfo=UTC))
    monkeypatch.setattr(db_core, "datetime", clock)

    # The shop sends a refund for order 9701 before the order itself.
    refund, refund_job = core.enqueue_source(
        session,
        tenant,
        "shopify",
        "refund",
        "97011",
        _refund(97011, 9701, 97010, 1, "10.00", "no_restock"),
        context={},
    )
    assert accept_pending_import_jobs(session, tenant) == (0, 1)
    assert refund_job.id in _classes(session, business, "source_interpretation_failure")

    # The bank sends a payment naming order #9702, which is not in yet either.
    at = datetime(2026, 9, 10, 9, 30, tzinfo=UTC)
    reference = Reference(type="shop_order_number", value="#9702")
    payment_source, _ = core.enqueue_source(
        session,
        tenant,
        "bank_statement",
        "payment",
        "stmt-9702",
        {"references": [{"type": reference.type, "value": reference.value}]},
    )
    _, payment, _, allocation, resolution = accept_normalized_payment(
        session,
        tenant,
        payment_source,
        NormalisedPayment(
            party_id=business.customer.id,
            amount=Decimal("18.00"),
            currency="EUR",
            effective_at=at,
            external_payment_id="stmt-9702",
            references=(reference,),
            remittance_text="",
        ),
    )
    assert allocation is None
    assert resolution.reasons == ("no order #9702 for this customer",)

    # Both orders arrive; order #9702 is shipped and invoiced for 20.
    _intake(session, business, _order_payload(9701))
    _, interpreted = _intake(session, business, _order_payload(9702))
    line = interpreted[2][0]
    commitment = interpreted[3][0]
    _ship_line(session, business, commitment, "2")
    invoice = core.record_sales_invoice(
        session,
        tenant,
        lines=[{"order_line_id": line.id, "quantity": "2", "gross_amount": "20.00"}],
        gross_amount="20.00",
        number="RE-9702",
        effective_at=at + timedelta(hours=2),
    )
    invoice_id = next(
        row["id"] for row in invoice["records"] if row["family"] == "document"
    )

    # The retained failed preparation is explicitly retried and reviewed by its owner.
    clock.instant = clock.instant + timedelta(minutes=10)
    core.retry_import_job(session, tenant, refund_job.id)
    accept_pending_import_jobs(session, tenant)
    assert session.get(ImportJob, (tenant, refund_job.id)).status == "completed"
    (refunded,) = session.scalars(
        select(Document).where(
            Document.tenant_id == tenant,
            Document.type == "sales_refund",
            Document.source_record_id == refund.id,
        )
    )
    assert refunded.party_id == business.customer.id
    assert refund_job.id not in _classes(
        session, business, "source_interpretation_failure"
    )

    # The payment is short, so only its stated reference names the invoice.
    (candidate,) = payment_intake.payment_candidates(session, tenant, payment.id)
    assert (candidate.number, candidate.reasons) == (
        "RE-9702",
        ("stated reference names this invoice",),
    )
    # Positive control: until someone allocates it, the money is unallocated.
    assert payment_intake.unallocated_amount(session, tenant, payment.id) == 18
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "document_id": payment.id,
            "mode": "allocate_credit",
            "invoice_id": invoice_id,
            "amount": "18.00",
            "expected_revision": list_accounts(session, tenant)["revision"],
        },
        actor_type="human",
    )
    approve_and_execute_proposal(session, tenant, proposal.id)

    assert payment_intake.unallocated_amount(session, tenant, payment.id) == 0
    assert core.open_invoice_amount(session, tenant, invoice_id) == 2


def test_an_incomplete_shop_order_is_accepted_and_its_gap_reported(session, business):
    """P05: a line without a price is kept without one; no quantity fails visibly."""
    from reality.db.core import DocumentLine, ImportJob

    tenant = business.tenant.id
    unpriced = _order_payload(
        9801,
        line_items=[
            {"id": 98010, "sku": "BIKE-LIGHT", "quantity": 2, "price": "10.00"},
            {"id": 98011, "sku": "BIKE-LIGHT", "quantity": 1},
        ],
    )
    _, interpreted = _intake(session, business, unpriced)
    lines = {line.source_line_id: line for line in interpreted[2]}
    assert (lines["98010"].unit_price, lines["98011"].unit_price) == (10, None)
    assert len(interpreted[3]) == 2
    # Only the line without a price is reported; the priced line is the control.
    assert _classes(session, business, "order_line_price_missing") == {
        lines["98011"].id
    }
    stored = record_by_id(session, DocumentLine, lines["98011"].id)
    assert json.loads(stored.payload) == unpriced["line_items"][1]

    # An order line without a quantity stops only its own order.
    _, broken = core.enqueue_shopify_order(
        session,
        tenant,
        _order_payload(
            9802, line_items=[{"id": 98020, "sku": "BIKE-LIGHT", "price": "10.00"}]
        ),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    _, following = core.enqueue_shopify_order(
        session,
        tenant,
        _order_payload(9803),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    assert accept_pending_import_jobs(session, tenant) == (1, 1)
    failed = session.get(ImportJob, (tenant, broken.id))
    assert json.loads(failed.error)["reason_code"] == "source_line_quantity_missing"
    assert broken.id in _classes(session, business, "source_interpretation_failure")
    assert session.get(ImportJob, (tenant, following.id)).status == "completed"


def test_an_open_order_partly_delivered_before_go_live_is_traceable(
    session, business, tmp_path, monkeypatch
):
    """P08: the legacy order states 10, the promise is the open 6, both cite the source."""
    import csv

    from reality.services.artifacts import stage_artifact
    from reality.services.file_interpreters import suggested_mapping

    tenant = business.tenant.id
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    _stocked(session, business)
    legacy = tmp_path / "open_orders.csv"
    with legacy.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "order_id",
                "order_number",
                "line_id",
                "party_name",
                "sku",
                "quantity",
                "unit_price",
                "currency",
                "location",
                "requested_delivery_at",
                "delivered_quantity",
            ]
        )
        writer.writerow(
            [
                "L-4711",
                "AB-4711",
                "1",
                business.customer.name,
                business.item.sku,
                "10",
                "10.00",
                "EUR",
                business.location.name,
                "2026-09-15T00:00:00Z",
                "4",
            ]
        )
    columns = next(csv.reader(legacy.open(encoding="utf-8")))
    with legacy.open("rb") as handle:
        artifact, _ = stage_artifact(
            session, tenant, handle, filename=legacy.name, content_type="text/csv"
        )
    proposal = propose_tool(
        session,
        tenant,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "previous_erp",
            "source_type": "order",
            "expected_target": "sales_order",
            "column_mapping": suggested_mapping(columns, "sales_order"),
        },
    )
    job_id = json.loads(confirm_tool(session, tenant, proposal.id).output)[
        "import_job_id"
    ]
    accept_import_job(session, tenant, job_id)

    order = session.scalars(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "AB-4711"
        )
    ).one()
    legacy_source = record_by_id(session, SourceRecord, order.source_record_id)
    assert legacy_source.source_system == "previous_erp"
    commitment = session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant, Commitment.document_id == order.id
        )
    ).one()
    assert commitment.quantity == 10
    assert legacy_source.source_artifact_id == artifact.id
    legacy_line = session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == order.id
        )
    ).one()
    assert json.loads(legacy_line.payload)["delivered_quantity"] == "4"

    # At go-live a person states the open rest, citing the legacy record.
    receipt = _reviewed_revision(session, business, commitment, legacy_source)
    assert receipt["status"] == "executed"
    assert core.open_quantity(session, tenant, commitment.id) == 6
    revision = core.commitment_revisions(session, tenant, commitment.id)[-1]
    assert revision.source_record_id == legacy_source.id

    # Positive control: the open rest was due before today and is overdue.
    assert commitment.id in _classes(
        session, business, "overdue_outgoing_customer_commitment"
    )
    core.reserve(session, tenant, commitment.id)
    _ship_line(session, business, commitment, "6")
    # Positive control: the six shipped since go-live are unbilled until invoiced.
    unbilled = _classes(session, business, "shipped_not_billed")
    assert commitment.document_line_id in unbilled
    core.record_sales_invoice(
        session,
        tenant,
        lines=[
            {
                "order_line_id": commitment.document_line_id,
                "quantity": "6",
                "gross_amount": "60.00",
            }
        ],
        gross_amount="60.00",
        number="RE-4711",
    )
    # The four delivered before go-live are no one's open work.
    for class_id in ("shipped_not_billed", "overdue_outgoing_customer_commitment"):
        assert commitment.document_line_id not in _classes(session, business, class_id)
        assert commitment.id not in _classes(session, business, class_id)
    assert core.open_quantity(session, tenant, commitment.id) == 0


def _reviewed_revision(session, business, commitment, legacy_source):
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "commitment_revise",
        {
            "commitment_id": commitment.id,
            "quantity": "6",
            "source_record_id": legacy_source.id,
            "note": "4 delivered before go-live in the previous ERP",
        },
        request_id="p08-open-rest",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    return {"status": executed.status}
