"""Optional cockpit entry never substitutes configuration for company access."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from test_playground_api import playground_http as _playground_http
from test_shipping_performance import planned_shipping as _planned_shipping

from reality.db.core import BusinessEvent, TenantMembership
from reality.services.memberships import Principal
from reality.web.api import database_session
from reality.web.app import app

planned_shipping = _planned_shipping
playground_http = _playground_http


@pytest.fixture
def cockpit_client(session, scheduled_owner, monkeypatch):
    from reality.web import operations_cockpit as cockpit

    monkeypatch.setattr(
        cockpit, "request_principal", lambda request: Principal(scheduled_owner.id)
    )
    from reality.web import operational_cases

    monkeypatch.setattr(
        operational_cases,
        "request_principal",
        lambda request: Principal(scheduled_owner.id),
    )
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("legacy_value", [None, "", "false", "0", "invalid", "TRUE"])
@pytest.mark.parametrize("role", ["owner", "member"])
def test_cockpit_available_without_activation_and_ignores_retired_flag(
    session, business, scheduled_owner, cockpit_client, monkeypatch, legacy_value, role
):
    # BUSINESS PURPOSE: Anyone already allowed into a company can observe its Control Tower.
    # BUSINESS RULE: Presentation availability never approves actions or writes business records.
    if legacy_value is None:
        monkeypatch.delenv("REALITY_OPERATIONS_COCKPIT_ENABLED", raising=False)
    else:
        monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", legacy_value)
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    membership.role = role
    session.flush()
    before = list(session.scalars(select(BusinessEvent.id)))
    path = f"/api/tenants/{business.tenant.id}/operations-cockpit"
    response = cockpit_client.get(path + "/capabilities")
    assert response.status_code == 200, response.text
    assert response.json() == {"enabled": True}
    for suffix in ("", "/orders", "/activity"):
        response = cockpit_client.get(path + suffix)
        assert response.status_code == 200, response.text
    register = cockpit_client.get(
        f"/api/tenants/{business.tenant.id}/operational-cases/register"
    )
    assert register.status_code == 200, register.text
    assert register.json()["total"] == 0
    assert list(session.scalars(select(BusinessEvent.id))) == before


@pytest.mark.parametrize("refusal", ["removed", "inactive_user", "foreign", "archived"])
def test_cockpit_capability_never_discloses_company_access_after_revocation(
    session, business, scheduled_owner, cockpit_client, monkeypatch, refusal
):
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    tenant_id = business.tenant.id
    if refusal == "removed":
        membership.status = "removed"
    elif refusal == "inactive_user":
        scheduled_owner.status = "inactive"
    elif refusal == "archived":
        from reality.db.core import now

        business.tenant.archived_at = now()
    else:
        tenant_id = "ten_unknown"
    session.flush()
    response = cockpit_client.get(
        f"/api/tenants/{tenant_id}/operations-cockpit/capabilities"
    )
    assert response.status_code in {403, 404}, response.text
    assert "enabled" not in response.json()


def test_cockpit_http_uses_shared_shipping_and_full_supporting_orders(
    session, business, planned_shipping, cockpit_client, monkeypatch
):
    # BUSINESS PURPOSE: Every displayed shipping number has the same shared read basis.
    # BUSINESS RULE: HTTP observes canonical evidence without creating business events.
    from reality.services.shipping_performance import shipping_performance

    before = list(session.scalars(select(BusinessEvent.id)))
    path = f"/api/tenants/{business.tenant.id}/operations-cockpit"
    result = cockpit_client.get(path, params={"day": "2026-10-06"})
    assert result.status_code == 200, result.text
    shared = shipping_performance(session, business.tenant.id, day="2026-10-06")
    assert result.json()["shipping"]["totals"] == shared["totals"]
    orders = cockpit_client.get(path + "/orders", params={"day": "2026-10-06"})
    assert orders.status_code == 200, orders.text
    assert orders.json()["total"] == 1
    assert orders.json()["items"][0]["order_id"]
    assert list(session.scalars(select(BusinessEvent.id))) == before
    register = cockpit_client.get(
        f"/api/tenants/{business.tenant.id}/operational-cases/register"
    )
    assert register.status_code == 200, register.text
    assert register.json()["adopted"] is True
    assert register.json()["total"] == 1
    assert register.json()["coordination"]["rollout_provenance"] == "platform_version"


def test_cockpit_rejects_invalid_order_filters(
    session, business, cockpit_client, monkeypatch
):
    path = f"/api/tenants/{business.tenant.id}/operations-cockpit"
    response = cockpit_client.get(path + "/orders", params={"measure": "invented"})
    assert response.status_code in {400, 422}, response.text


def test_cockpit_read_tools_need_observed_viewer_and_reject_public_authority(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: CLI and external Agent reads observe the same guarded company.
    # BUSINESS RULE: Public arguments cannot assert membership or owner authority.
    from reality.services import core
    from reality.services.memberships import Principal
    from reality.tools import shipping_operations
    from reality.tools.application import run_read_tool

    with pytest.raises((core.InvalidOperation, core.NotFound)):
        run_read_tool(session, business.tenant.id, "operations_cockpit", {})
    with shipping_operations.viewer_context(
        session, business.tenant.id, Principal(scheduled_owner.id)
    ):
        result = run_read_tool(session, business.tenant.id, "operations_cockpit", {})
        assert "shipping" in result
        with pytest.raises(core.InvalidOperation):
            run_read_tool(
                session,
                business.tenant.id,
                "operations_cockpit",
                {"user_id": scheduled_owner.id},
            )
        assert (
            run_read_tool(
                session,
                business.tenant.id,
                "operations_cockpit_activity",
                {"minutes": 5},
            )["minutes"]
            == 5
        )


def test_cockpit_mcp_read_requires_current_exact_credential_and_membership(
    session, business, scheduled_owner, monkeypatch
):
    from reality.db.core import MCPAccessToken, uid
    from reality.mcp.catalog import dispatch_tool
    from reality.mcp.principal import MCPPrincipal
    from reality.services import core

    token = MCPAccessToken(
        id=uid("mcp"),
        tenant_id=business.tenant.id,
        name="Read Agent",
        token_prefix="prefix",
        token_hash=uid("hash"),
        created_by_user_id=scheduled_owner.id,
        allowed_tools='["operations_cockpit"]',
    )
    session.add(token)
    session.flush()
    principal = MCPPrincipal(
        "manual",
        token.id,
        None,
        None,
        business.tenant.id,
        token.id,
        frozenset({"reality:read"}),
        frozenset({"operations_cockpit"}),
    )
    assert "shipping" in dispatch_tool(
        session, business.tenant.id, "operations_cockpit", {}, principal=principal
    )
    token.revoked_at = core.now()
    session.flush()
    with pytest.raises((core.InvalidOperation, core.NotFound)):
        dispatch_tool(
            session, business.tenant.id, "operations_cockpit", {}, principal=principal
        )


def test_cockpit_read_tools_refuse_foreign_company_without_business_effects(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: No company observer can discover another company's operational evidence.
    # BUSINESS RULE: Every registered cockpit reader verifies actual current company membership.
    from reality.services import core
    from reality.tools.application import run_read_tool
    from reality.tools.shipping_operations import viewer_context

    foreign = core.create_tenant(session, "Foreign company")
    session.flush()
    before = list(session.scalars(select(BusinessEvent.id)))
    with viewer_context(session, foreign.id, Principal(scheduled_owner.id)):
        for tool in (
            "operations_cockpit",
            "shipping_performance",
            "shipping_supporting_orders",
            "operations_cockpit_activity",
            "operations_cockpit_agents",
            "operational_case_register",
        ):
            with pytest.raises(core.NotFound):
                run_read_tool(session, foreign.id, tool, {})
    assert list(session.scalars(select(BusinessEvent.id))) == before


@pytest.mark.parametrize("persisted_admin", [False, True])
def test_business_company_admin_visibility_does_not_grant_owner_inventory(
    session, business, scheduled_owner, cockpit_client, persisted_admin
):
    from reality.services import core, operations_cockpit

    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    membership.status = "removed"
    scheduled_owner.is_platform_admin = persisted_admin
    session.flush()
    principal = Principal(scheduled_owner.id, is_platform_admin=True)
    path = f"/api/tenants/{business.tenant.id}/operations-cockpit"
    response = cockpit_client.get(path + "/capabilities")
    if persisted_admin:
        assert response.status_code == 200, response.text
        assert response.json() == {"enabled": True}
        assert cockpit_client.get(path).status_code == 200
        assert "shipping" in operations_cockpit.operations_cockpit(
            session, business.tenant.id, principal
        )
    else:
        assert response.status_code in {403, 404}, response.text
        with pytest.raises(core.NotFound):
            operations_cockpit.capabilities(session, business.tenant.id, principal)
    assert cockpit_client.get(path + "/agents").status_code == 404


@pytest.mark.parametrize("kind", ["practice", "temporary"])
@pytest.mark.parametrize("state", ["active", "pending", "archived"])
def test_owned_ready_playground_has_control_tower_without_egress_or_mutation(
    session, playground_http, monkeypatch, kind, state
):
    from reality.services import operations_cockpit
    from reality.services.tenant_policy import (
        business_operation_allowed,
    )

    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    client, tenant, owner, run, login = playground_http
    run.sandbox_kind = kind
    if state == "pending":
        owner.status = "pending_approval"
    elif state == "archived":
        from reality.db.core import now

        run.status = "archived"
        run.archived_at = now()
        tenant.archived_at = now()
    session.flush()
    login(owner)
    before = list(session.scalars(select(BusinessEvent.id)))
    egress_before = business_operation_allowed(session, tenant.id, "mcp_token_use")
    base = f"/api/tenants/{tenant.id}"
    assert client.get(base + "/operations-cockpit/capabilities").json() == {
        "enabled": True
    }
    for suffix in ("", "/orders", "/activity", "/agents"):
        response = client.get(base + "/operations-cockpit" + suffix)
        assert response.status_code == 200, response.text
    response = client.get(base + "/operational-cases/register")
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 0
    status = client.get(base + "/operational-cases/status")
    assert status.status_code == 200, status.text
    assert status.json()["can_control"] is False
    assert operations_cockpit.capabilities(session, tenant.id, Principal(owner.id)) == {
        "enabled": True
    }
    assert (
        business_operation_allowed(session, tenant.id, "mcp_token_use") == egress_before
    )
    assert client.post(
        base + "/operational-cases/unknown/takeover",
        json={
            "confirmed": True,
            "request_key": "not-permitted",
            "expected_revision": 1,
        },
    ).status_code in {403, 404}
    assert list(session.scalars(select(BusinessEvent.id))) == before


@pytest.mark.parametrize(
    "refusal",
    ["foreign", "revoked", "unverified", "inactive", "rejected", "unready", "failed"],
)
def test_playground_control_tower_preserves_private_run_access(
    session, playground_http, monkeypatch, refusal
):
    from reality.services import core, operations_cockpit

    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    client, tenant, owner, run, login = playground_http
    if refusal == "foreign":
        from reality.db.core import AppUser, now, uid

        foreign = AppUser(
            id=uid("usr"),
            email=f"{uid('mail')}@example.test",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        session.add(foreign)
        session.flush()
        run.owner_user_id = foreign.id
    elif refusal == "revoked":
        member = session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == owner.id,
            )
        )
        member.status = "removed"
    elif refusal == "unverified":
        owner.email_verified_at = None
    elif refusal in {"inactive", "rejected"}:
        owner.status = refusal
    else:
        run.status = "initializing" if refusal == "unready" else "initialization_failed"
    session.flush()
    login(owner)
    base = f"/api/tenants/{tenant.id}"
    for suffix in (
        "/operations-cockpit/capabilities",
        "/operations-cockpit",
        "/operations-cockpit/activity",
        "/operational-cases/register",
    ):
        response = client.get(base + suffix)
        assert response.status_code in {401, 403, 404}, response.text
        assert "enabled" not in response.json()
    with pytest.raises((core.NotFound, core.InvalidOperation)):
        operations_cockpit.capabilities(session, tenant.id, Principal(owner.id))


@pytest.mark.parametrize("kind", ["practice", "temporary"])
def test_direct_control_tower_bootstrap_can_resolve_owned_playground_only(
    session, playground_http, monkeypatch, kind
):
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    client, tenant, owner, run, login = playground_http
    run.sandbox_kind = kind
    session.flush()
    login(owner)
    normal = client.get("/api/v1/bootstrap")
    assert normal.status_code == 200, normal.text
    normal_ids = {row["id"] for row in normal.json()["tenants"]}
    assert (tenant.id in normal_ids) == (kind == "practice")
    scoped = client.get("/api/v1/bootstrap", params={"cockpit_tenant": tenant.id})
    assert scoped.status_code == 200, scoped.text
    company = next(row for row in scoped.json()["tenants"] if row["id"] == tenant.id)
    assert company["purpose"] == "playground"
    assert company["sandbox_run_id"] == run.id
    unknown = client.get("/api/v1/bootstrap", params={"cockpit_tenant": "ten_missing"})
    assert unknown.status_code == 404, unknown.text
