import inspect
import json

import pytest
from fastapi.testclient import TestClient
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.server.fastmcp.exceptions import ToolError
from sqlalchemy.orm import sessionmaker

from reality.agent import settings as settings_module
from reality.agent.settings import configured_api_key, copilot_api_key, save_ai_settings
from reality.db.core import (
    ChangeProposal,
    MCPAccessToken,
    Secret,
    SecretAuditEvent,
    now,
)
from reality.mcp import auth as mcp_auth_module
from reality.mcp import server as mcp_module
from reality.mcp.auth import DatabaseTokenVerifier, create_mcp_access_token
from reality.mcp.catalog import (
    MCP_TOOL_CATALOG,
    MCP_TOOL_NAMES,
    dispatch_tool,
    model_tool_schemas,
)
from reality.security.secrets import resolve_secret
from reality.services.core import (
    NotFound,
    create_commitment,
    create_tenant,
    record_movement,
)


@pytest.mark.anyio
async def test_mcp_tool_list_publishes_nested_argument_schemas():
    server = mcp_module.build_server()
    tools = {tool.name: tool for tool in await server.list_tools()}
    payments = tools["payment_run_propose"].inputSchema["properties"]["payments"]
    assert payments["type"] == "array"
    assert payments["minItems"] == 1
    assert payments["items"]["required"] == ["invoice_id", "amount"]
    assert payments["items"]["properties"]["amount"]["type"] == "string"
    settlement = tools["finance_settlement_propose"].inputSchema
    assert "$ref" not in json.dumps(settlement)
    for name, tool in tools.items():
        for property_name, schema in tool.inputSchema["properties"].items():
            assert "type" in schema or "anyOf" in schema or "oneOf" in schema, (
                f"{name}.{property_name} is published without a type"
            )


@pytest.mark.anyio
async def test_mcp_tool_list_publishes_access_as_annotations():
    from reality.mcp.catalog import MCP_TOOL_CATALOG

    server = mcp_module.build_server()
    tools = {tool.name: tool for tool in await server.list_tools()}
    access = {definition.name: definition.access for definition in MCP_TOOL_CATALOG}
    assert set(tools) == set(access)
    for name, tool in tools.items():
        assert tool.annotations is not None, name
        assert tool.annotations.readOnlyHint is (access[name] == "read"), name
        assert tool.annotations.destructiveHint is (access[name] == "confirm"), name
    assert tools["exceptions_list"].annotations.readOnlyHint is True
    assert tools["reservation_propose"].annotations.readOnlyHint is False
    assert tools["reservation_propose"].annotations.destructiveHint is False
    assert tools["proposal_approve_and_execute"].annotations.destructiveHint is True


def test_canonical_mcp_registry_has_unique_bound_structured_tools():
    assert len(MCP_TOOL_CATALOG) == len(MCP_TOOL_NAMES)
    assert {tool.access for tool in MCP_TOOL_CATALOG} == {
        "read",
        "propose",
        "confirm",
    }
    for tool in MCP_TOOL_CATALOG:
        assert callable(tool.handler)
        assert tool.input_schema["type"] == "object"
        assert tool.input_schema["additionalProperties"] is False
        assert set(tool.input_schema["required"]) <= set(
            tool.input_schema["properties"]
        )


def test_copilot_schema_is_derived_from_registry_without_confirmation_tools():
    schemas = model_tool_schemas()
    exposed = {schema["function"]["name"]: schema for schema in schemas}

    assert "proposal_approve_and_execute" not in exposed
    assert {
        "member_invite",
        "invitation_resend",
        "invitation_revoke",
        "member_remove",
    }.isdisjoint(exposed)
    assert set(exposed) == {
        tool.name for tool in MCP_TOOL_CATALOG if tool.access in {"read", "propose"}
    }
    for tool in MCP_TOOL_CATALOG:
        if tool.name in exposed:
            assert exposed[tool.name]["function"]["parameters"] == tool.input_schema


def test_master_data_proposal_schemas_expose_required_fields_defaults_and_optional_source():
    schemas = {
        schema["function"]["name"]: schema["function"]["parameters"]
        for schema in model_tool_schemas(access=("propose",))
    }
    expected = {
        "party_create_propose": ({"name", "roles"}, {}),
        "item_create_propose": ({"sku", "name"}, {"unit": "pcs"}),
        "location_create_propose": (
            {"name"},
            {"type": "warehouse", "allows_stock": True},
        ),
    }
    for tool_name, (required, defaults) in expected.items():
        schema = schemas[tool_name]
        assert schema["required"] == ["records"]
        assert schema["properties"]["records"]["minItems"] == 1
        record_schema = schema["properties"]["records"]["items"]
        assert set(record_schema["required"]) == required
        assert record_schema["additionalProperties"] is False
        assert {"source_system", "external_id", "source_payload"} <= set(
            record_schema["properties"]
        )
        for field, value in defaults.items():
            assert record_schema["properties"][field]["default"] == value
    location_properties = schemas["location_create_propose"]["properties"]["records"][
        "items"
    ]["properties"]
    assert {"ref", "parent_ref", "parent_location_id"} <= set(location_properties)
    assert "opaque" in location_properties["parent_location_id"]["description"].lower()
    assert "same batch" in location_properties["parent_ref"]["description"]


def test_copilot_module_has_no_stdio_or_subprocess_dependency():
    from reality.agent import mcp_chat

    source = inspect.getsource(mcp_chat)
    assert "mcp.client.stdio" not in source
    assert "StdioServerParameters" not in source
    assert "subprocess" not in source


def test_master_data_update_proposal_schemas_require_opaque_id_and_complete_values():
    schemas = {
        schema["function"]["name"]: schema["function"]["parameters"]
        for schema in model_tool_schemas(access=("propose",))
    }
    expected = {
        "party_update_propose": {"id", "name", "type", "roles"},
        "item_update_propose": {"id", "sku", "name", "unit"},
        "location_update_propose": {"id", "name", "type"},
    }
    for tool_name, required in expected.items():
        record_schema = schemas[tool_name]["properties"]["records"]["items"]
        assert set(record_schema["required"]) == required
        assert record_schema["additionalProperties"] is False
        assert "opaque" in record_schema["properties"]["id"]["description"].lower()
        assert {"source_system", "external_id", "source_payload"} <= set(
            record_schema["properties"]
        )
        assert all(
            "default" not in property_schema
            for property_schema in record_schema["properties"].values()
        )


def test_copilot_dispatch_cannot_execute_confirmation_tool(session, business):
    with pytest.raises(PermissionError, match="does not allow MCP confirm tool"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": "act_unknown", "approved": True},
            allowed_access=("read", "propose"),
        )


def test_ai_key_is_encrypted_and_tenant_scoped(
    session, business, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings_module, "KEY_PATH", tmp_path / "settings.key")

    settings = save_ai_settings(
        session,
        business.tenant.id,
        provider="openai_compatible",
        model="example-model",
        base_url="https://api.openai.com/v1/",
        api_key="secret-value",
    )

    assert settings.encrypted_api_key == ""
    assert settings.api_key_secret_id
    stored = session.get(Secret, settings.api_key_secret_id)
    assert stored is not None
    assert "secret-value" not in stored.ciphertext
    assert stored.fingerprint.endswith("alue")
    assert configured_api_key(settings) == "secret-value"
    assert settings.base_url == "https://api.openai.com/v1"

    other_tenant = create_tenant(session, "Other company")
    with pytest.raises(NotFound):
        resolve_secret(session, other_tenant.id, stored.id)
    assert {
        event.event_type
        for event in session.query(SecretAuditEvent).filter_by(secret_id=stored.id)
    } >= {"created", "used"}


def test_replacing_and_clearing_ai_key_revokes_old_secrets(
    session, business, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings_module, "KEY_PATH", tmp_path / "settings.key")
    settings = save_ai_settings(
        session,
        business.tenant.id,
        provider="openai_compatible",
        model="example-model",
        base_url="https://api.openai.com/v1",
        api_key="first-secret",
    )
    first_id = settings.api_key_secret_id
    settings = save_ai_settings(
        session,
        business.tenant.id,
        provider="openai_compatible",
        model="example-model",
        base_url="https://api.openai.com/v1",
        api_key="second-secret",
    )
    assert session.get(Secret, first_id).status == "revoked"
    second_id = settings.api_key_secret_id
    assert second_id != first_id
    assert configured_api_key(settings) == "second-secret"

    settings = save_ai_settings(
        session,
        business.tenant.id,
        provider="local",
        model="",
        base_url="",
        clear_api_key=True,
    )
    assert settings.api_key_secret_id is None
    assert session.get(Secret, second_id).status == "revoked"


def test_company_anthropic_key_overrides_managed_key(
    session, business, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings_module, "KEY_PATH", tmp_path / "settings.key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "managed-secret")
    settings = save_ai_settings(
        session,
        business.tenant.id,
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        base_url="https://api.anthropic.com",
        api_key="company-secret",
    )

    assert settings.provider == "anthropic"
    assert copilot_api_key(session, business.tenant.id) == "company-secret"

    save_ai_settings(
        session,
        business.tenant.id,
        provider="local",
        model="",
        base_url="",
        clear_api_key=True,
    )
    assert copilot_api_key(session, business.tenant.id) == "managed-secret"


@pytest.mark.anyio
async def test_mcp_tools_read_and_only_propose_mutations(
    session, business, monkeypatch
):
    monkeypatch.setattr(mcp_module, "Session", lambda: session)
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        2,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-10",
    )
    server = mcp_module.build_server()
    access = AccessToken(
        token="test",
        client_id="mcp_test",
        scopes=["reality:read", "reality:tool:*"],
        subject=business.tenant.id,
    )
    context = auth_context_var.set(AuthenticatedUser(access))
    tools = await server.list_tools()
    assert {tool.name for tool in tools} >= {
        "inventory_read",
        "fulfillment_queue",
        "fulfillment_blockers",
        "item_supply_demand",
        "order_explain",
        "reservation_propose",
        "source_ingest_propose",
        "party_create_propose",
        "item_create_propose",
        "location_create_propose",
        "exceptions_list",
        "exception_explain",
        "proposals_awaiting_approval",
        "proposal_approve_and_execute",
    }
    try:
        inventory = await server.call_tool("inventory_read", {})
        assert "Bike Light" in str(inventory)
        inventory_page = json.loads(inventory[0].text)
        assert inventory_page["records"][0]["item_id"] == business.item.id
        assert inventory_page["has_more"] is False
        assert inventory_page["metadata"]["contract_version"] == 2
        queue = await server.call_tool("fulfillment_queue", {})
        assert commitment.id in str(queue)
        blockers = await server.call_tool("fulfillment_blockers", {})
        assert "insufficient_reservation" in str(blockers)
        proposal_result = await server.call_tool(
            "reservation_propose", {"commitment_id": commitment.id}
        )

        proposal = (
            session.query(ChangeProposal).filter_by(tenant_id=business.tenant.id).one()
        )
        assert proposal.status == "proposed"
        assert proposal.type == "tool:reserve"
        assert commitment.id in json.loads(proposal.input).values()
        assert "requires_human_confirmation" in str(proposal_result)
        pending = await server.call_tool("proposals_awaiting_approval", {})
        assert proposal.id in str(pending)
        confirmed = await server.call_tool(
            "proposal_approve_and_execute",
            {"proposal_id": proposal.id, "approved": True, "review_token": json.loads(proposal.input)["_delivery_review"]["token"]},
        )
    finally:
        auth_context_var.reset(context)
    proposal = session.query(ChangeProposal).filter_by(id=proposal.id).one()
    assert proposal.status == "executed"
    assert "executed" in str(confirmed)


@pytest.mark.skip(
    reason="Retired server-rendered UI; covered by the React/API boundary."
)
def test_ai_settings_page_never_renders_stored_key(
    session, business, tmp_path, monkeypatch
):
    from reality.web import api as api_module
    from reality.web import app as web_module

    monkeypatch.setattr(settings_module, "KEY_PATH", tmp_path / "settings.key")
    save_ai_settings(
        session,
        business.tenant.id,
        provider="openai_compatible",
        model="example-model",
        base_url="https://api.openai.com/v1",
        api_key="never-render-this",
    )
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    page = TestClient(web_module.app).get(
        "/settings/ai", params={"tenant": business.tenant.id}
    )

    assert page.status_code == 200
    assert "AI &amp; MCP" in page.text
    assert "never-render-this" not in page.text
    assert "Secured in the company vault" in page.text
    assert 'class="br-select"' in page.text
    assert page.text.count('class="br-input"') == 4
    assert page.text.count('class="br-field-help"') == 5
    assert 'name="provider_preset"' in page.text
    assert "OpenRouter" in page.text
    assert "Groq" in page.text
    assert "Mistral AI" in page.text
    explorer = TestClient(web_module.app).get(
        "/explorer", params={"tenant": business.tenant.id}
    )
    assert explorer.status_code == 200


@pytest.mark.anyio
async def test_mcp_bearer_tokens_are_hashed_tenant_scoped_and_revocable(
    session, business, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(mcp_auth_module, "Session", factory)

    record, clear_token = create_mcp_access_token(
        session, business.tenant.id, "Claude production"
    )
    assert clear_token.startswith("ros_mcp_")
    assert record.token_hash != clear_token
    assert clear_token not in record.token_hash

    verified = await DatabaseTokenVerifier().verify_token(clear_token)
    assert verified is not None
    assert verified.subject == business.tenant.id
    assert "reality:tool:*" in verified.scopes
    assert await DatabaseTokenVerifier().verify_token("ros_mcp_invalid") is None

    record.revoked_at = now()
    session.commit()
    assert await DatabaseTokenVerifier().verify_token(clear_token) is None


@pytest.mark.anyio
async def test_mcp_token_scopes_match_its_explicit_tool_allowlist(
    session, business, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(mcp_auth_module, "Session", factory)
    record, clear_token = create_mcp_access_token(
        session,
        business.tenant.id,
        "Issue reader",
        ["exceptions_list", "exception_explain"],
    )

    verified = await DatabaseTokenVerifier().verify_token(clear_token)

    assert json.loads(record.allowed_tools) == ["exceptions_list", "exception_explain"]
    assert verified is not None
    assert set(verified.scopes) == {
        "reality:read",
        "reality:tool:exceptions_list",
        "reality:tool:exception_explain",
    }


@pytest.mark.anyio
async def test_remote_mcp_server_enforces_tool_permission_on_every_call(
    session, business, monkeypatch
):
    monkeypatch.setattr(mcp_module, "Session", lambda: session)
    access = AccessToken(
        token="test",
        client_id="mcp_test",
        scopes=["reality:read", "reality:tool:exceptions_list"],
        subject=business.tenant.id,
    )
    context = auth_context_var.set(AuthenticatedUser(access))
    try:
        server = mcp_module.build_server()
        allowed = await server.call_tool("exceptions_list", {})
        with pytest.raises(ToolError, match="does not allow tool: inventory_read"):
            await server.call_tool("inventory_read", {})
    finally:
        auth_context_var.reset(context)

    assert "does not allow" not in str(allowed)


@pytest.mark.skip(
    reason="Retired server-rendered UI; covered by the React/API boundary."
)
def test_ai_settings_can_create_and_revoke_remote_mcp_token(
    session, business, monkeypatch
):
    from reality.web import api as api_module
    from reality.web import app as web_module

    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    created = TestClient(web_module.app).post(
        "/settings/mcp/tokens",
        data={
            "tenant": business.tenant.id,
            "name": "Claude production",
            "allowed_tools": ["exceptions_list", "exception_explain"],
        },
    )
    assert created.status_code == 200
    assert "Bearer token" in created.text
    assert "Copy this token now" in created.text
    assert "ros_mcp_" in created.text
    assert "python -m reality.mcp.server" not in created.text

    token = session.query(MCPAccessToken).filter_by(tenant_id=business.tenant.id).one()
    assert json.loads(token.allowed_tools) == ["exceptions_list", "exception_explain"]
    assert "2 selected tools" in created.text
    revoked = TestClient(web_module.app).post(
        f"/settings/mcp/tokens/{token.id}/revoke",
        data={"tenant": business.tenant.id},
        follow_redirects=False,
    )
    assert revoked.status_code == 303
    session.refresh(token)
    assert token.revoked_at is not None


def test_web_application_does_not_serve_mcp():
    from reality.web import app as web_module

    assert all(
        getattr(route, "path", None) != "/mcp/" for route in web_module.app.routes
    )
