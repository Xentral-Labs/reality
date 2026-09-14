"""One request deadline shared by SQL, derived loops and serialization."""

import time
from contextvars import ContextVar

DEADLINE: ContextVar[float | None] = ContextVar("analytics_deadline", default=None)
CANCELLED: ContextVar[object | None] = ContextVar("analytics_cancelled", default=None)


def check_budget():
    from reality.services.analytics.execution import AnalyticsError

    cancelled = CANCELLED.get()
    if cancelled is not None and cancelled.is_set():
        raise AnalyticsError("The analysis was cancelled.", "query_cancelled")
    deadline = DEADLINE.get()
    if deadline is not None and time.monotonic() >= deadline:
        raise AnalyticsError(
            "The analysis exceeded its execution limit.", "query_timeout"
        )
