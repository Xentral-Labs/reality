"""One request deadline shared by SQL, derived loops and serialization."""

import time
from contextvars import ContextVar

DEADLINE: ContextVar[float | None] = ContextVar("analytics_deadline", default=None)
CANCELLED: ContextVar[object | None] = ContextVar("analytics_cancelled", default=None)

#: How much of a company a derivation may hold, when the caller is a worker rather
#: than a request. Absent — the normal case — leaves every declared cap as it is.
#:
#: This changes whether the work is attempted, never what it returns. A context
#: variable that could change an answer would not be acceptable here; one that
#: decides whether an answer is reachable is the same kind of statement as the
#: deadline above it.
DEFERRED_INPUTS: ContextVar[int | None] = ContextVar(
    "analytics_deferred_inputs", default=None
)


def input_ceiling(declared: int) -> int:
    """The cap in force: the declared one, or the worker's if this is a worker."""
    deferred = DEFERRED_INPUTS.get()
    return max(declared, deferred) if deferred else declared


def check_budget():
    from reality.services.analytics.errors import AnalyticsError

    cancelled = CANCELLED.get()
    if cancelled is not None and cancelled.is_set():
        raise AnalyticsError("The analysis was cancelled.", "query_cancelled")
    deadline = DEADLINE.get()
    if deadline is not None and time.monotonic() >= deadline:
        raise AnalyticsError(
            "The analysis exceeded its execution limit.", "query_timeout"
        )
