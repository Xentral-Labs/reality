"""Record each crossing into the application as one interaction (spec 266).

A boundary — the web middleware, an MCP tool invocation, a chat tool call, a CLI
command, a worker job — opens an observation with `observe()`. Everything that
runs inside it only annotates it: the tool layer says whether it proposed or
decided, `emit_business_event` names the events it wrote. When the boundary
closes, one row is written in a session of its own, so that a business
transaction that rolls back still leaves its trace and a trace that fails never
touches the business transaction.

Nothing here is business authority. Rows carry no argument or result values; the
events an interaction links to are only those that were committed.
"""

from __future__ import annotations

import atexit
import logging
import os
import queue
import re
import threading
import time
import uuid
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CORRELATION = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ARGUMENT_LIMIT = 32
_EVENT_CHUNK = 1000
_KIND_RANK = {"read": 0, "write": 1, "job": 2, "propose": 3, "decide": 4}


@dataclass
class Observation:
    tenant_id: str | None
    channel: str
    operation: str
    correlation_id: str
    kind: str = "read"
    actor_user_id: str | None = None
    mcp_token_id: str | None = None
    job_id: str | None = None
    refresh: bool = False
    arguments: tuple[str, ...] = ()
    choices: dict[str, str] = field(default_factory=dict)
    result_count: int | None = None
    proposal_id: str | None = None
    proposal_status: str | None = None
    event_ids: list[str] = field(default_factory=list)
    http_status: int | None = None
    duration_ms: int = 0
    finished_at: datetime | None = None
    outcome: str | None = None
    error_code: str | None = None
    started_at: datetime | None = None
    started: float = 0.0


_current: ContextVar[Observation | None] = ContextVar(
    "engine_room_observation", default=None
)
_session_factory: Callable[[], Session] | None = None

#: How often one process tidies one company's expired interactions, and how many
#: rows one tidy removes. The work that makes the history is the work that tidies
#: it (the spec 181 FR-005 rule for job runs): a company cannot add rows without
#: also forgetting old ones, and a quiet company costs nothing.
TIDY_INTERVAL_SECONDS = 600.0
TIDY_BATCH = 500
_last_tidy: dict[str, float] = {}


def enabled() -> bool:
    return os.environ.get("REALITY_INTERACTIONS", "on").lower() != "off"


def correlation(value: str | None) -> str:
    """A client-supplied correlation if it is well-formed, otherwise a fresh one."""
    if value and CORRELATION.match(value):
        return value
    return "c_" + uuid.uuid4().hex[:20]


def current() -> Observation | None:
    return _current.get()


@contextmanager
def use_session_factory(factory: Callable[[], Session]) -> Iterator[None]:
    """Write interactions through another session factory (tests bind their own)."""
    global _session_factory
    previous = _session_factory
    _session_factory = factory
    try:
        yield
    finally:
        _session_factory = previous


def _factory() -> Callable[[], Session]:
    if _session_factory is not None:
        return _session_factory
    from reality.db.core import Session as ApplicationSession

    return ApplicationSession


def begin(
    tenant_id: str | None,
    channel: str,
    operation: str,
    *,
    correlation_id: str | None = None,
    kind: str = "read",
    actor_user_id: str | None = None,
    mcp_token_id: str | None = None,
    job_id: str | None = None,
    refresh: bool = False,
    arguments: Iterable[str] = (),
    choices: dict[str, str] | None = None,
) -> tuple[Observation | None, Any]:
    """Open an observation, or join the one already open.

    Returns the observation to finish with `end()` — None when this call joined an
    outer one or recording is off — and the context token to reset.

    Only the outermost boundary records. The one exception is a chat tool call
    inside the web request that carries the chat turn: the model crossing into the
    application is its own interaction, and it shares the request's correlation.
    """
    if not enabled():
        return None, None
    outer = _current.get()
    if outer is not None and not (channel == "chat" and outer.channel == "web"):
        return None, None
    observation = Observation(
        tenant_id=tenant_id,
        channel=channel,
        operation=operation[:200],
        correlation_id=(
            outer.correlation_id if outer is not None else correlation(correlation_id)
        ),
        kind=kind,
        actor_user_id=actor_user_id
        if actor_user_id is not None or outer is None
        else outer.actor_user_id,
        mcp_token_id=mcp_token_id,
        job_id=job_id,
        refresh=refresh,
        arguments=tuple(sorted(set(arguments)))[:ARGUMENT_LIMIT],
        choices=dict(choices or {}),
        started_at=_now(),
        started=time.perf_counter(),
    )
    return observation, _current.set(observation)


def release(token: Any) -> None:
    """Make the observation stop being current, in the context that opened it."""
    if token is not None:
        try:
            _current.reset(token)
        except ValueError:
            # Closed from a context other than the opening one (a CLI close
            # callback); the observation is finished either way.
            _current.set(None)


def end(
    observation: Observation | None, token: Any, error: BaseException | None = None
) -> None:
    """Close what `begin()` opened and write it. Never raises.

    Pass `token=None` when `release()` already ran in the opening context — the
    web middleware writes from a worker thread, where the token cannot be reset.
    """
    if observation is None:
        return
    release(token)
    _finish(observation, error)


@contextmanager
def observe(
    tenant_id: str, channel: str, operation: str, **options: Any
) -> Iterator[None]:
    observation, token = begin(tenant_id, channel, operation, **options)
    error: BaseException | None = None
    try:
        yield
    except BaseException as exc:
        error = exc
        raise
    finally:
        end(observation, token, error)


@contextmanager
def tool_boundary(tenant_id: str, tool_name: str) -> Iterator[None]:
    """Used by the tool layer: tell an open observation which company it serves.

    A CLI command opens its observation before it knows the company; the first
    tool it calls, or the first event it writes, settles that.
    """
    observation = _current.get()
    if observation is not None and observation.tenant_id is None:
        observation.tenant_id = tenant_id
    yield


def note_kind(kind: str) -> None:
    observation = _current.get()
    if observation is not None and _KIND_RANK.get(kind, 0) > _KIND_RANK.get(
        observation.kind, 0
    ):
        observation.kind = kind


def note_proposal(proposal_id: str | None, status: str | None) -> None:
    observation = _current.get()
    if observation is not None and proposal_id:
        observation.proposal_id = proposal_id
        observation.proposal_status = status


def note_event(tenant_id: str, event_id: str) -> None:
    observation = _current.get()
    if observation is None:
        return
    if observation.tenant_id is None:
        observation.tenant_id = tenant_id
    if observation.tenant_id == tenant_id:
        observation.event_ids.append(event_id)


def note_result(result: Any) -> None:
    observation = _current.get()
    if observation is None:
        return
    if isinstance(result, list):
        observation.result_count = len(result)
    elif isinstance(result, dict):
        for key in ("items", "rows", "records", "results", "data", "entries"):
            if isinstance(result.get(key), list):
                observation.result_count = len(result[key])
                return


def note_outcome(outcome: str, error_code: str | None) -> None:
    """A boundary that turns a refusal into a normal return says so here."""
    observation = _current.get()
    if observation is not None:
        observation.outcome = outcome
        observation.error_code = error_code[:64] if error_code else None


def note_status(status: int) -> None:
    observation = _current.get()
    if observation is not None:
        observation.http_status = status


def _now() -> datetime:
    from reality.db.core import now

    return now()


def _classify(
    observation: Observation, error: BaseException | None
) -> tuple[str, str | None]:
    if error is not None:
        from pydantic import ValidationError

        from reality.services.core import (
            Conflict,
            InterpretationNeedsReview,
            InvalidOperation,
            NotFound,
            RealityError,
        )

        for kind, code in (
            (NotFound, "not_found"),
            (Conflict, "conflict"),
            (InterpretationNeedsReview, "needs_review"),
            (InvalidOperation, "invalid_operation"),
            (RealityError, "reality_error"),
            (PermissionError, "permission_denied"),
            (ValidationError, "validation_error"),
            (ValueError, "invalid_argument"),
        ):
            if isinstance(error, kind):
                return "refused", str(getattr(error, "code", None) or code)[:64]
        return "failed", type(error).__name__[:64]
    if observation.outcome is not None:
        return observation.outcome, observation.error_code
    status = observation.http_status
    if status is not None and status >= 500:
        return "failed", f"http_{status}"
    if status is not None and status >= 400:
        return "refused", f"http_{status}"
    if observation.kind == "propose" and observation.proposal_status not in (
        None,
        "executed",
        "rejected",
    ):
        return "awaiting_decision", None
    return "ok", None


#: Server processes hand rows to one writer thread, so recording costs the request
#: nothing but a queue put (SC-003). Short-lived processes — a CLI command, a worker
#: child — write in line, because they exit right after and would lose the queue.
QUEUE_SIZE = 10_000
QUEUED_CHANNELS = frozenset({"web", "mcp", "chat"})
_queue: queue.Queue | None = None
_writer_lock = threading.Lock()


def start_background_writer() -> None:
    """Start this process's writer thread once; flushed at interpreter exit."""
    global _queue
    with _writer_lock:
        if _queue is not None:
            return
        _queue = queue.Queue(maxsize=QUEUE_SIZE)
        threading.Thread(
            target=_drain, args=(_queue,), name="engine-room-writer", daemon=True
        ).start()
        atexit.register(flush)


def queued() -> bool:
    """Whether this process hands rows to the writer thread (a put, never a wait)."""
    return _queue is not None


def flush() -> None:
    """Wait until every queued interaction is written (tests, shutdown)."""
    if _queue is not None:
        _queue.join()


#: How many queued interactions one transaction writes at most.
BATCH = 200


def _drain(pending: queue.Queue) -> None:
    while True:
        batch = [pending.get()]
        while len(batch) < BATCH:
            try:
                batch.append(pending.get_nowait())
            except queue.Empty:
                break
        try:
            _record_batch(batch)
        finally:
            for _ in batch:
                pending.task_done()


def _finish(observation: Observation, error: BaseException | None) -> None:
    if observation.tenant_id is None:
        # A command that never touched a company is not a company interaction.
        return
    observation.duration_ms = int((time.perf_counter() - observation.started) * 1000)
    observation.finished_at = _now()
    try:
        outcome, error_code = _classify(observation, error)
    except Exception:  # the engine room never breaks the call it watches
        logger.exception("Interaction could not be classified")
        outcome, error_code = "failed", None
    pending = _queue
    if pending is not None and observation.channel in QUEUED_CHANNELS:
        try:
            pending.put_nowait((observation, outcome, error_code))
            return
        except queue.Full:
            # Better one missing row than a request that waits for telemetry.
            _failed(observation)
            return
    _record(observation, outcome, error_code)


def _failed(observation: Observation) -> None:
    from reality.telemetry import metrics

    metrics.record_interaction_failure(observation.channel)


def _record(observation: Observation, outcome: str, error_code: str | None) -> None:
    _record_batch([(observation, outcome, error_code)])


def _record_batch(batch: list) -> None:
    started = time.perf_counter()
    try:
        _write_batch(batch)
    except Exception:  # the engine room never breaks the call it watches
        logger.exception("Interactions could not be recorded")
        for observation, _, _ in batch:
            _failed(observation)
    finally:
        from reality.telemetry import metrics

        metrics.record_interaction_duration(
            batch[0][0].channel, (time.perf_counter() - started) * 1000 / len(batch)
        )


def _bounded(summary: dict[str, Any]) -> dict[str, Any]:
    """Keep the summary under the column's 1 KiB check rather than lose the row."""
    import json

    from reality.db.interactions import SUMMARY_BYTES

    while len(json.dumps(summary).encode()) > SUMMARY_BYTES - 16:
        if summary.get("arguments"):
            summary["arguments"] = summary["arguments"][:-1]
        elif summary.get("choices"):
            summary["choices"] = dict(list(summary["choices"].items())[:-1])
        else:
            return {}
    return summary


def _ranges(sequences: list[int]) -> list[list[int]]:
    ranges: list[list[int]] = []
    for sequence in sorted(sequences):
        if ranges and sequence == ranges[-1][1] + 1:
            ranges[-1][1] = sequence
        else:
            ranges.append([sequence, sequence])
    return ranges


Pending = tuple[Observation, str, str | None]


def _write(observation: Observation, outcome: str, error_code: str | None) -> None:
    _write_batch([(observation, outcome, error_code)])


def _write_batch(batch: list[Pending]) -> None:
    """Write several interactions in one transaction: one query per kind of link.

    Only what exists now is linked: a rolled-back event's sequence may already
    belong to somebody else's event, and a proposal or token that was never
    committed is left out rather than failing the row.
    """
    from sqlalchemy import insert, tuple_

    from reality.db.core import BusinessEvent, ChangeProposal, MCPAccessToken, uid
    from reality.db.interactions import Interaction

    with _factory()() as session:
        event_keys = list(
            dict.fromkeys(
                (observation.tenant_id, event_id)
                for observation, _, _ in batch
                for event_id in observation.event_ids
            )
        )
        sequence_of: dict[tuple[str, str], int] = {}
        for start in range(0, len(event_keys), _EVENT_CHUNK):
            chunk = event_keys[start : start + _EVENT_CHUNK]
            sequence_of.update(
                ((tenant, event_id), sequence)
                for tenant, event_id, sequence in session.execute(
                    select(
                        BusinessEvent.tenant_id,
                        BusinessEvent.id,
                        BusinessEvent.sequence,
                    ).where(
                        tuple_(BusinessEvent.tenant_id, BusinessEvent.id).in_(chunk)
                    )
                )
            )

        def existing(model, pairs: set[tuple[str, str]]) -> set[tuple[str, str]]:
            if not pairs:
                return set()
            return set(
                session.execute(
                    select(model.tenant_id, model.id).where(
                        tuple_(model.tenant_id, model.id).in_(list(pairs))
                    )
                ).tuples()
            )

        proposals = existing(
            ChangeProposal,
            {(o.tenant_id, o.proposal_id) for o, _, _ in batch if o.proposal_id},
        )
        tokens = existing(
            MCPAccessToken,
            {(o.tenant_id, o.mcp_token_id) for o, _, _ in batch if o.mcp_token_id},
        )
        rows = []
        for observation, outcome, error_code in batch:
            tenant_id = observation.tenant_id
            ranges = _ranges(
                [
                    sequence_of[(tenant_id, event_id)]
                    for event_id in dict.fromkeys(observation.event_ids)
                    if (tenant_id, event_id) in sequence_of
                ]
            )
            kind = observation.kind
            if kind == "read" and ranges:
                # Committed events without a proposal: a direct write, not a read.
                kind = "write"
            summary: dict[str, Any] = {}
            if observation.arguments:
                summary["arguments"] = list(observation.arguments)
            if observation.choices:
                summary["choices"] = observation.choices
            if observation.result_count is not None:
                summary["result_count"] = observation.result_count
            rows.append(
                {
                    "id": uid("int"),
                    "tenant_id": tenant_id,
                    "started_at": observation.started_at or _now(),
                    "recorded_at": observation.finished_at or _now(),
                    "duration_ms": observation.duration_ms,
                    "channel": observation.channel,
                    "kind": kind,
                    "operation": observation.operation,
                    "outcome": outcome,
                    "error_code": error_code,
                    "actor_user_id": observation.actor_user_id,
                    "mcp_token_id": observation.mcp_token_id
                    if (tenant_id, observation.mcp_token_id) in tokens
                    else None,
                    "job_id": observation.job_id,
                    "correlation_id": observation.correlation_id,
                    "proposal_id": observation.proposal_id
                    if (tenant_id, observation.proposal_id) in proposals
                    else None,
                    "event_first_sequence": ranges[0][0] if ranges else None,
                    "event_last_sequence": ranges[-1][1] if ranges else None,
                    "event_ranges": ranges or None,
                    "refresh": observation.refresh,
                    "summary": _bounded(summary),
                }
            )
        session.execute(insert(Interaction), rows)
        session.commit()
        for tenant_id in dict.fromkeys(o.tenant_id for o, _, _ in batch):
            _tidy(session, tenant_id)


def _tidy(session: Session, tenant_id: str) -> None:
    moment = time.monotonic()
    last = _last_tidy.get(tenant_id)
    if last is not None and moment - last < TIDY_INTERVAL_SECONDS:
        return
    _last_tidy[tenant_id] = moment
    from reality.services.interactions import purge_expired

    purge_expired(session, tenant_id, batch=TIDY_BATCH, batches=1)
    session.commit()
