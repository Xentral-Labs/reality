"""The call trace of a Storyline run (spec 182, FR-004).

Three producers feed one table:

- the tool dispatcher, wrapped so that every read, proposal, confirmation and
  rejection in a company that belongs to a storyline run leaves an entry;
- the HTTP middleware, which records the views a person opens;
- the storyline service, which enters a scope so entries carry the chapter.

The trace is an explanation aid. It is bounded per entry and per run, it lives only
for tenants whose run carries a storyline key, and business reads never join it.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import wraps
from typing import Any

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, PlaygroundRun, StorylineTraceEntry, now, uid

logger = logging.getLogger(__name__)

RUN_ENTRY_LIMIT = 2_000
ENTRY_BYTE_BOUND = 16_384
CACHE_TTL_SECONDS = 30.0
PREVIEW_CHARS = 2_000

KINDS = ("view", "read", "propose", "confirm", "reject", "error")
ACCESS_FOR_KIND = {
    "view": "read",
    "read": "read",
    "propose": "propose",
    "confirm": "confirm",
    "reject": "confirm",
    "error": "read",
}


@dataclass(frozen=True)
class TraceScope:
    tenant_id: str
    run_id: str
    step_id: str | None = None
    actor: str = "storyline"


_scope: ContextVar[TraceScope | None] = ContextVar(
    "storyline_trace_scope", default=None
)
_http_request: ContextVar[bool] = ContextVar("storyline_http_request", default=False)

# tenant id -> (expires_at, run id or None). One process, short-lived, and reset
# whenever a run starts or ends, so a stale answer is a matter of seconds.
_run_cache: dict[str, tuple[float, str | None]] = {}


@contextmanager
def trace_scope(
    tenant_id: str, run_id: str, *, step_id: str | None = None, actor: str = "storyline"
) -> Iterator[TraceScope]:
    scope = TraceScope(tenant_id, run_id, step_id, actor)
    token = _scope.set(scope)
    try:
        yield scope
    finally:
        _scope.reset(token)


@dataclass
class ChatCalls:
    tenant_id: str
    ids: list[str]
    reads: list[dict[str, Any]]


_chat_calls: ContextVar[ChatCalls | None] = ContextVar(
    "storyline_chat_calls", default=None
)


def current_chat_calls() -> ChatCalls | None:
    return _chat_calls.get()


@contextmanager
def chat_call_scope(tenant_id: str) -> Iterator[ChatCalls]:
    calls = ChatCalls(tenant_id, [], [])
    token = _chat_calls.set(calls)
    try:
        yield calls
    finally:
        _chat_calls.reset(token)


def wrap_chat(function: Callable[..., Any]) -> Callable[..., Any]:
    """Associate a saved reply with exact calls; trace failure never retries chat."""

    @wraps(function)
    def send(session: Session, tenant_id: str, *args: Any, **kwargs: Any) -> Any:
        target = _target(session, tenant_id)
        with chat_call_scope(tenant_id) as calls:
            if target is None:
                result = function(session, tenant_id, *args, **kwargs)
            else:
                with trace_scope(tenant_id, target.run_id, actor="chat"):
                    result = function(session, tenant_id, *args, **kwargs)
            _attach_answer_basis(session, result[1], calls)
            if target is None:
                return result
            _safe_record(
                session,
                TraceScope(tenant_id, target.run_id, actor="chat"),
                kind="read",
                name="chat.reply",
                input={"message_id": result[1].id},
                result={"trace_ids": calls.ids[:128], "has_more": len(calls.ids) > 128},
                commit=True,
            )
            return result

    return send


def _attach_answer_basis(session: Session, message: Any, calls: ChatCalls) -> None:
    """Attach support after reply persistence; failure never repeats the reply."""
    if not calls.reads:
        return
    try:
        message.answer_basis = bounded(
            {
                "version": 1,
                "calls": calls.reads[:128],
                "has_more": len(calls.reads) > 128,
            }
        )
        session.commit()
    except Exception:
        logger.exception("Chat answer basis could not be recorded")
        if session.get_nested_transaction() is None:
            session.rollback()


def current_scope() -> TraceScope | None:
    return _scope.get()


@contextmanager
def http_request() -> Iterator[None]:
    """Mark the current context as an HTTP request, so tool entries say 'person'."""
    token = _http_request.set(True)
    try:
        yield
    finally:
        _http_request.reset(token)


def clear_cache(tenant_id: str | None = None) -> None:
    if tenant_id is None:
        _run_cache.clear()
    else:
        _run_cache.pop(tenant_id, None)


FREE_PLAY_REQUEST_KEY = "standalone-free-play:v1"


def evidence_run_condition():
    """Storylines and the designated independent practice Sandbox, never lessons."""
    return or_(
        PlaygroundRun.storyline_key.is_not(None),
        and_(
            PlaygroundRun.client_request_key == FREE_PLAY_REQUEST_KEY,
            PlaygroundRun.sandbox_kind == "practice",
        ),
    )


def storyline_run_id(session: Session, tenant_id: str) -> str | None:
    """The active storyline run of a tenant, or None. Cached briefly per process."""
    cached = _run_cache.get(tenant_id)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    with session.no_autoflush:
        run_id = session.scalar(
            select(PlaygroundRun.id).where(
                PlaygroundRun.tenant_id == tenant_id,
                evidence_run_condition(),
                PlaygroundRun.status == "active",
            )
        )
    _run_cache[tenant_id] = (time.monotonic() + CACHE_TTL_SECONDS, run_id)
    return run_id


def _target(session: Session | None, tenant_id: str) -> TraceScope | None:
    if session is None:
        # Documentation contracts exercise the dispatcher without a session.
        return None
    scope = _scope.get()
    if scope is not None and scope.tenant_id == tenant_id:
        return scope
    run_id = storyline_run_id(session, tenant_id)
    if run_id is None:
        return None
    return TraceScope(
        tenant_id, run_id, None, "person" if _http_request.get() else "mcp"
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "id") and not isinstance(value, (str, bytes, int, float)):
        return value.id
    return value


def bounded(value: Any) -> dict[str, Any] | list[Any] | None:
    """A JSON object or list at most ENTRY_BYTE_BOUND bytes; larger values are cut."""
    if value is None:
        return None
    payload = _jsonable(value)
    if not isinstance(payload, (dict, list)):
        payload = {"value": payload}
    text = json.dumps(payload, sort_keys=True, default=str)
    if len(text.encode()) <= ENTRY_BYTE_BOUND:
        # Round-trip so that dates, Decimals and ids the walk above did not
        # reach are plain JSON before the JSONB column sees them.
        return json.loads(text)
    return {
        "truncated": True,
        "bytes": len(text.encode()),
        "preview": text[:PREVIEW_CHARS],
    }


def capture_marker(session: Session, tenant_id: str) -> dict[str, Any]:
    """Sequence, instant and the open findings before a mutating call."""
    from reality.services.exceptions import operational_exceptions

    latest = session.scalar(
        select(func.coalesce(func.max(BusinessEvent.sequence), 0)).where(
            BusinessEvent.tenant_id == tenant_id
        )
    )
    findings = sorted(
        exception.id for exception in operational_exceptions(session, tenant_id)
    )
    return {
        "marker_sequence": int(latest or 0),
        "marker_at": now(),
        "before_exceptions": findings,
    }


def record(
    session: Session,
    target: TraceScope,
    *,
    kind: str,
    name: str,
    input: Any = None,
    result: Any = None,
    error: str | None = None,
    duration_ms: int | None = None,
    proposal_id: str | None = None,
    marker: dict[str, Any] | None = None,
    step_id: str | None = None,
) -> StorylineTraceEntry:
    """Append one entry to the run's trace and keep the run within its ring."""
    if kind not in KINDS:
        raise ValueError(f"Unknown trace kind {kind}.")
    run = session.scalar(
        select(PlaygroundRun)
        .where(
            PlaygroundRun.tenant_id == target.tenant_id,
            PlaygroundRun.id == target.run_id,
        )
        .with_for_update()
    )
    if run is None:
        raise LookupError("Storyline run not found for trace.")
    ordinal = (
        int(
            session.scalar(
                select(func.coalesce(func.max(StorylineTraceEntry.ordinal), 0)).where(
                    StorylineTraceEntry.tenant_id == target.tenant_id,
                    StorylineTraceEntry.run_id == target.run_id,
                )
            )
            or 0
        )
        + 1
    )
    marker = marker or {}
    entry = StorylineTraceEntry(
        id=uid("trc"),
        tenant_id=target.tenant_id,
        run_id=target.run_id,
        step_id=step_id or target.step_id,
        ordinal=ordinal,
        kind=kind,
        name=name[:120],
        access=ACCESS_FOR_KIND[kind],
        actor=target.actor,
        proposal_id=proposal_id,
        marker_sequence=marker.get("marker_sequence"),
        marker_at=marker.get("marker_at"),
        before_exceptions=bounded(marker.get("before_exceptions")),
        input=bounded(input),
        result=bounded({"error": error}) if error is not None else bounded(result),
        duration_ms=duration_ms,
    )
    session.add(entry)
    session.flush()
    calls = current_chat_calls()
    if (
        calls is not None
        and calls.tenant_id == target.tenant_id
        and name != "chat.reply"
    ):
        calls.ids.append(entry.id)
    if ordinal > RUN_ENTRY_LIMIT:
        session.execute(
            delete(StorylineTraceEntry).where(
                StorylineTraceEntry.tenant_id == target.tenant_id,
                StorylineTraceEntry.run_id == target.run_id,
                StorylineTraceEntry.ordinal <= ordinal - RUN_ENTRY_LIMIT,
            )
        )
    return entry


def read_trace(
    session: Session,
    tenant_id: str,
    run_id: str,
    *,
    step_id: str | None = None,
    after_ordinal: int = 0,
    limit: int = 200,
    free: bool = False,
) -> dict[str, Any]:
    limit = max(1, min(limit, 500))
    statement = (
        select(StorylineTraceEntry)
        .where(
            StorylineTraceEntry.tenant_id == tenant_id,
            StorylineTraceEntry.run_id == run_id,
            StorylineTraceEntry.ordinal > after_ordinal,
            StorylineTraceEntry.name != "chat.reply",
        )
        .order_by(StorylineTraceEntry.ordinal)
        .limit(limit + 1)
    )
    if step_id is not None:
        statement = statement.where(StorylineTraceEntry.step_id == step_id)
    if free:
        statement = statement.where(StorylineTraceEntry.step_id.is_(None))
    rows = list(session.scalars(statement))
    return {
        "items": [entry_view(row) for row in rows[:limit]],
        "has_more": len(rows) > limit,
    }


def entry_view(row: StorylineTraceEntry) -> dict[str, Any]:
    return {
        "id": row.id,
        "ordinal": row.ordinal,
        "step_id": row.step_id,
        "kind": row.kind,
        "name": row.name,
        "access": row.access,
        "actor": row.actor,
        "proposal_id": row.proposal_id,
        "marker": (
            {"sequence": row.marker_sequence, "at": row.marker_at}
            if row.marker_sequence is not None
            else None
        ),
        "before_exceptions": row.before_exceptions,
        "input": row.input,
        "result": row.result,
        "duration_ms": row.duration_ms,
        "recorded_at": row.recorded_at,
    }


# ------------------------------------------------------------------ the producers


def _finish(session: Session, commit: bool) -> None:
    """Persist what was recorded without disturbing an enclosing savepoint."""
    if commit and session.get_nested_transaction() is None:
        session.commit()
    else:
        session.flush()


def _safe_record(session: Session, *args: Any, commit: bool, **kwargs: Any) -> None:
    try:
        record(session, *args, **kwargs)
        _finish(session, commit)
    except Exception:  # the trace never breaks the call it explains
        logger.exception("Storyline trace entry could not be recorded")
        if session.get_nested_transaction() is None:
            session.rollback()


def wrap_read(function: Callable[..., Any]) -> Callable[..., Any]:
    def run_read_tool(session: Session, tenant_id: str, tool_name: str, arguments=None):
        target = _target(session, tenant_id)
        started = time.perf_counter()
        try:
            result = function(session, tenant_id, tool_name, arguments)
        except Exception as exc:
            if target is not None and not tool_name.startswith("analytics.reports."):
                _safe_record(
                    session,
                    target,
                    kind="error",
                    name=tool_name,
                    input=arguments or {},
                    error=f"{type(exc).__name__}: {exc}",
                    duration_ms=_elapsed(started),
                    commit=False,
                )
            raise
        calls = current_chat_calls()
        if calls is not None and calls.tenant_id == tenant_id:
            snapshot = bounded(
                {
                    "operation": tool_name[:120],
                    "input": bounded(arguments or {}),
                    "result": bounded(result),
                }
            )
            if isinstance(snapshot, dict):
                calls.reads.append(snapshot)
        if target is not None and not tool_name.startswith("analytics.reports."):
            _safe_record(
                session,
                target,
                kind="read",
                name=tool_name,
                input=arguments or {},
                result=result,
                duration_ms=_elapsed(started),
                commit=True,
            )
        return result

    run_read_tool.__wrapped__ = function  # type: ignore[attr-defined]
    return run_read_tool


def wrap_propose(function: Callable[..., Any]) -> Callable[..., Any]:
    def create_change_proposal(session, tenant_id, tool_name, arguments, **kwargs):
        if tool_name.startswith("analytics.reports."):
            return function(session, tenant_id, tool_name, arguments, **kwargs)
        target = _target(session, tenant_id)
        if target is None:
            return function(session, tenant_id, tool_name, arguments, **kwargs)
        started = time.perf_counter()
        try:
            proposal = function(session, tenant_id, tool_name, arguments, **kwargs)
        except Exception as exc:
            _safe_record(
                session,
                target,
                kind="error",
                name=tool_name,
                input=arguments,
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=_elapsed(started),
                commit=False,
            )
            raise
        _safe_record(
            session,
            target,
            kind="propose",
            name=tool_name,
            input=arguments,
            result={"proposal_id": proposal.id, "status": proposal.status},
            proposal_id=proposal.id,
            duration_ms=_elapsed(started),
            commit=kwargs.get("_commit", True),
        )
        return proposal

    create_change_proposal.__wrapped__ = function  # type: ignore[attr-defined]
    return create_change_proposal


def wrap_decision(function: Callable[..., Any], kind: str) -> Callable[..., Any]:
    def decide(session, tenant_id, proposal_id, **kwargs):
        target = _target(session, tenant_id)
        if target is None:
            return function(session, tenant_id, proposal_id, **kwargs)
        marker = capture_marker(session, tenant_id) if kind == "confirm" else None
        started = time.perf_counter()
        try:
            proposal = function(session, tenant_id, proposal_id, **kwargs)
        except Exception as exc:
            _safe_record(
                session,
                target,
                kind="error",
                name=kind,
                input={"proposal_id": proposal_id},
                error=f"{type(exc).__name__}: {exc}",
                proposal_id=proposal_id,
                marker=marker,
                duration_ms=_elapsed(started),
                commit=False,
            )
            raise
        _safe_record(
            session,
            target,
            kind=kind,
            name=proposal.type.removeprefix("tool:"),
            input=json.loads(proposal.input or "{}"),
            result=json.loads(proposal.output or "{}"),
            proposal_id=proposal.id,
            marker=marker,
            duration_ms=_elapsed(started),
            commit=True,
        )
        return proposal

    decide.__wrapped__ = function  # type: ignore[attr-defined]
    decide.__name__ = function.__name__
    return decide


def _elapsed(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


EXCLUDED_VIEW_SUFFIXES = ("/activity-signal",)
EXCLUDED_VIEW_SEGMENTS = ("/storyline", "/analytics/reports")


def record_http_view(
    session_factory: Callable[[], Session],
    *,
    tenant_id: str,
    route: str,
    params: dict[str, Any],
    status: int,
    duration_ms: int,
) -> None:
    """Called by the web middleware after a GET on a tenant route."""
    if route.endswith(EXCLUDED_VIEW_SUFFIXES) or any(
        segment in route for segment in EXCLUDED_VIEW_SEGMENTS
    ):
        return
    with session_factory() as session:
        run_id = storyline_run_id(session, tenant_id)
        if run_id is None:
            return
        target = TraceScope(tenant_id, run_id, None, "person")
        _safe_record(
            session,
            target,
            kind="view",
            name=route,
            input=params,
            result={"status": status},
            duration_ms=duration_ms,
            commit=True,
        )
