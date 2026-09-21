"""A customer saying goods are coming back, before they have left.

Everything recorded here is something somebody stated. Nothing is generated —
the reference least of all, because a number this product invented would be a
number somebody has to tell the customer.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    announce_customer_return,
    announceable_quantity,
    announcement_outstanding,
    arrived_against_announcement,
    cancel_commitment,
    create_commitment,
    create_tenant,
    record_movement,
    return_announcements,
    returnable_quantity,
    returned_quantity,
    withdraw_return_announcement,
)

SHIPPED_AT = datetime(2026, 8, 20, 12, tzinfo=UTC)
ANNOUNCED_AT = datetime(2026, 8, 25, 12, tzinfo=UTC)
DUE = datetime(2026, 8, 15, 12, tzinfo=UTC)


def delivery(session, business, quantity=5, *, kind="customer_delivery"):
    return create_commitment(
        session,
        business.tenant.id,
        kind,
        business.company.id if kind == "customer_delivery" else business.supplier.id,
        business.customer.id if kind == "customer_delivery" else business.company.id,
        business.item.id,
        business.location.id,
        quantity,
        DUE,
    )


def stock(session, business, quantity=50):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def ship(session, business, commitment, quantity):
    return record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=SHIPPED_AT,
    )


def comes_back(session, business, commitment, quantity, *, announcement=None, at=None):
    return record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        return_announcement_id=announcement.id if announcement else None,
        occurred_at=at or datetime(2026, 8, 28, 12, tzinfo=UTC),
    )


def shipped_delivery(session, business, quantity=5):
    stock(session, business)
    commitment = delivery(session, business, quantity)
    ship(session, business, commitment, quantity)
    return commitment


def test_what_the_customer_said_is_recorded(session, business):
    """The sentence that had nowhere to live."""
    commitment = shipped_delivery(session, business)

    announcement = announce_customer_return(
        session,
        business.tenant.id,
        commitment.id,
        2,
        reference="RMA-4711",
        reason="Wrong colour",
        expected_by=datetime(2026, 9, 3, 12, tzinfo=UTC),
        announced_at=ANNOUNCED_AT,
    )

    assert announcement.commitment_id == commitment.id
    assert Decimal(announcement.quantity) == Decimal(2)
    # Exactly as stated. Nothing normalised, nothing generated.
    assert announcement.reference == "RMA-4711"
    assert announcement.reason == "Wrong colour"
    assert announcement.announced_at == ANNOUNCED_AT
    assert announcement.expected_by == datetime(2026, 9, 3, 12, tzinfo=UTC)
    assert announcement.status == "open"
    assert announcement.closed_at is None

    # The delivery it concerns is untouched: an announcement is a statement
    # about goods coming back, not a change to the promise that sent them.
    assert commitment.status == "fulfilled"
    assert Decimal(commitment.quantity) == Decimal(5)
    assert returned_quantity(session, business.tenant.id, commitment.id) == Decimal(0)

    # A customer who names no day is not a customer promising "soon": the
    # absence is the statement, and the queue judges the two differently.
    silent = announce_customer_return(
        session, business.tenant.id, commitment.id, 1, announced_at=ANNOUNCED_AT
    )
    assert silent.expected_by is None
    assert silent.reference == ""


def test_one_rule_answers_what_can_come_back(session, business):
    """The returning-movement path and the announcement ask the same rule."""
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id

    assert returnable_quantity(session, tenant_id, commitment.id) == Decimal(5)
    assert announceable_quantity(session, tenant_id, commitment.id) == Decimal(5)

    comes_back(session, business, commitment, 2)
    assert returnable_quantity(session, tenant_id, commitment.id) == Decimal(3)
    assert announceable_quantity(session, tenant_id, commitment.id) == Decimal(3)

    # Nothing else in the service or derivation layer answers it.
    from pathlib import Path

    sources = [
        Path(__file__).resolve().parents[1] / "src/reality/services/core.py",
        Path(__file__).resolve().parents[1] / "src/reality/services/exceptions.py",
    ]
    definitions = sum(
        text.count("def returnable_quantity")
        for text in (path.read_text() for path in sources)
    )
    assert definitions == 1


def test_two_announcements_cannot_claim_the_same_goods(session, business):
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id

    announce_customer_return(
        session, business.tenant.id, commitment.id, 2, announced_at=ANNOUNCED_AT
    )
    assert announceable_quantity(session, tenant_id, commitment.id) == Decimal(3)

    # Four more would mean the desk expecting six of five shipped.
    with pytest.raises(InvalidOperation, match="can still come back"):
        announce_customer_return(session, tenant_id, commitment.id, 4)

    # The positive control: three is exactly what is left, and it is accepted.
    announce_customer_return(session, tenant_id, commitment.id, 3)
    assert announceable_quantity(session, tenant_id, commitment.id) == Decimal(0)


def test_an_announcement_refuses(session, business):
    tenant_id = business.tenant.id
    commitment = shipped_delivery(session, business)

    with pytest.raises(InvalidOperation, match="greater than zero"):
        announce_customer_return(session, tenant_id, commitment.id, 0)
    with pytest.raises(InvalidOperation, match="greater than zero"):
        announce_customer_return(session, tenant_id, commitment.id, "-1")

    # A supplier delivery is the mirror case and deliberately out of scope.
    incoming = delivery(session, business, 5, kind="supplier_delivery")
    with pytest.raises(InvalidOperation, match="customer delivery"):
        announce_customer_return(session, tenant_id, incoming.id, 1)

    # Nothing shipped means nothing can come back, so nothing can be announced.
    unshipped = delivery(session, business, 5)
    with pytest.raises(InvalidOperation, match="can still come back"):
        announce_customer_return(session, tenant_id, unshipped.id, 1)

    # A cancelled promise cannot receive one. A *fulfilled* one can, and must:
    # a fully shipped delivery is exactly when returns happen.
    cancel_commitment(session, tenant_id, unshipped.id)
    with pytest.raises(InvalidOperation, match="cancelled promise"):
        announce_customer_return(session, tenant_id, unshipped.id, 1)

    # An empty day is not "no day stated": a caller who passed the field meant
    # to say something, so saying nothing in it is refused rather than quietly
    # read as silence. Same call the promise revision makes.
    with pytest.raises(InvalidOperation, match="readable expected day"):
        announce_customer_return(session, tenant_id, commitment.id, 1, expected_by="")
    with pytest.raises(InvalidOperation, match="ISO 8601"):
        announce_customer_return(
            session, tenant_id, commitment.id, 1, expected_by="not a day"
        )
    with pytest.raises(NotFound):
        announce_customer_return(session, tenant_id, "com_missing", 1)

    # The positive control: the shipped, fulfilled delivery accepts one.
    assert (
        announce_customer_return(session, tenant_id, commitment.id, 1).status == "open"
    )


def test_the_parcel_names_its_announcement(session, business):
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id
    announcement = announce_customer_return(
        session, tenant_id, commitment.id, 2, announced_at=ANNOUNCED_AT
    )

    movement = comes_back(session, business, commitment, 2, announcement=announcement)

    assert movement.return_announcement_id == announcement.id
    # The return still names the delivery it reverses. That link bounds it and
    # four classes read it; the announcement is an additional statement about
    # the same event, not a substitute for it.
    assert movement.commitment_id == commitment.id
    assert movement.type == "return"
    assert returned_quantity(session, tenant_id, commitment.id) == Decimal(2)
    assert arrived_against_announcement(session, tenant_id, announcement.id) == Decimal(
        2
    )

    # A return naming no announcement is ordinary and unchanged.
    plain = comes_back(session, business, commitment, 1)
    assert plain.return_announcement_id is None
    assert returned_quantity(session, tenant_id, commitment.id) == Decimal(3)


def test_a_movement_refuses_a_foreign_announcement(session, business):
    tenant_id = business.tenant.id
    mine = shipped_delivery(session, business)
    theirs = delivery(session, business, 4)
    ship(session, business, theirs, 4)
    announcement = announce_customer_return(
        session, tenant_id, mine.id, 2, announced_at=ANNOUNCED_AT
    )

    # The check that makes the reference mean something.
    with pytest.raises(InvalidOperation, match="its own delivery only"):
        comes_back(session, business, theirs, 1, announcement=announcement)

    # Goods going the other way do not fulfil an announced customer return, and
    # the caller is told that rather than something about open quantity.
    with pytest.raises(InvalidOperation, match="Only returning goods"):
        record_movement(
            session,
            tenant_id,
            "shipment",
            business.item.id,
            1,
            from_location_id=business.location.id,
            commitment_id=mine.id,
            return_announcement_id=announcement.id,
        )

    # And a return naming an announcement but no delivery at all is refused for
    # the same reason: nothing would tie the two together.
    with pytest.raises(InvalidOperation, match="its own delivery only"):
        record_movement(
            session,
            tenant_id,
            "return",
            business.item.id,
            1,
            to_location_id=business.location.id,
            return_announcement_id=announcement.id,
        )

    # A withdrawn announcement is not open, so nothing fulfils it.
    withdraw_return_announcement(session, tenant_id, announcement.id)
    with pytest.raises(InvalidOperation, match="open announcement"):
        comes_back(session, business, mine, 1, announcement=announcement)

    # The positive control: a fresh announcement on the right delivery works.
    fresh = announce_customer_return(session, tenant_id, mine.id, 2)
    assert (
        comes_back(
            session, business, mine, 2, announcement=fresh
        ).return_announcement_id
        == fresh.id
    )


def test_an_announcement_is_finished_when_the_goods_arrive(session, business):
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id
    announcement = announce_customer_return(
        session, tenant_id, commitment.id, 2, announced_at=ANNOUNCED_AT
    )

    # Part of it arriving leaves it open for the rest.
    comes_back(session, business, commitment, 1, announcement=announcement)
    assert announcement.status == "open"
    assert announcement_outstanding(session, tenant_id, announcement) == Decimal(1)

    # The rest arriving finishes it at that moment, not at some later read:
    # there may be no later event, because the parcel arrived and that is that.
    comes_back(
        session,
        business,
        commitment,
        1,
        announcement=announcement,
        at=datetime(2026, 8, 29, 12, tzinfo=UTC),
    )
    assert announcement.status == "fulfilled"
    assert announcement.closed_at is not None
    assert announcement_outstanding(session, tenant_id, announcement) == Decimal(0)


def test_more_may_arrive_than_was_announced(session, business):
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id
    announcement = announce_customer_return(
        session, tenant_id, commitment.id, 2, announced_at=ANNOUNCED_AT
    )

    # The customer said two and sent three. Both are true, the third item
    # physically exists, and refusing would lose a movement that happened.
    comes_back(session, business, commitment, 3, announcement=announcement)

    assert announcement.status == "fulfilled"
    assert arrived_against_announcement(session, tenant_id, announcement.id) == Decimal(
        3
    )
    # Never below nothing: outstanding is zero rather than minus one.
    assert announcement_outstanding(session, tenant_id, announcement) == Decimal(0)
    assert returned_quantity(session, tenant_id, commitment.id) == Decimal(3)

    # What the delivery allows back is still the bound: five went out, three
    # came back, and a fourth announcement of three is refused.
    with pytest.raises(InvalidOperation, match="can still come back"):
        announce_customer_return(session, tenant_id, commitment.id, 3)


def test_an_announcement_can_be_withdrawn(session, business):
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id
    announcement = announce_customer_return(
        session,
        tenant_id,
        commitment.id,
        2,
        reference="RMA-4711",
        announced_at=ANNOUNCED_AT,
    )
    assert announceable_quantity(session, tenant_id, commitment.id) == Decimal(3)

    withdrawn = withdraw_return_announcement(
        session, tenant_id, announcement.id, note="Customer keeps them"
    )

    assert withdrawn.status == "withdrawn"
    assert withdrawn.closed_at is not None
    # What they announced is kept. A withdrawal is another statement about the
    # same conversation, not a reason to forget the first one.
    assert Decimal(withdrawn.quantity) == Decimal(2)
    assert withdrawn.reference == "RMA-4711"
    assert withdrawn.note == "Customer keeps them"
    assert withdrawn.announced_at == ANNOUNCED_AT
    # And the delivery allows the full five again.
    assert announceable_quantity(session, tenant_id, commitment.id) == Decimal(5)

    with pytest.raises(InvalidOperation, match="open announcement"):
        withdraw_return_announcement(session, tenant_id, announcement.id)

    # The positive control: a fresh one can still be withdrawn.
    fresh = announce_customer_return(session, tenant_id, commitment.id, 1)
    assert (
        withdraw_return_announcement(session, tenant_id, fresh.id).status == "withdrawn"
    )


def test_announcements_are_ordered_and_nothing_is_lost(session, business):
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id
    first = announce_customer_return(
        session, tenant_id, commitment.id, 1, announced_at=ANNOUNCED_AT
    )
    second = announce_customer_return(
        session,
        tenant_id,
        commitment.id,
        1,
        announced_at=ANNOUNCED_AT + timedelta(days=1),
    )
    third = announce_customer_return(
        session,
        tenant_id,
        commitment.id,
        1,
        announced_at=ANNOUNCED_AT + timedelta(days=2),
    )
    withdraw_return_announcement(session, tenant_id, second.id)

    rows = return_announcements(session, tenant_id, commitment_id=commitment.id)

    # All three, in the order they were said, including the withdrawn one.
    assert [row.id for row in rows] == [first.id, second.id, third.id]
    assert [row.status for row in rows] == ["open", "withdrawn", "open"]
    assert [
        row.id for row in return_announcements(session, tenant_id, status="open")
    ] == [
        first.id,
        third.id,
    ]


def test_announcements_are_tenant_scoped(session, business):
    commitment = shipped_delivery(session, business)
    tenant_id = business.tenant.id
    announcement = announce_customer_return(
        session, tenant_id, commitment.id, 2, announced_at=ANNOUNCED_AT
    )

    other = create_tenant(session, "Foreign GmbH")

    assert return_announcements(session, other.id) == []
    with pytest.raises(NotFound):
        withdraw_return_announcement(session, other.id, announcement.id)
    with pytest.raises(NotFound):
        announce_customer_return(session, other.id, commitment.id, 1)
    with pytest.raises(NotFound):
        return_announcements(session, "ten_missing")

    # The positive control: its own tenant reads and withdraws it.
    assert [row.id for row in return_announcements(session, tenant_id)] == [
        announcement.id
    ]
    assert (
        withdraw_return_announcement(session, tenant_id, announcement.id).status
        == "withdrawn"
    )
