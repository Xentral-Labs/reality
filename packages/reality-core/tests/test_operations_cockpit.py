"""Live business observation keeps identity, coverage and authorization explicit."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from test_shipping_performance import OBSERVED
from test_shipping_performance import planned_shipping as _planned_shipping

from reality.db.core import BusinessEvent, MCPAccessToken, TenantMembership, uid
from reality.db.interactions import Interaction
from reality.db.mcp_authorization import MCPClientGrant
from reality.services import activity_volume, core, operations_cockpit
from reality.services.memberships import Principal

planned_shipping = _planned_shipping


def test_case_register_retains_its_own_snapshot_time_without_existing_work(
    scheduled_database, monkeypatch
):
    # BUSINESS PURPOSE: Independently refreshed responsibility data needs its own truthful freshness time.
    # BUSINESS RULE: Return the read snapshot's time even during incomplete rollout; never create work or borrow another panel's clock.
    _, factory, tenant, owner = scheduled_database
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    with factory() as session:
        before = session.scalar(select(func.clock_timestamp()))
        events = list(session.scalars(select(BusinessEvent.id)))
        value = operations_cockpit.case_register(session, tenant, Principal(owner))
        after = session.scalar(select(func.clock_timestamp()))
        assert before <= datetime.fromisoformat(value["observed_at"]) <= after
        assert value["adopted"] is True
        assert value["counts"] == dict.fromkeys(
            ("automation", "human", "outstanding", "completed", "abandoned"), 0
        )
        assert value["coordination"]["coverage_ready"] is False
        assert value["total"] == 0 and value["items"] == []
        assert list(session.scalars(select(BusinessEvent.id))) == events


def test_rolling_activity_uses_first_recording_and_complete_counts_before_limit(
    session, business
):
    # BUSINESS PURPOSE: Activity shows newly recorded business entities, not retries or throughput.
    # BUSINESS RULE: Recording time, tenant creation and bounded samples never alter full totals.
    end = datetime(2026, 10, 6, 12, 30, 30, tzinfo=UTC)
    business.tenant.created_at = end - timedelta(minutes=7)
    for index in range(63):
        row = core.emit_business_event(
            session,
            business.tenant.id,
            "movement.recorded",
            "movement",
            f"movement-{index}",
            {},
            occurred_at=end - timedelta(days=2),
        )
        row.recorded_at = end - timedelta(minutes=2)
    original = core.emit_business_event(
        session, business.tenant.id, "movement.recorded", "movement", "repeated", {}
    )
    original.recorded_at = end - timedelta(hours=2)
    duplicate = core.emit_business_event(
        session, business.tenant.id, "movement.recorded", "movement", "repeated", {}
    )
    duplicate.recorded_at = end - timedelta(minutes=1)
    session.flush()
    before = list(session.scalars(select(BusinessEvent.id)))
    result = activity_volume.rolling(session, business.tenant.id, minutes=15, as_of=end)
    assert result["total"] == 63
    assert result["counts"] == {
        "orders": 0,
        "reservations": 0,
        "movements": 63,
        "documents": 0,
    }
    assert result["coverage_start"] == business.tenant.created_at.isoformat()
    assert len(result["buckets"]) == 16
    assert result["buckets"][0]["partial"] is True
    assert result["buckets"][-1]["partial"] is True
    assert len(result["events"]) == 50 and result["has_more"]
    assert all(row["occurred_at"] != row["recorded_at"] for row in result["events"])
    assert list(session.scalars(select(BusinessEvent.id))) == before
    for minutes in (0, 6, 61, True):
        with pytest.raises(core.InvalidOperation):
            activity_volume.rolling(session, business.tenant.id, minutes=minutes)


def access_records(session, business, owner):
    tokens = []
    for index in range(63):
        token = MCPAccessToken(
            id=f"token_{index:03}",
            tenant_id=business.tenant.id,
            name="Shared shipping Agent",
            token_prefix="secret-prefix",
            token_hash=uid("hash"),
            created_by_user_id=owner.id,
            allowed_tools='["*"]',
        )
        session.add(token)
        tokens.append(token)
    for index in range(2):
        session.add(
            MCPClientGrant(
                id=f"grant_{index}",
                tenant_id=business.tenant.id,
                user_id=owner.id,
                client_id="same-client",
                client_name="Shared shipping Agent",
                client_uri=None,
                allowed_tools=["inventory"],
                scopes=["reality:read"],
            )
        )
    session.flush()
    return tokens


def test_named_access_paging_is_complete_redacted_and_never_invents_runtime_identity(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: An owner sees exactly which named accesses contribute to the company.
    # BUSINESS RULE: Duplicate names remain distinct; only exact credential attribution is evidence of action.
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    tokens = access_records(session, business, scheduled_owner)
    observed = datetime(2026, 10, 6, 12, 30, tzinfo=UTC)
    tokens[0].last_used_at = observed
    tokens[1].revoked_at = observed
    session.add(
        Interaction(
            id=uid("interaction"),
            tenant_id=business.tenant.id,
            started_at=observed,
            recorded_at=observed,
            duration_ms=20,
            channel="mcp",
            kind="read",
            operation="inventory",
            outcome="failed",
            mcp_token_id=tokens[0].id,
            actor_user_id=scheduled_owner.id,
            correlation_id=uid("correlation"),
            summary={},
        )
    )
    session.flush()
    principal = Principal(scheduled_owner.id)
    page = operations_cockpit.agents(session, business.tenant.id, principal, limit=50)
    assert page["total"] == 64
    assert len(page["items"]) == 50 and page["has_more"]
    next_page = operations_cockpit.agents(
        session, business.tenant.id, principal, limit=50, after=page["next_after"]
    )
    assert next_page["total"] == 64 and len(next_page["items"]) == 14
    rows = page["items"] + next_page["items"]
    assert len({row["identity"] for row in rows}) == 64
    oauth = [row for row in rows if row["connection_kind"] == "oauth"]
    assert len(oauth) == 2 and all(row["observed_action"] is None for row in oauth)
    exact = next(row for row in rows if row["identity"] == "manual:token_000")
    assert exact["observed_action"]["outcome"] == "failed"
    assert exact["runtime_state"] == "unknown"
    assert all(row["runtime_state"] == "unknown" for row in rows)
    assert "secret-prefix" not in str(page) + str(next_page)
    assert "token_hash" not in str(page) + str(next_page)
    assert tokens[2].last_used_at is None
    with pytest.raises(core.InvalidOperation):
        operations_cockpit.agents(
            session,
            business.tenant.id,
            principal,
            access_state="revoked",
            after=page["next_after"],
        )


def test_member_reads_business_activity_but_cannot_discover_access_names(
    session, business, scheduled_owner, monkeypatch
):
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    access_records(session, business, scheduled_owner)
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    member.role = "member"
    session.flush()
    principal = Principal(scheduled_owner.id)
    assert (
        operations_cockpit.activity(session, business.tenant.id, principal)["total"]
        == 0
    )
    with pytest.raises((core.NotFound, core.InvalidOperation)):
        operations_cockpit.agents(session, business.tenant.id, principal)


def test_cockpit_deviation_preserves_causal_blockers_without_inventing_a_response(
    session, business, scheduled_owner, monkeypatch, planned_shipping
):
    # BUSINESS PURPOSE: An observer sees the actual reason work cannot progress.
    # BUSINESS RULE: Planning actions stay visible without becoming causal blocker responses or provider outcomes.
    commitment = planned_shipping
    core.hold_commitment(
        session,
        business.tenant.id,
        commitment.id,
        "customer_request",
        "Customer requested a pause",
    )
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    monkeypatch.setattr(
        operations_cockpit.shipping_performance, "now", lambda: OBSERVED
    )
    session.flush()
    value = operations_cockpit.operations_cockpit(
        session, business.tenant.id, Principal(scheduled_owner.id), day="2026-10-06"
    )
    assert value["deviations"][0]["order_id"] == commitment.document_id
    blockers = value["deviations"][0]["blockers"][commitment.id]
    assert any(row["code"] == "commitment_hold" for row in blockers)
    deviation = value["deviations"][0]
    # Default coordination now retains the prepared/accepted planning proposals.
    # They are real case-linked actions, not proof of a response to the later hold.
    assert len(deviation["recorded_case_actions"]) == 2
    assert {row["type"] for row in deviation["recorded_case_actions"]} == {
        "tool:shipping_plan_state"
    }
    assert {row["status"] for row in deviation["recorded_case_actions"]} == {
        "proposed",
        "executed",
    }
    assert deviation["response_state"] == "recorded_case_actions"
    assert deviation["response_scope"] == "case_linked_no_causal_assertion"
    assert deviation["next_recorded_check"] is None
    assert all(
        row["external_outcome"] == "not_established_by_execution_status"
        for row in deviation["recorded_case_actions"]
    )


def test_dense_shipping_series_aggregate_every_order_at_exact_boundaries():
    # BUSINESS PURPOSE: An enterprise forecast must remain readable without losing source-backed order counts.
    # BUSINESS RULE: Dense curves contain complete cumulative counts at bounded disclosed boundaries, including opening and terminal values.
    from datetime import UTC, datetime, timedelta

    from reality.services.shipping_performance import _series

    start = datetime(2026, 10, 6, tzinfo=UTC)
    end = start + timedelta(hours=25)
    times = {str(i): start + timedelta(seconds=i * 70) for i in range(1400)}
    times["earlier"] = start - timedelta(seconds=1)
    times["duplicate"] = times["17"]
    times["terminal"] = end
    points = _series(times, start, end)
    assert len(points) <= 302
    assert points[0]["at"] == start.isoformat()
    assert points[-1]["at"] == end.isoformat()
    for index, point in enumerate(points):
        instant = datetime.fromisoformat(point["at"])
        expected = (
            sum(value < start for value in times.values())
            if index == 0
            else sum(value <= instant for value in times.values())
        )
        assert point["count"] == expected
    assert points[-1]["count"] == sum(value <= end for value in times.values())


def test_shipping_snapshot_does_not_repeat_independent_responsibility_register(
    session, business, planned_shipping, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: Shipping live refresh must not recompute a register the responsibility panel already reads independently.
    # BUSINESS RULE: Keep full canonical register counts/evidence in its own observation and shipping totals/deviations in theirs.
    from reality.services import operational_cases

    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    tenant = business.tenant.id
    principal = Principal(scheduled_owner.id)
    session.flush()
    before = operations_cockpit.case_register(session, tenant, principal)
    assert before["counts"]["automation"] > 0
    original = operational_cases.register_cases
    calls = []

    def registered(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(operational_cases, "register_cases", registered)
    overview = operations_cockpit.operations_cockpit(
        session, tenant, principal, day=OBSERVED.date().isoformat()
    )
    assert "supported_cases" not in overview
    assert calls == []
    after = operations_cockpit.case_register(session, tenant, principal)
    assert after["counts"] == before["counts"]
    assert after["items"] == before["items"]
    assert calls == [True]
    assert overview["shipping"]["totals"]["due"] == 1
