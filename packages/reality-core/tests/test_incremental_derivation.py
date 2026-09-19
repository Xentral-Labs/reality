"""Incremental refresh and full rebuild must leave the same rows (spec 241 FR-006).

This file is the safety net, and it is written before any builder narrows. The
danger in deriving by change is not slowness: it is a builder asked for the rows of
one record that misses a row the change affects indirectly — a blocker that clears,
a total that shifts. The result is a stored projection that is quietly wrong, which
is worse than a slow one.

So the property is stated as a property, and a second test deliberately breaks a
builder to prove the first one would notice. A net that has never caught anything is
not known to be a net.
"""

import json

from sqlalchemy import select

from reality.db.core import ProjectionRow
from reality.services import projections
from reality.services.core import (
    create_commitment,
    create_document,
    post_sales_invoice,
    record_customer_payment,
    record_movement,
)

#: Fields that record *when* a row was derived rather than what it says. Two
#: refreshes a second apart differ in these and in nothing else, so comparing them
#: would make the property fail for a reason that has nothing to do with narrowing.
EVALUATION_TIME_FIELDS = {"as_of"}


def _content(payload):
    """A payload without the moment it was evaluated."""
    if isinstance(payload, dict):
        return {
            key: _content(value)
            for key, value in payload.items()
            if key not in EVALUATION_TIME_FIELDS
        }
    if isinstance(payload, list):
        return [_content(item) for item in payload]
    return payload


def snapshot(session, tenant_id: str) -> dict[tuple[str, str], object]:
    """Every stored row, by projection and key, with what it says.

    The payload is compared without its evaluation timestamp: an exception carries
    the moment it was judged, and the property here is that incremental and full
    derivation agree about the business, not that they ran in the same second.
    """
    return {
        (row.projection_name, row.record_key): _content(json.loads(row.payload))
        for row in session.scalars(
            select(ProjectionRow).where(ProjectionRow.tenant_id == tenant_id)
        )
    }


def a_little_business(session, business) -> None:
    """Enough of an order-to-cash to give every projection something to hold."""
    tenant = business.tenant.id
    order = create_document(
        session,
        tenant,
        "sales_order",
        "ORD-241",
        business.customer.id,
        "100",
        document_date="2026-08-01",
    )
    create_commitment(
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
    invoice = create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-241",
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
    # A payment, so the payments projection holds something and the coverage test
    # below can insist that every projection is inside the property.
    record_customer_payment(session, tenant, business.customer.id, "40")


def test_incremental_refresh_and_full_rebuild_leave_the_same_rows(session, business):
    """FR-006: the property, stated as a property.

    Today both paths run the same derivation, so this passes for a reason that will
    change. It is written now because the moment a builder narrows, this is the only
    thing standing between an optimisation and a silently wrong projection.
    """
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    incremental = snapshot(session, tenant)
    assert incremental, "the fixture produced no projection rows to compare"

    projections.refresh_operational_projections(session, tenant, force=True)
    full = snapshot(session, tenant)

    assert incremental == full


def test_the_comparison_notices_a_builder_that_drops_a_row(
    session, business, monkeypatch
):
    """The positive control: a net that has never caught anything is not a net.

    A builder is made to withhold one row — exactly the failure a wrong narrowing
    produces — and the comparison must fail. Without this, the test above would keep
    passing after somebody broke the thing it guards.
    """
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant)
    complete = snapshot(session, tenant)

    original = projections.derive_projection_rows

    def short(session_, tenant_id, projection_name):
        rows = original(session_, tenant_id, projection_name)
        if projection_name == projections.DOCUMENT_REGISTER and rows:
            rows.pop(next(iter(rows)))
        return rows

    monkeypatch.setattr(projections, "derive_projection_rows", short)
    projections.refresh_operational_projections(session, tenant, force=True)
    narrowed = snapshot(session, tenant)

    assert narrowed != complete, (
        "a builder withheld a row and the comparison did not notice; the property "
        "test above is not guarding anything"
    )
    missing = set(complete) - set(narrowed)
    assert missing and all(name == projections.DOCUMENT_REGISTER for name, _ in missing)


def test_every_materialized_projection_is_covered_by_the_comparison(session, business):
    """A projection nobody built is a projection the property says nothing about."""
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant, force=True)
    built = {name for name, _ in snapshot(session, tenant)}
    missing = set(projections.MATERIALIZED_PROJECTIONS) - built
    assert not missing, (
        f"{sorted(missing)} produced no rows for this fixture, so the equivalence "
        "property does not cover them. Give the fixture a record they hold, or say "
        "here why they are empty."
    )


# --- the change set, and when it refuses to narrow (FR-001, FR-002, SC-004) ------


def test_the_change_set_names_the_records_whose_events_fell_in_the_window(
    session, business
):
    tenant = business.tenant.id
    a_little_business(session, business)
    projections.refresh_operational_projections(session, tenant, force=True)
    before = projections._latest_sequence(session, tenant)

    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-LATER",
        business.customer.id,
        "10",
        document_date="2026-08-05",
    )
    after = projections._latest_sequence(session, tenant)

    narrowing = projections.change_set(
        session, tenant, projections.DOCUMENT_REGISTER, before, after
    )
    assert narrowing.narrowed, narrowing.reason
    assert narrowing.subjects
    # Only what changed in the window, not the company.
    assert sum(len(ids) for ids in narrowing.subjects.values()) <= 4


def test_an_unknown_event_type_refuses_to_narrow(session, business):
    """Nothing may be assumed about what an unrecognised event left alone."""
    from reality.db.core import BusinessEvent, now, uid

    tenant = business.tenant.id
    a_little_business(session, business)
    before = projections._latest_sequence(session, tenant)
    session.add(
        BusinessEvent(
            id=uid("bev"),
            tenant_id=tenant,
            sequence=before + 1,
            event_type="something.the.catalog.does.not.list",
            schema_version=1,
            subject_type="document",
            subject_id="doc_probe",
            occurred_at=now(),
            payload="{}",
        )
    )
    session.flush()

    narrowing = projections.change_set(
        session, tenant, projections.DOCUMENT_REGISTER, before, before + 1
    )
    assert not narrowing.narrowed
    assert "unknown event type" in narrowing.reason


def test_too_many_changes_are_a_rebuild_wearing_another_name(session, business):
    """Visiting ten thousand records one at a time is slower than the company."""
    tenant = business.tenant.id
    a_little_business(session, business)
    before = 0
    after = projections._latest_sequence(session, tenant)
    monkey = projections.MAX_NARROWED_SUBJECTS
    try:
        projections.MAX_NARROWED_SUBJECTS = 1
        narrowing = projections.change_set(
            session, tenant, projections.DOCUMENT_REGISTER, before, after
        )
    finally:
        projections.MAX_NARROWED_SUBJECTS = monkey
    assert not narrowing.narrowed
    assert "too many" in narrowing.reason


def test_a_refresh_reports_which_projections_narrowed(session, business):
    """SC-004: all builders declining must look like that, not like success."""
    tenant = business.tenant.id
    a_little_business(session, business)
    with projections.narrowing_report() as report:
        projections.refresh_operational_projections(session, tenant, force=True)
    assert report, "a refresh that built projections reported nothing about narrowing"
    # A forced rebuild narrows nothing, and says so rather than staying silent.
    assert all(reason for reason in report.values())
    assert set(report) <= set(projections.MATERIALIZED_PROJECTIONS)
