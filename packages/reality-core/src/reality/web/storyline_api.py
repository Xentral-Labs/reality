"""Storyline HTTP surface (spec 182, contracts/storyline-api.md).

Two routers, both delegating every decision to ``reality.services.storyline``:

- ``/api/storyline`` is account-scoped: the library and starting a run.
- ``/api/tenants/{tenant_id}/storyline`` is tenant-scoped: the run's state, its
  chapters, the trace, the delta and tool explanations.

Chapters are confirmed and rejected here only (analysis C1): the ordinary
change-proposal routes would bypass the step receipt and the run's lock.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt
from sqlalchemy.engine import Connection

from reality.services import storyline
from reality.services.core import Conflict, NotFound
from reality.web import auth
from reality.web.api import DatabaseSession, require_tenant_surface_access
from reality.web.playground import _respond, playground_actor

Actor = Annotated[str, Depends(playground_actor)]

account_router = APIRouter(
    prefix="/api/storyline",
    tags=["storyline"],
    dependencies=[Depends(playground_actor)],
)


def tenant_actor(request: Request, session: DatabaseSession) -> str:
    user = auth.user_from_request(request, session)
    if user is None:
        raise HTTPException(401, "Authentication required.")
    return user.id


TenantActor = Annotated[str, Depends(tenant_actor)]

tenant_router = APIRouter(
    prefix="/api/tenants/{tenant_id}/storyline",
    tags=["storyline"],
    dependencies=[Depends(require_tenant_surface_access)],
)


class StartRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=2, max_length=80)
    version: StrictInt = Field(ge=1)
    request_key: str = Field(min_length=1, max_length=128)
    confirmed: StrictBool = False


class PrepareChapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_key: str = Field(min_length=1, max_length=128)


class ConfirmChapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1, max_length=64)
    preview_revision: str = Field(min_length=1, max_length=128)
    confirmed: StrictBool = False


class RejectChapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1, max_length=64)
    confirmed: StrictBool = False


class ChooseBranch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: str = Field(min_length=2, max_length=80)
    branch: str = Field(min_length=2, max_length=80)


class Restart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_key: str = Field(min_length=1, max_length=128)
    confirmed: StrictBool = False


def _engine(session):
    engine = session.get_bind()
    override = {"db_session": session} if isinstance(engine, Connection) else {}
    return engine, override


# ---------------------------------------------------------------- account


@account_router.get("/library")
def library(session: DatabaseSession, actor: Actor):
    return _respond(lambda: storyline.library(session, actor))


@account_router.get("/library/{key}/{version}")
def export_package(
    key: str,
    version: int,
    session: DatabaseSession,
    actor: Actor,
    download: str | None = Query(None, pattern="^(yaml|json)$"),
):
    def read():
        body, content_type, filename = storyline.export_package(
            session, actor, key, version, fmt=download or "json"
        )
        headers = (
            {"Content-Disposition": f'attachment; filename="{filename}"'}
            if download
            else {}
        )
        return Response(content=body, media_type=content_type, headers=headers)

    return _respond(read)


@account_router.get("/runs/{run_id}/draft")
def export_draft(
    session: DatabaseSession,
    actor: Actor,
    run_id: str,
    format: str = Query("yaml", pattern="^(yaml|json)$"),
):
    """The run as a storyline draft to edit and import (FR-021)."""

    def read():
        body, content_type, filename = storyline.export_draft(
            session, actor, run_id, fmt=format
        )
        return Response(
            content=body,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return _respond(read)


@account_router.post("/library", status_code=201)
async def import_package(
    request: Request,
    session: DatabaseSession,
    actor: Actor,
    filename: str = Query("", max_length=200),
    replace: bool = Query(False),
):
    raw = await request.body()
    try:
        return storyline.import_package(
            session, actor, raw, filename=filename, replace=replace
        )
    except storyline.ImportRefused as refused:
        return JSONResponse(
            {"detail": str(refused), "errors": refused.errors}, status_code=422
        )
    except Conflict as error:
        raise HTTPException(409, str(error)) from error


@account_router.delete("/library/{key}/{version}", status_code=204)
def delete_package(key: str, version: int, session: DatabaseSession, actor: Actor):
    try:
        storyline.delete_package(session, actor, key, version)
    except storyline.BuiltinPackage as error:
        raise HTTPException(405, str(error)) from error
    except NotFound as error:
        raise HTTPException(404, str(error)) from error
    return Response(status_code=204)


@account_router.post("/runs")
def start_run(payload: StartRun, session: DatabaseSession, actor: Actor):
    return _respond(
        lambda: storyline.start(
            session,
            actor,
            key=payload.key,
            version=payload.version,
            request_key=payload.request_key,
            confirmed=payload.confirmed,
        )
    )


# ----------------------------------------------------------------- tenant


@tenant_router.get("")
def run_state(tenant_id: str, session: DatabaseSession, actor: TenantActor):
    return _respond(lambda: storyline.state(session, actor, tenant_id))


@tenant_router.get("/chapters/{key}")
def chapter(tenant_id: str, key: str, session: DatabaseSession, actor: TenantActor):
    return _respond(lambda: storyline.chapter_detail(session, actor, tenant_id, key))


@tenant_router.post("/chapters/{key}/prepare")
def prepare(
    tenant_id: str,
    key: str,
    payload: PrepareChapter,
    session: DatabaseSession,
    actor: TenantActor,
):
    engine, override = _engine(session)
    return _respond(
        lambda: storyline.prepare(
            engine, actor, tenant_id, key, payload.request_key, **override
        )
    )


@tenant_router.post("/chapters/{key}/confirm")
def confirm(
    tenant_id: str,
    key: str,
    payload: ConfirmChapter,
    session: DatabaseSession,
    actor: TenantActor,
):
    engine, override = _engine(session)
    return _respond(
        lambda: storyline.confirm(
            engine,
            actor,
            tenant_id,
            key,
            payload.step_id,
            payload.preview_revision,
            confirmed=payload.confirmed,
            **override,
        )
    )


@tenant_router.post("/chapters/{key}/reject")
def reject(
    tenant_id: str,
    key: str,
    payload: RejectChapter,
    session: DatabaseSession,
    actor: TenantActor,
):
    engine, override = _engine(session)
    return _respond(
        lambda: storyline.reject(
            engine,
            actor,
            tenant_id,
            key,
            payload.step_id,
            confirmed=payload.confirmed,
            **override,
        )
    )


@tenant_router.post("/branches")
def choose_branch(
    tenant_id: str, payload: ChooseBranch, session: DatabaseSession, actor: TenantActor
):
    return _respond(
        lambda: storyline.choose_branch(
            session, actor, tenant_id, payload.chapter, payload.branch
        )
    )


@tenant_router.post("/restart")
def restart(
    tenant_id: str, payload: Restart, session: DatabaseSession, actor: TenantActor
):
    return _respond(
        lambda: storyline.restart(
            session,
            actor,
            tenant_id,
            request_key=payload.request_key,
            confirmed=payload.confirmed,
        )
    )


@tenant_router.get("/trace")
def trace(
    tenant_id: str,
    session: DatabaseSession,
    actor: TenantActor,
    step_id: str | None = Query(None, max_length=64),
    after_ordinal: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    free: bool = Query(False),
):
    return _respond(
        lambda: storyline.trace(
            session,
            actor,
            tenant_id,
            step_id=step_id,
            after_ordinal=after_ordinal,
            limit=limit,
            free=free,
        )
    )


@tenant_router.get("/delta")
def delta(
    tenant_id: str,
    session: DatabaseSession,
    actor: TenantActor,
    step_id: str | None = Query(None, max_length=64),
    after_sequence: int | None = Query(None, ge=0),
    after_at: datetime | None = None,
    record: str | None = Query(None, max_length=120),
    ordinal: int | None = Query(None, ge=1),
):
    return _respond(
        lambda: storyline.delta(
            session,
            actor,
            tenant_id,
            step_id=step_id,
            after_sequence=after_sequence,
            after_at=after_at,
            record=record,
            ordinal=ordinal,
        )
    )


@tenant_router.get("/tool-reference/{name:path}")
def tool_reference(
    tenant_id: str, name: str, session: DatabaseSession, actor: TenantActor
):
    return _respond(lambda: storyline.tool_reference(name))
