"""Spec 296: a later Shopify order version applies only reductions of unshipped quantity."""

from decimal import Decimal

import pytest
from conftest import record_by_id
from intake_review_support import accept_import_job, reviewed_reserve
from sqlalchemy import func, select

from reality.db.core import (
    BusinessEvent,
    Commitment,
    CommitmentRevision,
    InterpretationOutcome,
)
from reality.services import core
from reality.services.shop_order_changes import stated_lines

LINE_A, LINE_B = 11, 12


def _payload(*, updated_at="2026-09-01T10:00:00Z", lines=None, **changes):
    return {
        "id": 5101,
        "name": "#5101",
        "currency": "EUR",
        "total_price": "150.00",
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": updated_at,
        "shipping_address": {"address1": "Hauptstr. 1", "city": "Augsburg"},
        "line_items": lines
        if lines is not None
        else [
            {"id": LINE_A, "sku": "BIKE-LIGHT", "quantity": 10, "price": "10.00"},
            {"id": LINE_B, "sku": "BIKE-LIGHT", "quantity": 5, "price": "10.00"},
        ],
        **changes,
    }


def _line(line_id, quantity, *, price="10.00", **extra):
    return {
        "id": line_id,
        "sku": "BIKE-LIGHT",
        "quantity": quantity,
        "price": price,
        **extra,
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


_versions = iter(range(2, 1000))


def _version(session, business, lines=None, **changes):
    """A later version of order 5101, one minute after the previous one."""
    minute = next(_versions)
    return _intake(
        session,
        business,
        _payload(
            updated_at=f"2026-09-02T10:{minute % 60:02d}:{minute // 60:02d}Z",
            lines=lines,
            **changes,
        ),
    )


def _outcome(session, business, source):
    return session.scalars(
        select(InterpretationOutcome)
        .where(
            InterpretationOutcome.tenant_id == business.tenant.id,
            InterpretationOutcome.source_record_id == source.id,
        )
        .order_by(InterpretationOutcome.attempt.desc())
    ).first()


def _stock(session, business, quantity="100"):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def _order(session, business):
    _stock(session, business)
    _, interpreted = _intake(session, business, _payload())
    first, second = interpreted[3]
    return first, second


def _ship(session, business, commitment, quantity):
    reviewed_reserve(session, business.tenant.id, commitment.id)
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )


def _quantity(session, business, commitment):
    return core.commitment_quantity(session, business.tenant.id, commitment.id)


def _status(session, commitment):
    session.expire_all()
    return record_by_id(session, Commitment, commitment.id).status


# --- T005: what a version states ------------------------------------------------


def test_the_stated_quantity_is_the_current_quantity_when_the_shop_sends_it():
    lines = stated_lines(
        {
            "line_items": [
                _line(1, 10, current_quantity=7),
                _line(2, 4),
                _line(3, 3, current_quantity=0),
            ]
        }
    )

    assert {line_id: line["quantity"] for line_id, line in lines.items()} == {
        "1": Decimal(7),
        "2": Decimal(4),
        "3": Decimal(0),
    }
    assert lines["1"]["price"] == Decimal("10.00")


# --- T008: reductions of unshipped quantity apply themselves -------------------


def test_a_lowered_open_line_revises_its_promise_and_cites_the_version(
    session, business
):
    first, second = _order(session, business)
    reviewed_reserve(session, business.tenant.id, first.id)
    assert core.active_reserved(session, business.tenant.id, business.item.id) == 10

    source, result = _version(
        session, business, [_line(LINE_A, 10, current_quantity=6), _line(LINE_B, 5)]
    )

    assert _outcome(session, business, source).classification == "interpreted"
    assert result is not None
    assert _quantity(session, business, first) == 6
    assert _quantity(session, business, second) == 5
    assert core.active_reserved(session, business.tenant.id, business.item.id) == 6
    revision = session.scalars(
        select(CommitmentRevision).where(CommitmentRevision.commitment_id == first.id)
    ).one()
    assert revision.source_record_id == source.id


def test_a_line_lowered_to_what_shipped_closes_its_rest(session, business):
    first, _ = _order(session, business)
    _ship(session, business, first, "4")

    source, _ = _version(
        session, business, [_line(LINE_A, 10, current_quantity=4), _line(LINE_B, 5)]
    )

    assert _outcome(session, business, source).classification == "interpreted"
    assert _status(session, first) == "fulfilled"
    assert core.open_quantity(session, business.tenant.id, first.id) == 0


def test_a_removed_open_line_is_cancelled_citing_the_version(session, business):
    first, second = _order(session, business)

    source, _ = _version(session, business, [_line(LINE_A, 10)])

    assert _outcome(session, business, source).classification == "interpreted"
    assert _status(session, second) == "cancelled"
    assert _status(session, first) == "open"
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.event_type == "commitment.cancelled",
            BusinessEvent.subject_id == second.id,
        )
    ).one()
    assert event.source_record_id == source.id


def test_a_cancellation_with_nothing_shipped_cancels_every_line(session, business):
    first, second = _order(session, business)
    reviewed_reserve(session, business.tenant.id, first.id)

    source, _ = _version(
        session,
        business,
        cancelled_at="2026-09-02T12:00:00Z",
        cancel_reason="customer",
    )

    assert _outcome(session, business, source).classification == "interpreted"
    assert {_status(session, first), _status(session, second)} == {"cancelled"}
    assert core.active_reserved(session, business.tenant.id, business.item.id) == 0


def test_a_change_to_uninterpreted_fields_applies_nothing(session, business):
    first, _second = _order(session, business)
    revisions = session.scalar(select(func.count()).select_from(CommitmentRevision))

    source, _ = _version(session, business, note="Please ring twice", tags="vip")

    assert _outcome(session, business, source).classification == "interpreted"
    assert session.scalar(select(func.count()).select_from(CommitmentRevision)) == (
        revisions
    )
    # Positive control: the same kind of version with a lower quantity does apply.
    _version(
        session,
        business,
        [_line(LINE_A, 10, current_quantity=9), _line(LINE_B, 5)],
        note="Please ring twice",
    )
    assert _quantity(session, business, first) == 9


def test_replaying_an_applied_version_changes_nothing(session, business):
    first, _ = _order(session, business)
    source, _ = _version(
        session, business, [_line(LINE_A, 10, current_quantity=6), _line(LINE_B, 5)]
    )
    job = session.scalars(
        select(core.ImportJob).where(core.ImportJob.source_record_id == source.id)
    ).one()

    accept_import_job(session, business.tenant.id, job.id)

    assert (
        session.scalar(
            select(func.count())
            .select_from(CommitmentRevision)
            .where(CommitmentRevision.commitment_id == first.id)
        )
        == 1
    )


def test_an_older_version_never_undoes_a_newer_one(session, business):
    first, _ = _order(session, business)
    _newer, _ = _version(
        session, business, [_line(LINE_A, 10, current_quantity=5), _line(LINE_B, 5)]
    )
    older, _ = _intake(
        session,
        business,
        _payload(
            updated_at="2026-09-02T09:00:00Z",
            lines=[_line(LINE_A, 10, current_quantity=8), _line(LINE_B, 5)],
        ),
    )

    assert _outcome(session, business, older).classification == "stale"
    assert _quantity(session, business, first) == 5


def test_a_superseded_version_processed_late_applies_nothing(session, business):
    first, _ = _order(session, business)
    v2, job2 = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        _payload(
            updated_at="2026-09-02T10:00:00Z",
            lines=[_line(LINE_A, 10, current_quantity=8), _line(LINE_B, 5)],
        ),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    _v3, job3 = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        _payload(
            updated_at="2026-09-02T11:00:00Z",
            lines=[_line(LINE_A, 10, current_quantity=6), _line(LINE_B, 5)],
        ),
        business.company.id,
        business.customer.id,
        business.location.id,
    )

    accept_import_job(session, business.tenant.id, job3.id)
    with pytest.raises(core.InvalidOperation, match="reviewed intake state"):
        accept_import_job(session, business.tenant.id, job2.id)

    assert _outcome(session, business, v2).classification == "failed"
    assert _outcome(session, business, v2).reason_code == "intake_review_stale"
    assert _quantity(session, business, first) == 6


# --- T009: everything else waits, all or nothing --------------------------------


def _held(session, business, source):
    outcome = _outcome(session, business, source)
    assert outcome.classification == "needs_review"
    return outcome


@pytest.mark.parametrize(
    ("lines", "changes", "code"),
    [
        ([_line(LINE_A, 12), _line(LINE_B, 5)], {}, "quantity_increased"),
        (
            [_line(LINE_A, 10), _line(LINE_B, 5), _line(13, 1)],
            {},
            "line_added",
        ),
        ([_line(LINE_A, 10, price="9.00"), _line(LINE_B, 5)], {}, "price_changed"),
        (
            None,
            {"shipping_address": {"address1": "Nebenstr. 2", "city": "Ulm"}},
            "address_changed",
        ),
        (None, {"currency": "CHF"}, "currency_changed"),
    ],
)
def test_a_change_that_is_not_a_reduction_waits_with_its_code(
    session, business, lines, changes, code
):
    first, second = _order(session, business)

    source, result = _version(session, business, lines, **changes)

    assert result is None
    outcome = _held(session, business, source)
    assert outcome.reason_code == code
    assert code in outcome.summary
    assert (
        _quantity(session, business, first),
        _quantity(session, business, second),
    ) == (
        10,
        5,
    )


def test_a_cancellation_after_shipment_waits_and_cancels_nothing(session, business):
    first, second = _order(session, business)
    _ship(session, business, first, "10")

    source, _ = _version(
        session, business, cancelled_at="2026-09-03T08:00:00Z", cancel_reason="customer"
    )

    outcome = _held(session, business, source)
    assert outcome.reason_code == "cancelled_after_shipment"
    assert "return_announce" in outcome.summary
    assert _status(session, second) == "open"


def test_a_line_lowered_below_what_shipped_waits(session, business):
    first, _ = _order(session, business)
    _ship(session, business, first, "6")

    source, _ = _version(
        session, business, [_line(LINE_A, 10, current_quantity=4), _line(LINE_B, 5)]
    )

    assert _held(session, business, source).reason_code == "reduces_shipped_quantity"
    assert _quantity(session, business, first) == 10


def test_a_change_to_a_closed_line_waits(session, business):
    _first, second = _order(session, business)
    core.cancel_commitment(session, business.tenant.id, second.id, reason="Test")

    source, _ = _version(
        session, business, [_line(LINE_A, 10), _line(LINE_B, 5, current_quantity=3)]
    )

    assert _held(session, business, source).reason_code == "closed_line_changed"


def test_a_reduction_needing_a_reservation_choice_waits(session, business):
    tenant = business.tenant.id
    tracked = reviewed_create_item(
        session, tenant, "TRACKED-LIGHT", "Tracked light", tracking_type="lot"
    )
    lots = [core.create_lot(session, tenant, tracked.id, name) for name in ("A", "B")]
    for lot in lots:
        core.record_movement(
            session,
            tenant,
            "opening_stock",
            tracked.id,
            "5",
            to_location_id=business.location.id,
            lot_id=lot.id,
        )
    lines = [
        {"id": LINE_A, "sku": "TRACKED-LIGHT", "quantity": 10, "price": "10.00"},
    ]
    _, interpreted = _intake(session, business, _payload(lines=lines))
    first = interpreted[3][0]
    for lot in lots:
        reviewed_reserve(session, tenant, first.id, "5", lot_id=lot.id)

    source, _ = _version(
        session,
        business,
        [{**lines[0], "current_quantity": 7}],
    )

    assert _held(session, business, source).reason_code == "reservation_choice_required"
    assert _quantity(session, business, first) == 10


def test_a_mixed_version_applies_nothing_and_names_every_code(session, business):
    first, second = _order(session, business)

    source, _ = _version(
        session,
        business,
        [_line(LINE_A, 10, current_quantity=4), _line(LINE_B, 8)],
        shipping_address={"address1": "Nebenstr. 2", "city": "Ulm"},
    )

    outcome = _held(session, business, source)
    assert outcome.reason_code == "shopify_changes_require_review"
    assert "quantity_increased" in outcome.summary
    assert "address_changed" in outcome.summary
    # The lowered line is not applied on its own.
    assert _quantity(session, business, first) == 10
    assert _quantity(session, business, second) == 5


def test_the_source_inspector_says_why_a_change_waits(session, business):
    from reality.services.delivery_reads import delivery_evidence

    _order(session, business)
    source, _ = _version(session, business, [_line(LINE_A, 12), _line(LINE_B, 5)])

    rows = {
        row["label"]: row["value"]
        for section in delivery_evidence(
            session, business.tenant.id, "source_record", source.id
        )["sections"]
        for row in section["rows"]
    }

    assert rows["Reason"] == "quantity_increased"
    assert "quantity_increased (line 11)" in rows["Why it waits"]


def test_a_removed_line_left_out_again_is_no_change(session, business):
    """Regression (A16/L05 story): the next version must not trip over the removed line."""
    first, second = _order(session, business)
    _version(session, business, [_line(LINE_A, 10)])
    assert _status(session, second) == "cancelled"

    source, _ = _version(session, business, [_line(LINE_A, 10, current_quantity=8)])

    assert _outcome(session, business, source).classification == "interpreted"
    assert _quantity(session, business, first) == 8


# --- Review round (T024) ------------------------------------------------------------


def test_a_redelivered_version_never_undoes_a_persons_later_revision(session, business):
    first, _ = _order(session, business)
    payload = _payload(
        updated_at="2026-09-02T10:00:00Z",
        lines=[_line(LINE_A, 10, current_quantity=6), _line(LINE_B, 5)],
    )
    source, _ = _intake(session, business, payload)
    assert _quantity(session, business, first) == 6

    for quantity in (8, 4):
        core.revise_commitment(
            session, business.tenant.id, first.id, quantity=quantity, note="Phoned"
        )
        # The webhook delivers the same version again, and a person retries its job.
        _intake(session, business, payload)
        job = session.scalars(
            select(core.ImportJob).where(core.ImportJob.source_record_id == source.id)
        ).one()
        core.retry_import_job(session, business.tenant.id, job.id)
        accept_import_job(session, business.tenant.id, job.id)
        assert _quantity(session, business, first) == quantity


def test_an_address_change_is_held_once_and_does_not_block_a_later_cancellation(
    session, business
):
    first, second = _order(session, business)
    moved = {"address1": "Nebenstr. 2", "city": "Ulm"}
    held, _ = _version(session, business, None, shipping_address=moved)
    assert _outcome(session, business, held).reason_code == "address_changed"

    source, _ = _version(
        session,
        business,
        None,
        shipping_address=moved,
        cancelled_at="2026-09-03T00:00:00Z",
    )

    assert _outcome(session, business, source).classification == "interpreted"
    assert {_status(session, first), _status(session, second)} == {"cancelled"}


def test_a_later_version_after_a_held_price_change_is_not_held_for_it(
    session, business
):
    first, _ = _order(session, business)
    priced = [_line(LINE_A, 10, price="9.00"), _line(LINE_B, 5)]
    held, _ = _version(session, business, priced)
    assert _outcome(session, business, held).reason_code == "price_changed"

    source, _ = _version(
        session,
        business,
        [_line(LINE_A, 10, price="9.00", current_quantity=7), _line(LINE_B, 5)],
    )

    assert _outcome(session, business, source).classification == "interpreted"
    assert _quantity(session, business, first) == 7


def test_geocoded_address_fields_are_no_address_change(session, business):
    first, _ = _order(session, business)
    geocoded = {
        "address1": "Hauptstr. 1",
        "city": "Augsburg",
        "latitude": 48.37,
        "longitude": 10.89,
    }

    source, _ = _version(
        session,
        business,
        [_line(LINE_A, 10, current_quantity=9), _line(LINE_B, 5)],
        shipping_address=geocoded,
    )

    assert _outcome(session, business, source).classification == "interpreted"
    assert _quantity(session, business, first) == 9


def test_a_refunded_shipped_line_does_not_block_later_versions(session, business):
    first, second = _order(session, business)
    _ship(session, business, first, "10")
    refund = {
        "id": 931,
        "refund_line_items": [
            {"line_item_id": LINE_A, "quantity": 2, "restock_type": "return"}
        ],
    }

    # Should Shopify lower current_quantity for refunded shipped goods, the kept
    # promise must not read as a reduction below what shipped.
    source, _ = _version(
        session,
        business,
        [_line(LINE_A, 10, current_quantity=8), _line(LINE_B, 5, current_quantity=3)],
        refunds=[refund],
    )

    assert _outcome(session, business, source).classification == "interpreted"
    assert _quantity(session, business, second) == 3


from intake_review_support import reviewed_create_item
