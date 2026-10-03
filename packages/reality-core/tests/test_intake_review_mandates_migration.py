"""Spec 355: mandate migration preserves actual retained delegation history."""

from datetime import timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal
from reality.db.intake_review import IntakeReviewMandate
from reality.mcp.auth import create_mcp_access_token
from reality.services import core


def test_mandate_migration_roundtrip_and_retained_history_refusal(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0140_unstated_document_totals")
    command.upgrade(config, "0141_intake_review_mandates")
    engine = create_engine(postgres_database)
    try:
        assert "intake_review_mandate" in inspect(engine).get_table_names()
        command.downgrade(config, "0140_unstated_document_totals")
        assert "intake_review_mandate" not in inspect(engine).get_table_names()
        command.upgrade(config, "0141_intake_review_mandates")
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Mandate history")
            token, _ = create_mcp_access_token(session, tenant.id, "Historical token")
            grant = ChangeProposal(
                id=core.uid("act"),
                tenant_id=tenant.id,
                type="tool:intake_mandate_grant",
                status="executed",
            )
            session.add(grant)
            session.flush()
            mandate = IntakeReviewMandate(
                id=core.uid("mandate"),
                tenant_id=tenant.id,
                grant_decision_id=grant.id,
                agent_token_id=token.id,
                scope={},
                expires_at=core.now() + timedelta(days=1),
            )
            session.add(mandate)
            session.commit()
            mandate_id = mandate.id
            tenant_id = tenant.id
        with pytest.raises(RuntimeError, match="preserve actual delegation history"):
            command.downgrade(config, "0140_unstated_document_totals")
        with Session(engine) as session:
            assert session.get(IntakeReviewMandate, (tenant_id, mandate_id)) is not None
    finally:
        engine.dispose()
