"""Additive default rollout, retained owner history and safe downgrade limits."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from reality.db.core import AppUser, ChangeProposal, now, uid
from reality.db.operational_cases import CaseAdoption
from reality.services import core
from reality.services import operational_cases as cases


def test_schema_roundtrip_and_populated_downgrade_guard(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0144_operational_cases")
    engine = create_engine(postgres_database)
    try:
        assert "case_proposal_link" in inspect(engine).get_table_names()
        command.downgrade(config, "0143_intake_review_mandates")
        assert "operational_case" not in inspect(engine).get_table_names()
        command.upgrade(config, "0144_operational_cases")
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Historical owner adoption")
            owner = AppUser(
                id=uid("usr"),
                email=f"{uid('mail')}@example.test",
                password_hash="unused",
                status="active",
                email_verified_at=now(),
            )
            session.add(owner)
            session.flush()
            decision = ChangeProposal(
                id=uid("act"),
                tenant_id=tenant.id,
                type="case:adopt",
                actor_type="human",
                status="executed",
                input="{}",
                output='{"capture_sequence": 0}',
                decided_at=now(),
                decided_by_user_id=owner.id,
            )
            session.add(decision)
            session.flush()
            # Retained pre-upgrade fixture, not a fabricated application decision.
            session.add(
                CaseAdoption(
                    tenant_id=tenant.id,
                    decision_id=decision.id,
                    capture_sequence=0,
                    selected_order_ids=[],
                    selected_return_ids=[],
                )
            )
            session.commit()
            tenant_id, decision_id, receipt = tenant.id, decision.id, decision.output
            assert not cases.coordination_status(session, tenant_id)["migration_ready"]
            with pytest.raises(core.InvalidOperation) as error:
                cases.coordination_enabled(session, tenant_id)
            assert error.value.code == "case_schema_not_ready"
        command.upgrade(config, "0145_default_operational_cases")
        assert "ix_scheduled_run_claim_history" in {
            index["name"] for index in inspect(engine).get_indexes("scheduled_job_run")
        }
        command.downgrade(config, "0144_operational_cases")
        assert "ix_scheduled_run_claim_history" not in {
            index["name"] for index in inspect(engine).get_indexes("scheduled_job_run")
        }
        command.upgrade(config, "0145_default_operational_cases")
        with Session(engine) as session:
            cases.reconcile_events(session, tenant_id)
            assert cases.coordination_status(session, tenant_id)["coverage_ready"]
            assert session.get(CaseAdoption, tenant_id).decision_id == decision_id
            assert (
                session.get(ChangeProposal, (tenant_id, decision_id)).output == receipt
            )
        with pytest.raises(RuntimeError, match="control history"):
            command.downgrade(config, "0144_operational_cases")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM case_adoption")) == 1
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "0145_default_operational_cases"
            )
    finally:
        engine.dispose()
