"""Reactive operator comparisons for spec 373."""

import pytest

from scenarios.company_simulator.controller import profile, run_company


@pytest.mark.parametrize("operator", ["prompt", "delayed", "idle"])
def test_operator_comparison(session, scheduled_owner, tmp_path, operator):
    result = run_company(
        session,
        scheduled_owner.id,
        profile(),
        days=30,
        operator=operator,
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed", result
    assert len(result["goals"]) == 12
    if operator == "prompt":
        assert all(g["status"] == "met" for g in result["goals"])
    else:
        assert any(g["status"] == "missed" for g in result["goals"])
    if operator == "idle":
        assert not any(e["kind"] == "supplier_arrival" for e in result["world_events"])
        assert result["final"]["physical"] == {"A": "4", "B": "4"}


def test_future_requests_hidden():
    from scenarios.company_simulator.world import World

    world = World(profile())
    world.release(0)
    assert not world.view(0)["requests"]
    world.release(1)
    assert len(world.view(1)["requests"]) == 1
    assert "oracle" not in world.view(1)


def test_confirmation_and_horizon(session, scheduled_owner, tmp_path):
    for kwargs in ({"confirmed": False, "days": 30}, {"confirmed": True, "days": 31}):
        with pytest.raises(ValueError):
            run_company(
                session,
                scheduled_owner.id,
                profile(),
                operator="prompt",
                output_root=tmp_path,
                **kwargs,
            )
    assert not list(tmp_path.iterdir())


def test_supplier_arrival_depends_on_purchase_day():
    from scenarios.company_simulator.world import World

    first, second = World(profile()), World(profile())
    first.purchased("P1", "A", 4)
    second.purchased("P1", "A", 9)
    assert first.purchases["P1"]["arrival"] == 6
    assert second.purchases["P1"]["arrival"] == 11
    assert first.stock == second.stock == {"A": 4, "B": 4}


def test_short_horizon_leaves_goal_pending(session, scheduled_owner, tmp_path):
    result = run_company(
        session,
        scheduled_owner.id,
        profile(),
        days=1,
        operator="idle",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "passed"
    assert result["goals"][0]["status"] == "pending"


def test_oracle_discrepancy_stops_run(session, scheduled_owner, tmp_path, monkeypatch):
    from scenarios.company_simulator.world import World

    original = World.expected

    def corrupt(self):
        result = original(self)
        result["physical"]["A"] = "999"
        return result

    monkeypatch.setattr(World, "expected", corrupt)
    result = run_company(
        session,
        scheduled_owner.id,
        profile(),
        days=30,
        operator="prompt",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "failed"
    assert result["failure"]["day"] == 1
    assert len(result["goals"]) == 1


def test_operator_view_is_detached_from_world():
    from scenarios.company_simulator.world import World

    world = World(profile())
    world.release(1)
    view = world.view(1)
    view["stock"]["A"] = 999
    view["requests"][0]["quantity"] = 999
    assert world.stock["A"] == 4
    assert world.requests["S01"]["quantity"] == 3


def test_cli_help_requires_no_database(monkeypatch):
    from scenarios.company_simulator.controller import main

    monkeypatch.delenv("REALITY_DATABASE_URL", raising=False)
    monkeypatch.setattr("sys.argv", ["controller", "--help"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 0


def test_unknown_execution_is_reported_without_retry(
    session, scheduled_owner, tmp_path, monkeypatch
):
    from scenarios.reference_week.simulator import Simulator

    calls = []

    def fail(self, *args):
        calls.append(args)
        raise RuntimeError("private diagnostic must not be serialized")

    monkeypatch.setattr(Simulator, "masters", fail)
    result = run_company(
        session,
        scheduled_owner.id,
        profile(),
        days=30,
        operator="prompt",
        output_root=tmp_path,
        confirmed=True,
    )
    assert result["core_status"] == "unknown"
    assert len(calls) == 1
    assert "private diagnostic" not in str(result)


def test_unreviewed_profile_rejected_before_creation(
    session, scheduled_owner, tmp_path
):
    scenario = profile()
    scenario["quote"]["pack_quantity"] = 999
    with pytest.raises(ValueError, match="reviewed"):
        run_company(
            session,
            scheduled_owner.id,
            scenario,
            days=30,
            operator="prompt",
            output_root=tmp_path,
            confirmed=True,
        )
    assert not list(tmp_path.iterdir())
