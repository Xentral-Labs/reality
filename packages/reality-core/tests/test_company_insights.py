from datetime import UTC, datetime
from decimal import Decimal

import pytest
from unified_fixtures import delivery_fixture

from reality.services.company_insights import company_insights, insight_contributors
from reality.services.core import (
    correct_movement,
    create_tenant,
    record_movement,
    reserve,
)


def test_current_position_and_contributors_share_exact_totals(session, business):
    first = delivery_fixture(session, business)
    delivery_fixture(session, business)
    reserve(session, business.tenant.id, first.commitment.id, "12")
    result = company_insights(session, business.tenant.id, days=7)
    assert result["position"]["open"] == 2
    assert result["position"]["fully_reserved"] == 1
    assert Decimal(result["position"]["coverage_percent"]) == 50
    assert result["position"]["unknown_due"] == 2
    for metric in ["open", "fully_reserved", "needs_reservation", "overdue"]:
        records = insight_contributors(
            session, business.tenant.id, metric=metric, size=1
        )
        assert records["page"]["total"] == result["position"][metric]
        for record in records["items"]:
            assert record["label"] and record["label"] != record["id"]
    other = create_tenant(session, "Other analytics")
    assert company_insights(session, other.id)["position"]["coverage_percent"] is None


def test_utc_activity_excludes_corrected_original_and_compensation(session, business):
    delivery_fixture(session, business)
    tid = business.tenant.id
    movement = record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        occurred_at=datetime(2026, 9, 6, 23, 59, tzinfo=UTC),
    )
    observed = datetime(2026, 9, 7, 12, tzinfo=UTC)
    before = company_insights(session, tid, observed_at=observed)
    assert sum(row["shipped"] for row in before["series"]) == 1
    correct_movement(
        session,
        tid,
        movement.id,
        reason="Wrong count",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "from_location_id": business.location.id,
            "quantity": "3",
            "occurred_at": "2026-09-07T00:01:00Z",
        },
    )
    after = company_insights(session, tid, observed_at=observed)
    assert (
        next(row["shipped"] for row in after["series"] if row["date"] == "2026-09-06")
        == 0
    )
    assert (
        next(row["shipped"] for row in after["series"] if row["date"] == "2026-09-07")
        == 1
    )
    rows = insight_contributors(
        session, tid, metric="shipped", day="2026-09-07", observed_at=observed
    )
    assert rows["page"]["total"] == 1
    assert rows["items"][0]["id"] != movement.id
    with pytest.raises(ValueError):
        company_insights(session, tid, days=365)


def test_current_position_uses_revisions_and_remaining_work(session, business):
    from reality.services.core import revise_commitment

    fixture = delivery_fixture(session, business)
    observed = datetime(2026, 9, 7, 12, tzinfo=UTC)
    revise_commitment(
        session,
        business.tenant.id,
        fixture.commitment.id,
        due_at=datetime(2026, 9, 6, tzinfo=UTC),
    )
    result = company_insights(session, business.tenant.id, days=7, observed_at=observed)
    assert result["position"]["overdue"] == 1
    assert result["position"]["unknown_due"] == 0
    assert (
        company_insights(session, business.tenant.id, days=90, observed_at=observed)[
            "position"
        ]
        == result["position"]
    )
    with pytest.raises(ValueError):
        insight_contributors(
            session,
            business.tenant.id,
            metric="created",
            day="2020-01-01",
            observed_at=observed,
        )
