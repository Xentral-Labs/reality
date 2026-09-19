"""Which projections change when only the clock moves (spec 241 FR-004).

A projection on `TIME_SENSITIVE_PROJECTIONS` is rebuilt for the whole company every
sixty seconds whether or not anything happened, because its rows are judged against
the moment they are read. That is the right treatment for a projection that does read
the clock and pure waste for one that does not — at ten thousand companies it is the
standing load of spec 181.

So the membership of that list is measured here rather than assumed. The clock is
moved a long way with no event in between, and every projection is derived twice. One
that answers the same is not time-sensitive; one that answers differently is. The
exceptions projection is the control: if the clock-faking below stopped working, it
would answer the same too, and this file would quietly approve of anything.
"""

import datetime as dt
import json

import pytest
from sqlalchemy import select

import reality.db.core as db_core
import reality.services.core as core_services
import reality.services.exceptions as exception_services
from reality.services import projections
from reality.services.core import (
    create_commitment,
    create_document,
    hold_commitment,
    post_sales_invoice,
    record_customer_payment,
    record_movement,
    revise_commitment,
)


def _content(rows) -> str:
    return json.dumps(rows, sort_keys=True, default=str)


def a_company_with_something_to_age(session, business) -> None:
    """Records that a clock could plausibly move: a promise past due, one ahead of it,
    a revision that restated the date, a hold, an unpaid invoice and stock."""
    tenant = business.tenant.id
    order = create_document(
        session,
        tenant,
        "sales_order",
        "ORD-CLOCK",
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
        note="the customer moved the date",
        _commit=False,
    )
    hold_commitment(session, tenant, overdue.id, "credit_check", _commit=False)
    invoice = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-CLOCK",
        business.customer.id,
        "100",
        document_date="2026-08-02",
    )
    post_sales_invoice(session, tenant, invoice.id)
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "6",
        to_location_id=business.location.id,
    )
    record_customer_payment(session, tenant, business.customer.id, "40")


def derived_twice_far_apart(session, business, monkeypatch) -> dict[str, bool]:
    """Every materialized projection, derived now and again long afterwards."""
    tenant = business.tenant.id
    a_company_with_something_to_age(session, business)
    names = list(projections.MATERIALIZED_PROJECTIONS)
    before = {
        name: projections.derive_projection_rows(session, tenant, name)
        for name in names
    }

    later = db_core.now() + dt.timedelta(days=400)
    for module in (core_services, exception_services, projections, db_core):
        monkeypatch.setattr(module, "now", lambda: later, raising=False)
    after = {
        name: projections.derive_projection_rows(session, tenant, name)
        for name in names
    }
    return {
        name: _content(before[name]) != _content(after[name])
        for name in names
        if before[name]
    }


def test_the_exceptions_projection_moves_when_only_the_clock_does(
    session, business, monkeypatch
):
    """The control. Without it the measurement below could pass for the wrong reason."""
    moved = derived_twice_far_apart(session, business, monkeypatch)
    assert moved[projections.EXCEPTIONS], (
        "four hundred days passed and the exceptions projection did not move, so the "
        "clock in this test is not reaching the derivation and nothing it says is "
        "worth believing"
    )


@pytest.mark.parametrize(
    "name", [projections.COMMITMENT_REGISTER, projections.TENANT_USAGE]
)
def test_the_projections_taken_off_the_cadence_do_not_read_the_clock(
    session, business, monkeypatch, name
):
    """Why these two stopped rebuilding every sixty seconds.

    A promise's risk is `reserved < open` and its date in force is the last one
    stated; a usage summary is counts and a latest timestamp. None of that is judged
    against the present, so a refresh the clock triggered could not change an answer.
    """
    moved = derived_twice_far_apart(session, business, monkeypatch)
    assert not moved[name], (
        f"{name} changed when only the clock moved, so it is time-sensitive after all "
        "and belongs back on TIME_SENSITIVE_PROJECTIONS"
    )


def test_every_projection_that_reads_the_clock_is_on_the_cadence(
    session, business, monkeypatch
):
    """The list is the measurement, not a recollection of one."""
    moved = derived_twice_far_apart(session, business, monkeypatch)
    missing = sorted(
        name
        for name, changed in moved.items()
        if changed and name not in projections.TIME_SENSITIVE_PROJECTIONS
    )
    assert not missing, (
        f"{missing} answer differently when only the clock moves but are refreshed "
        "only when an event arrives, so they can sit stale indefinitely. Put them on "
        "TIME_SENSITIVE_PROJECTIONS or stop deriving them against the present."
    )


def test_a_refresh_the_clock_triggered_rebuilds_only_the_exceptions(session, business):
    """The saving, as a count of projections rather than a stopwatch.

    Nothing has happened in this company since the last refresh. The cadence still
    comes round every sixty seconds, and what it now costs is one projection instead
    of three — at ten thousand companies that difference is the standing load.
    """
    from reality.db.core import ProjectionCheckpoint

    tenant = business.tenant.id
    a_company_with_something_to_age(session, business)
    projections.refresh_operational_projections(session, tenant)

    # A minute passes and no business event arrives.
    for checkpoint in session.scalars(
        select(ProjectionCheckpoint).where(ProjectionCheckpoint.tenant_id == tenant)
    ):
        checkpoint.updated_at = db_core.now() - dt.timedelta(minutes=2)
    session.flush()

    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant)

    assert set(report) == {projections.EXCEPTIONS}, (
        "a refresh with no events behind it rebuilt more than the one projection that "
        f"reads the clock: {sorted(report)}"
    )
