import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, Commitment, Document, Movement
from reality.services.core import (
    InvalidOperation,
    cancel_commitment,
    close_stale_promises,
    create_commitment,
    create_tenant,
    hold_commitment,
    hold_party_delivery,
    preview_stale_promise_closure,
    record_movement,
    reserve,
)
from reality.services.exceptions import operational_exceptions

AS_OF = datetime(2026, 9, 1, 12, tzinfo=UTC)
CUTOFF = AS_OF - timedelta(days=30)


def promise(session, business, *, due_at=CUTOFF - timedelta(days=1), quantity=5):
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        due_at,
    )


def stock(session, business, quantity=200):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def preview(session, business, *, before=CUTOFF, direction="sales"):
    return preview_stale_promise_closure(
        session, business.tenant.id, direction=direction, due_before=before
    )


def close(session, business, count, *, before=CUTOFF, reason="Imported history"):
    return close_stale_promises(
        session,
        business.tenant.id,
        direction="sales",
        due_before=before,
        expected_count=count,
        reason=reason,
    )


def test_the_preview_states_what_would_close(session, business):
    stock(session, business)
    stale = [promise(session, business) for _ in range(3)]
    reserve(session, business.tenant.id, stale[0].id)
    promise(session, business, due_at=CUTOFF + timedelta(days=5))

    result = preview(session, business)

    # Only what is due before the date, and only the sales side.
    assert result["count"] == 3
    assert result["released_quantity"] == Decimal("5.0000")
    assert len(result["sample"]) <= result["count"]
    assert set(result["sample"]) <= {row.id for row in stale}

    # Criteria matching nothing report nothing rather than failing.
    empty = preview(session, business, before=CUTOFF - timedelta(days=3650))
    assert empty["count"] == 0
    assert empty["sample"] == []


def test_the_preview_writes_nothing(session, business):
    stock(session, business)
    standing = promise(session, business)
    reserve(session, business.tenant.id, standing.id)
    events_before = session.scalar(select(func.count(BusinessEvent.id)))

    preview(session, business)

    assert standing.status == "open"
    assert session.scalar(select(func.count(BusinessEvent.id))) == events_before


def test_a_promise_with_movement_is_never_closed(session, business):
    from reality.services.core import correct_movement

    stock(session, business)
    shipped = promise(session, business)
    untouched = promise(session, business)
    movement = record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=shipped.id,
    )

    # Something has happened against it, so it is work rather than residue.
    assert preview(session, business)["sample"] == [untouched.id]

    # Voiding that shipment means nothing ever moved, and it matches again.
    correct_movement(
        session,
        business.tenant.id,
        movement.id,
        reason="Recorded against the wrong order",
    )
    assert set(preview(session, business)["sample"]) == {shipped.id, untouched.id}


def test_only_open_dated_promises_match(session, business):
    stock(session, business)
    matching = promise(session, business)
    already_closed = promise(session, business)
    cancel_commitment(session, business.tenant.id, already_closed.id, reason="Test cancellation")
    promise(session, business, due_at=None)

    # A cancelled promise and a dateless one are somebody else's business.
    assert preview(session, business)["sample"] == [matching.id]


def test_a_held_promise_is_never_closed(session, business):
    stock(session, business)
    matching = promise(session, business)
    held = promise(session, business)
    hold_commitment(session, business.tenant.id, held.id, reason_code="credit_check")

    # A hold is a person saying they are dealing with this.
    assert preview(session, business)["sample"] == [matching.id]

    # And a party under a delivery hold takes its promises with it.
    hold_party_delivery(
        session, business.tenant.id, business.customer.id, reason_code="credit_check"
    )
    assert preview(session, business)["count"] == 0


def test_a_stale_count_refuses_the_closure(session, business):
    stock(session, business)
    promises = [promise(session, business) for _ in range(3)]

    with pytest.raises(InvalidOperation, match="count"):
        close(session, business, 2)

    # Nothing closed, so a refused closure leaves no half-cleared wall.
    assert all(row.status == "open" for row in promises)


def test_a_closure_requires_a_reason(session, business):
    stock(session, business)
    promise(session, business)

    with pytest.raises(InvalidOperation, match="reason"):
        close(session, business, 1, reason="   ")

    # The same call with one succeeds.
    assert close(session, business, 1)["closed"] == 1


def test_closing_nothing_is_not_a_failure(session, business):
    stock(session, business)
    promise(session, business)
    close(session, business, 1)

    # Running the same closure again is safe rather than an error.
    assert close(session, business, 0)["closed"] == 0


def test_closing_clears_the_wall(session, business):
    stock(session, business)
    promises = [promise(session, business) for _ in range(3)]
    reserve(session, business.tenant.id, promises[0].id)
    documents_before = session.scalar(select(func.count(Document.id)))
    movements_before = session.scalar(select(func.count(Movement.id)))

    result = close(session, business, 3)

    assert result["closed"] == 3
    assert all(row.status == "cancelled" for row in promises)
    assert all(row.cancelled_at is not None for row in promises)

    # The queue falls silent for them, which is the point.
    classes = [
        row.class_id
        for row in operational_exceptions(session, business.tenant.id, as_of=AS_OF)
    ]
    assert "overdue_outgoing_customer_commitment" not in classes

    # And nothing a source said was touched.
    assert session.scalar(select(func.count(Document.id))) == documents_before
    assert session.scalar(select(func.count(Movement.id))) == movements_before


def test_the_act_is_recorded_once(session, business):
    stock(session, business)
    for _ in range(2):
        promise(session, business)

    close(session, business, 2, reason="Imported from the old system")

    event = session.scalars(
        select(BusinessEvent).where(BusinessEvent.event_type == "promises.closed")
    ).one()
    payload = json.loads(event.payload)

    assert payload["reason"] == "Imported from the old system"
    assert payload["closed"] == 2
    assert payload["direction"] == "sales"
    assert payload["due_before"]
    # Identities, not restated business fields.
    assert len(payload["commitment_ids"]) == 2


def test_a_closure_is_tenant_scoped(session, business):
    stock(session, business)
    mine = promise(session, business)

    foreign = create_tenant(session, "Foreign closure tenant")
    from reality.services.core import create_item, create_location, create_party

    other_company = create_party(session, foreign.id, "Other GmbH", "company")
    other_customer = create_party(session, foreign.id, "Other Kunde GmbH", "customer")
    other_item = create_item(session, foreign.id, "OTHER-1", "Other Item")
    other_location = create_location(session, foreign.id, "Other Warehouse")
    theirs = create_commitment(
        session,
        foreign.id,
        "customer_delivery",
        other_company.id,
        other_customer.id,
        other_item.id,
        other_location.id,
        5,
        CUTOFF - timedelta(days=1),
    )

    close(session, business, 1)

    assert mine.status == "cancelled"
    assert theirs.status == "open"
    assert (
        session.scalar(
            select(func.count(Commitment.id)).where(
                Commitment.tenant_id == foreign.id, Commitment.status == "cancelled"
            )
        )
        == 0
    )
