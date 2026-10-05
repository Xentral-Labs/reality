"""Tenant-scoped case reads and explicit human responsibility controls."""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from reality.services import operational_cases as cases
from reality.services.core import InvalidOperation, NotFound
from reality.web.api import (
    DatabaseSession,
    api_error,
    optional_request_principal,
    request_principal,
    require_tenant_surface_access,
)

router = APIRouter(
    prefix="/api/tenants/{tenant_id}/operational-cases",
    tags=["operational-cases"],
    dependencies=[Depends(require_tenant_surface_access)],
)


class Control(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: StrictBool
    request_key: str = Field(min_length=1, max_length=128)


class Takeover(Control):
    expected_revision: StrictInt = Field(ge=1)
    reason: str = Field(default="", max_length=1000)


class Handback(Control):
    review_digest: str = Field(min_length=64, max_length=64)


class Adopt(Control):
    order_ids: list[str] = Field(default_factory=list, max_length=500)
    return_ids: list[str] = Field(default_factory=list, max_length=500)


def _respond(operation):
    try:
        return operation()
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("")
def list_cases(
    tenant_id: str,
    session: DatabaseSession,
    after: str = "",
    limit: int = Query(100, ge=1, le=100),
):
    return _respond(
        lambda: cases.list_cases(session, tenant_id, after=after, limit=limit)
    )


@router.get("/status")
def status(tenant_id: str, request: Request, session: DatabaseSession):
    principal = optional_request_principal(request)
    if principal is None:
        return {
            "adopted": cases.adoption(session, tenant_id) is not None,
            "can_adopt": False,
            "can_control": False,
            "kinds": list(cases.KINDS),
        }
    member = _respond(lambda: cases._member(session, tenant_id, principal))
    return {
        "adopted": cases.adoption(session, tenant_id) is not None,
        "can_adopt": member.role == "owner",
        "can_control": True,
        "kinds": list(cases.KINDS),
    }


@router.post("/adoption")
def adopt(tenant_id: str, body: Adopt, request: Request, session: DatabaseSession):
    return _respond(
        lambda: cases.adopt(
            session, tenant_id, request_principal(request), **body.model_dump()
        )
    )


@router.get("/objects/{record_type}/{record_id}")
def object_cases(
    tenant_id: str, record_type: str, record_id: str, session: DatabaseSession
):
    return _respond(
        lambda: {
            "case_ids": cases.object_cases(session, tenant_id, record_type, record_id)
        }
    )


@router.get("/{case_id}")
def explain(tenant_id: str, case_id: str, session: DatabaseSession):
    return _respond(lambda: cases.explain(session, tenant_id, case_id))


@router.post("/{case_id}/takeover")
def takeover(
    tenant_id: str,
    case_id: str,
    body: Takeover,
    request: Request,
    session: DatabaseSession,
):
    return _respond(
        lambda: cases.takeover(
            session, tenant_id, case_id, request_principal(request), **body.model_dump()
        )
    )


@router.get("/{case_id}/handback-review")
def handback_review(tenant_id: str, case_id: str, session: DatabaseSession):
    return _respond(lambda: cases.handback_preview(session, tenant_id, case_id))


@router.post("/{case_id}/handback")
def handback(
    tenant_id: str,
    case_id: str,
    body: Handback,
    request: Request,
    session: DatabaseSession,
):
    return _respond(
        lambda: cases.handback(
            session, tenant_id, case_id, request_principal(request), **body.model_dump()
        )
    )
