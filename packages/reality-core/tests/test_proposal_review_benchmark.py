import pytest

from reality.benchmarks.proposal_review import measure, percentile


def test_measure_warms_once_and_reports_each_timed_read():
    reads = []
    ticks = iter([1.0, 1.005, 2.0, 2.010])

    durations = measure(lambda: reads.append(True), 2, clock=lambda: next(ticks))

    assert reads == [True, True, True]
    assert durations == pytest.approx([5.0, 10.0])
    assert percentile(durations, 0.95) == pytest.approx(10.0)
