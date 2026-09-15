import pytest
from conftest import seed_company
from sqlalchemy import func, select

from reality.db.core import Item, PlaygroundRun, Tenant
from reality.services import company_setup
from reality.services.core import Conflict, InvalidOperation


def test_empty_creation_replay_and_changed_kind(session, scheduled_owner, monkeypatch):
    actor = scheduled_owner.id
    result = company_setup.create_company(
        session,
        actor,
        "same-request",
        "Harbor Supply",
        "business",
        "empty",
        confirmed=True,
    )
    assert (
        company_setup.create_company(
            session,
            actor,
            "same-request",
            "Harbor Supply",
            "business",
            "empty",
            confirmed=True,
        )["tenant_id"]
        == result["tenant_id"]
    )
    with pytest.raises(Conflict):
        company_setup.create_company(
            session,
            actor,
            "same-request",
            "Harbor Supply",
            "sandbox",
            "empty",
            confirmed=True,
        )
    assert (
        session.scalar(
            select(func.count())
            .select_from(Item)
            .where(Item.tenant_id == result["tenant_id"])
        )
        == 0
    )


@pytest.mark.parametrize("retired_flag", [None, "false", "true", "", "invalid"])
def test_pending_empty_sandbox_and_ordinary_refusal(
    session, scheduled_owner, monkeypatch, retired_flag
):
    if retired_flag is None:
        monkeypatch.delenv("REALITY_PLAYGROUND_ENABLED", raising=False)
    else:
        monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", retired_flag)
    scheduled_owner.status = "pending_approval"
    session.commit()
    options = company_setup.options(session, scheduled_owner.id)
    assert options["practice_enabled"] is True
    assert options["environments"] == ["sandbox"]
    with pytest.raises(InvalidOperation):
        company_setup.create_company(
            session,
            scheduled_owner.id,
            "ordinary",
            "No",
            "business",
            "empty",
            confirmed=True,
        )
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "sandbox",
        "My Practice",
        "sandbox",
        "empty",
        confirmed=True,
    )
    assert result["status"] == "ready" and result["destination"].startswith(
        "/playground"
    )
    assert session.get(Tenant, result["tenant_id"]).purpose == "playground"
    assert (
        session.scalar(
            select(func.count())
            .select_from(Item)
            .where(Item.tenant_id == result["tenant_id"])
        )
        == 0
    )
    assert session.get(PlaygroundRun, result["run_id"]).status == "active"


def test_failed_seed_rolls_back_all_evidence_and_explicit_retry_reuses_tenant(
    session, scheduled_owner, monkeypatch
):
    from reality.db.core import Party, SourceRecord
    from reality.services import core, demo_profile

    original = demo_profile.seed_profile

    def fail_after_write(db, run, anchor, **kwargs):
        core.create_party(db, run.tenant_id, "Temporary", "customer", _commit=False)
        raise RuntimeError("private diagnostic detail")

    monkeypatch.setattr(demo_profile, "seed_profile", fail_after_write)
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "retry",
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert result["status"] == "initializing" and result["destination"] is None
    tenant = result["tenant_id"]
    assert seed_company(session, tenant) == "succeeded"
    assert (
        company_setup.read_request(session, scheduled_owner.id, "retry")["status"]
        == "initialization_failed"
    )
    for model in (Party, Item, SourceRecord):
        assert (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            == 0
        )
    assert (
        company_setup.read_request(session, scheduled_owner.id, "retry")["status"]
        == "initialization_failed"
    )
    monkeypatch.setattr(demo_profile, "seed_profile", original)
    retried = company_setup.create_company(
        session,
        scheduled_owner.id,
        "retry",
        "Harbor Supply",
        "sandbox",
        "international_demo",
        confirmed=True,
    )
    assert retried["tenant_id"] == tenant and retried["status"] == "ready"
    renamed = session.get(Tenant, tenant)
    renamed.name = "Renamed after setup"
    session.commit()
    assert (
        company_setup.create_company(
            session,
            scheduled_owner.id,
            "retry",
            "Harbor Supply",
            "sandbox",
            "international_demo",
            confirmed=True,
        )["tenant_id"]
        == tenant
    )


def test_concurrent_request_creates_one_ordinary_company(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor

    from reality.db.company_setup import OrdinaryCompanyCreation

    _engine, factory, _tenant, actor = scheduled_database

    def create():
        with factory() as db:
            return company_setup.create_company(
                db,
                actor,
                "concurrent",
                "One Company",
                "business",
                "empty",
                confirmed=True,
            )["tenant_id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: create(), range(2)))
    assert results[0] == results[1]
    with factory() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(OrdinaryCompanyCreation)
                .where(
                    OrdinaryCompanyCreation.actor_id == actor,
                    OrdinaryCompanyCreation.request_key == "concurrent",
                )
            )
            == 1
        )


def test_initializing_sandbox_receipt_retains_original_intent(
    session, scheduled_owner, monkeypatch
):
    from reality.services import playground

    original = playground._initialize
    monkeypatch.setattr(
        playground,
        "_initialize",
        lambda db, run_id, actor_id: db.get(PlaygroundRun, run_id),
    )
    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "interrupted",
        "Still Starting",
        "sandbox",
        "empty",
        confirmed=True,
    )
    assert result["status"] == "initializing"
    replay = company_setup.create_company(
        session,
        scheduled_owner.id,
        "interrupted",
        "Still Starting",
        "sandbox",
        "empty",
        confirmed=True,
    )
    assert replay["tenant_id"] == result["tenant_id"] and replay["status"] == "ready"
    monkeypatch.setattr(playground, "_initialize", original)
    original(session, result["run_id"], scheduled_owner.id)
    assert (
        company_setup.read_request(session, scheduled_owner.id, "interrupted")["status"]
        == "ready"
    )


def test_concurrent_cross_environment_request_has_one_winner(
    scheduled_database, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor

    _engine, factory, _tenant, actor = scheduled_database

    def create(environment):
        with factory() as db:
            try:
                return company_setup.create_company(
                    db,
                    actor,
                    "cross-kind",
                    "One Company",
                    environment,
                    "empty",
                    confirmed=True,
                )["tenant_id"]
            except Conflict:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(create, ("business", "sandbox")))
    assert results.count("conflict") == 1
    assert len(set(results)) == 2


@pytest.mark.parametrize("pending", [False, True])
def test_live_creation_provisions_and_starts_once(
    session, scheduled_owner, monkeypatch, pending
):
    from reality.services import demo_data

    if pending:
        scheduled_owner.status = "pending_approval"
        session.commit()
    actor = scheduled_owner.id
    result = company_setup.create_company(
        session,
        actor,
        "live-create",
        "Live Demo",
        "sandbox",
        "international_demo",
        live_simulation=True,
        confirmed=True,
    )
    assert result["status"] == "initializing"
    assert seed_company(session, result["tenant_id"]) == "succeeded"
    assert (
        company_setup.read_request(session, actor, "live-create")["status"] == "ready"
    )
    state = demo_data.status(session, result["tenant_id"], actor)
    assert state["state"] == "running" and state["rate"] == 60
    assert state["generated"] == 0
    demo_data.control(
        session,
        result["tenant_id"],
        actor,
        "pause",
        state["revision"],
        "pause-live",
        confirmed=True,
    )
    replay = company_setup.create_company(
        session,
        actor,
        "live-create",
        "Live Demo",
        "sandbox",
        "international_demo",
        live_simulation=True,
        confirmed=True,
    )
    assert replay["tenant_id"] == result["tenant_id"]
    current = demo_data.status(session, result["tenant_id"], actor)
    assert (
        current["state"] == "paused" and current["schedule_id"] == state["schedule_id"]
    )
    with pytest.raises(Conflict):
        company_setup.create_company(
            session,
            actor,
            "live-create",
            "Live Demo",
            "sandbox",
            "international_demo",
            confirmed=True,
        )


def test_live_creation_failure_is_retryable_without_partial_connection(
    session, scheduled_owner, monkeypatch
):
    from reality.services import demo_data

    actor = scheduled_owner.id
    original = demo_data.control

    def fail(*args, **kwargs):
        raise RuntimeError("injected setup interruption")

    monkeypatch.setattr(demo_data, "control", fail)
    result = company_setup.create_company(
        session,
        actor,
        "live-retry",
        "Live Retry",
        "sandbox",
        "international_demo",
        live_simulation=True,
        confirmed=True,
    )
    assert result["status"] == "initializing" and result["destination"] is None
    assert seed_company(session, result["tenant_id"]) == "succeeded"
    assert (
        company_setup.read_request(session, actor, "live-retry")["status"]
        == "initialization_failed"
    )
    assert (
        demo_data.status(session, result["tenant_id"], actor)["state"]
        == "not_connected"
    )
    assert (
        company_setup.read_request(session, actor, "live-retry")["status"]
        == "initialization_failed"
    )
    monkeypatch.setattr(demo_data, "control", original)
    ready = company_setup.retry_request(session, actor, "live-retry", confirmed=True)
    assert ready["status"] == "ready" and ready["tenant_id"] == result["tenant_id"]
    assert demo_data.status(session, ready["tenant_id"], actor)["state"] == "running"


@pytest.mark.parametrize(
    "environment,content",
    [("business", "empty"), ("sandbox", "empty"), ("sandbox", "execution")],
)
def test_live_creation_refuses_other_company_kinds(
    session, scheduled_owner, environment, content
):
    with pytest.raises(InvalidOperation):
        company_setup.create_company(
            session,
            scheduled_owner.id,
            "invalid-live",
            "Invalid",
            environment,
            content,
            live_simulation=True,
            confirmed=True,
        )
