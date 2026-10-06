"""Committed concurrent readers preserve a snapshot without preserving revoked authority."""

import pytest
from sqlalchemy import select

from reality.db.core import SourceRecord, TenantMembership
from reality.services import core
from reality.services.memberships import Principal


def test_readonly_repeatable_snapshot_is_stable_during_a_committed_source_change(
    scheduled_database, monkeypatch
):
    from reality.services.operations_cockpit import _with_snapshot

    _, factory, tenant, owner = scheduled_database
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    with factory() as writer:
        core.store_source_record(
            writer, tenant, "carrier", "capacity", "concurrent", {"slots": 2}
        )
        writer.commit()
    with factory() as reader:

        def observation(snapshot):
            assert snapshot.connection().get_isolation_level() == "REPEATABLE READ"
            before = list(
                snapshot.scalars(
                    select(SourceRecord.id).where(SourceRecord.tenant_id == tenant)
                )
            )
            with factory() as writer:
                core.store_source_record(
                    writer, tenant, "carrier", "capacity", "concurrent", {"slots": 0}
                )
                writer.commit()
            after = list(
                snapshot.scalars(
                    select(SourceRecord.id).where(SourceRecord.tenant_id == tenant)
                )
            )
            assert before == after
            return {"source_count": len(after)}

        result = _with_snapshot(reader, tenant, Principal(owner), observation)
        assert result["source_count"] == 1
    with factory() as current:
        assert (
            len(
                list(
                    current.scalars(
                        select(SourceRecord.id).where(SourceRecord.tenant_id == tenant)
                    )
                )
            )
            == 2
        )


def test_membership_removed_during_snapshot_prevents_the_response(
    scheduled_database, monkeypatch
):
    from reality.services.operations_cockpit import _with_snapshot

    _, factory, tenant, owner = scheduled_database
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    with factory() as reader:

        def observation(snapshot):
            with factory() as writer:
                membership = writer.scalar(
                    select(TenantMembership).where(
                        TenantMembership.tenant_id == tenant,
                        TenantMembership.user_id == owner,
                    )
                )
                membership.status = "removed"
                writer.commit()
            return {"must_not_escape": "company data"}

        with pytest.raises(core.NotFound):
            _with_snapshot(reader, tenant, Principal(owner), observation)


def test_snapshot_is_readonly_and_feature_off_never_opens_business_observation(
    scheduled_database, monkeypatch
):
    from reality.services.operations_cockpit import _with_snapshot

    _, factory, tenant, owner = scheduled_database
    monkeypatch.delenv("REALITY_OPERATIONS_COCKPIT_ENABLED", raising=False)
    with factory() as reader, pytest.raises(core.NotFound):
        _with_snapshot(
            reader,
            tenant,
            Principal(owner),
            lambda snapshot: pytest.fail("Feature-off read ran."),
        )
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    with factory() as reader:
        from sqlalchemy import text
        from sqlalchemy.exc import DBAPIError

        def attempted_write(snapshot):
            snapshot.execute(
                text("UPDATE tenant SET name = 'changed' WHERE id = :tenant"),
                {"tenant": tenant},
            )

        with pytest.raises(DBAPIError, match="read-only"):
            _with_snapshot(reader, tenant, Principal(owner), attempted_write)


def test_only_overlapping_identical_observations_share_independent_response_values(
    monkeypatch,
):
    """Concurrent observers share one calculation; later calls never reuse a result."""
    from concurrent.futures import Future, ThreadPoolExecutor
    from threading import Barrier, Event, Lock

    from reality.services import operations_cockpit

    joined = Event()
    ready = Barrier(4)
    lock = Lock()
    waiters = 0
    calls = 0

    class ObservedFuture(Future):
        def result(self, timeout=None):
            nonlocal waiters
            with lock:
                waiters += 1
                if waiters == 3:
                    joined.set()
            return super().result(timeout)

    monkeypatch.setattr(operations_cockpit, "Future", ObservedFuture)

    def calculate():
        nonlocal calls
        calls += 1
        assert joined.wait(5), (
            "The other three observers must actually join the live read."
        )
        return {"items": [{"version": calls}]}

    def observe():
        ready.wait(5)
        return operations_cockpit._inflight_read(("test", "identical"), calculate)

    with ThreadPoolExecutor(max_workers=4) as pool:
        values = list(pool.map(lambda _: observe(), range(4)))
    assert calls == 1
    values[0]["items"][0]["version"] = 999
    assert all(value["items"][0]["version"] == 1 for value in values[1:])
    assert operations_cockpit._inflight_read(
        ("test", "identical"), lambda: {"version": 2}
    ) == {"version": 2}
    assert not operations_cockpit._inflight


def test_failed_or_distinct_observations_never_supply_another_request(monkeypatch):
    """An exception retires the live calculation; exact context keys stay isolated."""
    from reality.services import operations_cockpit

    def fail():
        raise core.InvalidOperation(code="shipping_plan_source_unresolved")

    with pytest.raises(core.InvalidOperation):
        operations_cockpit._inflight_read(("test", "tenant_a", "today"), fail)
    assert not operations_cockpit._inflight
    assert (
        operations_cockpit._inflight_read(("test", "tenant_b", "today"), lambda: "B")
        == "B"
    )
    assert (
        operations_cockpit._inflight_read(
            ("test", "tenant_a", "today"), lambda: "current A"
        )
        == "current A"
    )


def test_joined_snapshot_rechecks_each_membership_after_committed_revocation(
    scheduled_database, monkeypatch
):
    """Sharing a calculation never shares authority with either waiting viewer."""
    from concurrent.futures import Future, ThreadPoolExecutor
    from threading import Event

    from reality.services import operations_cockpit

    _, factory, tenant, owner = scheduled_database
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    started, joined = Event(), Event()
    calculations = 0

    class JoinedFuture(Future):
        def result(self, timeout=None):
            joined.set()
            return super().result(timeout)

    monkeypatch.setattr(operations_cockpit, "Future", JoinedFuture)

    def observation(snapshot):
        nonlocal calculations
        calculations += 1
        snapshot.scalar(
            select(SourceRecord.id).where(SourceRecord.tenant_id == tenant).limit(1)
        )
        started.set()
        assert joined.wait(5)
        with factory() as writer:
            membership = writer.scalar(
                select(TenantMembership).where(
                    TenantMembership.tenant_id == tenant,
                    TenantMembership.user_id == owner,
                )
            )
            membership.status = "removed"
            writer.commit()
        return {"must_not_escape": "shared company data"}

    def observe():
        with factory() as reader, pytest.raises(core.NotFound):
            operations_cockpit._with_snapshot(
                reader,
                tenant,
                Principal(owner),
                observation,
                observation_key=("revocation",),
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(observe)
        assert started.wait(5)
        second = pool.submit(observe)
        first.result(timeout=10)
        second.result(timeout=10)
    assert calculations == 1
    assert not operations_cockpit._inflight


def test_different_context_does_not_join_an_in_progress_snapshot():
    """Tenant, operation and filters remain exact while another read is running."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from reality.services import operations_cockpit

    started, finish = Event(), Event()

    def waiting():
        started.set()
        assert finish.wait(5)
        return "A"

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(
            operations_cockpit._inflight_read, ("engine", "tenant_a", "today"), waiting
        )
        assert started.wait(5)
        try:
            assert (
                operations_cockpit._inflight_read(
                    ("engine", "tenant_b", "today"), lambda: "B"
                )
                == "B"
            )
            assert (
                operations_cockpit._inflight_read(
                    ("engine", "tenant_a", "yesterday"), lambda: "past A"
                )
                == "past A"
            )
        finally:
            finish.set()
        assert pending.result(timeout=5) == "A"
    assert not operations_cockpit._inflight


def test_opaque_id_cohort_preserves_postgresql_values_and_large_membership(session):
    """The exact SQL cohort includes unusual strings and exceeds the old bind limit."""
    from sqlalchemy import literal

    values = [
        "plain",
        'quote"comma,brace{}',
        "back\\slash",
        "actual\nline",
        "NULL",
        "",
        None,
    ]
    for value in values[:-1]:
        assert (
            session.scalar(
                select(literal(value)).where(core._id_cohort(literal(value), values))
            )
            == value
        )
    assert (
        session.scalar(
            select(literal("absent")).where(core._id_cohort(literal("absent"), values))
        )
        is None
    )
    assert (
        session.scalar(
            select(literal("plain")).where(core._id_cohort(literal("plain"), []))
        )
        is None
    )
    large = [f"opaque_{index}" for index in range(70000)]
    assert (
        session.scalar(
            select(literal(large[-1])).where(core._id_cohort(literal(large[-1]), large))
        )
        == large[-1]
    )
