"""Compressed local rehearsal controller; no background scheduler or agent authority."""

import argparse
import importlib
import re
import subprocess
import time
import uuid
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path

import yaml
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from scenarios.harness.observer import differences, observe
from scenarios.harness.reporting import Recorder, encode, timestamp

DEFAULT_FIXTURE = Path(__file__).parents[1] / "reference_week/scenario.yaml"


def load_scenario(path: Path) -> dict:
    with path.open() as stream:
        scenario = yaml.safe_load(stream)
    validate_scenario(scenario)
    return scenario


def validate_scenario(scenario: dict) -> None:
    if not isinstance(scenario, dict) or not scenario.get("events"):
        raise ValueError("scenario must contain events")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", scenario.get("adapter", "")):
        raise ValueError("invalid adapter")
    if not isinstance(scenario.get("version"), int) or not scenario.get("id"):
        raise ValueError("scenario ID and version required")
    start = datetime.fromisoformat(scenario["start"])
    if start.utcoffset() != timedelta(0):
        raise ValueError("UTC scenario start required")
    identities = set()
    previous = -1
    for event in scenario["events"]:
        if event["id"] in identities:
            raise ValueError("duplicate event identity")
        identities.add(event["id"])
        day, minute = event["day"], event["minute"]
        if (
            type(day) is not int
            or type(minute) is not int
            or not 1 <= day <= 7
            or not 0 <= minute < 1440
        ):
            raise ValueError("invalid event time")
        current = (day - 1) * 1440 + minute
        if current < previous:
            raise ValueError("events must be chronological")
        previous = current
        if (
            not isinstance(event.get("steps"), list)
            or not isinstance(event.get("expected"), dict)
            or not event["expected"]
        ):
            raise ValueError("every event requires steps and an explicit oracle")


def revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def run_scenario(
    session: Session,
    owner_id: str,
    scenario: dict,
    *,
    scope: str,
    output_root: Path,
    confirmed: bool = False,
    barrier_timeout: float = 120,
) -> dict:
    if confirmed is not True:
        raise ValueError("explicit confirmation required before company creation")
    if scope not in {"day", "week"} or barrier_timeout <= 0:
        raise ValueError("invalid scope or barrier timeout")
    validate_scenario(scenario)
    module = importlib.import_module(f"scenarios.{scenario['adapter']}.simulator")
    module.validate_fixture(scenario)
    run_id = uuid.uuid4().hex
    directory = Path(output_root) / run_id
    recorder = Recorder(directory)
    manifest = {
        "run_id": run_id,
        "scenario_id": scenario["id"],
        "version": scenario["version"],
        "fixture_hash": sha256(encode(scenario).encode()).hexdigest(),
        "code_revision": revision(),
        "runner_source_hashes": {
            str(path.relative_to(Path(__file__).parents[1])): sha256(
                path.read_bytes()
            ).hexdigest()
            for path in [
                *sorted(Path(__file__).parent.glob("*.py")),
                Path(module.__file__),
            ]
        },
        "scope": scope,
        "owner_id": owner_id,
        "started_at": timestamp(),
        "scenario_start": scenario["start"],
        "clock": "compressed ordered events; application clock remains real",
        "authority": "explicit local human confirmation of the exact authored fixture",
        "adapter": scenario["adapter"],
        "barrier_timeout_seconds": barrier_timeout,
        "coverage": "manual-source core replay; no external intake, AI or projection proof",
    }
    recorder.write("manifest.json", manifest)
    result = {
        "run_id": run_id,
        "scope": scope,
        "status": "failed",
        "artifact_dir": str(directory.resolve()),
    }
    simulator = module.Simulator(
        session,
        owner_id,
        scenario,
        run_id,
        recorder,
        datetime.fromisoformat(scenario["start"]),
    )
    current_id = "company_setup"
    try:
        created = simulator.create()
        result["company_id"] = created["tenant_id"]
        manifest.update(company_id=created["tenant_id"], setup_receipt=created)
        recorder.write("manifest.json", manifest)
        for authored_event in scenario["events"]:
            if scope == "day" and authored_event["day"] > 1:
                break
            current_id = authored_event["id"]
            event = {
                **authored_event,
                "scenario_time": (
                    simulator.start
                    + timedelta(
                        days=authored_event["day"] - 1, minutes=authored_event["minute"]
                    )
                ).isoformat(),
            }
            began = time.monotonic()
            recorder.append(
                "events.jsonl",
                {
                    "event_id": current_id,
                    "phase": "submitted",
                    "scenario_time": event["scenario_time"],
                },
            )
            simulator.execute(event)
            actual = observe(session, simulator.tenant_id)
            mismatch = differences(event["expected"], actual)
            # Invariants are always enforced, even if a fixture omits their oracle keys.
            for key in ("invariants", "evidence_errors"):
                if actual[key] and not any(d["path"] == key for d in mismatch):
                    mismatch.extend(differences([], actual[key], key))
            checkpoint = {
                "event_id": current_id,
                "checkpoint": event.get("checkpoint", current_id),
                "scenario_time": event["scenario_time"],
                "expected": event["expected"],
                "actual": actual,
                "differences": mismatch,
            }
            recorder.append("checkpoints.jsonl", checkpoint)
            result["final"] = actual
            if mismatch:
                result["failure"] = {
                    "event_id": current_id,
                    "kind": "oracle_mismatch",
                    "differences": mismatch,
                }
                break
            if time.monotonic() - began > barrier_timeout:
                result["failure"] = {"event_id": current_id, "kind": "barrier_timeout"}
                break
        else:
            result["status"] = "passed"
        if not result.get("failure"):
            result["status"] = "passed"
    except Exception as error:  # noqa: BLE001 - retain evidence of unknown effects without retry
        # Never redispatch an uncertain effect, and never serialize raw DB/provider errors.
        session.rollback()
        result["failure"] = {
            "event_id": current_id,
            "kind": "execution_or_observation_error",
            "error_type": type(error).__name__,
            "error_code": getattr(error, "code", None),
            "outcome": "reconcile retained receipts before retry; no automatic retry",
        }
        if simulator.tenant_id:
            try:
                result["final"] = observe(session, simulator.tenant_id)
            except Exception:  # noqa: BLE001 - observation failure must not erase the original failure
                result.pop("final", None)
    result["finished_at"] = timestamp()
    recorder.finish(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the local Reality reference day/week"
    )
    parser.add_argument(
        "--actor-id", required=True, help="Existing eligible local owner ID"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Approve this exact authored fixture"
    )
    parser.add_argument("--scope", choices=("day", "week"), default="day")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument(
        "--output", type=Path, default=Path("../../artifacts/reference_week")
    )
    args = parser.parse_args()
    if not args.confirm:
        parser.error("--confirm is required; no company was created")
    from reality.db.core import build_engine, resolve_database_url

    database_url = resolve_database_url()
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        parser.error("this developer runner requires a local PostgreSQL database")
    engine = build_engine(database_url)
    try:
        with Session(engine, expire_on_commit=False) as session:
            result = run_scenario(
                session,
                args.actor_id,
                load_scenario(args.fixture),
                scope=args.scope,
                output_root=args.output,
                confirmed=True,
            )
        print(f"{result['status']}: {result['artifact_dir']}/report.md")
        return 0 if result["status"] == "passed" else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
