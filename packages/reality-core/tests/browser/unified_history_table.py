"""Explicit real-browser proof of the History register (spec 269) against a live stack."""

import os
from pathlib import Path

from live_stack import add_member, live_stack, migrate, run_browser_script
from sqlalchemy.orm import sessionmaker

from reality.db.core import build_engine
from reality.services import core


def test_history_register_reads_by_business_names(postgres_database, tmp_path):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this browser test"
    )
    artifacts = (
        Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path))) / "history-table"
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            tenant = core.create_tenant(session, "History company")
            item = core.create_item(session, tenant.id, "LAMP-1", "Desk lamp")
            warehouse = core.create_location(session, tenant.id, "Main warehouse")
            core.record_movement(
                session, tenant.id, "receipt", item.id, "5", to_location_id=warehouse.id
            )
            add_member(session, tenant.id, "owner@example.test", "Olga Owner", "owner")
            session.commit()
            tenant_id = tenant.id
    finally:
        engine.dispose()
    with live_stack(env, artifacts) as stack:
        run_browser_script(
            "history-table-browser.mjs",
            dict(
                stack["env"],
                HISTORY_BASE_URL=stack["web"],
                TENANT=tenant_id,
                SHOTS=str(artifacts),
            ),
            artifacts,
        )
    print(f"History register verified against a live stack; artifacts: {artifacts}")
