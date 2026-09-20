"""Which exception classes answer differently when only the clock moves.

`exceptions` is the one projection still refreshed every sixty seconds for every
company, because some of its classes judge a record against the moment it is read.
Spec 181 FR-004 wants that cadence taken apart, and the first thing that needs is a
list of the classes it exists for — measured, not recalled, the way
`test_clock_sensitivity.py` measures which projections read the clock at all.

The probe here is universal: the same company, derived twice, four hundred days
apart, with nothing else changed. A class that answers the same does not read the
clock; one that answers differently does.

The *other* property this work wants — whether a class's verdict about one record can
be changed by another record — has no universal probe, and a first attempt to measure
it was wrong in a way worth recording. Adding an unrelated record says nothing,
because "unrelated" is what each class defines differently: for `credit_limit_exceeded`
it is another invoice of the same party, for `duplicate_supplier_invoice` another
invoice under the same number, and for a class with a learned threshold it is any
finished promise at all. Both of those were measured as record-local by such a probe,
and both are company-wide. That property therefore belongs with each class's own
narrowing, tested per class, and not in a table filled in advance.
"""

import datetime as dt
import json

from reality.services import exceptions as exception_services
from reality.services.core import (
    create_commitment,
    create_document,
    hold_commitment,
    hold_party_delivery,
    post_sales_invoice,
    record_customer_payment,
    record_movement,
    reserve,
    revise_commitment,
)

#: Measured by the test below, not declared for it to confirm.
CLOCK_READING = {
    "overdue_outgoing_customer_commitment",
    "overdue_incoming_supplier_commitment",
    "overdue_receivable",
}
#: Classes this fixture does not bring about at all. They are named so the gap is
#: visible and shrinks when someone gives them a scenario; a class that starts
#: producing rows here fails the test until it is moved out of this list.
WITHOUT_A_SCENARIO = {
    "outgoing_commitment_at_risk",
    "order_stalled",
    "shipped_not_billed",
    "billed_not_received",
    "invoice_price_differs",
    "sold_below_purchase_price",
    "returned_not_credited",
    "credited_not_returned",
    "supplier_return_not_credited",
    "supplier_credit_not_returned",
    "return_unresolved",
    "receipt_unbilled",
    "units_not_comparable",
    "reservation_exceeds_stock",
    "silent_source",
    "source_interpretation_failure",
    "sales_invoice_unposted",
    "supplier_invoice_unposted",
    "credit_note_unposted",
    "credit_note_unsettled",
    "supplier_credit_unposted",
    "supplier_credit_unclaimed",
    "overdue_payable",
    "purchase_discount_available",
    "announced_return_not_arrived",
    "commitment_hold_unreleased",
    "party_hold_unreleased",
    "stock_expired",
}


def _rows_by_id(session, tenant, as_of=None):
    """Every row by its id, so a new row is not mistaken for a changed verdict."""
    rows = exception_services.operational_exception_rows(session, tenant, as_of=as_of)
    return {
        row["id"]: (row["class_id"], json.dumps(row, sort_keys=True, default=str))
        for row in rows
    }


def _classes_that_changed(before, after):
    """Classes where a row that existed before now says something else, or is gone."""
    changed = set()
    for row_id, (class_id, payload) in before.items():
        if row_id not in after or after[row_id][1] != payload:
            changed.add(class_id)
    return changed


def _rich_company(session, business):
    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    order = create_document(
        session,
        tenant,
        "sales_order",
        "ORD-M1",
        business.customer.id,
        "100",
        document_date="2026-08-01",
    )
    overdue = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "4",
        "2026-08-10T00:00:00+00:00",
        document_id=order.id,
    )
    ahead = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        "2099-01-01T00:00:00+00:00",
        document_id=order.id,
    )
    revise_commitment(
        session,
        tenant,
        ahead.id,
        "2099-06-01T00:00:00+00:00",
        note="moved",
        _commit=False,
    )
    hold_commitment(session, tenant, overdue.id, "credit_check", _commit=False)
    reserve(session, tenant, ahead.id, "2", _commit=False)
    supply = create_commitment(
        session,
        tenant,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "5",
        "2026-08-05T00:00:00+00:00",
    )
    invoice = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-M1",
        business.customer.id,
        "100",
        document_date="2026-08-02",
    )
    post_sales_invoice(session, tenant, invoice.id)
    record_customer_payment(session, tenant, business.customer.id, "40")
    hold_party_delivery(session, tenant, business.customer.id, "credit_check")
    # A sales invoice nobody posted, two supplier invoices under one number, and a
    # customer over an agreed limit: three more classes for a few lines.
    create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-UNPOSTED",
        business.customer.id,
        "70",
        document_date="2026-08-02",
    )
    for number in ("SUP-DUP", "SUP-DUP"):
        create_document(
            session,
            tenant,
            "supplier_invoice",
            number,
            business.supplier.id,
            "60",
            document_date="2026-08-03",
        )
    business.customer.credit_limit = 10
    session.flush()
    return {"order": order, "overdue": overdue, "supply": supply, "invoice": invoice}


def test_the_classes_that_read_the_clock_are_measured(session, business):

    tenant = business.tenant.id
    _rich_company(session, business)
    session.flush()

    now = dt.datetime.now(dt.UTC)
    before = _rows_by_id(session, tenant, as_of=now)
    later = _rows_by_id(session, tenant, as_of=now + dt.timedelta(days=400))

    assert before, (
        "the fixture produced no rows, so this file would approve of anything"
    )
    measured = _classes_that_changed(before, later)
    assert measured == CLOCK_READING
    assert measured, "the clock probe moved nothing; the measurement is not measuring"


def test_every_class_is_either_brought_about_here_or_named_as_missing(
    session, business
):
    """The gap is pinned, so it cannot quietly stay the same size."""
    from reality.services.exceptions import DERIVATION_REGISTRY

    tenant = business.tenant.id
    _rich_company(session, business)
    session.flush()
    now = dt.datetime.now(dt.UTC)
    present = {
        class_id for class_id, _ in _rows_by_id(session, tenant, as_of=now).values()
    } | {
        class_id
        for class_id, _ in _rows_by_id(
            session, tenant, as_of=now + dt.timedelta(days=400)
        ).values()
    }

    assert present | WITHOUT_A_SCENARIO == set(DERIVATION_REGISTRY)
    assert not present & WITHOUT_A_SCENARIO, (
        "a class produces rows here and is still listed as missing a scenario"
    )


def test_the_next_clock_moment_is_the_earliest_date_in_the_window(session, business):
    """What replaces asking every sixty seconds (spec 181 FR-004).

    A promise due tomorrow can turn overdue tonight with nobody doing anything, so
    that date is when this projection next has something to say. The answer is the
    earliest such date, and never later than a day, because an age-based verdict on an
    idle company is judged against a span this cannot see.
    """
    from reality.services.core import create_commitment
    from reality.services.exceptions import IDLE_CLOCK_FLOOR, next_clock_moment

    tenant = business.tenant.id
    now = dt.datetime.now(dt.UTC)
    assert next_clock_moment(session, tenant, as_of=now) == now + IDLE_CLOCK_FLOOR

    soon = now + dt.timedelta(hours=5)
    create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "3",
        soon.isoformat(),
    )
    later = now + dt.timedelta(hours=9)
    create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        later.isoformat(),
    )
    session.flush()

    assert next_clock_moment(session, tenant, as_of=now) == soon


def test_a_date_beyond_the_window_does_not_move_the_moment(session, business):
    """A promise due next year says nothing about tonight.

    Without the cap this would be the answer and the projection would sit untouched
    for months; with it, the company is looked at once a day, which is what bounds
    everything that ages.
    """
    from reality.services.core import create_commitment
    from reality.services.exceptions import IDLE_CLOCK_FLOOR, next_clock_moment

    tenant = business.tenant.id
    now = dt.datetime.now(dt.UTC)
    create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "3",
        (now + dt.timedelta(days=200)).isoformat(),
    )
    session.flush()

    assert next_clock_moment(session, tenant, as_of=now) == now + IDLE_CLOCK_FLOOR


def test_a_revised_date_inside_the_window_is_its_own_candidate(session, business):
    """The date in force is the last one stated, so a revision is a moment too."""
    from reality.services.core import create_commitment, revise_commitment
    from reality.services.exceptions import next_clock_moment

    tenant = business.tenant.id
    now = dt.datetime.now(dt.UTC)
    promise = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "3",
        (now - dt.timedelta(days=1)).isoformat(),
    )
    revised = now + dt.timedelta(hours=3)
    revise_commitment(
        session, tenant, promise.id, revised.isoformat(), note="moved", _commit=False
    )
    session.flush()

    assert next_clock_moment(session, tenant, as_of=now) == revised


def test_a_promise_falling_due_tonight_is_looked_at_tonight(session, business):
    """The saving must not be bought with a late verdict.

    A company whose promise falls due in five hours records that moment, so it is
    evaluated then — not a day later, and not 1,440 times before.
    """
    from reality.services.core import create_commitment
    from reality.services.exceptions import IDLE_CLOCK_FLOOR
    from reality.services.projections import (
        EXCEPTIONS,
        projection_metadata,
        projection_state_expressions,
        rebuild_projections,
    )

    tenant = business.tenant.id
    now = dt.datetime.now(dt.UTC)
    due = now + dt.timedelta(hours=5)
    create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "3",
        due.isoformat(),
    )
    session.flush()
    rebuild_projections(session, tenant, [EXCEPTIONS], force=True)
    session.flush()

    def state(at):
        import reality.services.projections as module

        values = dict(
            session.execute(
                __import__("sqlalchemy").select(
                    *[
                        expression.label(key)
                        for key, expression in projection_state_expressions(
                            tenant, EXCEPTIONS
                        ).items()
                    ]
                )
            )
            .mappings()
            .one()
        )
        original = module.now
        module.now = lambda: at
        try:
            return projection_metadata(EXCEPTIONS, values)["state"]
        finally:
            module.now = original

    assert state(now + dt.timedelta(minutes=2)) == "ready", (
        "two minutes cannot have aged anything"
    )
    assert state(due + dt.timedelta(minutes=1)) == "pending", (
        "the promise is overdue and nobody was told"
    )
    assert due + dt.timedelta(minutes=1) < now + IDLE_CLOCK_FLOOR, (
        "the fixture no longer tests the dated case"
    )
