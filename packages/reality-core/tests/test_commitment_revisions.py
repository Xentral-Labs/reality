from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    cancel_commitment,
    commitment_due_at,
    commitment_quantity,
    commitment_revisions,
    create_commitment,
    create_tenant,
    fulfilled_quantity,
    hold_commitment,
    open_quantity,
    record_movement,
    revise_commitment,
)

ORIGINAL = datetime(2026, 7, 10, 12, tzinfo=UTC)
REVISED = datetime(2026, 7, 24, 12, tzinfo=UTC)


def promise(session, business, *, kind="supplier_delivery", due=ORIGINAL, quantity=10):
    return create_commitment(
        session,
        business.tenant.id,
        kind,
        business.supplier.id if kind == "supplier_delivery" else business.company.id,
        business.company.id if kind == "supplier_delivery" else business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        due,
    )


def test_a_new_date_never_erases_the_old_one(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business)

    revision = revise_commitment(
        session,
        tenant_id,
        commitment.id,
        REVISED,
        note="Acknowledged two weeks later",
    )

    # The promise's own date is what the promise was made with, and it stays.
    # Without it, "originally due" could not be answered at all.
    assert commitment.due_at == ORIGINAL
    assert revision.due_at == REVISED
    assert revision.stated_at is not None
    assert revision.note == "Acknowledged two weeks later"

    # A second statement does not overwrite the first: both are kept, and the
    # date each names is the date somebody stated, unadjusted.
    later = REVISED + timedelta(days=7)
    revise_commitment(session, tenant_id, commitment.id, later)

    stated = commitment_revisions(session, tenant_id, commitment.id)
    assert [row.due_at for row in stated] == [REVISED, later]
    assert commitment.due_at == ORIGINAL


def test_the_date_in_force_is_the_latest_stated(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business)

    # With nothing stated, the promise's own date is in force.
    assert commitment_due_at(session, tenant_id, commitment.id) == ORIGINAL

    revise_commitment(session, tenant_id, commitment.id, REVISED)
    assert commitment_due_at(session, tenant_id, commitment.id) == REVISED

    # Two statements in the same instant still resolve the same way on every
    # read, because identity breaks the tie. On its own promise, so nothing
    # stated at another moment decides it instead.
    tied = promise(session, business)
    instant = datetime(2026, 7, 20, 9, tzinfo=UTC)
    first = revise_commitment(
        session, tenant_id, tied.id, ORIGINAL, stated_at=instant
    )
    second = revise_commitment(
        session, tenant_id, tied.id, REVISED, stated_at=instant
    )
    winner = max((first, second), key=lambda row: row.id)
    assert commitment_due_at(session, tenant_id, tied.id) == winner.due_at
    assert commitment_due_at(session, tenant_id, tied.id) == winner.due_at

    # And "latest stated" means stated, not recorded: a statement made later
    # about an earlier conversation does not win.
    assert commitment_due_at(session, tenant_id, commitment.id) == REVISED


def test_a_revision_is_refused_where_it_makes_no_sense(session, business):
    tenant_id = business.tenant.id

    with pytest.raises(NotFound):
        revise_commitment(session, tenant_id, "cmt_missing", REVISED)

    cancelled = promise(session, business)
    cancel_commitment(session, tenant_id, cancelled.id)
    with pytest.raises(InvalidOperation, match="open"):
        revise_commitment(session, tenant_id, cancelled.id, REVISED)

    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        50,
        to_location_id=business.location.id,
    )
    fulfilled = promise(session, business, quantity=2)
    record_movement(
        session,
        tenant_id,
        "receipt",
        business.item.id,
        2,
        to_location_id=business.location.id,
        commitment_id=fulfilled.id,
    )
    assert fulfilled.status == "fulfilled"
    with pytest.raises(InvalidOperation, match="open"):
        revise_commitment(session, tenant_id, fulfilled.id, REVISED)

    open_promise = promise(session, business)
    with pytest.raises(InvalidOperation):
        revise_commitment(session, tenant_id, open_promise.id, "not a date")

    # The positive control: the same promise takes a readable date, and one
    # already past is accepted, because admitted lateness is a real statement.
    assert revise_commitment(
        session, tenant_id, open_promise.id, datetime(2026, 6, 1, tzinfo=UTC)
    ) is not None


def test_a_hold_does_not_block_recording_what_was_said(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business)
    hold_commitment(session, tenant_id, commitment.id, reason_code="manual_review")

    # A hold stops execution. What the other side said is not execution, and
    # refusing it would lose a statement because of an unrelated block.
    assert revise_commitment(
        session, tenant_id, commitment.id, REVISED
    ) is not None
    assert commitment_due_at(session, tenant_id, commitment.id) == REVISED


def test_revisions_are_tenant_scoped(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business)
    revise_commitment(session, tenant_id, commitment.id, REVISED)
    foreign = create_tenant(session, "Foreign revision tenant")

    with pytest.raises(NotFound):
        revise_commitment(session, foreign.id, commitment.id, REVISED)
    with pytest.raises(NotFound):
        commitment_due_at(session, foreign.id, commitment.id)
    assert commitment_revisions(session, foreign.id, commitment.id) == []

    # The positive control: its own tenant reads them.
    assert len(commitment_revisions(session, tenant_id, commitment.id)) == 1


# --- Eighty of the hundred (spec 097) --------------------------------------


def test_one_statement_can_restate_both(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business, quantity=100)

    revision = revise_commitment(
        session,
        tenant_id,
        commitment.id,
        due_at=REVISED,
        quantity=80,
        note="Eighty pieces, two weeks later",
    )

    # One sentence, one record, one moment it was said.
    assert revision.due_at == REVISED
    assert revision.quantity == Decimal(80)
    assert revision.note == "Eighty pieces, two weeks later"

    # The promise keeps what it was made with; both figures are the ones stated.
    assert commitment.due_at == ORIGINAL
    assert Decimal(commitment.quantity) == Decimal(100)
    assert commitment_due_at(session, tenant_id, commitment.id) == REVISED
    assert commitment_quantity(session, tenant_id, commitment.id) == Decimal(80)
    assert open_quantity(session, tenant_id, commitment.id) == Decimal(80)


def test_a_statement_must_restate_something(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business, quantity=100)

    with pytest.raises(InvalidOperation, match="restate"):
        revise_commitment(session, tenant_id, commitment.id)

    for bad in (0, -5):
        with pytest.raises(InvalidOperation, match="quantity"):
            revise_commitment(session, tenant_id, commitment.id, quantity=bad)

    cancelled = promise(session, business, quantity=10)
    cancel_commitment(session, tenant_id, cancelled.id)
    with pytest.raises(InvalidOperation, match="open"):
        revise_commitment(session, tenant_id, cancelled.id, quantity=5)

    # The positive control: either figure alone is a statement.
    assert revise_commitment(session, tenant_id, commitment.id, quantity=80) is not None
    assert revise_commitment(session, tenant_id, commitment.id, due_at=REVISED) is not None


def test_the_quantity_in_force_is_the_latest_stated(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business, quantity=100)

    assert commitment_quantity(session, tenant_id, commitment.id) == Decimal(100)

    revise_commitment(session, tenant_id, commitment.id, quantity=80)
    assert commitment_quantity(session, tenant_id, commitment.id) == Decimal(80)

    # A later statement about the date alone leaves the eighty standing, which
    # is what the sentence meant: nobody restated the quantity.
    revise_commitment(session, tenant_id, commitment.id, due_at=REVISED)
    assert commitment_quantity(session, tenant_id, commitment.id) == Decimal(80)
    assert commitment_due_at(session, tenant_id, commitment.id) == REVISED

    revise_commitment(session, tenant_id, commitment.id, quantity=60)
    assert commitment_quantity(session, tenant_id, commitment.id) == Decimal(60)

    # And the symmetry holds the other way: a statement about the quantity alone
    # leaves an earlier date standing. Without this the date rule would return
    # the None a quantity-only statement carries, and every date-judged class
    # would go quiet — which is exactly what it did until a test caught it.
    revise_commitment(session, tenant_id, commitment.id, quantity=55)
    assert commitment_due_at(session, tenant_id, commitment.id) == REVISED

    # Every statement is still there, in the order it was made.
    stated = commitment_revisions(session, tenant_id, commitment.id)
    assert [row.quantity for row in stated] == [
        Decimal(80),
        None,
        Decimal(60),
        Decimal(55),
    ]


def test_shrinking_to_what_arrived_finishes_the_promise(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business, quantity=100)
    record_movement(
        session, tenant_id, "receipt", business.item.id, 90,
        to_location_id=business.location.id, commitment_id=commitment.id,
    )
    assert commitment.status == "open"

    revise_commitment(session, tenant_id, commitment.id, quantity=90)

    # Settled at that moment: there may never be another movement to settle it.
    assert commitment.status == "fulfilled"
    assert open_quantity(session, tenant_id, commitment.id) == Decimal(0)


def test_a_promise_can_shrink_below_what_arrived(session, business):
    tenant_id = business.tenant.id
    commitment = promise(session, business, quantity=100)
    record_movement(
        session, tenant_id, "receipt", business.item.id, 90,
        to_location_id=business.location.id, commitment_id=commitment.id,
    )

    # The supplier said eighty and ninety came. Both are true, the ninety is
    # recorded, and refusing would lose the statement.
    revise_commitment(session, tenant_id, commitment.id, quantity=80)

    assert commitment_quantity(session, tenant_id, commitment.id) == Decimal(80)
    assert open_quantity(session, tenant_id, commitment.id) == Decimal(0)
    assert fulfilled_quantity(session, tenant_id, commitment.id) == Decimal(90)
    assert commitment.status == "fulfilled"
