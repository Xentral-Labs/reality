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


def _run(revision: str = "abc1234", **overrides) -> IngestResult:
    """One recorded run, small enough that a test can state what it expects."""
    step = {
        "step": "order",
        "produced": 1,
        "queries": 120,
        "sql_ms": 100.0,
        "wall_ms": 110.0,
        "interpreting_queries": 60,
        "interpreting_ms": 50.0,
        **overrides,
    }
    return IngestResult.from_samples(
        [{"orders_before": 0, "steps": [step]}],
        created_at=datetime(2026, 9, 20, tzinfo=UTC),
        git_revision=revision,
        python="3.12",
        platform="test",
        postgresql="17",
        tenant_id="ten_compare",
    )


def test_two_identical_runs_agree_on_every_recorded_cost():
    """SC-005 asks the measurement to know its own spread before it is believed."""
    from benchmarks.ingest_cost.compare import compare

    verdict = compare(_run(), _run())

    assert verdict["repeatable"] is True
    assert verdict["findings"] == []
    assert verdict["compared"] == 6, "every figure of the step is compared"


def test_a_query_that_ran_once_more_is_reported_however_small():
    """A count is the same arithmetic on any host, so it is held to equality.

    Ten per cent of a hundred and twenty queries is twelve; a tolerance would let
    a builder read eleven more times a run and call it weather.
    """
    from benchmarks.ingest_cost.compare import compare

    verdict = compare(_run(), _run(queries=121))

    assert verdict["repeatable"] is False
    assert [
        (finding["step"], finding["figure"], finding["difference"])
        for finding in verdict["findings"]
    ] == [("order", "queries", 1)]


def test_a_timing_within_the_tolerance_is_weather_and_beyond_it_is_a_finding():
    from benchmarks.ingest_cost.compare import compare

    assert compare(_run(), _run(sql_ms=109.0))["repeatable"] is True
    beyond = compare(_run(), _run(sql_ms=120.0))
    assert [finding["figure"] for finding in beyond["findings"]] == ["sql_ms"]
    assert beyond["findings"][0]["spread"] == pytest.approx(0.167, abs=0.001)


def test_a_finding_names_the_checkpoint_and_the_step_it_belongs_to():
    """User Story 5: every change in cost is attributable to an intake step."""
    from benchmarks.ingest_cost.compare import compare

    verdict = compare(_run(), _run(interpreting_queries=61))

    assert verdict["findings"][0]["orders_before"] == 0
    assert verdict["findings"][0]["step"] == "order"
    assert verdict["findings"][0]["kind"] == "count"


def test_two_runs_of_different_commits_are_refused_rather_than_diffed():
    """SC-005 is about repeatability, and two commits cannot answer it."""
    from benchmarks.ingest_cost.compare import NotComparable, compare

    with pytest.raises(NotComparable, match="same commit"):
        compare(_run("abc1234"), _run("def5678"))


def test_a_checkpoint_that_drifted_is_reported_rather_than_refused():
    """The fixture cannot land on a checkpoint exactly.

    One sweep delivers several orders, so growing "to 250" can stop at 251 — and
    two runs of the same command then record different sizes. That is drift in the
    company, not in the cost, so the comparison says so and carries on comparing.
    """
    from benchmarks.ingest_cost.compare import compare

    first = _run()
    second = _run()
    second.samples[0].orders_before = 251

    verdict = compare(first, second)

    assert [finding["figure"] for finding in verdict["findings"]] == ["checkpoint"]
    assert verdict["findings"][0]["difference"] == 251


def test_two_runs_with_a_different_number_of_checkpoints_are_refused():
    from benchmarks.ingest_cost.compare import NotComparable, compare

    first = _run()
    second = _run()
    second.samples.append(second.samples[0].model_copy(deep=True))

    with pytest.raises(NotComparable, match="number of checkpoints"):
        compare(first, second)


def test_no_ratio_is_reported_when_the_samples_hold_different_steps():
    """A missing step is an incomplete measurement, not a cheaper order to cash.

    One run reported 0.53x — a halving — because its largest company had found no
    single-record payment sweep and the ratio divided two different measurements
    (spec 181 SC-005, 2026-09-20).
    """
    complete = {
        "orders_before": 0,
        "steps": [
            {
                "step": "order",
                "produced": 1,
                "queries": 144,
                "sql_ms": 30.0,
                "wall_ms": 40.0,
                "interpreting_queries": 52,
                "interpreting_ms": 12.0,
            },
            {
                "step": "payment",
                "produced": 1,
                "queries": 208,
                "sql_ms": 60.0,
                "wall_ms": 70.0,
                "interpreting_queries": 113,
                "interpreting_ms": 30.0,
            },
        ],
    }
    partial = {
        "orders_before": 500,
        "steps": [complete["steps"][0]],
    }
    result = IngestResult.from_samples(
        [complete, partial],
        created_at=datetime(2026, 9, 20, tzinfo=UTC),
        git_revision="abc1234",
        python="3.12",
        platform="test",
        postgresql="17",
        tenant_id="ten_shape",
    )

    assert result.growth() is None
    assert "No ratio" in result.summary()
