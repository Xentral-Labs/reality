"""Storage invariants for private learning runs (096/DR-003, DR-004)."""

from pathlib import Path

import pytest
import yaml
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from reality.db.core import (
    AppUser,
    Base,
    ChangeProposal,
    PlaygroundRun,
    PlaygroundStep,
    Tenant,
    now,
    uid,
)


@pytest.fixture
def learning_owner(session, monkeypatch):
    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    user = owner(session)
    session.commit()
    return user


@pytest.mark.parametrize("status", ["active", "pending_approval"])
def test_start_seeds_only_private_references(session, learning_owner, status):
    from reality.db.core import (
        BusinessEvent,
        Commitment,
        Fact,
        Item,
        Location,
        Movement,
        Party,
        SourceRecord,
        TenantMembership,
    )
    from reality.services.playground import start_run

    learning_owner.status = status
    session.commit()
    result = start_run(session, learning_owner.id, "first", confirmed=True)
    assert result.status == "active"
    assert result.ready_at is not None
    assert result.preset_key == "trading" and result.preset_version == 1
    assert session.get(Tenant, result.tenant_id).purpose == "playground"
    membership = session.scalar(
        select(TenantMembership).where(TenantMembership.tenant_id == result.tenant_id)
    )
    assert membership.user_id == learning_owner.id and membership.role == "owner"
    for model, expected in [
        (Party, 4),
        (Item, 3),
        (Location, 1),
        (Movement, 0),
        (Commitment, 0),
        (Fact, 0),
        (SourceRecord, 0),
        (PlaygroundStep, 0),
    ]:
        assert (
            len(
                list(
                    session.scalars(
                        select(model).where(model.tenant_id == result.tenant_id)
                    )
                )
            )
            == expected
        )
    assert set(result.initialization_progress["items"]) == {
        "BIKE-LIGHT",
        "HELMET",
        "BIKE-BELL",
    }
    assert (
        len(
            list(
                session.scalars(
                    select(BusinessEvent).where(
                        BusinessEvent.tenant_id == result.tenant_id
                    )
                )
            )
        )
        == 8
    )
    replay = start_run(session, learning_owner.id, "first", confirmed=True)
    assert replay.id == result.id
    assert replay.initialization_progress == result.initialization_progress


def test_scenario_selection_persists_and_restart_preserves_history(
    session, learning_owner
):
    from reality.services.playground import restart_run, start_run

    original = start_run(session, learning_owner.id, "first", confirmed=True)
    fresh = restart_run(
        session,
        learning_owner.id,
        original.id,
        preset_key="partial-delivery",
        preset_version=1,
        confirmed=True,
    )
    assert fresh.preset_key == "partial-delivery"
    assert fresh.lesson_key == "partial-delivery"
    assert fresh.tenant_id != original.tenant_id
    assert session.get(PlaygroundRun, original.id).status == "archived"
    session.expire_all()
    assert session.get(PlaygroundRun, fresh.id).preset_key == "partial-delivery"


def test_selected_scenario_restart_replays_after_lost_response(session, learning_owner):
    from reality.services.playground import restart_run, start_run

    original = start_run(session, learning_owner.id, "first", confirmed=True)
    arguments = {
        "preset_key": "partial-delivery",
        "preset_version": 1,
        "request_key": "scenario-switch",
        "confirmed": True,
    }
    fresh = restart_run(session, learning_owner.id, original.id, **arguments)
    repeated = restart_run(session, learning_owner.id, original.id, **arguments)
    assert repeated.id == fresh.id
    # A refreshed client may already know the replacement. Retry must not archive it.
    refreshed = restart_run(session, learning_owner.id, fresh.id, **arguments)
    assert refreshed.id == fresh.id and refreshed.status == "active"
    assert len(list(session.scalars(select(PlaygroundRun)))) == 2


def test_unavailable_scenario_does_not_archive_current_run(session, learning_owner):
    from reality.services.core import InvalidOperation
    from reality.services.playground import restart_run, start_run

    original = start_run(session, learning_owner.id, "first", confirmed=True)
    with pytest.raises(InvalidOperation):
        restart_run(
            session,
            learning_owner.id,
            original.id,
            preset_key="customer-return",
            preset_version=1,
            confirmed=True,
        )
    assert session.get(PlaygroundRun, original.id).status == "active"


@pytest.mark.parametrize(
    "status,verified", [("active", False), ("suspended", True), ("rejected", True)]
)
def test_start_rejects_unavailable_accounts(session, learning_owner, status, verified):
    from reality.services.playground import start_run
    from reality.services.tenant_policy import PlaygroundOperationDenied

    learning_owner.status = status
    learning_owner.email_verified_at = now() if verified else None
    session.commit()
    with pytest.raises(PlaygroundOperationDenied):
        start_run(session, learning_owner.id, "first", confirmed=True)
    assert session.scalar(select(PlaygroundRun.id)) is None


def test_start_needs_confirmation_and_enabled_feature(
    session, learning_owner, monkeypatch
):
    from reality.services.playground import start_run
    from reality.services.tenant_policy import PlaygroundOperationDenied

    with pytest.raises(PlaygroundOperationDenied):
        start_run(session, learning_owner.id, "first")
    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "false")
    with pytest.raises(PlaygroundOperationDenied):
        start_run(session, learning_owner.id, "first", confirmed=True)
    assert session.scalar(select(PlaygroundRun.id)) is None


def test_start_retry_after_failed_seed_has_no_partial_data(
    session, learning_owner, monkeypatch
):
    from reality.db.core import Item, Party
    from reality.services import playground

    real_create = playground.create_item

    def broken(*args, **kwargs):
        real_create(*args, **kwargs)
        raise RuntimeError("Sensitive internal failure must not be exposed")

    monkeypatch.setattr(playground, "create_item", broken)
    failed = playground.start_run(session, learning_owner.id, "first", confirmed=True)
    assert failed.status == "initialization_failed"
    assert failed.initialization_error_code == "seed_failed"
    assert failed.initialization_progress == {}
    for model in (Party, Item):
        assert (
            session.scalar(select(model.id).where(model.tenant_id == failed.tenant_id))
            is None
        )
    monkeypatch.setattr(playground, "create_item", real_create)
    ready = playground.start_run(session, learning_owner.id, "first", confirmed=True)
    assert ready.id == failed.id and ready.status == "active"
    assert ready.initialization_error_code is None


def test_start_conflicts_and_owner_scoped_keys(session, learning_owner):
    from reality.services.core import Conflict
    from reality.services.playground import start_run

    first = start_run(session, learning_owner.id, "first", confirmed=True)
    with pytest.raises(Conflict):
        start_run(session, learning_owner.id, "first", preset_version=2, confirmed=True)
    with pytest.raises(Conflict):
        start_run(session, learning_owner.id, "second", confirmed=True)
    other = owner(session)
    session.commit()
    second = start_run(session, other.id, "first", confirmed=True)
    assert first.id != second.id and first.tenant_id != second.tenant_id


@pytest.mark.parametrize(
    "limit_name",
    ["REALITY_PLAYGROUND_DAILY_RUN_LIMIT", "REALITY_PLAYGROUND_RETAINED_RUN_LIMIT"],
)
def test_run_quota_counts_retained_failures(
    session, learning_owner, monkeypatch, limit_name
):
    from reality.services.playground import PlaygroundQuotaExceeded, start_run

    run(session, learning_owner, status="initialization_failed")
    session.commit()
    monkeypatch.setenv(limit_name, "1")
    with pytest.raises(PlaygroundQuotaExceeded):
        start_run(session, learning_owner.id, "new", confirmed=True)


@pytest.mark.parametrize("same_key", [True, False])
def test_concurrent_start_serializes_owner(postgres_database, monkeypatch, same_key):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Item
    from reality.services.core import Conflict
    from reality.services.playground import start_run

    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as setup:
            user_id = owner(setup).id
            setup.commit()
        barrier = Barrier(2)

        def start(index):
            with factory() as worker:
                barrier.wait(timeout=10)
                try:
                    return start_run(
                        worker,
                        user_id,
                        "same" if same_key else str(index),
                        confirmed=True,
                    ).id
                except Conflict:
                    return "conflict"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(start, [1, 2]))
        with factory() as check:
            assert check.scalar(select(func.count()).select_from(PlaygroundRun)) == 1
            assert check.scalar(select(func.count()).select_from(Item)) == 3
        if same_key:
            assert results[0] == results[1] and "conflict" not in results
        else:
            assert results.count("conflict") == 1
    finally:
        engine.dispose()


def test_seed_permission_never_opens_business_egress_or_lesson_actions(
    session, learning_owner, monkeypatch
):
    from reality.services import playground
    from reality.services.core import create_item, create_tenant
    from reality.services.tenant_policy import (
        PlaygroundOperationDenied,
        require_business_operation,
        require_core_operation,
    )

    production = create_tenant(session, "Real business")
    original = playground._seed_references

    def inspect_scope(db, record):
        for operation in (
            "record_movement",
            "reserve",
            "create_manual_order",
            "store_source_record",
            "unknown",
        ):
            with pytest.raises(PlaygroundOperationDenied):
                require_core_operation(db, record.tenant_id, operation)
        with pytest.raises(PlaygroundOperationDenied):
            require_business_operation(db, record.tenant_id, "secret_resolve")
        with pytest.raises(PlaygroundOperationDenied):
            require_core_operation(db, production.id, "create_item")
        with pytest.raises(PlaygroundOperationDenied):
            require_business_operation(db, production.id, "secret_resolve")
        return original(db, record)

    monkeypatch.setattr(playground, "_seed_references", inspect_scope)
    result = playground.start_run(session, learning_owner.id, "first", confirmed=True)
    assert result.status == "active"
    with pytest.raises(PlaygroundOperationDenied):
        create_item(session, result.tenant_id, "EXTRA", "Not authorized")


def test_seed_cannot_commit_a_partial_dataset(session, learning_owner, monkeypatch):
    from reality.db.core import Party
    from reality.services import playground

    original = playground.create_party

    def accidental_commit(*args, **kwargs):
        result = original(*args, **kwargs)
        args[0].commit()
        return result

    monkeypatch.setattr(playground, "create_party", accidental_commit)
    result = playground.start_run(session, learning_owner.id, "first", confirmed=True)
    assert result.status == "initialization_failed"
    assert (
        session.scalar(select(Party.id).where(Party.tenant_id == result.tenant_id))
        is None
    )


def test_start_resumes_after_metadata_commit_interruption(
    session, learning_owner, monkeypatch
):
    from reality.services import playground

    initialize = playground._initialize

    def interrupted(*args, **kwargs):
        raise RuntimeError("Simulated process interruption")

    monkeypatch.setattr(playground, "_initialize", interrupted)
    with pytest.raises(RuntimeError, match="interruption"):
        playground.start_run(session, learning_owner.id, "first", confirmed=True)
    saved = session.scalar(
        select(PlaygroundRun).where(PlaygroundRun.owner_user_id == learning_owner.id)
    )
    assert saved.status == "initializing"
    saved_id = saved.id
    monkeypatch.setattr(playground, "_initialize", initialize)
    assert (
        playground.start_run(session, learning_owner.id, "first", confirmed=True).id
        == saved_id
    )
    assert saved.status == "active"


def test_archived_start_replay_never_reseeds(session, learning_owner, monkeypatch):
    from reality.services import playground

    saved = playground.start_run(session, learning_owner.id, "first", confirmed=True)
    references = saved.initialization_progress
    saved.status = "archived"
    saved.archived_at = now()
    session.get(Tenant, saved.tenant_id).archived_at = now()
    session.commit()

    def forbidden(*args, **kwargs):
        pytest.fail("Archived replay must not initialize references")

    monkeypatch.setattr(playground, "_seed_references", forbidden)
    replay = playground.start_run(session, learning_owner.id, "first", confirmed=True)
    assert replay.status == "archived" and replay.initialization_progress == references


@pytest.mark.parametrize("request_key", ["", " ", " padded", "x" * 129])
def test_start_rejects_invalid_request_keys(session, learning_owner, request_key):
    from reality.services.core import InvalidOperation
    from reality.services.playground import start_run

    with pytest.raises(InvalidOperation):
        start_run(session, learning_owner.id, request_key, confirmed=True)
    assert session.scalar(select(PlaygroundRun.id)) is None


def test_retry_does_not_consume_another_quota_slot(
    session, learning_owner, monkeypatch
):
    from reality.services.playground import start_run

    monkeypatch.setenv("REALITY_PLAYGROUND_RETAINED_RUN_LIMIT", "1")
    monkeypatch.setenv("REALITY_PLAYGROUND_DAILY_RUN_LIMIT", "1")
    first = start_run(session, learning_owner.id, "first", confirmed=True)
    assert start_run(session, learning_owner.id, "first", confirmed=True).id == first.id


def owner(session):
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    return user


def run(session, user, *, status="initializing", request_key=None):
    tenant = Tenant(id=uid("ten"), name="Learning", purpose="playground")
    session.add(tenant)
    session.flush()
    record = PlaygroundRun(
        id=uid("pgr"),
        tenant_id=tenant.id,
        owner_user_id=user.id,
        preset_key="trading",
        preset_version=1,
        lesson_key="order-stock",
        lesson_version=1,
        client_request_key=request_key or uid("request"),
        status=status,
        ready_at=now() if status == "active" else None,
    )
    session.add(record)
    session.flush()
    return record


def proposal(session, tenant_id):
    record = ChangeProposal(
        id=uid("act"), tenant_id=tenant_id, type="tool", status="proposed"
    )
    session.add(record)
    session.flush()
    return record


def step(record, action, **overrides):
    return PlaygroundStep(
        **{
            "id": uid("pgs"),
            "tenant_id": record.tenant_id,
            "run_id": record.id,
            "proposal_id": action.id,
            "sequence": 1,
            "request_key": uid("request"),
            **overrides,
        }
    )


def test_tenant_purpose_defaults_to_business_and_cannot_be_converted(session):
    tenant = Tenant(id=uid("ten"), name="Old demo is still business")
    session.add(tenant)
    session.flush()
    assert tenant.purpose == "business"
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            update(Tenant).where(Tenant.id == tenant.id).values(purpose="playground")
        )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(Tenant(id=uid("ten"), name="Invalid", purpose="guess"))
        session.flush()


def test_one_active_run_per_owner_and_idempotent_request_constraint(session):
    user = owner(session)
    first = run(session, user, status="active", request_key="start-1")
    run(session, user)  # A replacement may initialize while the old run stays active.
    with pytest.raises(IntegrityError), session.begin_nested():
        run(session, user, status="active")
    with pytest.raises(IntegrityError), session.begin_nested():
        run(session, user, request_key="start-1")
    other = owner(session)
    run(session, other, status="active", request_key="start-1")
    assert (
        session.scalar(
            select(PlaygroundRun).where(
                PlaygroundRun.tenant_id == first.tenant_id,
                PlaygroundRun.id == first.id,
            )
        ).owner_user_id
        == user.id
    )


def test_step_foreign_keys_enforce_run_and_proposal_tenant(session):
    user = owner(session)
    first, second = run(session, user), run(session, user)
    action = proposal(session, first.tenant_id)
    foreign = proposal(session, second.tenant_id)
    for record in (
        step(first, foreign),
        step(first, action, tenant_id=second.tenant_id),
        step(first, action, run_id=second.id),
    ):
        with pytest.raises(IntegrityError), session.begin_nested():
            session.add(record)
            session.flush()
    valid = step(first, action)
    session.add(valid)
    session.flush()
    assert valid.before_observation is None  # Captured on execution, not preview.
    assert valid.receipt_observation is None
    assert valid.created_at.utcoffset().total_seconds() == 0


@pytest.mark.parametrize("duplicate", ["proposal_id", "sequence", "request_key"])
def test_step_uniqueness(session, duplicate):
    record = run(session, owner(session))
    first = step(record, proposal(session, record.tenant_id))
    session.add(first)
    session.flush()
    second = step(record, proposal(session, record.tenant_id), sequence=2)
    setattr(second, duplicate, getattr(first, duplicate))
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(second)
        session.flush()


def test_run_and_step_metadata_are_tenant_scoped_not_reality_authority():
    for name in ("playground_run", "playground_step"):
        assert any(
            fk.target_fullname == "tenant.id"
            for fk in Base.metadata.tables[name].c.tenant_id.foreign_keys
        )
    assert "status" not in PlaygroundStep.__table__.c
    assert "quantity" not in PlaygroundStep.__table__.c
    assert "document_id" not in PlaygroundStep.__table__.c
    catalog = yaml.safe_load(
        (Path(__file__).parents[1] / "config/data_model.yaml").read_text()
    )
    registered = {
        table for section in catalog["sections"] for table in section["tables"]
    }
    assert {"playground_run", "playground_step"} <= registered


def test_observations_and_seed_progress_are_bounded_objects(session):
    record = run(session, owner(session))
    for value in (["not an object"], {"dump": "x" * 65537}):
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(
                update(PlaygroundRun)
                .where(PlaygroundRun.id == record.id)
                .values(initialization_progress=value)
            )
        for column in ("before_observation", "receipt_observation"):
            action = proposal(session, record.tenant_id)
            with pytest.raises(IntegrityError), session.begin_nested():
                session.add(step(record, action, **{column: value}))
                session.flush()


def test_run_requires_existing_owner_and_unique_tenant(session):
    user = owner(session)
    record = run(session, user)
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            PlaygroundRun(
                id=uid("pgr"),
                tenant_id=record.tenant_id,
                owner_user_id=user.id,
                preset_key="trading",
                preset_version=1,
                lesson_key="order-stock",
                lesson_version=1,
                client_request_key=uid("request"),
            )
        )
        session.flush()
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            update(PlaygroundRun)
            .where(PlaygroundRun.id == record.id)
            .values(owner_user_id="missing")
        )


@pytest.mark.parametrize(
    "values",
    [
        {"status": "pretend"},
        {"status": "active"},
        {"status": "archived"},
        {"preset_version": 0},
        {"lesson_version": -1},
    ],
)
def test_run_lifecycle_values_and_versions_are_constrained(session, values):
    record = run(session, owner(session))
    with pytest.raises(IntegrityError), session.begin_nested():
        session.execute(
            update(PlaygroundRun).where(PlaygroundRun.id == record.id).values(**values)
        )
