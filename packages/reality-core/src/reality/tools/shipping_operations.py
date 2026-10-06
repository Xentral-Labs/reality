"""Shipping planning adapters use the shared reviewed application service."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    ValidationError,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import MCPAccessToken
from reality.db.mcp_authorization import MCPClientGrant
from reality.mcp.principal import current_mcp_principal
from reality.services import core, operations_cockpit
from reality.services.memberships import Principal


class OverviewQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    day: str = Field(default="today", max_length=10)
    location_id: str | None = Field(default=None, max_length=200)


class OrdersQuery(OverviewQuery):
    measure: Literal["due", "plan", "handover", "forecast", "risk", "unplanned"] = "due"
    at: str | None = None
    from_at: str | None = None
    until: str | None = None
    after: str = Field(default="", max_length=4096)
    limit: StrictInt = Field(default=50, ge=1, le=100)
    basis_key: str | None = Field(default=None, max_length=200)


class ActivityQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    minutes: Literal[5, 15, 60] = 15


class AgentsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    access_state: Literal["active", "inactive", "revoked", "all"] = "active"
    after: str = Field(default="", max_length=4096)
    limit: StrictInt = Field(default=6, ge=1, le=50)


class CaseRegisterQuery(BaseModel):
    query: str = Field(default="", max_length=200)
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["order_fulfillment", "customer_return"] | None = None
    control_mode: Literal["automation", "human"] | None = None
    outstanding_only: StrictBool = False
    after: str = Field(default="", max_length=4096)
    limit: StrictInt = Field(default=50, ge=1, le=100)


_viewer_context: ContextVar[tuple[Session, str, Principal] | None] = ContextVar(
    "operations_read_viewer", default=None
)


@contextmanager
def viewer_context(
    session: Session, tenant_id: str, principal: Principal
) -> Iterator[None]:
    """Bind trusted local read attribution; this cannot authorize a mutation."""
    token = _viewer_context.set((session, tenant_id, principal))
    try:
        yield
    finally:
        _viewer_context.reset(token)


def _viewer(session: Session, tenant_id: str, tool_name: str) -> Principal:
    authenticated = current_mcp_principal()
    if authenticated is not None:
        if (
            authenticated.tenant_id != tenant_id
            or "reality:read" not in authenticated.scopes
            or not authenticated.permits(tool_name)
        ):
            raise core.NotFound(code="company_not_found")
        if authenticated.authentication_kind == "manual":
            token = session.scalar(
                select(MCPAccessToken)
                .where(
                    MCPAccessToken.tenant_id == tenant_id,
                    MCPAccessToken.id == authenticated.credential_id,
                )
                .execution_options(populate_existing=True)
            )
            if token is None or token.revoked_at or not token.created_by_user_id:
                raise core.NotFound(code="company_not_found")
            allowed = json.loads(token.allowed_tools)
            if "*" not in allowed and tool_name not in allowed:
                raise core.NotFound(code="company_not_found")
            return Principal(token.created_by_user_id)
        from reality.services.mcp_authorization import _grant_view

        grant = session.scalar(
            select(MCPClientGrant)
            .where(
                MCPClientGrant.tenant_id == tenant_id,
                MCPClientGrant.id == authenticated.grant_id,
            )
            .execution_options(populate_existing=True)
        )
        if (
            grant is None
            or grant.user_id != authenticated.user_id
            or _grant_view(session, grant, include_user=False)["effective_state"]
            != "active"
            or tool_name not in grant.allowed_tools
            or "reality:read" not in grant.scopes
        ):
            raise core.NotFound(code="company_not_found")
        return Principal(grant.user_id)
    local = _viewer_context.get()
    if local is None or local[:2] != (session, tenant_id):
        raise core.NotFound(code="company_not_found")
    return local[2]


def _read(name: str, model: type[BaseModel]):
    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]):
        """
        BUSINESS PURPOSE:
        Expose the same optional company observation to authenticated read adapters.

        BUSINESS RULE shipping_operations.read.authority:
        Resolve current credential/grant or trusted local attribution internally;
        public arguments cannot assert an actor. Recheck it after the shared read.
        Read attribution never creates human proposal or confirmation authority.
        """
        # reality-rule: shipping_operations.read.authority
        principal = _viewer(session, tenant_id, name)
        try:
            filters = model.model_validate(arguments).model_dump()
        except ValidationError as error:
            raise core.InvalidOperation(
                code="shipping_observation_filter_invalid"
            ) from error
        if name in {"shipping_performance", "operations_cockpit"}:
            result = operations_cockpit.operations_cockpit(
                session, tenant_id, principal, **filters
            )
            if name == "shipping_performance":
                result = result["shipping"]
        else:
            operation = {
                "shipping_supporting_orders": operations_cockpit.supporting_orders,
                "operations_cockpit_activity": operations_cockpit.activity,
                "operations_cockpit_agents": operations_cockpit.agents,
                "operational_case_register": operations_cockpit.case_register,
            }[name]
            result = operation(session, tenant_id, principal, **filters)
        _viewer(session, tenant_id, name)
        return result

    return handler


def state_plan(session: Session, tenant_id: str, arguments: dict[str, Any]) -> dict:
    """
    BUSINESS PURPOSE:
    Accept reviewed planning evidence through the shared application service.

    BUSINESS RULE shipping_operations.state_plan.shared:
    Pass the selected company and exact confirmed arguments to the shipping-plan service. Its current-owner, source-version, quantity and replay checks govern acceptance.
    """
    from reality.services.shipping_plans import state_plan as accept

    # reality-rule: shipping_operations.state_plan.shared
    return accept(session, tenant_id, arguments)


def register() -> None:
    from reality.tools.application import TOOLS, Tool

    TOOLS["shipping_plan_state"] = Tool(
        "shipping_plan_state",
        "Review and retain exact source-stated shipping plan, revision or withdrawal without dispatching goods.",
        True,
        state_plan,
    )
    for name, model, description in (
        (
            "operational_case_register",
            CaseRegisterQuery,
            "Read a complete filtered supported-case register; human responsibility survives completion.",
        ),
        (
            "operations_cockpit",
            OverviewQuery,
            "Observe source-backed company/day shipping performance with exact coverage.",
        ),
        (
            "shipping_performance",
            OverviewQuery,
            "Read the canonical shipping plan, effective handover and future forecast.",
        ),
        (
            "shipping_supporting_orders",
            OrdersQuery,
            "Read all matching shipping orders with complete totals and bounded paging.",
        ),
        (
            "operations_cockpit_activity",
            ActivityQuery,
            "Observe recent first-recorded business entities; never operational throughput.",
        ),
        (
            "operations_cockpit_agents",
            AgentsQuery,
            "Owner-only redacted named access inventory with exact observed attribution.",
        ),
    ):
        TOOLS[name] = Tool(name, description, False, _read(name, model))
