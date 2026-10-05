"""Real PostgreSQL transactions serialize takeover against a stale cached agent state."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from conftest import business as business_fixture
from conftest import scheduled_owner as owner_fixture
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from test_operational_cases import activate, order

from reality.db.core import Base
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.case_action_guards import automated_execution
from reality.services.memberships import Principal


def test_committed_takeover_wins_against_separate_session_with_cached_automation(
    postgres_database,
):
    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as setup:
            company = business_fixture.__wrapped__(setup)
            owner = owner_fixture.__wrapped__(setup, company)
            setup.commit()
            activate(setup, company, owner)
            promise = order(setup, company)
            tenant_id, promise_id, owner_id = company.tenant.id, promise.id, owner.id
            case_id = cases.object_cases(setup, tenant_id, "commitment", promise_id)[0]
        cached, proceed = Event(), Event()

        def agent():
            with Session(engine, expire_on_commit=False) as session:
                assert (
                    cases._case(session, tenant_id, case_id).control_mode
                    == "automation"
                )
                cached.set()
                assert proceed.wait(5)
                try:
                    with automated_execution(session, tenant_id):
                        core.revise_commitment(
                            session, tenant_id, promise_id, quantity="20"
                        )
                except core.InvalidOperation as error:
                    session.rollback()
                    return error.code
                return "unexpected-success"

        with ThreadPoolExecutor(max_workers=1) as pool, Session(engine) as human:
            future = pool.submit(agent)
            assert cached.wait(5)
            cases.takeover(
                human,
                tenant_id,
                case_id,
                Principal(owner_id),
                expected_revision=1,
                request_key="race",
                confirmed=True,
                _commit=False,
            )
            proceed.set()
            human.commit()
            assert future.result(timeout=10) == "case_human_owned"
        with Session(engine) as check:
            assert core.commitment_quantity(check, tenant_id, promise_id) == 30
            assert cases.explain(check, tenant_id, case_id)["control_revision"] == 2
    finally:
        engine.dispose()
