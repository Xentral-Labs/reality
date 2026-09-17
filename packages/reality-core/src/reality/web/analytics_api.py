"""Thin Reports routes over the shared analytics tools and definition services."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from reality.domain.graph_report import GraphReportChange
from reality.services.analytics.errors import AnalyticsError
from reality.services.analytics.reports import caller, change_graph_report
from reality.services.core import InvalidOperation, NotFound
from reality.services.memberships import Principal
from reality.tools.application import run_read_tool
from reality.tools.graph import GraphAskRequest
from reality.web.auth import DatabaseSession

router = APIRouter(prefix="/analytics")


def principal(request):
    user = getattr(request.state, "user", None)
    return Principal(user.id) if user is not None else None


def read(session, tenant_id, name, values, request):
    try:
        with caller(principal(request)):
            return run_read_tool(session, tenant_id, name, values)
    except NotFound as error:
        raise HTTPException(404, str(error)) from error
    except (AnalyticsError, InvalidOperation, ValidationError) as error:
        raise HTTPException(
            422,
            {
                "code": getattr(error, "code", "invalid_definition"),
                "message": str(error),
            },
        ) from error


async def cancellable_read(session, tenant_id, name, values, request):
    import asyncio
    from contextlib import suppress
    from threading import Event

    from starlette.concurrency import run_in_threadpool

    from reality.services.analytics.budget import CANCELLED

    cancelled = Event()

    async def watch_disconnect():
        while True:
            if await request.is_disconnected():
                cancelled.set()
                return
            await asyncio.sleep(0.1)

    def worker():
        token = CANCELLED.set(cancelled)
        try:
            return read(session, tenant_id, name, values, request)
        finally:
            CANCELLED.reset(token)

    watcher = asyncio.create_task(watch_disconnect())
    try:
        return await run_in_threadpool(worker)
    finally:
        watcher.cancel()
        with suppress(asyncio.CancelledError):
            await watcher


@router.get("/graph/catalog")
def get_graph_catalog(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    node: str | None = None,
    language: str = "en",
):
    return read(
        session, tenant_id, "graph.catalog", {"node": node, "language": language}, request
    )


@router.post("/graph/ask")
async def post_graph_ask(
    tenant_id: str, body: GraphAskRequest, request: Request, session: DatabaseSession
):
    """A refusal reaches the browser as a refusal, with its code.

    The reason names the edge that fanned out or the unit that cannot be added,
    and the page shows it where the answer would have been — it is the most
    useful thing this feature says.
    """
    return await cancellable_read(
        session, tenant_id, "graph.ask", body.model_dump(mode="json"), request
    )


@router.get("/graph/reports")
def get_graph_reports(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    query: str = "",
    cursor: str | None = None,
):
    return read(
        session,
        tenant_id,
        "graph.reports.list",
        {"query": query, "cursor": cursor},
        request,
    )


@router.get("/graph/reports/{report_id}")
def get_graph_report(
    report_id: str, tenant_id: str, request: Request, session: DatabaseSession
):
    return read(session, tenant_id, "graph.reports.get", {"report_id": report_id}, request)


def _change(session, tenant_id, request, body, apply):
    try:
        result = apply(
            session, tenant_id, principal(request), body.model_dump(mode="json")
        )
        session.commit()
        return result
    except NotFound as error:
        session.rollback()
        raise HTTPException(404, str(error)) from error
    except (AnalyticsError, InvalidOperation) as error:
        session.rollback()
        raise HTTPException(
            409
            if getattr(error, "code", "")
            in {"revision_conflict", "idempotency_conflict"}
            else 422,
            {
                "code": getattr(error, "code", "invalid_definition"),
                "message": str(error),
            },
        ) from error


@router.post("/graph/reports/changes")
def post_graph_change(
    tenant_id: str,
    body: GraphReportChange,
    request: Request,
    session: DatabaseSession,
):
    """Save the question, never its answer.

    Reopening re-executes the traversal, so what comes back is a fresh
    observation rather than a preserved number — the only honest thing a report
    can be when the records underneath it keep changing.
    """
    return _change(session, tenant_id, request, body, change_graph_report)


@router.get("/reports/proposals/{proposal_id}")
def get_report_proposal(
    tenant_id: str, proposal_id: str, request: Request, session: DatabaseSession
):
    from reality.services.analytics.proposals import preview

    try:
        return preview(session, tenant_id, principal(request), proposal_id)
    except (NotFound, AnalyticsError) as error:
        raise HTTPException(404, "Report proposal not found.") from error
