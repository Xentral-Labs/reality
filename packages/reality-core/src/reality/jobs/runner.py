"""Bounded process execution for registered database-only handlers."""

from __future__ import annotations

import json
import subprocess
import sys
from threading import Event
from time import monotonic
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Engine

from reality.jobs.registry import JobError

SAFE_CODES = frozenset(
    {
        "stale_claim",
        "not_authorized",
        "not_found",
        "unknown_job_type",
        "unsupported_job_version",
        "invalid_configuration",
        "handler_timeout",
        "handler_commit_forbidden",
        "result_too_large",
        "handler_failed",
    }
)


def _session_info_from_stdin() -> dict[str, str]:
    try:
        value = json.loads(sys.stdin.readline(4096))
    except (ValueError, OSError):
        return {}
    if not isinstance(value, dict) or set(value) - {
        "desktop_installation_id",
        "desktop_owner_id",
    }:
        return {}
    return (
        value if all(isinstance(item, str) and item for item in value.values()) else {}
    )


def child_main(
    tenant_id: str,
    run_id: str,
    token: str,
    *,
    session_info: dict[str, str] | None = None,
) -> int:
    from sqlalchemy import select
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    from reality.jobs.runtime import database
    from reality.services.scheduled_jobs import execute_claim

    engine = None
    try:
        engine = database(child=True)
        from reality.db.scheduled_jobs import ScheduledJobRun

        with engine.connect() as connection:
            job_type = connection.scalar(
                select(ScheduledJobRun.job_type).where(
                    ScheduledJobRun.tenant_id == tenant_id,
                    ScheduledJobRun.id == run_id,
                )
            )
        execution_engine = (
            engine.execution_options(isolation_level="REPEATABLE READ")
            if job_type in {"projections.refresh", "costing.captured_report.refresh"}
            else engine
        )
        with (
            Session(execution_engine, info=session_info or {}) as session,
            session.begin(),
        ):
            status = execute_claim(session, tenant_id, run_id, token)
        print(json.dumps({"status": status}))
        return 0
    except JobError as error:
        print(
            json.dumps(
                {
                    "code": error.code
                    if error.code in SAFE_CODES
                    else "handler_failed",
                    "retryable": error.code == "handler_timeout",
                }
            )
        )
    except SQLAlchemyError:
        print(json.dumps({"code": "database_error", "retryable": True}))
    except Exception:  # noqa: BLE001 - child boundary must not expose payloads or secrets
        print(json.dumps({"code": "handler_failed", "retryable": False}))
    finally:
        if engine is not None:
            engine.dispose()
    return 1


def execute_process(
    engine: Engine,
    tenant_id: str,
    run_id: str,
    token: str,
    *,
    stop: Event | None = None,
    timeout: float = 30,
    session_info: dict[str, str] | None = None,
) -> str:
    """Wait at most timeout+2s; settle from durable state after child termination."""
    from sqlalchemy.orm import Session

    from reality.services.scheduled_jobs import record_failure

    # No inherited connection or caller-controlled shell; child uses only shared core.
    child = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "reality.jobs.runner",
            tenant_id,
            run_id,
            token,
            "--session-info-stdin",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    deadline = monotonic() + timeout
    timed_out = False
    child_input = json.dumps(session_info or {}) + "\n"
    try:
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                timed_out = True
                child.terminate()
                try:
                    output, _ = child.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    output, _ = child.communicate(timeout=2)
                break
            try:
                output, _ = child.communicate(
                    input=child_input,
                    timeout=min(0.2, remaining),
                )
                break
            except subprocess.TimeoutExpired:
                child_input = None
                # SIGTERM stops new dispatch. Already handed-off work gets its bound.
                continue
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=2)
    try:
        payload = json.loads(output)
        if not isinstance(payload, dict):
            raise TypeError()
    except (ValueError, TypeError):
        payload = {"code": "child_exited", "retryable": True}
    code = "handler_timeout" if timed_out else payload.get("code", "child_exited")
    # Even a successful child is re-read under the claim lock. A lost response never
    # redispatches a committed effect; a dead transaction must settle before this lock.
    with Session(engine) as session, session.begin():
        return record_failure(
            session,
            tenant_id,
            run_id,
            token,
            code,
            retryable=timed_out or bool(payload.get("retryable")),
        )


if __name__ == "__main__":
    if len(sys.argv) not in {4, 5}:
        raise SystemExit(2)
    with_info = len(sys.argv) == 5 and sys.argv[4] == "--session-info-stdin"
    if len(sys.argv) == 5 and not with_info:
        raise SystemExit(2)
    raise SystemExit(
        child_main(
            *sys.argv[1:4], session_info=_session_info_from_stdin() if with_info else {}
        )
    )
