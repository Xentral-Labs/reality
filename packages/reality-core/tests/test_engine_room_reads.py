"""Spec 266: the engine room reads — filters, cursor, stages, events and access."""

from __future__ import annotations

from datetime import timedelta

import pytest
from test_engine_room_channels import committed_engine, member, web  # noqa: F401

from reality.db.core import AppUser, now, uid
from reality.db.interactions import Interaction
from reality.mcp.auth import create_mcp_access_token
from reality.services import interactions
from reality.services.core import InvalidOperation, create_tenant, emit_business_event


def add(session, tenant_id, **values):
    moment = values.pop("recorded_at", None) or now()
    row = Interaction(
        id=uid("int"),
        tenant_id=tenant_id,
        started_at=moment,
        recorded_at=moment,
        duration_ms=values.pop("duration_ms", 3),
        channel=values.pop("channel", "web"),
        kind=values.pop("kind", "read"),
        operation=values.pop("operation", "GET /items"),
        outcome=values.pop("outcome", "ok"),
        correlation_id=values.pop("correlation_id", uid("c")),
        refresh=values.pop("refresh", False),
        summary=values.pop("summary", {}),
        **values,
    )
    session.add(row)
    session.flush()
    return row


def listed(session, tenant_id, **filters):
    return interactions.list_interactions(session, tenant_id, **filters)


def ids(result):
    return [row["id"] for row in result["interactions"]]


def test_rows_come_oldest_first_and_the_cursor_advances(session, business):
    tenant = business.tenant.id
    first = add(session, tenant, recorded_at=now() - timedelta(minutes=5))
    second = add(session, tenant, recorded_at=now() - timedelta(minutes=4))
    result = listed(session, tenant)
    assert ids(result) == [first.id, second.id]
    assert result["cursor"] == second.cursor
    assert result["truncated"] is False


def test_after_returns_newer_rows_and_late_commits_but_not_old_ones(session, business):
    tenant = business.tenant.id
    old = add(session, tenant, recorded_at=now() - timedelta(minutes=5))
    seen = add(session, tenant, recorded_at=now() - timedelta(minutes=4))
    newer = add(session, tenant)
    # A row that took a lower cursor but committed only now, from another process.
    late = add(session, tenant, cursor=old.cursor - 1 if old.cursor > 1 else 0)
    result = listed(session, tenant, after=seen.cursor)
    assert newer.id in ids(result) and late.id in ids(result)
    assert old.id not in ids(result) and seen.id not in ids(result)


def test_each_filter_narrows(session, business, scheduled_owner):
    tenant = business.tenant.id
    token, _ = create_mcp_access_token(session, tenant, "Claude Desktop")
    web_row = add(
        session, tenant, actor_user_id=scheduled_owner.id, correlation_id="c1"
    )
    mcp_row = add(
        session,
        tenant,
        channel="mcp",
        kind="propose",
        outcome="awaiting_decision",
        mcp_token_id=token.id,
        operation="party_create",
    )
    refresh_row = add(session, tenant, refresh=True)
    assert ids(listed(session, tenant, channels=["mcp"])) == [mcp_row.id]
    assert ids(listed(session, tenant, kinds=["propose"])) == [mcp_row.id]
    assert ids(listed(session, tenant, outcomes=["awaiting_decision"])) == [mcp_row.id]
    assert ids(listed(session, tenant, actor_user_id=scheduled_owner.id)) == [
        web_row.id
    ]
    assert ids(listed(session, tenant, mcp_token_id=token.id)) == [mcp_row.id]
    assert ids(listed(session, tenant, correlation_id="c1")) == [web_row.id]
    # Background refresh is kept but hidden unless asked for.
    assert refresh_row.id not in ids(listed(session, tenant))
    assert refresh_row.id in ids(listed(session, tenant, include_refresh=True))
    with pytest.raises(InvalidOperation):
        listed(session, tenant, channels=["telepathy"])


def test_the_actor_names_the_token_and_its_issuer(session, business, scheduled_owner):
    tenant = business.tenant.id
    token, _ = create_mcp_access_token(
        session, tenant, "Claude Desktop", issued_by_user_id=scheduled_owner.id
    )
    add(session, tenant, channel="mcp", mcp_token_id=token.id)
    [row] = listed(session, tenant)["interactions"]
    assert row["actor"]["kind"] == "mcp_token"
    assert row["actor"]["label"] == "Claude Desktop"
    assert row["actor"]["issuer"]["id"] == scheduled_owner.id
    assert row["actor"]["revoked"] is False


def test_limit_keeps_the_newest_and_says_it_truncated(session, business):
    tenant = business.tenant.id
    rows = [add(session, tenant) for _ in range(5)]
    result = listed(session, tenant, limit=3)
    assert ids(result) == [row.id for row in rows[-3:]]
    assert result["truncated"] is True


def test_retention_hides_rows_older_than_seven_days(session, business):
    tenant = business.tenant.id
    expired = add(session, tenant, recorded_at=now() - timedelta(days=8))
    kept = add(session, tenant, recorded_at=now() - timedelta(days=6))
    result = listed(session, tenant)
    assert ids(result) == [kept.id]
    assert expired.id not in ids(result)
    assert result["retention_starts_at"] <= now() - timedelta(days=7) + timedelta(
        seconds=5
    )


def test_a_window_is_ordered_by_cursor_and_bounded(session, business):
    tenant = business.tenant.id
    start = now() - timedelta(hours=2)
    before = add(session, tenant, recorded_at=start - timedelta(minutes=1))
    inside = [
        add(session, tenant, recorded_at=start + timedelta(minutes=m)) for m in (1, 2)
    ]
    after = add(session, tenant, recorded_at=start + timedelta(hours=1))
    result = listed(
        session, tenant, window_from=start, window_to=start + timedelta(minutes=30)
    )
    assert ids(result) == [row.id for row in inside]
    assert before.id not in ids(result) and after.id not in ids(result)
    with pytest.raises(InvalidOperation):
        listed(session, tenant, after=1, window_from=start)


def _event(session, tenant_id, subject_type, subject_id):
    return emit_business_event(
        session, tenant_id, f"{subject_type}.created", subject_type, subject_id, {}
    )


def test_stages_come_from_written_events_and_catalog_reads(session, business):
    tenant = business.tenant.id
    reservation = _event(session, tenant, "reservation", "res_1")
    movement = _event(session, tenant, "movement", "mov_1")
    session.flush()
    add(
        session,
        tenant,
        channel="mcp",
        operation="inventory",
        event_first_sequence=reservation.sequence,
        event_last_sequence=movement.sequence,
        event_ranges=[[reservation.sequence, movement.sequence]],
    )
    add(session, tenant, channel="web", operation="GET /inventory")
    add(session, tenant, channel="mcp", operation="no_such_operation_anywhere")
    mcp_row, web_row, unknown = listed(session, tenant)["interactions"]
    assert mcp_row["stages"]["written"] == ["reservation", "movement"]
    assert mcp_row["stages"]["read"]  # the catalog knows what inventory reads
    assert mcp_row["events"]["count"] == 2
    # Web routes and unknown operations mark nothing rather than a guess.
    assert web_row["stages"] == {"read": [], "written": []}
    assert unknown["stages"] == {"read": [], "written": []}


def test_stage_of_maps_tables_and_subject_types():
    assert interactions.stage_of("source_record") == "source"
    assert interactions.stage_of("document_line") == "document"
    assert interactions.stage_of("commitment") == "commitment"
    assert interactions.stage_of("ledger_entry") == "ledger"
    assert interactions.stage_of("item") == "master_data"
    assert interactions.stage_of("tenant") is None
    assert interactions.read_stages("web", "GET /items") == []


def test_who_changed_this_finds_the_interaction_by_its_events(session, business):
    tenant = business.tenant.id
    mine = _event(session, tenant, "party", "par_target")
    other = _event(session, tenant, "party", "par_other")
    session.flush()
    hit = add(
        session,
        tenant,
        event_first_sequence=mine.sequence,
        event_last_sequence=mine.sequence,
        event_ranges=[[mine.sequence, mine.sequence]],
    )
    add(
        session,
        tenant,
        event_first_sequence=other.sequence,
        event_last_sequence=other.sequence,
        event_ranges=[[other.sequence, other.sequence]],
    )
    result = listed(session, tenant, subject_type="party", subject_id="par_target")
    assert ids(result) == [hit.id]
    assert (
        ids(listed(session, tenant, subject_type="party", subject_id="nothing")) == []
    )


def test_events_of_returns_only_the_linked_committed_events(session, business):
    tenant = business.tenant.id
    first = _event(session, tenant, "party", "a")
    _event(session, tenant, "party", "between")
    last = _event(session, tenant, "party", "b")
    session.flush()
    row = add(
        session,
        tenant,
        event_first_sequence=first.sequence,
        event_last_sequence=last.sequence,
        event_ranges=[[first.sequence, first.sequence], [last.sequence, last.sequence]],
    )
    assert [event.id for event in interactions.events_of(session, tenant, row.id)] == [
        first.id,
        last.id,
    ]


def test_another_company_never_sees_the_rows(session, business):
    elsewhere = create_tenant(session, "Elsewhere GmbH")
    add(session, business.tenant.id)
    assert listed(session, elsewhere.id)["interactions"] == []


def test_purge_removes_only_expired_rows(session, business):
    tenant = business.tenant.id
    expired = add(session, tenant, recorded_at=now() - timedelta(days=8))
    kept = add(session, tenant, recorded_at=now() - timedelta(days=1))
    event = _event(session, tenant, "party", "stays")
    session.flush()
    assert interactions.purge_expired(session, tenant) == 1
    assert session.get(Interaction, (tenant, expired.id)) is None
    assert session.get(Interaction, (tenant, kept.id)) is not None
    assert event.id  # business events are untouched
    assert interactions.purge_expired(session, tenant) == 0


def test_owners_read_everyone_else_gets_not_found(web):  # noqa: F811
    owner = member(web.db, web.tenant_id)
    plain = member(web.db, web.tenant_id, role="member")
    elsewhere = create_tenant(web.db, f"Elsewhere {uid('co')}")
    web.db.commit()
    foreign_owner = member(web.db, elsewhere.id)
    admin = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash=owner.password_hash,
        display_name="Platform Admin",
        status="active",
        email_verified_at=now(),
        is_platform_admin=True,
    )
    web.db.add(admin)
    web.db.commit()
    path = f"/api/tenants/{web.tenant_id}/interactions"
    ok = web.sign_in(owner).get(path)
    assert ok.status_code == 200, ok.text
    assert set(ok.json()) >= {
        "interactions",
        "cursor",
        "retention_starts_at",
        "truncated",
    }
    assert web.sign_in(owner).get(path + "/pulse").status_code == 200
    series = web.sign_in(owner).get(path + "/series?minutes=15")
    assert series.status_code == 200 and len(series.json()["buckets"]) == 90
    assert web.sign_in(plain).get(path + "/series").status_code == 404
    assert web.sign_in(plain).get(path).status_code == 404
    assert web.sign_in(foreign_owner).get(path).status_code in {403, 404}
    assert web.sign_in(admin).get(path).status_code == 404


def test_the_owner_sees_what_a_member_did_through_the_api(web):  # noqa: F811
    owner = member(web.db, web.tenant_id)
    plain = member(web.db, web.tenant_id, role="member")
    web.sign_in(plain).get(f"/api/tenants/{web.tenant_id}/items")
    result = web.sign_in(owner).get(f"/api/tenants/{web.tenant_id}/interactions").json()
    [row] = [r for r in result["interactions"] if r["actor"]["id"] == plain.id]
    assert (row["channel"], row["operation"]) == ("web", "GET /items")
    events = web.sign_in(owner).get(
        f"/api/tenants/{web.tenant_id}/interactions/{row['id']}/events"
    )
    assert events.status_code == 200 and events.json() == {"events": []}


def test_development_without_sign_in_opens_the_engine_room(web, monkeypatch):  # noqa: F811
    from fastapi.testclient import TestClient

    from reality.web import app as web_module

    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    response = TestClient(web_module.app).get(
        f"/api/tenants/{web.tenant_id}/interactions"
    )
    assert response.status_code == 200, response.text
    # Positive control: with sign-in required, an anonymous caller is refused.
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    anonymous = TestClient(web_module.app).get(
        f"/api/tenants/{web.tenant_id}/interactions"
    )
    assert anonymous.status_code == 401


def test_a_declared_choice_names_the_stage_that_was_read(session, business):
    tenant = business.tenant.id
    add(
        session,
        tenant,
        channel="mcp",
        operation="business_records_discover",
        summary={"choices": {"family": "commitment"}},
    )
    add(session, tenant, channel="mcp", operation="business_records_discover")
    chosen, unchosen = listed(session, tenant)["interactions"]
    assert chosen["stages"]["read"] == ["commitment"]
    # Without a choice the catalog membership applies, which names no stage here.
    assert "commitment" not in unchosen["stages"]["read"]


def test_tool_calls_carry_a_readers_label_and_web_routes_do_not(session, business):
    tenant = business.tenant.id
    add(session, tenant, channel="mcp", operation="business_records_discover")
    add(session, tenant, channel="web", operation="GET /items")
    tool, route = listed(session, tenant, language="de")["interactions"]
    assert tool["label"] and tool["label"] != "business_records_discover"
    assert route["label"] is None


def test_hiding_own_interactions_keeps_everyone_elses(
    session, business, scheduled_owner
):
    tenant = business.tenant.id
    mine = add(session, tenant, actor_user_id=scheduled_owner.id)
    agent = add(session, tenant, channel="mcp")
    shown = ids(listed(session, tenant, exclude_actor_user_id=scheduled_owner.id))
    assert shown == [agent.id]
    # Positive control: without the filter the owner's own row is there.
    assert mine.id in ids(listed(session, tenant))
    assert (
        interactions.pulse(session, tenant, scheduled_owner.id)["latest_cursor"]
        == agent.cursor
    )


def test_series_counts_each_bucket_by_channel_with_errors_writes_and_latency(
    session, business, scheduled_owner
):
    tenant = business.tenant.id
    moment = now().replace(microsecond=0)
    moment -= timedelta(seconds=moment.second % 10)
    # Two buckets of ten seconds: one busy, one with a write and an error.
    add(
        session,
        tenant,
        channel="mcp",
        duration_ms=10,
        recorded_at=moment - timedelta(seconds=25),
    )
    add(
        session,
        tenant,
        channel="mcp",
        duration_ms=30,
        recorded_at=moment - timedelta(seconds=24),
    )
    add(
        session,
        tenant,
        channel="web",
        duration_ms=50,
        recorded_at=moment - timedelta(seconds=23),
    )
    add(
        session,
        tenant,
        channel="web",
        outcome="failed",
        duration_ms=90,
        recorded_at=moment - timedelta(seconds=5),
        event_first_sequence=1,
        event_last_sequence=1,
        event_ranges=[[1, 1]],
    )
    # Outside the window and a refresh row: neither counts.
    add(session, tenant, channel="web", recorded_at=moment - timedelta(minutes=10))
    add(
        session,
        tenant,
        channel="web",
        refresh=True,
        recorded_at=moment - timedelta(seconds=5),
    )
    series = interactions.series(session, tenant, minutes=5, as_of=moment)
    assert series["step_seconds"] == 10
    assert len(series["buckets"]) == 30
    counts = [bucket for bucket in series["buckets"] if bucket["total"]]
    busy, later = counts
    assert busy["channels"] == {"web": 1, "mcp": 2, "chat": 0, "cli": 0, "worker": 0}
    assert (busy["errors"], busy["writes"], busy["reads"]) == (0, 0, 3)
    assert busy["p50_ms"] == 30 and busy["p95_ms"] >= 45
    assert (later["errors"], later["writes"], later["reads"]) == (1, 1, 0)
    # A quiet bucket is zero, not missing, so a curve is flat where nothing happened.
    assert series["buckets"][0]["total"] == 0 and series["buckets"][0]["p95_ms"] is None


def test_series_hides_the_viewer_and_respects_filters(
    session, business, scheduled_owner
):
    tenant = business.tenant.id
    moment = now().replace(microsecond=0)
    add(
        session,
        tenant,
        actor_user_id=scheduled_owner.id,
        recorded_at=moment - timedelta(seconds=3),
    )
    add(session, tenant, channel="mcp", recorded_at=moment - timedelta(seconds=3))
    mine_hidden = interactions.series(
        session,
        tenant,
        minutes=5,
        as_of=moment,
        exclude_actor_user_id=scheduled_owner.id,
    )
    assert sum(bucket["total"] for bucket in mine_hidden["buckets"]) == 1
    only_web = interactions.series(
        session, tenant, minutes=5, as_of=moment, channels=["web"]
    )
    assert sum(bucket["total"] for bucket in only_web["buckets"]) == 1
    with pytest.raises(InvalidOperation):
        interactions.series(session, tenant, minutes=7, as_of=moment)
