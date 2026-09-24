"""Spec 266: each crossing into the application leaves one value-free interaction."""

from __future__ import annotations

import contextvars

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import BusinessEvent
from reality.db.interactions import Interaction
from reality.mcp.catalog import schema_argument_names
from reality.services import interaction_recorder as interactions
from reality.services.core import NotFound, emit_business_event


@pytest.fixture
def recording(session, monkeypatch):
    """Switch the engine room on and let it write through this test's connection."""
    monkeypatch.setenv("REALITY_INTERACTIONS", "on")
    factory = sessionmaker(
        bind=session.connection(),
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    with interactions.use_session_factory(factory):
        yield


def rows(session, tenant_id):
    session.expire_all()
    return session.scalars(
        select(Interaction)
        .where(Interaction.tenant_id == tenant_id)
        .order_by(Interaction.cursor)
    ).all()


def emit(session, tenant_id, subject_id="sub_1"):
    return emit_business_event(
        session, tenant_id, "party.created", "party", subject_id, {}
    )


def test_recording_is_on_unless_an_operator_switches_it_off(monkeypatch):
    monkeypatch.delenv("REALITY_INTERACTIONS", raising=False)
    assert interactions.enabled()
    monkeypatch.setenv("REALITY_INTERACTIONS", "off")
    assert not interactions.enabled()


def test_one_boundary_records_one_row_with_its_shape(session, business, recording):
    tenant = business.tenant.id
    with interactions.observe(
        tenant, "mcp", "inventory.read", arguments=["item_id", "location_id"]
    ):
        interactions.note_result([1, 2, 3])
    [row] = rows(session, tenant)
    assert (row.channel, row.kind, row.operation, row.outcome) == (
        "mcp",
        "read",
        "inventory.read",
        "ok",
    )
    assert row.summary == {"arguments": ["item_id", "location_id"], "result_count": 3}
    assert row.duration_ms >= 0 and row.correlation_id.startswith("c_")
    assert row.event_ranges is None and row.refresh is False


def test_nested_boundaries_join_the_outer_one(session, business, recording):
    tenant = business.tenant.id
    with (
        interactions.observe(tenant, "web", "GET /items", correlation_id="click_1"),
        interactions.observe(tenant, "mcp", "inner.read"),
    ):
        interactions.note_kind("propose")
    [row] = rows(session, tenant)
    assert (row.channel, row.operation, row.kind) == ("web", "GET /items", "propose")
    assert row.correlation_id == "click_1"


def test_a_chat_call_inside_a_web_request_is_its_own_row_sharing_correlation(
    session, business, scheduled_owner, recording
):
    tenant = business.tenant.id
    with interactions.observe(
        tenant,
        "web",
        "POST /chat",
        correlation_id="turn_1",
        actor_user_id=scheduled_owner.id,
    ):
        with interactions.observe(tenant, "chat", "inventory.read"):
            pass
        with interactions.observe(tenant, "chat", "open_items.read"):
            pass
    recorded = rows(session, tenant)
    assert [(row.channel, row.operation) for row in recorded] == [
        ("chat", "inventory.read"),
        ("chat", "open_items.read"),
        ("web", "POST /chat"),
    ]
    assert {row.correlation_id for row in recorded} == {"turn_1"}
    assert {row.actor_user_id for row in recorded} == {scheduled_owner.id}


def test_notes_without_an_open_observation_do_nothing(session, business, recording):
    interactions.note_kind("decide")
    interactions.note_result([1])
    interactions.note_event(business.tenant.id, "evt_x")
    assert rows(session, business.tenant.id) == []


def test_a_malformed_client_correlation_is_replaced():
    assert interactions.correlation("abc_DEF-1") == "abc_DEF-1"
    assert interactions.correlation("has space").startswith("c_")
    assert interactions.correlation("x" * 65).startswith("c_")
    assert interactions.correlation(None).startswith("c_")


def test_only_declared_argument_names_reach_the_engine_room():
    names = schema_argument_names(
        "business_records_discover", {"limit": 5, "Müller GmbH owes 400": 1}
    )
    # Positive control: the tool exists and declares at least this argument.
    assert "limit" in names
    assert "Müller GmbH owes 400" not in names
    assert schema_argument_names("no.such.tool", {"a": 1}) == []


def test_committed_events_are_linked_by_their_sequence(session, business, recording):
    tenant = business.tenant.id
    with interactions.observe(tenant, "web", "POST /parties"):
        first = emit(session, tenant, "a")
        second = emit(session, tenant, "b")
        session.commit()
    [row] = rows(session, tenant)
    # Committed events without a proposal make a read boundary a write.
    assert row.kind == "write"
    assert row.event_ranges == [[first.sequence, second.sequence]]
    assert (row.event_first_sequence, row.event_last_sequence) == (
        first.sequence,
        second.sequence,
    )


def test_rolled_back_events_are_not_linked_even_when_their_sequence_is_reused(
    session, business, recording
):
    tenant = business.tenant.id
    with interactions.observe(tenant, "web", "POST /parties"):
        nested = session.begin_nested()
        discarded = emit(session, tenant, "discarded")
        session.flush()
        discarded_sequence = discarded.sequence
        nested.rollback()
        kept = emit(session, tenant, "kept")
        session.commit()
    # The kept event took the sequence the discarded one had held.
    assert kept.sequence == discarded_sequence
    [row] = rows(session, tenant)
    # Positive control: the kept event is linked; nothing else is.
    assert row.event_ranges == [[kept.sequence, kept.sequence]]
    other = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant, BusinessEvent.subject_id == "discarded"
        )
    ).all()
    assert other == []


def test_non_contiguous_events_keep_exact_ranges(session, business, recording):
    tenant = business.tenant.id
    with interactions.observe(tenant, "worker", "demo.intake", kind="job"):
        a = emit(session, tenant, "a")
        session.commit()
        # Somebody else writes in between, outside this observation.
        contextvars.Context().run(emit, session, tenant, "outsider")
        b = emit(session, tenant, "b")
        session.commit()
    row = next(r for r in rows(session, tenant) if r.operation == "demo.intake")
    assert row.event_ranges == [[a.sequence, a.sequence], [b.sequence, b.sequence]]
    assert (row.event_first_sequence, row.event_last_sequence) == (
        a.sequence,
        b.sequence,
    )


def test_a_refusal_is_recorded_with_its_code_and_travels_on(
    session, business, recording
):
    tenant = business.tenant.id
    with pytest.raises(NotFound), interactions.observe(tenant, "mcp", "item.read"):
        raise NotFound("Item not found: secret-sku-4711")
    [row] = rows(session, tenant)
    assert (row.outcome, row.error_code) == ("refused", "not_found")
    assert "secret-sku-4711" not in repr(
        {
            column.name: getattr(row, column.name)
            for column in Interaction.__table__.columns
        }
    )


def test_an_unexpected_error_is_failed(session, business, recording):
    tenant = business.tenant.id
    with (
        pytest.raises(RuntimeError),
        interactions.observe(tenant, "cli", "reality tenant"),
    ):
        raise RuntimeError("boom")
    [row] = rows(session, tenant)
    assert (row.outcome, row.error_code) == ("failed", "RuntimeError")


def test_a_proposal_that_waits_for_a_decision_says_so(session, business, recording):
    tenant = business.tenant.id
    with interactions.observe(tenant, "mcp", "party.create"):
        interactions.note_kind("propose")
        interactions.note_proposal("act_missing", "proposed")
    [row] = rows(session, tenant)
    assert (row.kind, row.outcome) == ("propose", "awaiting_decision")
    # The proposal did not exist when the row was written, so it is not linked.
    assert row.proposal_id is None


def test_a_recorder_failure_never_fails_the_call(session, business, monkeypatch):
    monkeypatch.setenv("REALITY_INTERACTIONS", "on")
    failures = []
    monkeypatch.setattr(
        "reality.telemetry.metrics.record_interaction_failure", failures.append
    )

    def broken():
        raise RuntimeError("database gone")

    tenant = business.tenant.id
    pending = emit(session, tenant, "pending")
    with (
        interactions.use_session_factory(broken),
        interactions.observe(tenant, "web", "GET /items"),
    ):
        result = "the answer"
    assert result == "the answer"
    assert failures == ["web"]
    # The caller's transaction was neither committed nor rolled back by the recorder.
    assert pending in session.new or session.in_transaction()


def test_a_working_recorder_writes_positive_control(
    session, business, recording, monkeypatch
):
    failures = []
    monkeypatch.setattr(
        "reality.telemetry.metrics.record_interaction_failure", failures.append
    )
    with interactions.observe(business.tenant.id, "web", "GET /items"):
        pass
    assert failures == []
    assert len(rows(session, business.tenant.id)) == 1


def test_switched_off_records_nothing(session, business, recording, monkeypatch):
    monkeypatch.setenv("REALITY_INTERACTIONS", "off")
    with interactions.observe(business.tenant.id, "web", "GET /items"):
        pass
    assert rows(session, business.tenant.id) == []


def test_recording_tidies_expired_rows_of_its_company_at_most_every_interval(
    session, business, recording, monkeypatch
):
    from datetime import timedelta

    from reality.db.core import now, uid

    tenant = business.tenant.id
    monkeypatch.setattr(interactions, "_last_tidy", {})

    def expired_row():
        moment = now() - timedelta(days=8)
        session.add(
            Interaction(
                id=uid("int"),
                tenant_id=tenant,
                started_at=moment,
                recorded_at=moment,
                duration_ms=1,
                channel="web",
                kind="read",
                operation="GET /old",
                outcome="ok",
                correlation_id="old",
                refresh=False,
                summary={},
            )
        )
        session.flush()

    expired_row()
    with interactions.observe(tenant, "web", "GET /items"):
        pass
    assert [row.operation for row in rows(session, tenant)] == ["GET /items"]
    # Within the interval a second write does not tidy again.
    expired_row()
    with interactions.observe(tenant, "web", "GET /items"):
        pass
    assert sorted(row.operation for row in rows(session, tenant)) == [
        "GET /items",
        "GET /items",
        "GET /old",
    ]
