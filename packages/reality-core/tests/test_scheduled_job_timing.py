from datetime import UTC, datetime, timedelta

import pytest

from reality.scheduling.timing import next_time, preview, validate_timing

NOW = datetime(2026, 9, 9, 12, tzinfo=UTC)


def test_interval_coalesces_without_drift_or_burst():
    due = NOW - timedelta(hours=1)
    assert next_time(NOW, interval_seconds=12, previous=due) == NOW + timedelta(
        seconds=12
    )
    assert preview(NOW, interval_seconds=12) == [
        NOW + timedelta(seconds=12 * i) for i in range(1, 6)
    ]


def test_cron_utc_day_or_and_leap_day():
    assert next_time(NOW, cron_expression="0 3 * * *") == datetime(
        2026, 9, 10, 3, tzinfo=UTC
    )
    assert next_time(NOW, cron_expression="0 0 1 * 1") == datetime(
        2026, 9, 14, tzinfo=UTC
    )
    assert next_time(NOW, cron_expression="0 0 29 2 *") == datetime(
        2028, 2, 29, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "cron",
    ["* * * * * *", "@daily", "0 0 * * mon", "0 0 31 2 *", "*/0 * * * *", "0 0 L * *"],
)
def test_invalid_cron_rejected(cron):
    with pytest.raises(ValueError):
        validate_timing(cron_expression=cron)


@pytest.mark.parametrize("interval", [0, 4, True, 5.5])
def test_invalid_intervals_rejected(interval):
    with pytest.raises(ValueError):
        validate_timing(interval_seconds=interval)
