"""The engine room over HTTP (spec 266). Transport only; owners only.

These routes are never recorded themselves: `record_interactions` skips every
path under `/interactions`, so watching does not become something to watch.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from reality.services import interactions
from reality.services.business_projection import overview as business_overview
from reality.services.core import InvalidOperation, NotFound
from reality.web.api import (
    DatabaseSession,
    api_error,
    request_principal,
    require_tenant_surface_access,
)

router = APIRouter(
    prefix="/api/tenants/{tenant_id}/interactions",
    tags=["engine-room"],
    dependencies=[Depends(require_tenant_surface_access)],
)


def _owner(request: Request, session: DatabaseSession, tenant_id: str) -> str | None:
    """The viewing owner's id, or None in development without sign-in."""
    if (
        getattr(request.state, "user", None) is None
        and os.environ.get("REALITY_AUTH_MODE", "enabled").lower() == "disabled"
    ):
        # Development without sign-in opens every company surface; the engine room
        # follows it rather than answering 401, which the web reads as a lost session.
        return None
    principal = request_principal(request)
    try:
        interactions.require_engine_room_access(session, tenant_id, principal.user_id)
    except NotFound as error:
        raise api_error(error) from error
    return principal.user_id


@router.get("")
def list_interactions(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    after: int | None = Query(None, ge=0),
    window_from: Annotated[datetime | None, Query(alias="from")] = None,
    window_to: Annotated[datetime | None, Query(alias="to")] = None,
    channel: Annotated[list[str] | None, Query()] = None,
    kind: Annotated[list[str] | None, Query()] = None,
    outcome: Annotated[list[str] | None, Query()] = None,
    actor_user_id: str | None = Query(None, max_length=64),
    mcp_token_id: str | None = Query(None, max_length=64),
    correlation_id: str | None = Query(None, max_length=64),
    subject_type: str | None = Query(None, max_length=64),
    subject_id: str | None = Query(None, max_length=64),
    include_refresh: bool = False,
    hide_own: bool = False,
    language: str = Query("en", pattern="^[a-z]{2}$"),
    limit: int = Query(200, ge=1, le=interactions.LIMIT_MAX),
) -> dict[str, Any]:
    viewer = _owner(request, session, tenant_id)
    try:
        return interactions.list_interactions(
            session,
            tenant_id,
            after=after,
            window_from=window_from,
            window_to=window_to,
            channels=channel,
            kinds=kind,
            outcomes=outcome,
            actor_user_id=actor_user_id,
            mcp_token_id=mcp_token_id,
            correlation_id=correlation_id,
            subject_type=subject_type,
            subject_id=subject_id,
            include_refresh=include_refresh,
            exclude_actor_user_id=viewer if hide_own else None,
            language=language,
            limit=limit,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/series")
def interaction_series(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    minutes: int = Query(15),
    channel: Annotated[list[str] | None, Query()] = None,
    actor_user_id: str | None = Query(None, max_length=64),
    mcp_token_id: str | None = Query(None, max_length=64),
    hide_own: bool = True,
) -> dict[str, Any]:
    viewer = _owner(request, session, tenant_id)
    try:
        return interactions.series(
            session,
            tenant_id,
            minutes=minutes,
            channels=channel,
            actor_user_id=actor_user_id,
            mcp_token_id=mcp_token_id,
            exclude_actor_user_id=viewer if hide_own else None,
        )
    except InvalidOperation as error:
        raise api_error(error) from error


@router.get("/pulse")
def interaction_pulse(
    tenant_id: str, request: Request, session: DatabaseSession, hide_own: bool = True
) -> dict[str, Any]:
    viewer = _owner(request, session, tenant_id)
    # The owner's own navigation must not make the indicator blink at them.
    return interactions.pulse(
        session, tenant_id, exclude_actor_user_id=viewer if hide_own else None
    )


@router.get("/business")
def business_operations(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    order_filter: str = Query(
        "",
        pattern="^(|ready|blocked|reservation_blocked|held|overdue|at_risk|complete|partial|unshipped|eligible|received_last_hour|completed_last_hour|first_dispatch_sample|complete_dispatch_sample)$",
    ),
    mail_filter: str = Query("", pattern="^(|incoming|waiting|outgoing)$"),
    order_cursor: str = Query("", max_length=2000),
    mail_cursor: str = Query("", max_length=2000),
    order_limit: int = Query(200, ge=1, le=200),
    mail_limit: int = Query(50, ge=1, le=50),
) -> dict[str, Any]:
    _owner(request, session, tenant_id)
    try:
        return business_overview(
            session,
            tenant_id,
            order_filter=order_filter,
            mail_filter=mail_filter,
            order_cursor=order_cursor,
            mail_cursor=mail_cursor,
            order_limit=order_limit,
            mail_limit=mail_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{interaction_id}/events")
def interaction_events(
    tenant_id: str, interaction_id: str, request: Request, session: DatabaseSession
) -> dict[str, Any]:
    _owner(request, session, tenant_id)
    try:
        events = interactions.events_of(session, tenant_id, interaction_id)
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {
        "events": [
            {
                "id": event.id,
                "sequence": event.sequence,
                "type": event.event_type,
                "subject_type": event.subject_type,
                "subject_id": event.subject_id,
                "occurred_at": event.occurred_at,
                "recorded_at": event.recorded_at,
                "action_id": event.action_id,
                "source_record_id": event.source_record_id,
            }
            for event in events
        ]
    }
