"""Spec 355: real source selection, lost responses and actual queue receipts."""

import json
import os
import subprocess
from pathlib import Path

from conftest import business
from live_stack import PASSWORD, ROOT, add_member, live_stack, migrate
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from test_bulk_intake_admission import prepared_orders

from reality.db.core import Document, TenantMembership, build_engine
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.services import core
from reality.services.intake import review_intake_original_source
from reality.services.intake_batches import batch_status


def test_real_bulk_intake_decisions(postgres_database, tmp_path):
    artifacts = Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path / "bulk-intake")))
    artifacts.mkdir(parents=True, exist_ok=True)
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            company = business.__wrapped__(session)
            owner = add_member(
                session,
                company.tenant.id,
                "bulk-owner@example.test",
                "Bulk Owner",
                "owner",
            )
            foreign = core.create_tenant(session, "Other review company")
            session.add(
                TenantMembership(
                    id=core.uid("mem"),
                    tenant_id=foreign.id,
                    user_id=owner.id,
                    role="owner",
                    status="active",
                )
            )
            session.commit()
            entries = prepared_orders(session, company, 3)
            fixture = {
                "tenant": company.tenant.id,
                "foreign": foreign.id,
                "email": owner.email,
                "password": PASSWORD,
                "entries": entries,
                "originals": {
                    entry["proposal_id"]: review_intake_original_source(
                        session, company.tenant.id, entry["proposal_id"]
                    )["payload"]
                    for entry in entries
                },
            }
            session.commit()
        with live_stack(env, artifacts) as stack:
            browser_env = dict(
                stack["env"],
                JOURNEY_BASE_URL=stack["web"],
                JOURNEY_FIXTURE=json.dumps(fixture),
                JOURNEY_ARTIFACTS=str(artifacts),
            )
            with (artifacts / "browser.log").open("w") as output:
                completed = subprocess.run(
                    ["node", "scripts/unified-bulk-intake-browser.mjs"],
                    cwd=ROOT / "apps/web",
                    env=browser_env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    timeout=240,
                    check=False,
                )
            if completed.returncode != 0:
                with sessionmaker(engine, expire_on_commit=False)() as diagnostics:
                    runs = diagnostics.scalars(select(ScheduledJobRun).where(
                        ScheduledJobRun.tenant_id.in_([fixture["tenant"], fixture["foreign"]])
                    ).order_by(ScheduledJobRun.created_at, ScheduledJobRun.id))
                    queue = [
                        {"id": run.id, "tenant_id": run.tenant_id, "job_type": run.job_type,
                         "status": run.status, "attempt_count": run.attempt_count,
                         "last_error_code": run.last_error_code}
                        for run in runs
                    ]
                    (artifacts / "queue-on-failure.json").write_text(json.dumps(queue, indent=2))
            assert completed.returncode == 0, (artifacts / "browser.log").read_text()
        result = json.loads((artifacts / "result.json").read_text())
        with sessionmaker(engine, expire_on_commit=False)() as session:
            status = batch_status(session, fixture["tenant"], result["batch_id"])
            assert status["counts"] == {"applied": 3}
            assert (
                len(
                    list(
                        session.scalars(
                            select(Document).where(
                                Document.tenant_id == fixture["tenant"]
                            )
                        )
                    )
                )
                == 3
            )
            assert all(
                row["receipt"]["batch_authorization"]["reviewer_user_id"] == owner.id
                for row in status["results"]
            )
    finally:
        engine.dispose()
