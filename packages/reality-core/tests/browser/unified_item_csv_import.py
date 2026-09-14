"""Explicit real-browser proof; owns all database and process resources."""

import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import AppUser, TenantMembership, build_engine
from reality.services import core
from reality.web.auth import password_hasher

ROOT = Path(__file__).resolve().parents[4]


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def ready(url, process):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        assert process.poll() is None, f"Server exited before {url} was ready"
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise AssertionError(f"Server was not ready: {url}")


def test_real_unified_item_csv_import(postgres_database, tmp_path):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this explicit browser test"
    )
    artifacts = Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path)))
    artifacts.mkdir(parents=True, exist_ok=True)
    api_port, web_port = free_port(), free_port()
    while web_port == api_port:
        web_port = free_port()
    env = dict(
        os.environ,
        REALITY_DATABASE_URL=postgres_database,
        REALITY_AUTH_MODE="enabled",
        REALITY_BOOTSTRAP_TENANT_NAME="",
        REALITY_PLATFORM_ADMIN_EMAIL="",
        REALITY_PLATFORM_ADMIN_PASSWORD="",
        REALITY_COOKIE_SECURE="false",
        APP_URL=f"http://127.0.0.1:{web_port}",
        API_URL=f"http://127.0.0.1:{api_port}",
        PYTHONPATH="src",
        REALITY_ARTIFACT_DIR=str(artifacts / "originals"),
    )
    processes, logs = [], []
    engine = None
    try:
        with (artifacts / "migration.log").open("w") as output:
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=ROOT / "packages/reality-core",
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=90,
            )
        engine = build_engine(postgres_database)
        factory = sessionmaker(engine, expire_on_commit=False)
        password = secrets.token_urlsafe(24)
        with factory() as session:
            tenant = core.create_tenant(session, "CSV import test company")
            foreign = core.create_tenant(session, "Foreign CSV company")
            # Authentication scaffolding only; business setup above uses canonical services.
            owner = AppUser(
                id=core.uid("usr"),
                email="journey@example.test",
                password_hash=password_hasher.hash(password),
                status="active",
                email_verified_at=core.now(),
                is_platform_admin=False,
            )
            session.add(owner)
            session.flush()
            session.add(
                TenantMembership(
                    id=core.uid("mem"),
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role="member",
                    status="active",
                )
            )
            session.commit()
            fixture = {
                "tenant": tenant.id,
                "foreign": foreign.id,
                "email": owner.email,
                "password": password,
            }
        for name, command, cwd, child_env in [
            (
                "api",
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "reality.web.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                ],
                ROOT / "packages/reality-core",
                env,
            ),
            (
                "web",
                [
                    "npm",
                    "run",
                    "dev",
                    "--",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(web_port),
                    "--strictPort",
                ],
                ROOT / "apps/web",
                dict(
                    env,
                    VITE_API_PROXY_TARGET=f"http://127.0.0.1:{api_port}",
                ),
            ),
        ]:
            output = (artifacts / f"{name}.log").open("w")
            logs.append(output)
            processes.append(
                subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=child_env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            )
        ready(f"http://127.0.0.1:{api_port}/healthz", processes[0])
        ready(f"http://127.0.0.1:{web_port}", processes[1])
        browser_env = dict(
            env,
            JOURNEY_BASE_URL=f"http://127.0.0.1:{web_port}",
            JOURNEY_FIXTURE=json.dumps(fixture),
            JOURNEY_ARTIFACTS=str(artifacts),
        )
        with (artifacts / "browser.log").open("w") as output:
            browser_process = subprocess.Popen(
                ["node", "scripts/unified-item-import-browser.mjs"],
                cwd=ROOT / "apps/web",
                env=browser_env,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            processes.append(browser_process)
            browser_process.wait(timeout=240)
        assert browser_process.returncode == 0, (artifacts / "browser.log").read_text()
        result = json.loads((artifacts / "result.json").read_text())
        with factory() as session:
            from reality.db.core import Item, SourceRecord
            from reality.services.delivery_actions import delivery_proposal_detail

            detail = delivery_proposal_detail(session, tenant.id, result["proposal"])
            assert detail["verification"] == "verified"
            receipt = detail["receipt"]
            assert len(receipt["item_ids"]) == 2
            assert (
                len(
                    list(
                        session.scalars(select(Item).where(Item.tenant_id == tenant.id))
                    )
                )
                == 2
            )
            source = session.get(SourceRecord, receipt["source_record_id"])
            assert source.source_artifact_id == receipt["artifact_id"]
            assert all(
                session.get(Item, identity).source_record_id == source.id
                for identity in receipt["item_ids"]
            )
        print(f"Real item CSV import verified; artifacts: {artifacts}")
    finally:
        import signal

        for process in reversed(processes):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
        for output in logs:
            output.close()
        if engine:
            engine.dispose()
