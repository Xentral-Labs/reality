"""Universal operational entry with current company inspection authorization."""

from fastapi import APIRouter, Depends, Query, Request

from reality.services import operations_cockpit
from reality.services.core import InvalidOperation, NotFound
from reality.web.api import (
    DatabaseSession,
    api_error,
    request_principal,
    require_tenant_surface_access,
)

router = APIRouter(
    prefix="/api/tenants/{tenant_id}/operations-cockpit",
    tags=["operations-cockpit"],
    dependencies=[Depends(require_tenant_surface_access)],
)


@router.get("/capabilities")
def capabilities(tenant_id: str, request: Request, session: DatabaseSession):
    try:
        return operations_cockpit.capabilities(
            session, tenant_id, request_principal(request)
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("")
def overview(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    day: str = "today",
    location_id: str | None = None,
):
    try:
        return operations_cockpit.operations_cockpit(
            session,
            tenant_id,
            request_principal(request),
            day=day,
            location_id=location_id,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/orders")
def supporting_orders(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    day: str = "today",
    location_id: str | None = None,
    measure: str = "due",
    at: str | None = None,
    from_at: str | None = Query(None, alias="from"),
    until: str | None = None,
    after: str = "",
    limit: int = Query(50, ge=1, le=100),
    basis_key: str | None = None,
):
    try:
        return operations_cockpit.supporting_orders(
            session,
            tenant_id,
            request_principal(request),
            day=day,
            location_id=location_id,
            measure=measure,
            at=at,
            from_at=from_at,
            until=until,
            after=after,
            limit=limit,
            basis_key=basis_key,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/activity")
def activity(
    tenant_id: str, request: Request, session: DatabaseSession, minutes: int = 15
):
    try:
        return operations_cockpit.activity(
            session, tenant_id, request_principal(request), minutes=minutes
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error


@router.get("/agents")
def agents(
    tenant_id: str,
    request: Request,
    session: DatabaseSession,
    access_state: str = "active",
    after: str = "",
    limit: int = Query(6, ge=1, le=50),
):
    try:
        return operations_cockpit.agents(
            session,
            tenant_id,
            request_principal(request),
            access_state=access_state,
            after=after,
            limit=limit,
        )
    except (NotFound, InvalidOperation) as error:
        raise api_error(error) from error
