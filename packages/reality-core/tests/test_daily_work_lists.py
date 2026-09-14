from datetime import UTC, datetime, timedelta

from reality.services.core import change_proposal_count, change_proposals, create_tenant
from reality.tools.application import propose_tool


def test_pending_queue_filters_before_paging_and_orders_oldest_first(session):
    tenant = create_tenant(session, "Work queue")
    foreign = create_tenant(session, "Other queue")
    start = datetime(2026, 1, 1, tzinfo=UTC)
    expected = []
    for index in range(6):
        row = propose_tool(
            session,
            tenant.id,
            "demo_seed" if index % 2 else "location_create",
            {"index": index},
        )
        row.created_at = start + timedelta(minutes=index)
        if index % 2:
            expected.append(row.id)
    propose_tool(session, foreign.id, "demo_seed", {})
    session.commit()
    assert (
        change_proposal_count(session, tenant.id, pending=True, tool="demo_seed") == 3
    )
    first = change_proposals(
        session, tenant.id, pending=True, tool="demo_seed", limit=2
    )
    second = change_proposals(
        session, tenant.id, pending=True, tool="demo_seed", offset=2, limit=2
    )
    assert [row.id for row in first + second] == expected
    assert (
        change_proposal_count(
            session, tenant.id, pending=True, tool="demo_seed", query="location"
        )
        == 0
    )
