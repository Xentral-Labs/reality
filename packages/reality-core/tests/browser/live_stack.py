"""A real, disposable stack for browser proofs against the live API.

Each proof owns its database (the ``postgres_database`` fixture), migrates it, seeds it
through canonical services and starts the processes a deployment runs: API, Vite, worker
and scheduler, and the MCP runtime when asked. Logs land in the artifacts directory.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen

from reality.db.core import AppUser, TenantMembership
from reality.services import core
from reality.web.auth import password_hasher

ROOT = Path(__file__).resolve().parents[4]
PASSWORD = "a-long-account-password"


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def ready(url: str, process: subprocess.Popen) -> None:
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


def add_member(session, tenant_id: str, email: str, name: str, role: str) -> AppUser:
    """Authentication scaffolding only; business setup uses canonical services."""
    user = AppUser(
        id=core.uid("usr"),
        email=email,
        display_name=name,
        password_hash=password_hasher.hash(PASSWORD),
        status="active",
        email_verified_at=core.now(),
        is_platform_admin=False,
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=core.uid("mem"),
            tenant_id=tenant_id,
            user_id=user.id,
            role=role,
            status="active",
        )
    )
    session.commit()
    return user


def migrate(database_url: str, artifacts: Path) -> dict[str, str]:
    """Migrate the proof's database and return the environment every process shares."""
    env = dict(
        os.environ,
        REALITY_DATABASE_URL=database_url,
        REALITY_AUTH_MODE="enabled",
        REALITY_BOOTSTRAP_TENANT_NAME="",
        REALITY_PLATFORM_ADMIN_EMAIL="",
        REALITY_PLATFORM_ADMIN_PASSWORD="",
        REALITY_COOKIE_SECURE="false",
        # The test suite turns interaction recording off (tests/conftest.py); a deployment
        # records, and the live monitor needs it.
        REALITY_INTERACTIONS="on",
        PYTHONPATH="src",
    )
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
    return env


@contextmanager
def live_stack(env: dict[str, str], artifacts: Path, *, mcp: bool = False):
    """Start API, Vite, worker, scheduler (and the MCP runtime); stop them afterwards."""
    api_port, web_port, mcp_port = free_port(), free_port(), free_port()
    while len({api_port, web_port, mcp_port}) < 3:
        web_port, mcp_port = free_port(), free_port()
    api = f"http://127.0.0.1:{api_port}"
    web = f"http://127.0.0.1:{web_port}"
    mcp_url = f"http://127.0.0.1:{mcp_port}/"
    env = dict(env, APP_URL=web, API_URL=api, MCP_URL=mcp_url)
    python = sys.executable
    core_dir = ROOT / "packages/reality-core"
    commands = [
        (
            "api",
            [
                python,
                "-m",
                "uvicorn",
                "reality.web.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(api_port),
            ],
            core_dir,
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
            dict(env, VITE_API_PROXY_TARGET=api),
        ),
        # Registers read background projections (spec 179), as in production.
        (
            "worker",
            [python, "-m", "reality.worker.cli", "work", "--poll-seconds", "1"],
            core_dir,
            env,
        ),
        (
            "scheduler",
            [python, "-m", "reality.scheduler.cli", "work", "--poll-seconds", "1"],
            core_dir,
            env,
        ),
    ]
    if mcp:
        commands.append(
            (
                "mcp",
                [
                    python,
                    "-m",
                    "uvicorn",
                    "reality.mcp.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(mcp_port),
                ],
                core_dir,
                dict(env, MCP_AUTHORIZATION_ISSUER=api),
            )
        )
    processes, logs = [], []
    try:
        for name, command, cwd, child_env in commands:
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
        ready(f"{api}/healthz", processes[0])
        ready(web, processes[1])
        if mcp:
            ready(f"{mcp_url}healthz", processes[-1])
        yield {"api": api, "web": web, "mcp": mcp_url, "env": env}
    finally:
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


def run_browser_script(
    script: str, env: dict[str, str], artifacts: Path, timeout: int = 240
):
    """Run one apps/web script against the stack; its output is the assertion message."""
    log = artifacts / (script + ".log")
    with log.open("w") as output:
        result = subprocess.run(
            ["node", "scripts/" + script],
            cwd=ROOT / "apps/web",
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    assert result.returncode == 0, log.read_text()
