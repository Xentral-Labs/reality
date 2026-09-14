"""Two explicit authenticated contexts, one synthetic integration service."""

from typing import Literal

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from reality.services import demo_data
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    require_playground_account,
    require_playground_run,
)
from reality.web.api import DatabaseSession
from reality.web.playground import Actor
from reality.web.playground import _respond as _playground_respond

router = APIRouter(tags=["demo-data"])


def _respond(operation):
    from fastapi.responses import JSONResponse

    from reality.jobs.registry import JobError

    try:
        return _playground_respond(operation)
    except JobError as error:
        return JSONResponse(
            {
                "detail": "Demo Data changed; reload its current status.",
                "code": error.code,
            },
            status_code=403 if error.code == "not_authorized" else 409,
        )


class Confirm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: StrictBool = False


class Connect(Confirm):
    request_key: str = Field(min_length=1, max_length=128)
    preview_fingerprint: str = Field(min_length=64, max_length=64)


class Control(Confirm):
    request_key: str = Field(min_length=1, max_length=128)
    expected_revision: StrictInt = Field(ge=1)
    action: Literal[
        "start", "pause", "resume", "stop", "disconnect", "reconnect", "set_rate"
    ]
    rate: Literal[10, 60, 300] | None = None


def tenant(request: Request, session: DatabaseSession, actor: str) -> str:
    if "run_id" in request.path_params:
        return require_playground_run(
            session, request.path_params["run_id"], actor, for_write=True
        ).tenant_id
    if require_playground_account(session, actor).status != "active":
        raise PlaygroundOperationDenied(
            "Production access is required for App integration routes."
        )
    return request.path_params["tenant_id"]


@router.get("/api/tenants/{tenant_id}/demo-data/preview")
@router.get("/api/playground/runs/{run_id}/demo-data/preview")
def preview(request: Request, session: DatabaseSession, actor: Actor):
    return _respond(
        lambda: demo_data.preview(session, tenant(request, session, actor), actor)
    )


@router.get("/api/tenants/{tenant_id}/demo-data")
@router.get("/api/playground/runs/{run_id}/demo-data")
def status(request: Request, session: DatabaseSession, actor: Actor):
    return _respond(
        lambda: demo_data.status(session, tenant(request, session, actor), actor)
    )


@router.post("/api/tenants/{tenant_id}/demo-data/connect")
@router.post("/api/playground/runs/{run_id}/demo-data/connect")
def connect(body: Connect, request: Request, session: DatabaseSession, actor: Actor):
    return _respond(
        lambda: demo_data.connect(
            session, tenant(request, session, actor), actor, **body.model_dump()
        )
    )


@router.post("/api/tenants/{tenant_id}/demo-data/control")
@router.post("/api/playground/runs/{run_id}/demo-data/control")
def control(body: Control, request: Request, session: DatabaseSession, actor: Actor):
    return _respond(
        lambda: demo_data.control(
            session, tenant(request, session, actor), actor, **body.model_dump()
        )
    )


@router.get("/api/tenants/{tenant_id}/demo-data/imports")
@router.get("/api/playground/runs/{run_id}/demo-data/imports")
def imports(
    request: Request,
    session: DatabaseSession,
    actor: Actor,
    cursor: str = Query(default="", max_length=2048),
    limit: int = Query(default=25, ge=1, le=100),
    recent: bool = Query(default=False),
):
    return _respond(
        lambda: demo_data.imports(
            session,
            tenant(request, session, actor),
            actor,
            cursor=cursor,
            limit=limit,
            recent=recent,
        )
    )


@router.post("/api/tenants/{tenant_id}/demo-data/imports/{import_id}/retry")
@router.post("/api/playground/runs/{run_id}/demo-data/imports/{import_id}/retry")
def retry(
    import_id: str,
    body: Confirm,
    request: Request,
    session: DatabaseSession,
    actor: Actor,
):
    return _respond(
        lambda: demo_data.retry_import(
            session,
            tenant(request, session, actor),
            actor,
            import_id,
            confirmed=body.confirmed,
        )
    )


@router.get("/api/tenants/{tenant_id}/demo-data/imports/{import_id}")
@router.get("/api/playground/runs/{run_id}/demo-data/imports/{import_id}")
def read_import(
    import_id: str, request: Request, session: DatabaseSession, actor: Actor
):
    return _respond(
        lambda: demo_data.read_import(
            session, tenant(request, session, actor), actor, import_id
        )
    )
