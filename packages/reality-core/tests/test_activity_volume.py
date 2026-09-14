from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from unified_fixtures import delivery_fixture

from reality.db.core import BusinessEvent
from reality.services import activity_volume
from reality.services.core import (
    create_manual_order,
    create_tenant,
    emit_business_event,
    reserve,
)


def test_volume_counts_business_entities_not_import_steps(session, business):
    fixture = delivery_fixture(session, business)
    reserve(session, business.tenant.id, fixture.commitment.id, "1")
    create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "GRAPH-1",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": "pcs",
                "label": "Item",
                "gross_amount": "10",
            }
        ],
        "10",
    )
    movement = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.event_type == "movement.recorded",
        )
    )
    emit_business_event(
        session,
        business.tenant.id,
        "movement.recorded",
        "movement",
        movement.subject_id,
        {},
    )
    end = datetime.now(UTC) + timedelta(seconds=1)
    graph = activity_volume.volume(session, business.tenant.id, days=1, as_of=end)
    totals = {
        key: sum(row["counts"][key] for row in graph["buckets"])
        for key in activity_volume.CATEGORIES
    }
    assert totals == {"orders": 1, "reservations": 1, "movements": 1, "documents": 0}
    details = activity_volume.details(
        session, business.tenant.id, start=end - timedelta(days=1), end=end
    )
    assert details["total"] == 3
    assert len({row["id"] for row in details["events"]}) == 3
    assert (
        activity_volume.volume(session, create_tenant(session, "Foreign").id, days=1)[
            "total"
        ]
        == 0
    )


def test_bucket_boundaries_and_creation_coverage(session, business):
    end = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    business.tenant.created_at = end - timedelta(hours=2)
    for minute in (-31, -30, 0):
        row = emit_business_event(
            session,
            business.tenant.id,
            "movement.recorded",
            "movement",
            f"m{minute}",
            {},
        )
        row.recorded_at = end + timedelta(minutes=minute)
    session.flush()
    graph = activity_volume.volume(session, business.tenant.id, days=1, as_of=end)
    assert graph["total"] == 2  # Half-open window excludes exactly end.
    assert len(graph["buckets"]) == 48
    assert graph["buckets"][-1]["counts"]["movements"] == 1
    assert graph["buckets"][-2]["counts"]["movements"] == 1
    assert graph["coverage_start"] == business.tenant.created_at.isoformat()
    assert (
        activity_volume.details(
            session, business.tenant.id, start=end - timedelta(minutes=30), end=end
        )["total"]
        == 1
    )
    for days in (0, 2, 31):
        with pytest.raises(ValueError):
            activity_volume.volume(session, business.tenant.id, days=days)


def test_duplicate_recording_cannot_reappear_in_a_later_drilldown(session, business):
    end = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    for minutes in (60, 10):
        row = emit_business_event(
            session, business.tenant.id, "movement.recorded", "movement", "same", {}
        )
        row.recorded_at = end - timedelta(minutes=minutes)
    session.flush()
    assert (
        activity_volume.details(
            session, business.tenant.id, start=end - timedelta(minutes=30), end=end
        )["total"]
        == 0
    )


from test_playground_api import playground_http as _playground_http

playground_http = _playground_http


def test_graph_http_uses_practice_admission_and_validates_ranges(
    session, playground_http
):
    client, tenant, user, run, login = playground_http
    run.sandbox_kind = "practice"
    session.flush()
    assert client.get(f"/api/tenants/{tenant.id}/activity-volume").status_code == 401
    login(user)
    assert (
        client.get(f"/api/tenants/{tenant.id}/activity-volume?days=30").status_code
        == 200
    )
    assert (
        client.get(f"/api/tenants/{tenant.id}/activity-volume?days=2").status_code
        == 422
    )
    assert (
        client.get(
            f"/api/tenants/{tenant.id}/activity-volume/events?start=2026-09-09&end=2026-09-10"
        ).status_code
        == 422
    )
    assert client.get("/api/tenants/foreign/activity-volume").status_code in (403, 404)
