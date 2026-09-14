"""Authenticated account-scoped Playground entry, delegating all state to services."""

from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    field_validator,
)
from sqlalchemy.engine import Connection

from reality.catalogs import (
    load_exception_class_labels,
    load_operational_exception_catalog,
)
from reality.playground import catalog
from reality.services import playground
from reality.services.core import Conflict, InvalidOperation, NotFound
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    require_playground_account,
)
from reality.web import auth
from reality.web.api import DatabaseSession


def playground_actor(request: Request, session: DatabaseSession) -> str:
    # Deliberately require a real cookie even when ordinary local business auth is off.
    user = auth.user_from_request(request, session)
    if user is None:
        raise HTTPException(401, "Authentication required.")
    require_playground_account(session, user.id)
    return user.id


Actor = Annotated[str, Depends(playground_actor)]
router = APIRouter(
    prefix="/api/playground",
    tags=["playground"],
    dependencies=[Depends(playground_actor)],
)


class StartRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_key: str = Field(min_length=1, max_length=128)
    preset_key: str = catalog.PRESET_KEY
    preset_version: StrictInt = catalog.PRESET_VERSION
    sandbox_kind: Literal["temporary", "practice"] = "temporary"
    company_name: str | None = Field(default=None, max_length=120)
    confirmed: StrictBool = False

    @field_validator("company_name", mode="before")
    @classmethod
    def trim_company_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class PrepareStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_key: str = Field(min_length=1, max_length=128)
    tool_name: str = Field(min_length=1, max_length=80)
    arguments: dict


class ConfirmStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_revision: str = Field(min_length=1, max_length=128)
    confirmed: StrictBool = False


class RejectStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: StrictBool = False


class RestartRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_key: str | None = None
    preset_version: StrictInt | None = None
    request_key: str | None = Field(default=None, min_length=1, max_length=128)
    confirmed: StrictBool = False


class ConfirmRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: StrictBool = False


def _respond(operation: Callable):
    try:
        return operation()
    except PlaygroundOperationDenied:
        raise
    except playground.PlaygroundQuotaExceeded as error:
        return JSONResponse(
            jsonable_encoder(
                {"detail": str(error), "code": error.code, "quotas": error.capacity}
            ),
            status_code=429,
        )
    except NotFound as error:
        raise HTTPException(404, str(error)) from error
    except Conflict as error:
        raise HTTPException(409, str(error)) from error
    except InvalidOperation as error:
        raise HTTPException(422, str(error)) from error


@router.get("")
def entry(
    session: DatabaseSession,
    actor: Actor,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return _respond(
        lambda: playground.list_runs(session, actor, limit=limit, offset=offset)
    )


@router.get("/exception-catalog")
def exception_catalog():
    """Expose descriptive global metadata behind the Playground account boundary."""
    current = load_operational_exception_catalog()
    labels = load_exception_class_labels()
    fields = ("id", "label", "description", "severity", "owner", "clears_through")
    return {
        "version": current.version,
        "classes": [
            {**{key: row[key] for key in fields}, "labels": labels.get(row["id"], {})}
            for row in current.classes
        ],
    }


@router.get("/runs/{run_id}")
def run_detail(run_id: str, session: DatabaseSession, actor: Actor):
    return _respond(lambda: playground.read_run(session, actor, run_id))


@router.get("/runs/{run_id}/steps/{step_id}")
def step_detail(run_id: str, step_id: str, session: DatabaseSession, actor: Actor):
    return _respond(lambda: playground.read_step(session, actor, run_id, step_id))


@router.get("/runs/{run_id}/reality")
def reality_detail(run_id: str, session: DatabaseSession, actor: Actor):
    return _respond(lambda: playground.read_reality(session, actor, run_id))


@router.post("/runs/{run_id}/steps")
def prepare_step(
    run_id: str, payload: PrepareStep, session: DatabaseSession, actor: Actor
):
    engine = session.get_bind()
    session_override = {"db_session": session} if isinstance(engine, Connection) else {}
    return _respond(
        lambda: playground.prepare_step(
            engine,
            actor,
            run_id,
            payload.request_key,
            payload.tool_name,
            payload.arguments,
            **session_override,
        )
    )


@router.post("/runs/{run_id}/steps/{step_id}/confirm")
def confirm_step(
    run_id: str,
    step_id: str,
    payload: ConfirmStep,
    session: DatabaseSession,
    actor: Actor,
):
    engine = session.get_bind()
    session_override = {"db_session": session} if isinstance(engine, Connection) else {}
    return _respond(
        lambda: playground.confirm_step(
            engine,
            actor,
            run_id,
            step_id,
            payload.preview_revision,
            confirmed=payload.confirmed,
            **session_override,
        )
    )


@router.post("/runs/{run_id}/steps/{step_id}/reject")
def reject_step(
    run_id: str,
    step_id: str,
    payload: RejectStep,
    session: DatabaseSession,
    actor: Actor,
):
    engine = session.get_bind()
    session_override = {"db_session": session} if isinstance(engine, Connection) else {}
    return _respond(
        lambda: playground.reject_step(
            engine,
            actor,
            run_id,
            step_id,
            confirmed=payload.confirmed,
            **session_override,
        )
    )


@router.post("/runs/{run_id}/restart")
def restart(run_id: str, payload: RestartRun, session: DatabaseSession, actor: Actor):
    def execute():
        fresh = playground.restart_run(
            session,
            actor,
            run_id,
            confirmed=payload.confirmed,
            preset_key=payload.preset_key,
            preset_version=payload.preset_version,
            request_key=payload.request_key,
        )
        return playground.read_run(session, actor, fresh.id)

    return _respond(execute)


@router.post("/runs/{run_id}/archive")
def archive(run_id: str, payload: ConfirmRun, session: DatabaseSession, actor: Actor):
    """Spec 186: hide an owned sandbox from the switcher; nothing is deleted."""

    def execute():
        run = playground.archive_run(
            session, actor, run_id, confirmed=payload.confirmed
        )
        return playground.read_run(session, actor, run.id)

    return _respond(execute)


@router.post("/runs/{run_id}/restore")
def restore(run_id: str, payload: ConfirmRun, session: DatabaseSession, actor: Actor):
    """Spec 186: bring an archived sandbox back to the switcher."""

    def execute():
        run = playground.restore_run(
            session, actor, run_id, confirmed=payload.confirmed
        )
        return playground.read_run(session, actor, run.id)

    return _respond(execute)


@router.post("/runs")
def start(payload: StartRun, session: DatabaseSession, actor: Actor):
    def execute():
        run = playground.start_run(session, actor, **payload.model_dump())
        return playground.read_run(session, actor, run.id)

    return _respond(execute)


class CompanionHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class CompanionQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=4000)
    history: list[CompanionHistory] = Field(default_factory=list, max_length=12)


@router.post("/runs/{run_id}/chat")
def ask_companion(
    run_id: str, payload: CompanionQuestion, session: DatabaseSession, actor: Actor
):
    from reality.services.playground_chat import ask

    return _respond(
        lambda: ask(
            session,
            actor,
            run_id,
            payload.message,
            [row.model_dump() for row in payload.history],
        )
    )
