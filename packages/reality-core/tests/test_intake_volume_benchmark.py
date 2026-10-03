"""Spec 355: volume evidence must come from exact approved real effects."""

import pytest


def test_volume_runner_requires_explicit_disposable_database():
    from reality.benchmarks.intake import validate_target

    with pytest.raises(ValueError, match="disposable"):
        validate_target("postgresql://localhost/production", confirmed=True)
    with pytest.raises(ValueError, match="confirm-disposable"):
        validate_target(
            "postgresql://localhost/reality_benchmark_intake_probe", confirmed=False
        )
    validate_target(
        "postgresql://localhost/reality_benchmark_intake_probe", confirmed=True
    )


def test_qualification_compares_measured_medians_and_every_budget():
    from reality.benchmarks.intake import qualification

    def trial(mode, seconds, queries):
        return {
            "mode": mode,
            "workload": "orders",
            "records": 500,
            "phases": {"apply": {"seconds": seconds, "queries": queries}},
            "incremental_peak_rss_mib": 10,
            "max_chunk_seconds": 2,
            "effects_match": True,
        }

    trials = [
        trial("single", 10, 100),
        trial("single", 20, 200),
        trial("single", 30, 300),
        trial("bulk", 29, 299),
        trial("bulk", 30, 300),
        trial("bulk", 31, 301),
    ]
    result = qualification(trials)
    assert result["passed"]
    assert result["workloads"]["orders"]["time_ratio"] == 1.5
    trials[-1]["effects_match"] = False
    assert not qualification(trials)["passed"]
    trials[-1]["effects_match"] = True
    trials[-1]["max_chunk_seconds"] = 121
    assert not qualification(trials)["passed"]
    with pytest.raises(ValueError, match="three"):
        qualification(trials[:2])


@pytest.fixture
def volume_database():
    import uuid

    from conftest import _drop_database, admin_engine, admin_url
    from sqlalchemy import create_engine, text

    from reality.db.core import Base

    name = f"reality_benchmark_intake_{uuid.uuid4().hex[:10]}"
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url = admin_url.set(database=name).render_as_string(hide_password=False)
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    try:
        yield url
    finally:
        _drop_database(name)


@pytest.mark.parametrize("workload,records", [("orders", 3), ("items", 501)])
@pytest.mark.parametrize("mode", ["single", "bulk"])
def test_small_real_trials_count_only_exact_owner_approved_effects(
    volume_database, workload, records, mode, monkeypatch
):
    from reality.benchmarks.intake import run_trial

    monkeypatch.setenv("REALITY_DATABASE_URL", volume_database)
    result = run_trial(volume_database, workload, mode, records=records, confirmed=True)
    assert result["effects_match"]
    assert result["records"] == records
    assert result["units"] == (records if workload == "orders" else 2)
    assert all(
        row["queries"] > 0 and row["seconds"] > 0 for row in result["phases"].values()
    )
    assert result["queue_config_bytes"] <= 15000
