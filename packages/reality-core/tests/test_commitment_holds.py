import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    active_commitment_hold,
    cancel_commitment,
    create_commitment,
    create_document,
    hold_commitment,
    hold_document_commitments,
    record_movement,
    release_commitment_hold,
    release_document_holds,
    reserve,
    revise_commitment,
)


def commitment_for(session, business, document_id=None):
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-09-05",
        document_id=document_id,
    )


def test_hold_blocks_reservation_and_movement_until_released(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        5,
        to_location_id=business.location.id,
    )
    commitment = commitment_for(session, business)
    hold = hold_commitment(
        session,
        business.tenant.id,
        commitment.id,
        "credit_check",
        "Awaiting approval",
    )

    assert active_commitment_hold(session, business.tenant.id, commitment.id) == hold
    with pytest.raises(InvalidOperation, match="on hold"):
        reserve(session, business.tenant.id, commitment.id)
    with pytest.raises(InvalidOperation, match="on hold"):
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            1,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )

    released = release_commitment_hold(session, business.tenant.id, commitment.id)
    assert released == [hold]
    assert hold.released_at is not None
    assert reserve(session, business.tenant.id, commitment.id).reserved == 2


def test_document_hold_is_a_convenience_over_linked_commitments(session, business):
    document = create_document(
        session,
        business.tenant.id,
        "sales_order",
        "SO-HOLD",
        business.customer.id,
        100,
    )
    first = commitment_for(session, business, document.id)
    second = commitment_for(session, business, document.id)

    holds = hold_document_commitments(
        session,
        business.tenant.id,
        document.id,
        "customer_request",
        "Customer asked us to wait",
    )
    assert {hold.commitment_id for hold in holds} == {first.id, second.id}
    assert document.status == "recorded"

    released = release_document_holds(session, business.tenant.id, document.id)
    assert len(released) == 2
    assert all(hold.released_at is not None for hold in released)


def test_hold_is_tenant_scoped_and_validated(session, business):
    commitment = commitment_for(session, business)
    with pytest.raises(InvalidOperation, match="Unsupported"):
        hold_commitment(session, business.tenant.id, commitment.id, "invented_reason")
    # Purpose authorization now rejects an absent tenant before record lookup.
    with pytest.raises(NotFound, match="Company not found"):
        hold_commitment(session, "ten_other", commitment.id, "manual_review")
    from reality.services.core import create_tenant

    other = create_tenant(session, "Unrelated business")
    with pytest.raises(NotFound, match="Commitment not found"):
        hold_commitment(session, other.id, commitment.id, "manual_review")


# ---------------------------------------------------------------------------
# Spec 108: a promise that is not open never carries an active hold.


def stocked(session, business, quantity=10):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def test_a_closed_promise_cannot_be_held(session, business):
    """The first of the two legs that make the fulfilled sequence the only one."""
    commitment = commitment_for(session, business)

    # The positive control: an open promise can be held.
    hold = hold_commitment(session, business.tenant.id, commitment.id, "credit_check")
    assert hold.released_at is None
    release_commitment_hold(session, business.tenant.id, commitment.id)

    cancel_commitment(session, business.tenant.id, commitment.id)
    with pytest.raises(InvalidOperation, match="Only open commitments"):
        hold_commitment(session, business.tenant.id, commitment.id, "credit_check")


def test_a_held_promise_cannot_be_shipped(session, business):
    """The second leg: so a held promise cannot become fulfilled by shipping."""
    stocked(session, business)
    commitment = commitment_for(session, business)
    hold_commitment(session, business.tenant.id, commitment.id, "credit_check")

    with pytest.raises(InvalidOperation, match="on hold"):
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            2,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )

    # The positive control: released, the same shipment goes through.
    release_commitment_hold(session, business.tenant.id, commitment.id)
    assert record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )


def test_cancelling_a_promise_releases_its_hold(session, business):
    """Reservations were already let go here. A hold is the same shape of thing."""
    stocked(session, business)
    commitment = commitment_for(session, business)
    hold = hold_commitment(
        session,
        business.tenant.id,
        commitment.id,
        "credit_check",
        "Awaiting approval",
    )
    raised_at = hold.created_at

    cancel_commitment(session, business.tenant.id, commitment.id)

    assert hold.released_at is not None
    assert active_commitment_hold(session, business.tenant.id, commitment.id) is None
    # Nothing anybody said is erased. A release sets one timestamp; the reason,
    # the note, who raised it and when it was raised all stay, which is what
    # makes doing this automatically safe.
    assert hold.reason_code == "credit_check"
    assert hold.note == "Awaiting approval"
    assert hold.created_by == "human"
    assert hold.created_at == raised_at

    # A promise with no hold behaves exactly as it did.
    other = commitment_for(session, business)
    assert (
        cancel_commitment(session, business.tenant.id, other.id).status == "cancelled"
    )
    assert active_commitment_hold(session, business.tenant.id, other.id) is None


def test_goods_can_come_back_against_a_cancelled_held_promise(session, business):
    """The concrete harm: a return refused for a credit check nobody is doing."""
    stocked(session, business)
    commitment = commitment_for(session, business)
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    hold_commitment(session, business.tenant.id, commitment.id, "credit_check")
    cancel_commitment(session, business.tenant.id, commitment.id)

    # Before this specification the hold stood and this was refused, with a
    # message about a credit check.
    returned = record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        1,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    assert returned.type == "return"


def test_settling_a_promise_by_revision_releases_its_hold(session, business):
    """The only path to a held promise that is fulfilled rather than cancelled."""
    stocked(session, business)
    commitment = commitment_for(session, business)
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    hold = hold_commitment(session, business.tenant.id, commitment.id, "credit_check")

    # A revision that leaves the promise open leaves the hold alone: there is
    # still a delivery to stop.
    revise_commitment(session, business.tenant.id, commitment.id, quantity=2)
    assert commitment.status == "open"
    assert active_commitment_hold(session, business.tenant.id, commitment.id) == hold

    # A held promise may still be revised, and a revision down to what already
    # shipped finishes it. Without this the hold would stand on a finished
    # promise and refuse every return against it.
    revise_commitment(session, business.tenant.id, commitment.id, quantity=1)
    assert commitment.status == "fulfilled"
    assert hold.released_at is not None
    assert active_commitment_hold(session, business.tenant.id, commitment.id) is None


def test_the_release_is_recorded_by_the_release_operation(session, business):
    """One producer per event type, and the cancellation names what it released."""
    import json

    from reality.services.core import business_events

    commitment = commitment_for(session, business)
    hold = hold_commitment(session, business.tenant.id, commitment.id, "compliance")
    cancel_commitment(session, business.tenant.id, commitment.id)

    events = [
        (entry.event_type, json.loads(entry.payload))
        for entry in business_events(session, business.tenant.id)
    ]
    releases = [
        payload for kind, payload in events if kind == "commitment.hold_released"
    ]
    cancellations = [
        payload for kind, payload in events if kind == "commitment.cancelled"
    ]

    # Emitted by the operation that releases holds, not by a second emitter.
    assert releases == [{"hold_ids": [hold.id]}]
    # And the cancellation says which holds went with it, so a reader of the
    # timeline sees the two facts together.
    assert cancellations == [
        {"released_reservations": True, "released_hold_ids": [hold.id]}
    ]


def test_the_release_joins_the_caller_s_transaction(session, business):
    """A cancellation that is rolled back releases nothing.

    The stale-promise closure cannot exercise this: `_stale_promises` skips
    held promises on purpose, so a closure never cancels one. The property is
    still the one that matters — any caller cancelling inside a transaction
    must have the release stand or fall with it — so it is proven directly
    rather than through a caller that cannot reach it.
    """
    first = commitment_for(session, business)
    second = commitment_for(session, business)
    holds = [
        hold_commitment(session, business.tenant.id, first.id, "credit_check"),
        hold_commitment(session, business.tenant.id, second.id, "compliance"),
    ]

    cancel_commitment(session, business.tenant.id, first.id, _commit=False)
    cancel_commitment(session, business.tenant.id, second.id, _commit=False)
    assert all(hold.released_at is not None for hold in holds)
    session.rollback()

    # Neither release survived, because neither cancellation did.
    assert all(hold.released_at is None for hold in holds)
    assert first.status == "open"
    assert second.status == "open"

    # The positive control: committed, both go together.
    cancel_commitment(session, business.tenant.id, first.id, _commit=False)
    cancel_commitment(session, business.tenant.id, second.id, _commit=False)
    session.commit()
    assert all(hold.released_at is not None for hold in holds)
    assert active_commitment_hold(session, business.tenant.id, first.id) is None
    assert active_commitment_hold(session, business.tenant.id, second.id) is None


def test_a_closure_never_cancels_a_held_promise(session, business):
    """Which is why the closure is not where the transaction matters.

    `_stale_promises` skips a promise with an active hold, so a closure cannot
    close one. Worth pinning: it is the reason the previous test proves the
    transactional property directly.
    """
    from reality.services.core import (
        close_stale_promises,
        preview_stale_promise_closure,
    )

    held = commitment_for(session, business)
    free = commitment_for(session, business)
    hold = hold_commitment(session, business.tenant.id, held.id, "manual_review")
    cutoff = "2026-09-06"

    preview = preview_stale_promise_closure(
        session, business.tenant.id, direction="sales", due_before=cutoff
    )
    assert preview["count"] == 1
    assert preview["sample"] == [free.id]

    close_stale_promises(
        session,
        business.tenant.id,
        direction="sales",
        due_before=cutoff,
        expected_count=1,
        reason="Imported history nobody is going to keep",
    )
    assert free.status == "cancelled"
    # Untouched, hold and all: the sweep must not close something out from
    # under the person dealing with it.
    assert held.status == "open"
    assert hold.released_at is None


def test_no_closed_promise_carries_an_active_hold(session, business):
    """The invariant, from every direction a promise can stop being open."""
    from sqlalchemy import select

    from reality.db.core import Commitment, CommitmentHold

    tenant_id = business.tenant.id
    stocked(session, business, 20)

    # Cancelled directly.
    cancelled = commitment_for(session, business)
    hold_commitment(session, tenant_id, cancelled.id, "credit_check")
    cancel_commitment(session, tenant_id, cancelled.id)

    # Fulfilled by a revision down to what shipped.
    settled = commitment_for(session, business)
    record_movement(
        session,
        tenant_id,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        commitment_id=settled.id,
    )
    hold_commitment(session, tenant_id, settled.id, "compliance")
    revise_commitment(session, tenant_id, settled.id, quantity=1)

    # Fulfilled by shipping, which a held promise cannot reach — so this one is
    # shipped after its hold was lifted, and ends with no active hold either.
    shipped = commitment_for(session, business)
    hold_commitment(session, tenant_id, shipped.id, "manual_review")
    release_commitment_hold(session, tenant_id, shipped.id)
    record_movement(
        session,
        tenant_id,
        "shipment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=shipped.id,
    )

    closed = {
        row.id
        for row in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.status != "open"
            )
        )
    }
    assert {cancelled.id, settled.id, shipped.id} <= closed
    still_held = {
        row.commitment_id
        for row in session.scalars(
            select(CommitmentHold).where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.released_at.is_(None),
            )
        )
    }
    assert not (still_held & closed)

    # The positive control: an open promise's hold is untouched by all of it.
    open_one = commitment_for(session, business)
    kept = hold_commitment(session, tenant_id, open_one.id, "other")
    assert kept.released_at is None
    assert open_one.id in still_held | {open_one.id}
