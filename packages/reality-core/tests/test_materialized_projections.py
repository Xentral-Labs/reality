from sqlalchemy import func, select

from reality.db.core import BusinessEvent, ProjectionCheckpoint, ProjectionRow
from reality.services.core import (
    cancel_commitment,
    create_commitment,
    record_movement,
    release_reservation,
    reserve,
)
from reality.services.projections import (
    COMMITMENT_REGISTER,
    FULFILLMENT_BLOCKERS,
    FULFILLMENT_QUEUE,
    INVENTORY,
    ISSUES,
    ITEM_SUPPLY_DEMAND,
    MATERIALIZED_PROJECTIONS,
    TENANT_USAGE,
    projection_rows,
    rebuild_projections,
    relevant_event_target,
)


def _customer_commitment(session, business, quantity="2"):
    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        "2026-09-10",
    )


def test_materialized_operational_views_refresh_from_business_events(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        2,
        to_location_id=business.location.id,
    )
    commitment = _customer_commitment(session, business)

    rebuild_projections(session, business.tenant.id, MATERIALIZED_PROJECTIONS)
    queue = projection_rows(session, business.tenant.id, FULFILLMENT_QUEUE)
    blockers = projection_rows(session, business.tenant.id, FULFILLMENT_BLOCKERS)
    supply = projection_rows(session, business.tenant.id, ITEM_SUPPLY_DEMAND)
    inventory = projection_rows(session, business.tenant.id, INVENTORY)
    materialized_issues = projection_rows(session, business.tenant.id, ISSUES)
    register = projection_rows(session, business.tenant.id, COMMITMENT_REGISTER)
    usage = projection_rows(session, business.tenant.id, TENANT_USAGE)

    assert queue[0]["order_key"] == commitment.id
    assert queue[0]["ship_ready"] is False
    assert queue[0]["blocking_reasons"] == ["insufficient_reservation"]
    assert blockers[0]["commitment_id"] == commitment.id
    assert supply[0]["open_customer_demand"] == "2"
    assert supply[0]["uncovered_demand"] == "2"
    assert inventory[0]["available"] == "2.0000"
    assert materialized_issues[0]["record_id"] == commitment.id
    assert register[0]["commitment_id"] == commitment.id
    assert usage[0]["state"] == "in_use"

    latest_sequence = session.scalar(
        select(func.max(BusinessEvent.sequence)).where(
            BusinessEvent.tenant_id == business.tenant.id
        )
    )
    checkpoints = list(
        session.scalars(
            select(ProjectionCheckpoint).where(
                ProjectionCheckpoint.tenant_id == business.tenant.id
            )
        )
    )
    assert {row.projection_name for row in checkpoints} == set(MATERIALIZED_PROJECTIONS)
    assert all(row.last_event_sequence <= latest_sequence for row in checkpoints)
    assert all(
        row.last_event_sequence
        == session.scalar(
            select(relevant_event_target(business.tenant.id, row.projection_name))
        )
        for row in checkpoints
    )

    reservation = reserve(session, business.tenant.id, commitment.id).reservation
    rebuild_projections(session, business.tenant.id, MATERIALIZED_PROJECTIONS)
    refreshed = projection_rows(session, business.tenant.id, FULFILLMENT_QUEUE)
    assert refreshed[0]["ship_ready"] is True
    assert projection_rows(session, business.tenant.id, FULFILLMENT_BLOCKERS) == []

    release_reservation(session, business.tenant.id, reservation.id)
    rebuild_projections(session, business.tenant.id, MATERIALIZED_PROJECTIONS)
    released = projection_rows(session, business.tenant.id, FULFILLMENT_QUEUE)
    assert released[0]["ship_ready"] is False


def test_materialized_projection_removes_stale_rows(session, business):
    commitment = _customer_commitment(session, business, "1")
    rebuild_projections(session, business.tenant.id, MATERIALIZED_PROJECTIONS)
    row_id = session.scalar(
        select(ProjectionRow.id).where(
            ProjectionRow.tenant_id == business.tenant.id,
            ProjectionRow.projection_name == FULFILLMENT_QUEUE,
            ProjectionRow.record_key == commitment.id,
        )
    )
    assert row_id

    cancel_commitment(session, business.tenant.id, commitment.id, reason="Test cancellation")
    rebuild_projections(session, business.tenant.id, MATERIALIZED_PROJECTIONS)

    assert projection_rows(session, business.tenant.id, FULFILLMENT_QUEUE) == []
    assert (
        session.scalar(
            select(ProjectionRow.id).where(
                ProjectionRow.tenant_id == business.tenant.id,
                ProjectionRow.id == row_id,
            )
        )
        is None
    )
