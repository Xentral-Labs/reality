import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
IMAGE_TAG = os.environ.get("REALITY_CONTAINER_IMAGE_TAG", "spec147")


@pytest.mark.parametrize("module", ["reality.scheduler.cli", "reality.worker.cli"])
def test_entrypoint_help_without_database_or_migrations(module):
    env = dict(os.environ)
    env.pop("REALITY_DATABASE_URL", None)
    env["PYTHONPATH"] = str(ROOT / "packages/reality-core/src")
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "work" in result.stdout


@pytest.mark.parametrize("role", ["scheduler", "worker"])
def test_distinct_container_command_and_no_port_or_migration(role):
    dockerfile = (ROOT / f"apps/{role}/Dockerfile").read_text()
    assert f'"reality-{role}"' in dockerfile
    assert "EXPOSE" not in dockerfile
    assert "alembic" not in dockerfile.split("CMD")[-1]
    assert "ENTRYPOINT" not in dockerfile


@pytest.mark.parametrize("role,command", [("scheduler", "tick"), ("worker", "once")])
def test_missing_schema_fails_without_running_migrations(
    postgres_database, monkeypatch, role, command
):
    from sqlalchemy import create_engine, inspect

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    result = subprocess.run(
        [sys.executable, "-m", f"reality.{role}.cli", command, "--json"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 1
    assert "schema_missing" in result.stdout
    assert "local-only" not in result.stdout + result.stderr
    engine = create_engine(postgres_database)
    try:
        assert inspect(engine).get_table_names() == []
    finally:
        engine.dispose()


def test_documented_process_names_and_defaults():
    guide = (ROOT / "docs/features/scheduled-jobs.md").read_text()
    deployment = (ROOT / "docs/WORKER_DEPLOYMENT.md").read_text()
    contract = (ROOT / "specs/147-scheduled-jobs/contracts/worker.md").read_text()
    for name in (
        "reality-scheduler work",
        "reality-scheduler tick",
        "reality-worker work",
        "reality-worker once",
    ):
        assert name in guide and name in contract
    assert "30s" in guide and "120s" in guide
    assert "REALITY_BACKGROUND_ROLE=scheduler" in deployment
    assert "REALITY_BACKGROUND_ROLE=worker" in deployment
    assert "postgresql+psycopg://" in deployment


@pytest.mark.skipif(
    os.getenv("REALITY_CONTAINER_SMOKE") != "1",
    reason="Opt-in local Docker image smoke test",
)
def test_built_images_share_queue_and_stop_cleanly(scheduled_database):
    import json
    import time

    from test_scheduled_worker import setup_due

    _engine, _factory, tenant, actor = scheduled_database
    url = os.environ["REALITY_DATABASE_URL"].replace(
        "localhost:", "host.docker.internal:"
    )
    setup_due(_factory, tenant, actor)

    def run(role, *args):
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-e",
                f"REALITY_DATABASE_URL={url}",
                f"reality-{role}:{IMAGE_TAG}",
                f"reality-{role}",
                *args,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    for role in ("scheduler", "worker"):
        assert "work" in run(role, "--help")
    assert {"invitations.cleanup", "demo.generate_orders"} <= {
        row["name"] for row in json.loads(run("worker", "jobs", "list", "--json"))
    }
    assert (
        json.loads(run("worker", "once", "--tenant", tenant, "--json"))["processed"]
        == 0
    )
    assert (
        json.loads(run("scheduler", "tick", "--tenant", tenant, "--json"))[
            "materialized"
        ]
        == 1
    )
    assert (
        json.loads(run("worker", "once", "--tenant", tenant, "--json"))["succeeded"]
        == 1
    )
    for role in ("scheduler", "worker"):
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "-e",
                f"REALITY_DATABASE_URL={url}",
                f"reality-{role}:{IMAGE_TAG}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        container = result.stdout.strip()
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                logs = subprocess.run(
                    ["docker", "logs", container],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if f"{role}_sweep" in logs.stdout + logs.stderr:
                    break
                time.sleep(0.1)
            else:
                pytest.fail(f"No {role} heartbeat")
            stopped = subprocess.run(
                ["docker", "stop", "-t", "35", container],
                capture_output=True,
                text=True,
                timeout=40,
                check=False,
            )
            assert stopped.returncode == 0
            inspected = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.ExitCode}}", container],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            assert inspected.stdout.strip() == "0"
        finally:
            subprocess.run(
                ["docker", "rm", "-f", container],
                capture_output=True,
                timeout=10,
                check=False,
            )


@pytest.mark.skipif(
    os.environ.get("REALITY_CONTAINER_SMOKE") != "1",
    reason="Opt-in built-image acceptance",
)
def test_built_images_deliver_demo_source_without_browser(
    scheduled_database, monkeypatch
):
    import json
    from datetime import timedelta

    from sqlalchemy import select

    from reality.db.core import Document, now
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.services import company_setup, demo_data

    engine, factory, _tenant, actor = scheduled_database
    with factory() as session:
        result = company_setup.create_company(
            session,
            actor,
            "container-demo",
            "Container Practice",
            "sandbox",
            "empty",
            confirmed=True,
        )
        tenant = result["tenant_id"]
        connected = demo_data.connect(
            session,
            tenant,
            actor,
            "container-connect",
            demo_data.preview(session, tenant, actor)["fingerprint"],
            confirmed=True,
        )
        started = demo_data.control(
            session,
            tenant,
            actor,
            "start",
            connected["revision"],
            "container-start",
            confirmed=True,
        )
        schedule = session.get(ScheduledJob, started["schedule_id"])
        schedule.next_run_at = now() - timedelta(seconds=1)
        session.commit()
    url = engine.url.set(host="host.docker.internal").render_as_string(
        hide_password=False
    )
    for role, command, count in (
        ("scheduler", "tick", "materialized"),
        ("worker", "once", "succeeded"),
    ):
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-e",
                f"REALITY_DATABASE_URL={url}",
                f"reality-{role}:{IMAGE_TAG}",
                f"reality-{role}",
                command,
                "--tenant",
                tenant,
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)[count] == 1
    with factory() as session:
        from reality.db.scheduled_jobs import ScheduledJobRun
        from reality.integrations import demo_data as synthetic

        schedule = session.get(ScheduledJob, started["schedule_id"])
        run = session.scalar(
            select(ScheduledJobRun).where(
                ScheduledJobRun.tenant_id == tenant,
                ScheduledJobRun.schedule_id == schedule.id,
            )
        )
        expected = synthetic.burst_size(
            schedule.configuration["arguments"]["seed"],
            schedule.id,
            run.id,
            run.created_at,
        )
        counts = demo_data.status(session, tenant, actor)
        assert counts["generated"] == counts["imported"] == expected
        assert (
            len(
                session.scalars(
                    select(Document.id).where(
                        Document.tenant_id == tenant, Document.type == "sales_order"
                    )
                ).all()
            )
            == expected
        )
