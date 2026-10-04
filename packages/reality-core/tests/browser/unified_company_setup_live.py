"""Explicit real-browser proof of live demo company setup against a live stack.

A platform administrator creates a demo company with live simulation through the setup
dialog; the worker seeds it and the dialog shows data, calculation and ready before the
company opens (specs 146, 199, 201).
"""

import json
import os
from pathlib import Path

from live_stack import PASSWORD, add_member, live_stack, migrate, run_browser_script
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from reality.db.core import ChangeProposal, Document, SourceRecord, build_engine
from reality.services import core


def test_live_demo_company_setup_reports_each_step(postgres_database, tmp_path):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this browser test"
    )
    artifacts = (
        Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path))) / "company-setup-live"
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            # The administrator already works in one company, so the app opens normally.
            tenant = core.create_tenant(session, "Existing company")
            admin = add_member(
                session, tenant.id, "admin@example.test", "Ada Admin", "owner"
            )
            admin.is_platform_admin = True
            session.commit()
    finally:
        engine.dispose()
    with live_stack(env, artifacts) as stack:
        run_browser_script(
            "company-setup-live-browser.mjs",
            dict(
                stack["env"],
                UNIFIED_APP_URL=stack["web"],
                REALITY_PLATFORM_ADMIN_EMAIL="admin@example.test",
                REALITY_PLATFORM_ADMIN_PASSWORD=PASSWORD,
                SHOTS=str(artifacts),
            ),
            artifacts,
            timeout=300,
        )
    result = json.loads((artifacts / "review-result.json").read_text())
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            proposal = session.get(
                ChangeProposal, (result["tenant"], result["proposal_id"])
            )
            source = session.get(
                SourceRecord, (result["tenant"], result["source_record_id"])
            )
            assert proposal.status == "executed"
            assert proposal.decided_by_user_id == admin.id
            assert proposal.decided_at is not None
            assert source.payload == result["original"]
            assert json.loads(proposal.output)["digest"] == result["digest"]
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(Document)
                    .where(
                        Document.tenant_id == result["tenant"],
                        Document.source_record_id == source.id,
                    )
                )
                == 1
            )
    finally:
        engine.dispose()
    print(f"Live demo company setup verified; artifacts: {artifacts}")
