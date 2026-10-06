"""Optional cockpit entry never substitutes configuration for company access."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from test_shipping_performance import planned_shipping as _planned_shipping

from reality.db.core import BusinessEvent, TenantMembership
from reality.services.memberships import Principal
from reality.web.api import database_session
from reality.web.app import app

planned_shipping = _planned_shipping


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


def test_cockpit_capability_defaults_off_and_read_has_no_business_effect(
    session, business, cockpit_client, monkeypatch
):
    # BUSINESS PURPOSE: An owner can discover availability without activating automation.
    # BUSINESS RULE: Configuration is not consent, adoption or a business mutation.
    monkeypatch.delenv("REALITY_OPERATIONS_COCKPIT_ENABLED", raising=False)
    before = list(session.scalars(select(BusinessEvent.id)))
    response = cockpit_client.get(
        f"/api/tenants/{business.tenant.id}/operations-cockpit/capabilities"
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"enabled": False}
    assert list(session.scalars(select(BusinessEvent.id))) == before


@pytest.mark.parametrize("enabled", ["1", "true", "TRUE"])
def test_cockpit_member_can_read_enabled_capability(
    session, business, scheduled_owner, cockpit_client, monkeypatch, enabled
):
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", enabled)
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    membership.role = "member"
    session.flush()
    response = cockpit_client.get(
        f"/api/tenants/{business.tenant.id}/operations-cockpit/capabilities"
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"enabled": True}


@pytest.mark.parametrize("refusal", ["removed", "inactive_user", "foreign", "archived"])
def test_cockpit_capability_never_discloses_company_access_after_revocation(
    session, business, scheduled_owner, cockpit_client, monkeypatch, refusal
):
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
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

    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
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


def test_disabled_cockpit_refuses_data_and_invalid_order_filters(
    session, business, cockpit_client, monkeypatch
):
    path = f"/api/tenants/{business.tenant.id}/operations-cockpit"
    monkeypatch.delenv("REALITY_OPERATIONS_COCKPIT_ENABLED", raising=False)
    for suffix in ("", "/orders"):
        response = cockpit_client.get(path + suffix)
        assert response.status_code == 404, response.text
        assert "shipping" not in response.json()
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
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

    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
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

    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
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

    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
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
