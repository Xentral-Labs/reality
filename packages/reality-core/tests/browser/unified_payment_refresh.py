"""Spec 121 FR-001/006: refresh an open dialog after external invoice acceptance."""

import json
import os
import subprocess
from pathlib import Path

from conftest import business
from live_stack import PASSWORD, ROOT, add_member, live_stack, migrate
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from test_financial_intake_admission import prepared_invoice

from reality.db.core import Document, build_engine
from reality.services.intake import review_intake


def test_payment_dialog_refreshes_real_accepted_invoice(postgres_database, tmp_path):
    artifacts = Path(
        os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path / "payment-refresh"))
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            company = business.__wrapped__(session)
            owner = add_member(
                session,
                company.tenant.id,
                "refresh-owner@example.test",
                "Refresh Owner",
                "owner",
            )
            _, proposal = prepared_invoice(session, company)
            fixture = {
                "tenant": company.tenant.id,
                "email": owner.email,
                "password": PASSWORD,
                "proposal": proposal.id,
                "digest": review_intake(session, company.tenant.id, proposal.id)[
                    "digest"
                ],
            }
        with live_stack(env, artifacts) as stack:
            with (artifacts / "browser.log").open("w") as output:
                result = subprocess.run(
                    ["node", "scripts/unified-payment-refresh-browser.mjs"],
                    cwd=ROOT / "apps/web",
                    env=dict(
                        stack["env"],
                        JOURNEY_BASE_URL=stack["web"],
                        JOURNEY_FIXTURE=json.dumps(fixture),
                        JOURNEY_ARTIFACTS=str(artifacts),
                    ),
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    timeout=240,
                    check=False,
                )
            assert result.returncode == 0, (artifacts / "browser.log").read_text()
        with sessionmaker(engine, expire_on_commit=False)() as session:
            payments = list(
                session.scalars(
                    select(Document).where(
                        Document.tenant_id == fixture["tenant"],
                        Document.type == "customer_payment",
                    )
                )
            )
            assert len(payments) == 1
            assert str(payments[0].gross_amount) == "5.0000"
    finally:
        engine.dispose()
