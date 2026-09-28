"""Explicit real-browser proof of the live monitor (spec 266) against a live stack.

The owner watches web and MCP accesses arrive; the member's writes go through the API and
the MCP read goes through the real MCP runtime with a bearer token.
"""

import os
import shlex
import sys
from pathlib import Path

from live_stack import add_member, live_stack, migrate, run_browser_script
from sqlalchemy.orm import sessionmaker

from reality.db.core import build_engine
from reality.mcp.auth import create_mcp_access_token
from reality.services import core


def test_live_monitor_shows_web_and_mcp_accesses(postgres_database, tmp_path):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this browser test"
    )
    artifacts = Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path))) / "engine-room"
    artifacts.mkdir(parents=True, exist_ok=True)
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            tenant = core.create_tenant(session, "Engine room company")
            core.create_item(session, tenant.id, "LAMP-1", "Desk lamp")
            owner = add_member(
                session, tenant.id, "owner@example.test", "Olga Owner", "owner"
            )
            add_member(
                session, tenant.id, "member@example.test", "Max Member", "member"
            )
            token, secret = create_mcp_access_token(
                session, tenant.id, "Claude Desktop", issued_by_user_id=owner.id
            )
            tenant_id, token_id = tenant.id, token.id
    finally:
        engine.dispose()
    with live_stack(env, artifacts, mcp=True) as stack:
        call = shlex.join(
            [
                sys.executable,
                str(Path(__file__).with_name("mcp_call.py")),
                stack["mcp"],
                secret,
            ]
        )
        run_browser_script(
            "engine-room-live-browser.mjs",
            dict(
                stack["env"],
                ENGINE_ROOM_BASE_URL=stack["web"],
                ENGINE_ROOM_MCP_CALL=call,
                TENANT=tenant_id,
                TOKEN=token_id,
                SHOTS=str(artifacts),
            ),
            artifacts,
        )
    print(f"Live monitor verified against a live stack; artifacts: {artifacts}")
