"""A customer deadline at risk before it is missed (spec 300 FR-002).

An open promise less than one day before its date, with quantity not yet shipped,
is reported whether or not it is reserved; once the date passes it is overdue.
"""

from datetime import timedelta

from intake_review_support import reviewed_manual_order, reviewed_reserve

from reality.services import core
from reality.services.exceptions import next_clock_moment, operational_exceptions

DUE_SOON = "outgoing_commitment_due_soon"


def _promise(session, business, number, due_at, *, quantity="4", reserve=True):
    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )
    _, _, _, commitments = reviewed_manual_order(
        session,
        tenant,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": "10.00",
                "gross_amount": "40.00",
            }
        ],
        "40.00",
        requested_delivery_at=due_at,
        sales_channel="amazon",
    )
    if reserve:
        reviewed_reserve(session, tenant, commitments[0].id)
    return commitments[0]


def _rows(session, tenant, as_of):
    return {
        (row.class_id, row.record_id): row
        for row in operational_exceptions(session, tenant, as_of=as_of)
    }


def test_a_fully_reserved_promise_due_within_a_day_is_reported(session, business):
    tenant = business.tenant.id
    now = core.now()
    soon = _promise(session, business, "SO-SOON", now + timedelta(hours=12))
    later = _promise(session, business, "SO-LATER", now + timedelta(days=3))

    rows = _rows(session, tenant, now)
    row = rows[(DUE_SOON, soon.id)]
    assert (row.record_type, row.severity, row.cause_ids) == ("commitment", "high", ())
    assert row.causal_values["remaining_quantity"] == 4
    assert row.causal_values["reserved_quantity"] == 4
    assert 11 <= row.causal_values["hours_left"] <= 12
    # Control: three days ahead is not at risk yet.
    assert (DUE_SOON, later.id) not in rows


def test_an_unreserved_promise_due_soon_is_one_row_with_its_cause(session, business):
    tenant = business.tenant.id
    now = core.now()
    promise = _promise(
        session, business, "SO-UNRES", now + timedelta(hours=6), reserve=False
    )

    rows = _rows(session, tenant, now)
    assert rows[(DUE_SOON, promise.id)].cause_ids == ("insufficient_reservation",)
    assert ("outgoing_commitment_at_risk", promise.id) not in rows
    # Control: three days ahead the same shortfall is at risk, as before.
    assert ("outgoing_commitment_at_risk", promise.id) in _rows(
        session, tenant, now - timedelta(days=3)
    )


def test_past_its_date_it_is_overdue_only(session, business):
    tenant = business.tenant.id
    now = core.now()
    promise = _promise(session, business, "SO-PAST", now + timedelta(hours=6))

    rows = _rows(session, tenant, now + timedelta(hours=7))
    assert ("overdue_outgoing_customer_commitment", promise.id) in rows
    assert (DUE_SOON, promise.id) not in rows


def test_shipping_cancelling_or_a_later_date_clears_it(session, business):
    tenant = business.tenant.id
    now = core.now()
    shipped = _promise(session, business, "SO-SHIP", now + timedelta(hours=6))
    cancelled = _promise(session, business, "SO-CANCEL", now + timedelta(hours=6))
    moved = _promise(session, business, "SO-MOVE", now + timedelta(hours=6))
    assert {(DUE_SOON, row.id) for row in (shipped, cancelled, moved)} <= set(
        _rows(session, tenant, now)
    )

    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "4",
        from_location_id=business.location.id,
        commitment_id=shipped.id,
    )
    core.cancel_commitment(session, tenant, cancelled.id, reason="Withdrawn")
    core.revise_commitment(
        session, tenant, moved.id, now + timedelta(days=3), note="Agreed later"
    )

    rows = _rows(session, tenant, now)
    assert not {(DUE_SOON, row.id) for row in (shipped, cancelled, moved)} & set(rows)


def test_a_revised_date_carries_its_revision(session, business):
    tenant = business.tenant.id
    now = core.now()
    promise = _promise(session, business, "SO-REV", now + timedelta(days=5))
    core.revise_commitment(
        session, tenant, promise.id, now + timedelta(hours=8), note="Customer asked"
    )

    row = _rows(session, tenant, now)[(DUE_SOON, promise.id)]
    assert row.cause_ids == ("promise_was_revised",)
    assert row.causal_values["times_revised"] == 1


def test_the_clock_wakes_when_the_window_opens(session, business):
    tenant = business.tenant.id
    now = core.now()
    promise_at = now + timedelta(hours=30)
    _promise(session, business, "SO-CLOCK", promise_at)

    # The verdict changes six hours from now, when the promise is a day away.
    moment = next_clock_moment(session, tenant, as_of=now)
    assert abs(moment - (promise_at - timedelta(days=1))) < timedelta(seconds=1)
