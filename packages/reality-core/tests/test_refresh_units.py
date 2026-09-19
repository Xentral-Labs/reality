"""A company with no change and no due date must cause no work (181 FR-004, SC-003).

The scheduler used to take every company in the instance and ask each of them twelve
questions about its projections. That is work proportional to how many companies exist
rather than to how many changed, which is the shape SC-003 forbids — at ten thousand
companies it is a hundred and twenty thousand reads a sweep to discover that nothing
happened.

The two things measured here are that a quiet company is not visited at all, and that a
company which *did* change still is. The second matters more: a selection that returns
nothing is cheap and useless.
"""

from datetime import timedelta

from sqlalchemy import event, func, select

from reality.db.core import Tenant, TenantEventProgress, now
from reality.services import projections
from reality.services.core import create_document
from reality.services.projection_jobs import (
    due_projection_tenants,
    due_projections,
    enqueue_due_projections,
)
from reality.services.scheduled_jobs import scheduler_tenants


def statements(session):
    """How many statements one block sends."""
    counted = [0]
    bind = session.get_bind()

    def before(conn, cursor, statement, parameters, context, executemany):
        counted[0] += 1

    event.listen(bind, "before_cursor_execute", before)
    return counted, lambda: event.remove(bind, "before_cursor_execute", before)


def quiet(session, business):
    """A company whose projections are all built and whose events have stopped."""
    tenant = business.tenant.id
    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-FR004",
        business.customer.id,
        "100",
        document_date="2026-08-01",
    )
    projections.refresh_operational_projections(session, tenant, force=True)
    return tenant


def test_a_company_with_nothing_new_is_not_offered_to_the_scheduler(session, business):
    tenant = quiet(session, business)
    assert tenant not in due_projection_tenants(session)
    assert tenant not in scheduler_tenants(session)


def test_a_company_that_changed_is_offered(session, business):
    tenant = quiet(session, business)
    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-FR004-B",
        business.customer.id,
        "10",
        document_date="2026-08-02",
    )
    session.flush()
    assert tenant in due_projection_tenants(session)
    assert tenant in scheduler_tenants(session)


def test_a_company_whose_cadence_came_round_is_offered(session, business):
    """The time-sensitive projection falls due with no event to announce it."""
    from reality.db.core import ProjectionCheckpoint

    tenant = quiet(session, business)
    assert tenant not in due_projection_tenants(session)
    for checkpoint in session.scalars(
        select(ProjectionCheckpoint).where(
            ProjectionCheckpoint.tenant_id == tenant,
            ProjectionCheckpoint.projection_name.in_(
                projections.TIME_SENSITIVE_PROJECTIONS
            ),
        )
    ):
        checkpoint.updated_at = now() - timedelta(minutes=2)
    session.flush()
    assert tenant in due_projection_tenants(session)


def test_a_company_whose_projections_were_never_built_is_offered(session, business):
    """Nothing built means nothing to fall behind, so absence is the signal."""
    assert business.tenant.id in due_projection_tenants(session)


def test_an_archived_company_is_never_offered(session, business):
    tenant = quiet(session, business)
    company = session.get(Tenant, tenant)
    company.archived_at = now()
    session.flush()
    assert tenant not in due_projection_tenants(session)


def test_asking_one_company_what_is_behind_is_one_round_trip(session, business):
    """Twelve projections, one read. It used to be a statement apiece."""
    tenant = quiet(session, business)
    counted, stop = statements(session)
    behind = due_projections(session, tenant)
    stop()
    assert behind == []
    assert counted[0] <= 2, (
        f"asking what is behind took {counted[0]} statements; the twelve projections "
        "are scalar expressions over one snapshot and belong in one read"
    )


def test_the_selection_does_not_grow_a_statement_per_company(session, business):
    """What SC-003 is about: the sweep's discovery must not scale with the instance."""
    quiet(session, business)
    counted, stop = statements(session)
    scheduler_tenants(session)
    stop()
    assert counted[0] <= 4, (
        f"discovering what to do took {counted[0]} statements for one company; it must "
        "be a fixed number however many companies exist"
    )


def test_the_progress_row_says_the_same_as_the_events(session, business):
    """The selection believes this number, so it may not drift from the events."""
    from reality.db.core import BusinessEvent

    tenant = quiet(session, business)
    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-FR004-C",
        business.customer.id,
        "5",
        document_date="2026-08-03",
    )
    session.flush()
    recorded = session.scalar(
        select(func.max(BusinessEvent.sequence)).where(
            BusinessEvent.tenant_id == tenant
        )
    )
    progress = session.get(TenantEventProgress, tenant)
    assert progress is not None and progress.last_event_sequence == recorded


def test_a_company_that_is_offered_actually_has_something_to_enqueue(session, business):
    """The filter over-selects on purpose; it may not under-select."""
    tenant = quiet(session, business)
    create_document(
        session,
        tenant,
        "sales_order",
        "ORD-FR004-D",
        business.customer.id,
        "7",
        document_date="2026-08-04",
    )
    session.flush()
    assert tenant in due_projection_tenants(session)
    assert due_projections(session, tenant)
    assert enqueue_due_projections(session, tenant) is not None
