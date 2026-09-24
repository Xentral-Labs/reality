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


def _owner(request: Request, session: DatabaseSession, tenant_id: str) -> None:
    if (
        getattr(request.state, "user", None) is None
        and os.environ.get("REALITY_AUTH_MODE", "enabled").lower() == "disabled"
    ):
        # Development without sign-in opens every company surface; the engine room
        # follows it rather than answering 401, which the web reads as a lost session.
        return
    principal = request_principal(request)
    try:
        interactions.require_engine_room_access(session, tenant_id, principal.user_id)
    except NotFound as error:
        raise api_error(error) from error


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
    limit: int = Query(200, ge=1, le=interactions.LIMIT_MAX),
) -> dict[str, Any]:
    _owner(request, session, tenant_id)
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
            limit=limit,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/pulse")
def interaction_pulse(
    tenant_id: str, request: Request, session: DatabaseSession
) -> dict[str, Any]:
    _owner(request, session, tenant_id)
    return interactions.pulse(session, tenant_id)


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
