"""Pure, bounded UTC calendar calculations; no persistence or execution."""

import re
from datetime import UTC, datetime, timedelta
from itertools import pairwise

from croniter import croniter


def validate_timing(
    *, interval_seconds: int | None = None, cron_expression: str | None = None
) -> None:
    if (interval_seconds is None) == (cron_expression is None):
        raise ValueError("Specify exactly one interval or cron expression.")
    if interval_seconds is not None:
        if type(interval_seconds) is not int or not 5 <= interval_seconds <= 2147483647:
            raise ValueError(
                "Interval must be an integer between 5 and 2147483647 seconds."
            )
    else:
        if not isinstance(cron_expression, str) or len(cron_expression) > 256:
            raise ValueError("Invalid cron expression.")
        fields = cron_expression.split()
        atom = r"(?:\*|\d+(?:-\d+)?)(?:/[1-9]\d*)?"
        if len(fields) != 5 or any(
            not re.fullmatch(rf"{atom}(?:,{atom})*", f) for f in fields
        ):
            raise ValueError("Use five numeric UTC cron fields.")
        try:
            croniter(
                cron_expression,
                datetime(2026, 1, 1, tzinfo=UTC),
                day_or=True,
                max_years_between_matches=8,
            ).get_next(datetime)
        except (ValueError, KeyError, OverflowError) as error:
            raise ValueError(
                "Cron has no valid occurrence within eight years."
            ) from error


def next_time(
    at: datetime,
    *,
    interval_seconds: int | None = None,
    cron_expression: str | None = None,
    previous: datetime | None = None,
) -> datetime:
    validate_timing(interval_seconds=interval_seconds, cron_expression=cron_expression)
    if at.tzinfo is None or (previous is not None and previous.tzinfo is None):
        raise ValueError("Scheduling requires aware UTC timestamps.")
    at = at.astimezone(UTC)
    if interval_seconds is not None:
        anchor = previous or at
        steps = max(1, (at - anchor) // timedelta(seconds=interval_seconds) + 1)
        return anchor + timedelta(seconds=steps * interval_seconds)
    return croniter(
        cron_expression, at, day_or=True, max_years_between_matches=8
    ).get_next(datetime)


def preview(at: datetime, **timing) -> list[datetime]:
    result = []
    for _ in range(5):
        at = next_time(at, **timing)
        result.append(at)
    return result


def validate_initial_offsets(
    offsets: tuple[int, ...], interval_seconds: int | None
) -> None:
    """Bound the optional first-activation sequence; regular schedules are unchanged."""
    if not offsets:
        return
    if (
        interval_seconds is None
        or len(offsets) > 10
        or any(type(value) is not int or not 0 <= value <= 3600 for value in offsets)
        or any(right - left < 5 for left, right in pairwise(offsets))
    ):
        raise ValueError(
            "Initial offsets require an interval and at most ten ordered slots."
        )


def next_initial_time(
    at: datetime, anchor: datetime, offsets: list[int], interval_seconds: int
) -> tuple[datetime, bool]:
    """Skip missed initial slots, then continue on the normal grid after the last."""
    for offset in offsets:
        candidate = anchor + timedelta(seconds=offset)
        if candidate > at:
            return candidate, True
    return next_time(
        at,
        interval_seconds=interval_seconds,
        previous=anchor + timedelta(seconds=offsets[-1]),
    ), False
