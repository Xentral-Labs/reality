"""The ingest measurement is a maintained tool, not a script somebody once ran.

Spec 181 FR-006 asks for exactly that, and the reason is in the repository's own
history: `research.md` records 300 queries and 660 ms for one order to cash,
measured on 2026-09-12 by scripts that no longer exist. Nobody can say today
whether that got better or worse.

These tests do not measure anything. They hold the parts a measurement needs to
stay trustworthy: that it refuses a database it might damage, that its per-record
arithmetic is per record, and that the record it leaves can be read back.
"""

from datetime import UTC, datetime

import pytest

from benchmarks.ingest_cost.measure import StepCost, measured
from benchmarks.ingest_cost.report import IngestResult
from benchmarks.ingest_cost.runner import validate_database_target


@pytest.mark.parametrize(
    "database, confirmed, reason",
    [
        ("reality_test", True, "must begin"),
        ("reality", True, "must begin"),
        ("reality_benchmark_ingest", False, "confirm-disposable"),
    ],
)
def test_the_measurement_refuses_a_database_it_might_damage(
    database, confirmed, reason
):
    """FR-006: refused on business companies, by a name it cannot mistake."""
    with pytest.raises(ValueError, match=reason):
        validate_database_target(database, confirmed=confirmed)


def test_a_disposable_database_is_accepted_once_confirmed():
    validate_database_target("reality_benchmark_ingest", confirmed=True)


def test_cost_is_reported_per_record_not_per_sweep():
    """One sweep delivers several orders; a cost per sweep would move with that."""
    cost = StepCost("order", queries=300, sql_ms=60.0, wall_ms=90.0, produced=3)
    record = cost.as_record()
    assert record["queries"] == 100
    assert record["sql_ms"] == 20.0
    assert record["produced"] == 3


def test_a_step_that_produced_nothing_is_not_divided_by_zero():
    cost = StepCost("invoice", queries=40, sql_ms=8.0, produced=0)
    assert cost.as_record()["queries"] == 40


def test_the_tables_a_step_read_most_are_named(session):
    """The third column of research.md's table: where the cost actually went."""
    engine = session.get_bind()
    with measured(engine, "probe") as cost:
        for _ in range(3):
            session.execute(_select_one_tenant())
    assert cost.queries >= 3
    assert dict(cost.tables).get("tenant", 0) >= 3
    assert ("tenant", 3) in [
        (name, n) for name, n in cost.repeated() if name == "tenant"
    ]


def _select_one_tenant():
    from sqlalchemy import select

    from reality.db.core import Tenant

    return select(Tenant.id).limit(1)


def test_the_record_states_what_it_cannot_prove():
    result = IngestResult.from_samples(
        [
            {
                "orders_before": 0,
                "steps": [
                    {
                        "step": "order",
                        "produced": 1,
                        "queries": 140,
                        "sql_ms": 150.0,
                        "wall_ms": 160.0,
                        "interpreting_queries": 70,
                        "interpreting_ms": 80.0,
                    }
                ],
            },
            {
                "orders_before": 1000,
                "steps": [
                    {
                        "step": "order",
                        "produced": 1,
                        "queries": 130,
                        "sql_ms": 180.0,
                        "wall_ms": 190.0,
                        "interpreting_queries": 84,
                        "interpreting_ms": 110.0,
                    }
                ],
            },
        ],
        tenant_id="ten_probe",
        git_revision="abcdef1234",
        python="3.12.4",
        platform="probe",
        postgresql="17",
        created_at=datetime.now(UTC),
    )
    # SC-001 is a ratio, so the record carries one rather than leaving a reader to
    # divide two numbers and guess which way round they go. It is measured on the
    # interpreting span: the sweep total here *falls* while the product path rises,
    # and a ratio taken from the sum would report no growth at all — which is the
    # mistake this split exists to prevent.
    assert result.growth() == 1.2
    assert any("curve" in limitation for limitation in result.limitations)
    assert any("milliseconds" in limitation for limitation in result.limitations)


def test_the_slowest_statements_are_separated_by_span():
    """A sweep statement must never be listed as an interpreting one.

    Mixing them is how the demo generator's throttle came to look like a problem
    with the intake: it was the dearest statement of the step, and the step's list
    did not say which half of the work it belonged to.
    """
    from benchmarks.ingest_cost.measure import StepCost

    cost = StepCost("invoice")
    cost.statements = {
        "SELECT throttle": {
            "sql": "SELECT throttle",
            "ms": 200.0,
            "count": 6,
            "interpreting": False,
        },
        "SELECT document": {
            "sql": "SELECT document",
            "ms": 40.0,
            "count": 12,
            "interpreting": True,
        },
        "SELECT tenant": {
            "sql": "SELECT tenant",
            "ms": 10.0,
            "count": 3,
            "interpreting": None,
        },
    }
    interpreting = cost.slowest(interpreting=True)
    assert [row["sql"] for row in interpreting] == ["SELECT document", "SELECT tenant"]
    sweep = cost.slowest(interpreting=False)
    assert sweep[0]["sql"] == "SELECT throttle"
    # A shape reached from both spans says so rather than claiming one.
    assert [row["span"] for row in interpreting] == ["interpreting", "both"]
