"""Application metrics.

Cardinality is the governing constraint. A Prometheus series is created for
every distinct combination of label values, so an unbounded label -- a user id,
an email address, a raw URL path -- multiplies every series by the size of that
set and is the usual way a Prometheus is destroyed.

The rule applied here: metric attributes are bounded enumerations only
(outcome, provider, role, status). Anything per-user or per-request belongs on a
SPAN, where high cardinality is the point, and is queried from traces instead.
`tenant_id` is deliberately NOT used as an attribute either: it is bounded today
but grows with the business, which is the same mistake arriving more slowly.

Every instrument is created lazily and every record call is a no-op when
telemetry is disabled, so importing this module costs nothing in environments
without a collector.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any

log = logging.getLogger(__name__)

_meter: Any = None
_instruments: dict[str, Any] = {}


def _get_meter() -> Any:
    global _meter
    if _meter is None:
        from opentelemetry import metrics

        _meter = metrics.get_meter("reality")
    return _meter


def _counter(name: str, description: str, unit: str = "1") -> Any:
    if name not in _instruments:
        _instruments[name] = _get_meter().create_counter(
            name, description=description, unit=unit
        )
    return _instruments[name]


def _histogram(name: str, description: str, unit: str) -> Any:
    if name not in _instruments:
        _instruments[name] = _get_meter().create_histogram(
            name, description=description, unit=unit
        )
    return _instruments[name]


def _enabled() -> bool:
    from reality.telemetry import enabled

    return enabled()


def count(name: str, description: str, **attributes: str) -> None:
    """Add one to a counter. Silent when telemetry is off or misbehaving."""
    if not _enabled():
        return
    try:
        _counter(name, description).add(1, attributes)
    except Exception:  # noqa: BLE001 - never let a metric break a request
        log.debug("metric %s failed", name, exc_info=True)


def record(name: str, description: str, unit: str, value: float, **attributes: str) -> None:
    if not _enabled():
        return
    try:
        _histogram(name, description, unit).record(value, attributes)
    except Exception:  # noqa: BLE001
        log.debug("metric %s failed", name, exc_info=True)


@contextmanager
def duration(name: str, description: str, **attributes: str):
    """Time a block and record it in seconds, tagging the outcome.

    The `outcome` attribute is set automatically, because a latency histogram
    that mixes successes with fast failures reads as an improvement when things
    break.
    """
    started = time.perf_counter()
    outcome = "success"
    try:
        yield
    except Exception:
        outcome = "error"
        raise
    finally:
        record(
            name,
            description,
            "s",
            time.perf_counter() - started,
            outcome=outcome,
            **attributes,
        )


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------
# Deliberately NOT counters for signup/verify/login attempts. The FastAPI
# instrumentation already emits request counts and status codes per route, so
# `http.server.duration{http.route="/api/auth/login", http.response.status_code="401"}`
# is the failed-login rate -- a second hand-maintained counter would only be a
# source of disagreement.
#
# What HTTP metrics cannot express is STATE: how many accounts exist and where
# they are stuck. That is the "signed up users" question, and it is a gauge
# read from the database, not a counter accumulated from requests.

_ACCOUNT_STATES = ("email_unverified", "pending_approval", "active", "rejected", "suspended")


def observe_accounts(session_factory: Any) -> None:
    """Report accounts by status, and pending access applications.

    A gauge rather than a counter: restarts must not reset it and two replicas
    must not double it. Every replica reports the same value, so query it with
    `max by (status)`.

    The callback runs on each collection (60s by default) and is a single
    grouped COUNT over a small table. It is wrapped so a database blip yields a
    gap in the series rather than an exception inside the metrics pipeline.
    """
    if not _enabled():
        return
    from opentelemetry import metrics
    from opentelemetry.metrics import CallbackOptions, Observation

    def accounts(_options: CallbackOptions):
        try:
            from sqlalchemy import func, select

            from reality.db.core import AppUser

            with session_factory() as session:
                rows = session.execute(
                    select(AppUser.status, func.count()).group_by(AppUser.status)
                ).all()
            seen = {str(status): int(total) for status, total in rows}
            # Emit a zero for states with no rows, so a status dropping to none
            # shows as 0 rather than the series simply vanishing.
            return [
                Observation(seen.get(state, 0), {"status": state})
                for state in set(_ACCOUNT_STATES) | set(seen)
            ]
        except Exception:  # noqa: BLE001
            return []

    def pending_applications(_options: CallbackOptions):
        try:
            from sqlalchemy import func, select

            from reality.db.core import AccessApplication

            with session_factory() as session:
                total = session.scalar(
                    select(func.count())
                    .select_from(AccessApplication)
                    .where(AccessApplication.status == "pending")
                )
            return [Observation(int(total or 0))]
        except Exception:  # noqa: BLE001
            return []

    meter = metrics.get_meter("reality")
    meter.create_observable_gauge(
        "reality.accounts",
        callbacks=[accounts],
        description="Accounts by status; the signup funnel as standing state",
    )
    meter.create_observable_gauge(
        "reality.access_applications.pending",
        callbacks=[pending_applications],
        description="Access applications awaiting a human decision",
    )


def access_review(decision: str) -> None:
    """Approve vs reject. Not derivable from HTTP metrics: both return 200."""
    count("reality.access_reviews", "Access applications reviewed", decision=decision)


# ---------------------------------------------------------------------------
# Copilot
# ---------------------------------------------------------------------------
# A Copilot turn is the slowest and most expensive thing the API does, and it is
# the one call that leaves the cluster. `provider` separates the managed
# Anthropic key from a tenant's own; `outcome` separates a real answer from the
# deterministic fallback, which is otherwise invisible -- the fallback returns
# HTTP 200 and looks healthy while answering uselessly.

def copilot_turn(provider: str, outcome: str) -> None:
    count("reality.copilot.turns", "Copilot turns served", provider=provider, outcome=outcome)


def copilot_tokens(direction: str, tokens: int, provider: str) -> None:
    if not _enabled() or tokens <= 0:
        return
    try:
        _counter("reality.copilot.tokens", "Copilot tokens billed", "1").add(
            tokens, {"direction": direction, "provider": provider}
        )
    except Exception:  # noqa: BLE001
        log.debug("token metric failed", exc_info=True)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
# Invitation delivery is at-least-once and every attempt rotates the token, so a
# silent send failure invalidates the link already in someone's inbox. A failure
# here is user-visible and otherwise undetectable.

def email_sent(provider: str, result: str, kind: str) -> None:
    count("reality.emails", "Emails dispatched", provider=provider, result=result, kind=kind)


# ---------------------------------------------------------------------------
# Background jobs
# ---------------------------------------------------------------------------
# The runners already compute exactly these counters per sweep. Without them a
# stalled worker is invisible: /healthz is a static route, so the pod stays
# Ready while processing nothing.

_SWEEP_OUTCOMES = (
    "materialized",
    "deferred",
    "processed",
    "succeeded",
    "retry",
    "failed",
    "unresolved",
)


def job_sweep(role: str, counts: dict, seconds: float) -> None:
    if not _enabled():
        return
    try:
        counter = _counter("reality.jobs.sweep_outcomes", "Job sweep outcomes")
        for outcome in _SWEEP_OUTCOMES:
            value = int(counts.get(outcome, 0) or 0)
            if value:
                counter.add(value, {"role": role, "outcome": outcome})
        record(
            "reality.jobs.sweep_duration",
            "Time to complete one job sweep",
            "s",
            seconds,
            role=role,
        )
        if counts.get("budget_exhausted"):
            count("reality.jobs.budget_exhausted", "Sweeps that hit their budget", role=role)
    except Exception:  # noqa: BLE001
        log.debug("job sweep metrics failed", exc_info=True)


# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------

def observe_pool(engine: Any) -> None:
    """Report SQLAlchemy pool occupancy as observable gauges.

    Read from the pool on collection rather than tracked on checkout, so the
    numbers cannot drift from reality if a code path forgets to instrument.
    """
    if not _enabled():
        return
    from opentelemetry import metrics
    from opentelemetry.metrics import CallbackOptions, Observation

    def _gauge(fn):
        def callback(_options: CallbackOptions):
            try:
                return [Observation(fn(engine.pool))]
            except Exception:  # noqa: BLE001 - a dead pool must not break collection
                return []
        return callback

    meter = metrics.get_meter("reality")
    meter.create_observable_gauge(
        "reality.db.pool.in_use",
        callbacks=[_gauge(lambda p: p.checkedout())],
        description="Connections currently checked out",
    )
    meter.create_observable_gauge(
        "reality.db.pool.available",
        callbacks=[_gauge(lambda p: p.checkedin())],
        description="Connections idle in the pool",
    )
    # SQLAlchemy counts overflow from -pool_size, so an idle pool reports a
    # negative number. Clamped to 0: an operator reads "overflow" as "we are
    # past the base pool", and a dashboard showing -4 looks broken.
    meter.create_observable_gauge(
        "reality.db.pool.overflow",
        callbacks=[_gauge(lambda p: max(0, p.overflow()))],
        description="Connections beyond pool_size; approaching max_overflow means saturation",
    )
