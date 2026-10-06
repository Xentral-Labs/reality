"""Independent two-site oracle; expectations never call the production evaluator."""

from datetime import datetime
from decimal import Decimal

from reality.domain.shipping_performance import (
    Capacity,
    DispatchWork,
    PhysicalContent,
    covered_at,
    evaluate,
)


def at(time):
    return datetime.fromisoformat(f"2026-10-06T{time}:00+02:00")


def work(identity, order, site, planned, actual=None, ready=True, due="16:00"):
    return DispatchWork(
        identity,
        order,
        site,
        Decimal(1),
        at(due),
        at(planned),
        at(actual) if actual else None,
        ready,
    )


def oracle():
    return [
        work("a", "A", "V", "14:00", "14:10"),
        work("b1", "B", "V", "14:00", "14:20", due="15:30"),
        work("b2", "B", "V", "15:00", due="15:30"),
        work("cv", "C", "V", "15:30"),
        work("cl", "C", "L", "15:30"),
        work("d", "D", "L", "16:00", ready=False),
    ], [
        Capacity("V", at("14:30"), at("16:00"), at("16:00"), 2, "confirmed"),
        Capacity("L", at("14:30"), at("16:00"), at("16:00"), 1, "confirmed"),
    ]


def test_company_completion_requires_all_quantities_and_sites():
    requirements, windows = oracle()
    result = evaluate(requirements, windows, observed_at=at("14:30"))
    assert result["actual_times"] == {"A": at("14:10")}
    assert result["planned_times"] == {
        "A": at("14:00"),
        "B": at("15:00"),
        "C": at("15:30"),
        "D": at("16:00"),
    }
    assert result["forecast_times"] == {
        "A": at("14:10"),
        "B": at("15:15"),
        "C": at("16:00"),
    }
    assert result["risk_order_ids"] == ["D"]
    assert result["sites"]["V"]["due"] == 3
    assert result["sites"]["L"]["due"] == 2
    assert result["sites"]["V"]["forecast"] == 3
    assert result["sites"]["L"]["forecast"] == 1


def test_fall_back_same_wall_time_retains_distinct_handover_instants():
    from zoneinfo import ZoneInfo

    zone = ZoneInfo("Europe/Berlin")
    early = datetime(2026, 10, 25, 2, 30, tzinfo=zone, fold=0)
    late = datetime(2026, 10, 25, 2, 30, tzinfo=zone, fold=1)
    due = datetime.fromisoformat("2026-10-25T05:00:00+00:00")
    rows = [
        DispatchWork("x", "X", "V", Decimal(1), due, early, early, True),
        DispatchWork("y", "X", "V", Decimal(1), due, late, late, True),
    ]
    result = evaluate(rows, [], observed_at=due)
    assert result["actual_times"]["X"].isoformat() == "2026-10-25T01:30:00+00:00"


def test_requested_collection_is_visible_but_excluded_from_baseline():
    requirements, windows = oracle()
    requirements.append(work("e", "E", "V", "17:00", due="17:00"))
    requested = Capacity("V", at("16:00"), at("17:00"), at("17:00"), 1, "requested")
    result = evaluate(requirements, windows + [requested], observed_at=at("14:30"))
    assert len(result["planned_times"]) == 5
    assert len(result["forecast_times"]) == 3
    confirmed = Capacity("V", at("16:00"), at("17:00"), at("17:00"), 1, "confirmed")
    result = evaluate(requirements, windows + [confirmed], observed_at=at("14:30"))
    assert result["forecast_times"]["E"] == at("17:00")


def test_earlier_cutoff_does_not_compress_original_capacity_pace():
    requirements = [work("x", "X", "V", "15:00"), work("y", "Y", "V", "15:30")]
    windows = [Capacity("V", at("14:30"), at("16:30"), at("15:30"), 2, "confirmed")]
    result = evaluate(requirements, windows, observed_at=at("14:30"))
    assert result["forecast_times"] == {"X": at("15:30")}


def test_observed_completions_consume_capacity_once_and_keep_original_pace():
    requirements = [work("x", "X", "V", "14:00", "14:40"), work("y", "Y", "V", "15:00")]
    windows = [Capacity("V", at("14:30"), at("16:30"), at("16:30"), 2, "confirmed")]
    result = evaluate(requirements, windows, observed_at=at("15:00"))
    assert result["forecast_times"]["Y"] == at("16:00")


def test_missing_capacity_or_timed_plan_remains_unknown():
    requirements, windows = oracle()
    result = evaluate(requirements, windows[:1], observed_at=at("14:30"))
    assert result["forecast_complete"] is False
    assert result["sites"]["L"]["forecast"] is None
    missing = DispatchWork("x", "X", "V", Decimal(1), at("16:00"), None, None, True)
    assert (
        evaluate([missing], windows[:1], observed_at=at("14:30"))["plan_complete"]
        is False
    )


def test_quantity_coverage_deduplicates_movements_and_requires_handover():
    first = PhysicalContent("m1", Decimal(1), at("14:00"), (at("14:10"), at("14:10")))
    second = PhysicalContent("m2", Decimal(1), at("14:00"), ())
    assert covered_at(Decimal(2), [first, first, second], observed_at=at("14:30")) == (
        None,
        (),
    )
    second = PhysicalContent("m2", Decimal(1), at("14:00"), (at("14:20"),))
    assert covered_at(Decimal(2), [first, first, second], observed_at=at("14:30")) == (
        at("14:20"),
        (),
    )


def test_conflicting_missing_future_or_prephysical_times_are_explicit_gaps():
    for times in [(at("14:10"), at("14:20")), (None,), (at("15:00"),), (at("13:59"),)]:
        content = PhysicalContent("m", Decimal(1), at("14:00"), times)
        completed, gaps = covered_at(Decimal(1), [content], observed_at=at("14:30"))
        assert completed is None
        assert gaps


def test_a_completion_on_adjacent_window_boundary_consumes_one_budget_only():
    requirements = [
        work("x", "X", "V", "15:00", "16:00"),
        work("y", "Y", "V", "16:30", due="17:00"),
        work("z", "Z", "V", "17:00", due="17:00"),
    ]
    windows = [
        Capacity("V", at("14:30"), at("16:00"), at("16:00"), 1, "confirmed"),
        Capacity("V", at("16:00"), at("17:00"), at("17:00"), 2, "confirmed"),
    ]
    result = evaluate(requirements, windows, observed_at=at("16:00"))
    assert result["forecast_times"]["Y"] == at("16:30")
    assert result["forecast_times"]["Z"] == at("17:00")


def test_observation_cannot_treat_future_handover_as_actual_or_ready_work():
    requirements = [work("x", "X", "V", "15:00", "15:00")]
    windows = [Capacity("V", at("14:30"), at("16:00"), at("16:00"), 2, "confirmed")]
    result = evaluate(requirements, windows, observed_at=at("14:30"))
    assert result["actual_times"] == {}
    assert result["forecast_complete"] is False


def test_unknown_handover_preserves_an_independently_valid_source_stated_plan():
    from dataclasses import replace

    requirements, windows = oracle()
    requirements[0] = replace(
        requirements[0],
        handed_over_at=None,
        coverage_gaps=("missing_or_conflicting_handover_time",),
    )
    result = evaluate(requirements, windows, observed_at=at("14:30"))
    assert result["plan_complete"] is True
    assert len(result["planned_times"]) == 4
    assert result["forecast_complete"] is False


def test_risk_retains_the_individual_earlier_deadline_in_a_split_site_order():
    from dataclasses import replace

    requirements, windows = oracle()
    requirements[3] = replace(requirements[3], due_at=at("15:45"))
    result = evaluate(requirements, windows, observed_at=at("14:30"))
    assert result["risk_order_ids"] == ["C", "D"]
    earlier = next(
        row for row in result["risk_requirements"] if row["commitment_id"] == "cv"
    )
    assert earlier["due_at"] == at("15:45")
    assert earlier["code"] == "after_deadline"
