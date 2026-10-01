"""The peak-intake benchmark measures what it claims (spec 300 FR-003).

A small run against a fresh database: Shopify orders through the import-job
path from parallel processes, then reservations from parallel connections, with
the invariants the 10,000-order run is judged by.
"""

import pytest

from benchmarks.peak_intake.runner import run, validate_database_target


def test_the_runner_refuses_a_database_it_might_damage():
    with pytest.raises(ValueError, match="reality_benchmark_"):
        validate_database_target("reality", confirmed=True)
    with pytest.raises(ValueError, match="confirm-disposable"):
        validate_database_target("reality_benchmark_peak", confirmed=False)
    # Positive control: a disposable database, once confirmed, is accepted.
    validate_database_target("reality_benchmark_peak", confirmed=True)


def test_a_small_run_interprets_every_order_once_and_never_over_reserves(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")

    result = run(postgres_database, orders=50, processes=2, items=5, seed=7)

    assert result["orders"] == 50
    assert result["intake"]["processes"] == 2
    assert result["intake"]["failed"] == 0
    assert result["intake"]["orders_per_second"] > 0
    checks = result["checks"]
    assert checks["sales_orders"] == 50
    assert checks["orders_interpreted_more_than_once"] == 0
    assert checks["over_reserved_items"] == []
    # The run sells more than it stocks, so the oversold check is not vacuous.
    assert checks["oversold_items"] > 0
    assert checks["oversold_matches_demand_less_stock"] is True
    assert result["reservations"]["reserved"] > 0
    # Stock runs out, so some promises get less than they asked for and none more.
    assert checks["promises_not_fully_reserved"] > 0
