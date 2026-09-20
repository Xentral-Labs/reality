"""PostgreSQL isolation and replay proofs for disposable experiment relations."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from benchmarks.large_tenant_registers.costing_cases import observe, order_read, publish
from benchmarks.large_tenant_registers.costing_dataset import Profile, build, validate


def test_profile_is_fixed_and_invalid_profile_refused():
    assert Profile.named("full").orders == 100_000
    with pytest.raises(ValueError):
        Profile.named("invented")


def test_exact_counts_tenant_isolation_and_reconstruction(session):
    connection = session.connection()
    profile = Profile.named("reduced")
    build(connection, profile)
    counts = validate(connection, profile)
    assert counts["a"]["movement"] == 1200
    first = observe(connection, "a")
    second = observe(connection, "b")
    assert first[0].cost != second[0].cost
    assert first == observe(connection, "a")
    assert len(first) == 720 + connection.scalar(
        text(
            "SELECT count(*) FROM costing_spike.movement WHERE tenant='a' AND kind='return'"
        )
    )
    assert observe(connection, "foreign") == []
    publish(connection, "a", first)
    row = order_read(connection, "a", 1)
    assert row["revenue"] == Decimal(120)
    assert row["db2"] == row["revenue"] - row["cost"] - Decimal(4)
    assert order_read(connection, "foreign", 1) is None
    assert order_read(connection, "b", 1) is None


def test_unknown_cost_projection_and_atomic_replacement(session):
    connection = session.connection()
    build(connection, Profile.named("reduced"))
    publish(connection, "a", observe(connection, "a"))
    before = order_read(connection, "a", 1)
    transaction = connection.begin_nested()
    connection.execute(
        text(
            "INSERT INTO costing_spike.adjustment VALUES ('a',1,1,100,'source:late:1')"
        )
    )
    publish(connection, "a", observe(connection, "a"))
    assert order_read(connection, "a", 1)["cost"] != before["cost"]
    transaction.rollback()
    assert order_read(connection, "a", 1) == before
    # Scope 100's receipt deliberately has unknown acquisition components.
    assert any(r.cost is None for r in observe(connection, "a"))
    with pytest.raises(ValueError, match="exists"):
        build(connection, Profile.named("reduced"))


def test_foreign_links_fail_and_scoped_refresh_preserves_other_pool(session):
    from sqlalchemy.exc import IntegrityError

    from benchmarks.large_tenant_registers.costing_cases import derive, refresh_pool

    connection = session.connection()
    build(connection, Profile.named("reduced"))
    rows, inventory = derive(connection, "a")
    publish(connection, "a", rows, inventory)
    other = order_read(connection, "a", 2)
    with connection.begin_nested():
        connection.execute(
            text(
                "INSERT INTO costing_spike.adjustment VALUES ('a',1,1,1,'source:late:1')"
            )
        )
        refresh_pool(connection, "a", 1)
    assert order_read(connection, "a", 2) == other
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(
            text(
                "INSERT INTO costing_spike.attribution VALUES ('foreign',999999,1,NULL,1)"
            )
        )


def test_late_evidence_keeps_original_amount_and_prior_knowledge(session):
    from benchmarks.large_tenant_registers.costing_cases import derive

    connection = session.connection()
    build(connection, Profile.named("reduced"))
    before = derive(connection, "a", 1)[0]
    connection.execute(
        text("INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')")
    )
    assert connection.scalar(
        text("SELECT amount FROM costing_spike.component WHERE tenant='a' AND id=1")
    ) == Decimal(41)
    assert derive(connection, "a", 1, knowledge_revision=0)[0] == before
    assert derive(connection, "a", 1)[0] != before


def test_readers_see_one_committed_generation(postgres_database):
    from sqlalchemy import create_engine

    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            build(connection, Profile.named("reduced"))
            publish(connection, "a", observe(connection, "a"))
            before = order_read(connection, "a", 1)
        with engine.connect() as writer:
            transaction = writer.begin()
            writer.execute(
                text(
                    "INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')"
                )
            )
            publish(writer, "a", observe(writer, "a"))
            with engine.connect() as reader:
                assert order_read(reader, "a", 1) == before
            transaction.commit()
        with engine.connect() as reader:
            assert order_read(reader, "a", 1)["cost"] != before["cost"]
            assert (
                reader.scalar(
                    text(
                        "SELECT generation FROM costing_spike.checkpoint WHERE tenant='a'"
                    )
                )
                == 2
            )
    finally:
        engine.dispose()


def test_adversarial_matching_returns_and_stated_reductions(session):
    from benchmarks.large_tenant_registers.costing_cases import derive

    connection = session.connection()
    build(connection, Profile.named("reduced"))
    rows, inventory = derive(connection, "a")
    assert len({r.issue_id for r in rows}) == len(rows)
    assert (
        connection.scalar(
            text(
                "SELECT count(*) FROM costing_spike.movement WHERE tenant='a' AND kind='return'"
            )
        )
        > 0
    )
    returned = [r for r in rows if r.cost is not None and r.cost < 0]
    assert returned
    # Order 10: first issue has two matching parts; second is absent; third partial.
    parts = {r.issue_id: r for r in rows if r.order_id == 10}
    assert parts[94].revenue == Decimal(20)
    assert parts[95].revenue is None
    assert parts[96].revenue is None
    assert (
        connection.scalar(
            text(
                "SELECT count(*) FROM costing_spike.component WHERE tenant='a' AND amount<0"
            )
        )
        > 0
    )
    expected_quantity = connection.scalar(
        text(
            "SELECT sum(CASE WHEN kind IN ('receipt','return') THEN quantity WHEN kind='issue' THEN -quantity ELSE 0 END) FROM costing_spike.movement WHERE tenant='a'"
        )
    )
    assert sum(r[1] for r in inventory) == expected_quantity
    publish(connection, "a", rows, inventory)
    assert order_read(connection, "a", 10)["db1"] is None
    assert order_read(connection, "a", 10)["revenue"] is None


def test_live_snapshot_refuses_stale_and_other_pool_cannot_advance_watermark(session):
    from benchmarks.large_tenant_registers.costing_cases import (
        derive,
        refresh_pool,
        snapshot_read,
    )

    connection = session.connection()
    build(connection, Profile.named("reduced"))
    assert (
        snapshot_read(connection, "a", lambda: None, live=True)["state"] == "not_ready"
    )
    rows, inventory = derive(connection, "a")
    publish(connection, "a", rows, inventory)
    assert (
        snapshot_read(
            connection, "a", lambda: order_read(connection, "a", 1), live=True
        )["state"]
        == "current"
    )
    connection.execute(
        text("INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')")
    )
    display = snapshot_read(connection, "a", lambda: order_read(connection, "a", 1))
    assert display["state"] == "stale" and display["value"] is not None
    live = snapshot_read(
        connection, "a", lambda: order_read(connection, "a", 1), live=True
    )
    assert live["state"] == "not_ready" and live["value"] is None
    refresh_pool(connection, "a", 2)
    assert snapshot_read(connection, "a", lambda: None)["state"] == "stale"
    refresh_pool(connection, "a", 1)
    assert snapshot_read(connection, "a", lambda: None)["state"] == "current"
    assert snapshot_read(connection, "foreign", lambda: None)["state"] == "not_ready"


def test_failed_refresh_retains_stale_generation_and_retry_recovers(
    session, monkeypatch
):
    from benchmarks.large_tenant_registers import costing_cases as cases

    connection = session.connection()
    build(connection, Profile.named("reduced"))
    rows, inventory = cases.derive(connection, "a")
    cases.publish(connection, "a", rows, inventory)
    before = order_read(connection, "a", 1)
    connection.execute(
        text("INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')")
    )
    original = cases.publish

    def fail_after_replacement(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("simulated worker failure before commit")

    with monkeypatch.context() as patch:
        patch.setattr(cases, "publish", fail_after_replacement)
        with pytest.raises(RuntimeError), connection.begin_nested():
            cases.refresh_pool(connection, "a", 1)
    assert order_read(connection, "a", 1) == before
    assert cases.snapshot_read(connection, "a", lambda: None)["state"] == "stale"
    cases.refresh_pool(connection, "a", 1)
    assert order_read(connection, "a", 1) != before
    assert cases.snapshot_read(connection, "a", lambda: None)["state"] == "current"


def test_mixed_load_keeps_changes_active_until_slow_readers_finish(
    postgres_database, monkeypatch
):
    import time

    from sqlalchemy import create_engine

    from benchmarks.large_tenant_registers import costing_runner as runner

    engine = create_engine(postgres_database, pool_size=7, max_overflow=0)
    original = runner.workload

    def slow_read(engine, name, index, orders, states=None):
        if states is not None and name == "attention":
            time.sleep(0.35)
        return original(engine, name, index, orders, states)

    try:
        with engine.begin() as connection:
            build(connection, Profile.named("reduced"))
        monkeypatch.setattr(runner, "workload", slow_read)
        result = runner.run(engine, Profile.named("reduced"), "projection", 4, 1)
        assert result["refresh"]["samples"] >= 2
        assert all(m["samples"] == 4 for m in result["mixed_measurements"].values())
        assert result["reconciliation"]["complete_values_equal"]
    finally:
        engine.dispose()


def test_new_evidence_can_commit_during_replay_without_false_watermark(
    postgres_database, monkeypatch
):
    from sqlalchemy import create_engine

    from benchmarks.large_tenant_registers import costing_cases as cases

    engine = create_engine(postgres_database)
    try:
        with engine.begin() as connection:
            build(connection, Profile.named("reduced"))
            rows, inventory = cases.derive(connection, "a")
            cases.publish(connection, "a", rows, inventory)
            connection.execute(
                text(
                    "INSERT INTO costing_spike.adjustment VALUES ('a',1,1,1,'source:late:1')"
                )
            )
        original = cases.derive

        def receive_during_replay(connection, tenant, *args, **kwargs):
            result = original(connection, tenant, *args, **kwargs)
            with engine.begin() as writer:
                writer.execute(text("SET LOCAL lock_timeout='100ms'"))
                writer.execute(
                    text("SELECT id FROM costing_spike.tenant WHERE id='a' FOR UPDATE")
                )
                writer.execute(
                    text(
                        "INSERT INTO costing_spike.adjustment VALUES ('a',2,1,1,'source:late:2')"
                    )
                )
            return result

        with monkeypatch.context() as patch:
            patch.setattr(cases, "derive", receive_during_replay)
            with engine.begin() as connection:
                cases.refresh_pool(connection, "a", 1)
        with engine.connect() as connection:
            state = cases.snapshot_read(connection, "a", lambda: None)
            assert state["state"] == "stale"
            assert state["published_revision"] == 1
            assert state["input_revision"] == 2
        with engine.begin() as connection:
            cases.refresh_pool(connection, "a", 1)
            assert (
                cases.snapshot_read(connection, "a", lambda: None)["state"] == "current"
            )
    finally:
        engine.dispose()


def test_live_order_scoped_freshness_fallback_and_read_only(session):
    from benchmarks.large_tenant_registers import costing_cases as cases

    c = session.connection()
    build(c, Profile.named("reduced"))
    rows, inventory = cases.derive(c, "a")
    cases.publish(c, "a", rows, inventory)
    baseline = order_read(c, "a", 2)
    c.execute(
        text("INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')")
    )
    unaffected = cases.live_order_read(c, "a", 2)
    assert unaffected["state"] == "current" and unaffected["basis"] == "projection"
    assert unaffected["value"] == baseline
    changed = cases.live_order_read(c, "a", 1)
    assert changed["state"] == "current" and changed["basis"] == "direct"
    assert changed["value"]["cost"] != order_read(c, "a", 1)["cost"]
    assert (
        c.scalar(
            text("SELECT generation FROM costing_spike.checkpoint WHERE tenant='a'")
        )
        == 1
    )
    cases.refresh_pool(c, "a", 1)
    assert changed["value"] == order_read(c, "a", 1)
    assert cases.live_order_read(c, "foreign", 1) == cases.live_order_read(
        c, "a", 999999
    )


def test_live_order_bound_refuses_before_replay_and_selling_change_invalidates(
    session, monkeypatch
):
    from benchmarks.large_tenant_registers import costing_cases as cases

    c = session.connection()
    build(c, Profile.named("reduced"))
    rows, inventory = cases.derive(c, "a")
    cases.publish(c, "a", rows, inventory)
    # First selling component belongs to order 1, independently of its receipt cost.
    c.execute(
        text("INSERT INTO costing_spike.adjustment VALUES ('a',1,721,1,'source:fee:1')")
    )
    assert cases.live_order_read(c, "a", 1)["basis"] == "direct"
    with monkeypatch.context() as patch:

        def forbidden(*args, **kwargs):
            raise AssertionError("Unbounded replay attempted")

        patch.setattr(cases, "derive", forbidden)
        result = cases.live_order_read(c, "a", 1, max_movements=1)
        assert result["state"] == "not_ready" and result["value"] is None
        financial = cases.live_order_read(c, "a", 1, max_parts=1)
        assert financial["state"] == "not_ready" and financial["value"] is None
    assert cases.live_order_read(c, "a", 2)["basis"] == "projection"


def test_live_order_snapshot_and_partial_coverage(postgres_database):
    from sqlalchemy import create_engine

    from benchmarks.large_tenant_registers import costing_cases as cases

    engine = create_engine(postgres_database)
    try:
        with engine.begin() as c:
            build(c, Profile.named("reduced"))
            rows, inventory = cases.derive(c, "a")
            cases.publish(c, "a", rows, inventory)
        with engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as reader:
            before = cases.live_order_read(reader, "a", 1)
            with engine.begin() as writer:
                writer.execute(
                    text(
                        "INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')"
                    )
                )
            assert cases.live_order_read(reader, "a", 1) == before
        with engine.connect() as reader:
            assert cases.live_order_read(reader, "a", 1)["basis"] == "direct"
            partial = cases.live_order_read(reader, "a", 10)
            assert partial["state"] == "current" and partial["value"]["db1"] is None
    finally:
        engine.dispose()


def test_unresolved_late_target_cannot_be_answered_by_direct_replay(session):
    from benchmarks.large_tenant_registers import costing_cases as cases

    c = session.connection()
    build(c, Profile.named("reduced"))
    # Author an unresolved target before publishing the initial synthetic view.
    c.execute(
        text(
            "DELETE FROM costing_spike.attribution WHERE tenant='a' AND component_id=2"
        )
    )
    rows, inventory = cases.derive(c, "a")
    cases.publish(c, "a", rows, inventory)
    c.execute(
        text(
            "INSERT INTO costing_spike.adjustment VALUES ('a',1,2,10,'source:unknown-target:1')"
        )
    )
    value = cases.live_order_read(c, "a", 1)
    assert value["state"] == "not_ready" and value["value"] is None
