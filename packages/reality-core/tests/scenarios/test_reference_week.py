"""Independent reference-day/week booking proofs (spec 372)."""

import copy
import json
from pathlib import Path

import pytest
from sqlalchemy import event

from scenarios.harness.observer import observe
from scenarios.harness.runner import load_scenario, run_scenario

FIXTURE = Path(__file__).parents[2] / "scenarios/reference_week/scenario.yaml"


def run(session, owner, tmp_path, *, scope="day", scenario=None, confirmed=True):
    return run_scenario(
        session,
        owner.id,
        scenario or load_scenario(FIXTURE),
        scope=scope,
        output_root=tmp_path,
        confirmed=confirmed,
    )


@pytest.mark.parametrize(
    "scope,physical,orders",
    [
        ("day", {"A": "0", "B": "6", "C": "0"}, 4),
        ("week", {"A": "7", "B": "4", "C": "4"}, 10),
    ],
)
def test_reference_day_and_week(
    session, scheduled_owner, tmp_path, scope, physical, orders
):
    result = run(session, scheduled_owner, tmp_path, scope=scope)
    assert result["status"] == "passed", result.get("failure")
    assert result["final"]["physical"] == physical
    assert result["final"]["counts"]["sales_orders"] == orders
    assert result["final"]["counts"]["ledger_entries"] == 0
    assert not result["final"]["evidence_errors"]
    directory = Path(result["artifact_dir"])
    assert json.loads((directory / "report.json").read_text())["status"] == "passed"
    manifest = json.loads((directory / "manifest.json").read_text())
    assert manifest["company_id"] == result["company_id"]
    assert manifest["fixture_hash"] and manifest["owner_id"] == scheduled_owner.id
    assert (directory / "events.jsonl").read_text()
    assert (directory / "checkpoints.jsonl").read_text()
    assert (directory / "report.md").exists()
    prepared = [
        json.loads(line)
        for line in (directory / "events.jsonl").read_text().splitlines()
        if json.loads(line)["phase"] == "prepared"
    ]
    assert prepared and all(row["accepted_effect_delta"] == [] for row in prepared)
    if scope == "week":
        assert result["final"]["return_open"] == {"A": "0", "B": "0", "C": "0"}
        assert result["final"]["locations"] == {
            "W1": {"A": "4", "B": "4", "C": "4"},
            "W2": {"A": "3", "B": "0", "C": "0"},
        }
        assert result["final"]["counts"]["customer_fulfilled"] == 22
        assert result["final"]["counts"]["customer_cancelled"] == 1
        assert result["final"]["movement_totals"]["shipment"] == {
            "A": "51",
            "B": "19",
            "C": "16",
        }


def test_bad_oracle_stops_before_next_effect(session, scheduled_owner, tmp_path):
    scenario = copy.deepcopy(load_scenario(FIXTURE))
    target = next(e for e in scenario["events"] if e["id"] == "E08")
    target["expected"]["physical"]["A"] = "999"
    result = run(session, scheduled_owner, tmp_path, scenario=scenario)
    assert result["status"] == "failed"
    assert result["failure"]["event_id"] == "E08"
    assert any(
        d["path"] == "physical.A" and d["actual"] == "6"
        for d in result["failure"]["differences"]
    )
    assert result["final"]["counts"]["purchase_orders"] == 0
    assert result["final"]["counts"]["sales_orders"] == 3
    assert "E09" not in (Path(result["artifact_dir"]) / "events.jsonl").read_text()


def test_fresh_runs_and_read_only_observer(session, scheduled_owner, tmp_path):
    first = run(session, scheduled_owner, tmp_path)
    second = run(session, scheduled_owner, tmp_path)
    assert first["status"] == second["status"] == "passed"
    assert first["company_id"] != second["company_id"]
    assert first["final"]["physical"] == second["final"]["physical"]

    def forbid_write(conn, cursor, statement, parameters, context, executemany):
        assert statement.lstrip().split()[0].upper() not in {
            "INSERT",
            "UPDATE",
            "DELETE",
        }

    connection = session.connection()
    event.listen(connection, "before_cursor_execute", forbid_write)
    try:
        snapshot = observe(session, first["company_id"])
        assert snapshot["physical"] == first["final"]["physical"]
    finally:
        event.remove(connection, "before_cursor_execute", forbid_write)


def test_confirmation_required_before_creation(session, scheduled_owner, tmp_path):
    with pytest.raises(ValueError, match="confirmation"):
        run(session, scheduled_owner, tmp_path, confirmed=False)
    assert list(tmp_path.iterdir()) == []


def test_invalid_fixture_rejected_before_execution(session, scheduled_owner, tmp_path):
    scenario = copy.deepcopy(load_scenario(FIXTURE))
    scenario["events"][1]["id"] = scenario["events"][0]["id"]
    with pytest.raises(ValueError, match="duplicate"):
        run(session, scheduled_owner, tmp_path, scenario=scenario)


def test_local_cli_uses_configured_database_and_emits_report(monkeypatch, tmp_path):
    """Exercise launch wiring without connecting a second uncommitted session."""
    from contextlib import nullcontext
    from types import SimpleNamespace

    from reality.db import core
    from scenarios.harness import runner

    url = "postgresql+psycopg://local:local-only@127.0.0.1:54329/test"
    monkeypatch.setenv("REALITY_DATABASE_URL", url)
    monkeypatch.setattr(
        "sys.argv",
        ["runner", "--actor-id", "local-owner", "--confirm", "--output", str(tmp_path)],
    )
    disposed = []
    engine = SimpleNamespace(dispose=lambda: disposed.append(True))

    def build(selected_url):
        assert selected_url == url
        return engine

    monkeypatch.setattr(core, "build_engine", build)
    monkeypatch.setattr(
        runner, "Session", lambda selected, **kw: nullcontext("local-session")
    )

    def execute(session, actor, scenario, **kwargs):
        assert session == "local-session" and actor == "local-owner"
        assert kwargs["confirmed"] and kwargs["scope"] == "day"
        return {"status": "passed", "artifact_dir": str(tmp_path)}

    monkeypatch.setattr(runner, "run_scenario", execute)
    assert runner.main() == 0
    assert disposed == [True]


def test_local_cli_refuses_remote_database(monkeypatch):
    from scenarios.harness.runner import main

    monkeypatch.setenv(
        "REALITY_DATABASE_URL", "postgresql://local:local-only@remote.invalid/test"
    )
    monkeypatch.setattr("sys.argv", ["runner", "--actor-id", "owner", "--confirm"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
