import inspect
import json
from dataclasses import FrozenInstanceError, replace

import pytest
from conftest import record_by_id
from fastapi.testclient import TestClient
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy.orm import sessionmaker

from reality.agent import settings as settings_module
from reality.agent.settings import configured_api_key, copilot_api_key, save_ai_settings
from reality.db.core import (
    ChangeProposal,
    MCPAccessToken,
    Party,
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
    MCP_TOOL_REGISTRY,
    dispatch_mcp_tool,
    dispatch_tool,
    model_tool_schemas,
)
from reality.mcp.principal import MCPPrincipal, current_mcp_principal
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
    payments = tools["payment_run_propose"].input_schema["properties"]["payments"]
    assert payments["type"] == "array"
    assert payments["minItems"] == 1
    assert payments["items"]["required"] == ["invoice_id", "amount"]
    assert payments["items"]["properties"]["amount"]["type"] == "string"
    settlement = tools["finance_settlement_propose"].input_schema
    assert "$ref" not in json.dumps(settlement)
    costing = tools["cost_change_propose"].input_schema
    assert "oneOf" in costing
    assert {
        branch["properties"]["operation"]["const"] for branch in costing["oneOf"]
    } >= {
        "assign",
        "allocate",
        "review",
        "inventory_review",
        "contribution_review",
        "commercial_match_review",
    }
    for name, tool in tools.items():
        if "oneOf" in tool.input_schema:
            continue
        for property_name, schema in tool.input_schema["properties"].items():
            assert "type" in schema or "anyOf" in schema or "oneOf" in schema, (
                f"{name}.{property_name} is published without a type"
            )


@pytest.mark.anyio
async def test_credit_union_transport_retains_common_and_shape_arguments(monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace

    captured = []
    monkeypatch.setattr(
        mcp_module,
        "get_access_token",
        lambda: SimpleNamespace(
            subject="ten_schema",
            client_id="schema_test",
            scopes=["reality:tool:*"],
        ),
    )
    monkeypatch.setattr(mcp_module, "Session", lambda: nullcontext(object()))

    def capture(_session, principal, _tool_name, arguments):
        assert isinstance(principal, MCPPrincipal)
        captured.append(arguments)
        return arguments

    monkeypatch.setattr(mcp_module, "dispatch_mcp_tool", capture)
    server = mcp_module.build_server()
    tool = server._tool_manager.get_tool("sales_credit_record_propose")
    assert tool is not None
    supplied = {
        "number": "GS-1",
        "gross_amount": "10.00",
        "invoice_id": "doc_invoice",
        "lines": [
            {
                "invoice_line_id": "lin_invoice",
                "quantity": "1",
                "gross_amount": "10.00",
            }
        ],
        "reason": "Agreed correction",
        "allocation_amount": "0",
    }

    await tool.run(supplied, None)

    assert captured[-1] == supplied


@pytest.mark.anyio
async def test_mcp_tool_list_publishes_access_as_annotations():
    from reality.mcp.catalog import MCP_TOOL_CATALOG

    server = mcp_module.build_server()
    tools = {tool.name: tool for tool in await server.list_tools()}
    access = {definition.name: definition.access for definition in MCP_TOOL_CATALOG}
    assert set(tools) == set(access)
    for name, tool in tools.items():
        assert tool.annotations is not None, name
        assert tool.annotations.read_only_hint is (access[name] == "read"), name
        assert tool.annotations.destructive_hint is (access[name] == "confirm"), name
    assert tools["exceptions_list"].annotations.read_only_hint is True
    assert tools["reservation_propose"].annotations.read_only_hint is False
    assert tools["reservation_propose"].annotations.destructive_hint is False
    assert tools["proposal_approve_and_execute"].annotations.destructive_hint is True


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
        branches = tool.input_schema.get("oneOf", [tool.input_schema])
        for branch in branches:
            if "properties" not in branch:
                continue
            assert branch["additionalProperties"] is False
            assert set(branch["required"]) <= set(branch["properties"])


def test_mcp_principal_is_immutable_and_authority_is_not_public_input():
    principal = MCPPrincipal(
        "interactive",
        "credential_1",
        "grant_1",
        "user_1",
        "tenant_1",
        "client_1",
        frozenset({"mcp:tools"}),
        frozenset({"exceptions_list"}),
    )

    with pytest.raises(FrozenInstanceError):
        principal.tenant_id = "tenant_forged"  # type: ignore[misc]

    forbidden = {"tenant_id", "user_id", "_confirming_user_id"}
    for tool in MCP_TOOL_CATALOG:
        assert forbidden.isdisjoint(json.dumps(tool.input_schema).split('"'))


def test_canonical_dispatch_propagates_only_server_owned_mcp_principal(monkeypatch):
    principal = MCPPrincipal(
        "interactive",
        "credential_1",
        "grant_1",
        "user_1",
        "tenant_1",
        "client_1",
        frozenset({"mcp:tools"}),
        frozenset({"exceptions_list"}),
    )
    observed = []
    definition = MCP_TOOL_REGISTRY["exceptions_list"]

    def capture(_session, tenant_id, arguments):
        observed.append((tenant_id, arguments, current_mcp_principal()))
        return {"ok": True}

    monkeypatch.setitem(
        MCP_TOOL_REGISTRY,
        definition.name,
        replace(definition, handler=capture),
    )

    assert dispatch_tool(
        object(),
        "tenant_1",
        definition.name,
        {},
        principal=principal,
    ) == {"ok": True}
    assert observed == [("tenant_1", {}, principal)]
    assert current_mcp_principal() is None

    with pytest.raises(PermissionError, match="does not match"):
        dispatch_tool(
            object(),
            "tenant_forged",
            definition.name,
            {},
            principal=principal,
        )


def test_manual_and_interactive_principals_share_dispatch_but_keep_attribution(
    monkeypatch,
):
    definition = MCP_TOOL_REGISTRY["exceptions_list"]

    def identify(_session, tenant_id, _arguments):
        principal = current_mcp_principal()
        assert principal is not None
        return {
            "tenant_id": tenant_id,
            "kind": principal.authentication_kind,
            "credential_id": principal.credential_id,
            "user_id": principal.user_id,
        }

    monkeypatch.setitem(
        MCP_TOOL_REGISTRY, definition.name, replace(definition, handler=identify)
    )
    manual = MCPPrincipal(
        "manual",
        "manual_credential",
        None,
        None,
        "tenant_1",
        "manual_client",
        frozenset({"reality:read", "reality:tool:*"}),
        frozenset({"*"}),
    )
    interactive = MCPPrincipal(
        "interactive",
        "user_credential",
        "grant_1",
        "user_1",
        "tenant_1",
        "interactive_client",
        frozenset({"reality:read"}),
        frozenset({"exceptions_list"}),
    )

    assert dispatch_mcp_tool(object(), manual, definition.name, {}) == {
        "tenant_id": "tenant_1",
        "kind": "manual",
        "credential_id": "manual_credential",
        "user_id": None,
    }
    assert dispatch_mcp_tool(object(), interactive, definition.name, {}) == {
        "tenant_id": "tenant_1",
        "kind": "interactive",
        "credential_id": "user_credential",
        "user_id": "user_1",
    }
    with pytest.raises(PermissionError, match="does not allow tool"):
        dispatch_mcp_tool(object(), interactive, "inventory_read", {})


def test_interactive_mcp_proposal_requires_separate_confirmation_and_records_actor(
    session, business, scheduled_owner
):
    principal = MCPPrincipal(
        "interactive",
        "credential_1",
        "grant_1",
        scheduled_owner.id,
        business.tenant.id,
        "client_1",
        frozenset({"reality:propose", "reality:confirm"}),
        frozenset({"party_create_propose", "proposal_approve_and_execute"}),
    )
    before = session.query(Party).filter_by(tenant_id=business.tenant.id).count()

    proposed = dispatch_mcp_tool(
        session,
        principal,
        "party_create_propose",
        {"records": [{"name": "MCP Customer", "roles": ["customer"]}]},
    )
    proposal = session.get(
        ChangeProposal, (business.tenant.id, proposed["proposal_id"])
    )
    assert proposal is not None
    assert proposal.status == "proposed"
    assert proposal.decided_by_user_id is None
    assert (
        session.query(Party).filter_by(tenant_id=business.tenant.id).count() == before
    )

    confirmed = dispatch_mcp_tool(
        session,
        principal,
        "proposal_approve_and_execute",
        {"proposal_id": proposal.id, "approved": True},
    )

    session.refresh(proposal)
    assert confirmed["status"] == "executed"
    assert proposal.decided_by_user_id == scheduled_owner.id
    assert (
        session.query(Party).filter_by(tenant_id=business.tenant.id).count()
        == before + 1
    )


def test_interactive_mcp_dispatch_intersects_access_scope_and_exact_tool():
    principal = MCPPrincipal(
        "interactive",
        "credential_1",
        "grant_1",
        "user_1",
        "tenant_1",
        "client_1",
        frozenset({"reality:read"}),
        frozenset({"party_create_propose"}),
    )

    with pytest.raises(PermissionError, match="propose access"):
        dispatch_mcp_tool(object(), principal, "party_create_propose", {})
    with pytest.raises(PermissionError, match="does not allow tool"):
        dispatch_mcp_tool(object(), principal, "exceptions_list", {})


def test_copilot_schema_is_derived_from_registry_without_confirmation_tools():
    schemas = model_tool_schemas()
    exposed = {schema["function"]["name"]: schema for schema in schemas}

    assert "proposal_approve_and_execute" not in exposed
    assert "proposal_reject" not in exposed
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


def test_proposal_result_names_review_principal_and_verification(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-09-24",
    )

    result = dispatch_tool(
        session,
        business.tenant.id,
        "reservation_propose",
        {"commitment_id": commitment.id},
        allowed_access=("propose",),
    )

    assert result["proposal_id"].startswith("act_")
    assert result["next_step"] == {
        "review_required": True,
        "review_read": "proposal_review",
        "decision_handoff": "proposal-review",
        "required_principal": "authenticated_active_member",
        "explicit_confirmation": True,
        "confirmation_tool": "proposal_approve_and_execute",
        "reconciliation_read": "proposal_execution_status",
        "verification_reads": ["inventory", "commitment_register"],
    }


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


def test_manual_document_and_movement_schemas_publish_closed_values():
    schemas = {
        schema["function"]["name"]: schema["function"]["parameters"]
        for schema in model_tool_schemas(access=("propose",))
    }
    assert schemas["document_create_propose"]["properties"]["document_type"][
        "enum"
    ] == [
        "sales_order",
        "purchase_order",
        "sales_invoice",
        "supplier_invoice",
        "credit_note",
        "supplier_credit_note",
    ]
    assert schemas["movement_create_propose"]["properties"]["movement_type"][
        "enum"
    ] == [
        "opening_stock",
        "receipt",
        "shipment",
        "transfer",
        "return",
        "supplier_return",
        "adjustment",
    ]


def test_credit_dunning_and_free_supplier_invoice_have_public_contracts():
    definitions = {tool.name: tool for tool in MCP_TOOL_CATALOG}
    assert definitions["invoice_credit_context"].access == "read"
    assert definitions["invoice_credit_context"].input_schema["required"] == [
        "invoice_id"
    ]
    assert definitions["supplier_invoice_free_record_propose"].access == "propose"
    assert {
        "supplier_id",
        "number",
        "currency",
        "gross_amount",
        "lines",
    } <= set(
        definitions["supplier_invoice_free_record_propose"].input_schema["required"]
    )
    assert definitions["finance_dunning_context"].access == "read"
    assert definitions["finance_dunning_notices"].access == "read"
    assert definitions["finance_dunning_notice"].access == "read"
    assert definitions["finance_dunning_record_propose"].access == "propose"
    assert definitions["finance_dunning_reverse_propose"].access == "propose"


def test_customer_credit_schema_distinguishes_invoice_and_legacy_shapes():
    schema = next(
        tool.input_schema
        for tool in MCP_TOOL_CATALOG
        if tool.name == "sales_credit_record_propose"
    )

    assert schema["additionalProperties"] is False
    assert schema["required"] == ["gross_amount", "number"]
    assert schema["properties"]["lines"]["items"]["required"] == [
        "invoice_line_id",
        "quantity",
        "gross_amount",
    ]
    assert schema["oneOf"] == [
        {
            "title": "Invoice-linked financial credit",
            "required": [
                "invoice_id",
                "lines",
                "reason",
                "allocation_amount",
            ],
            "not": {
                "anyOf": [{"required": ["order_line_id"]}, {"required": ["quantity"]}]
            },
        },
        {
            "title": "Legacy return credit",
            "required": ["order_line_id", "quantity"],
            "not": {
                "anyOf": [
                    {"required": ["invoice_id"]},
                    {"required": ["lines"]},
                    {"required": ["reason"]},
                    {"required": ["allocation_amount"]},
                ]
            },
        },
    ]


def test_canonical_schema_contract_keeps_required_enums_and_nested_shapes():
    definitions = {tool.name: tool for tool in MCP_TOOL_CATALOG}
    assert definitions["document_create_propose"].input_schema["properties"][
        "document_type"
    ]["enum"] == [
        "sales_order",
        "purchase_order",
        "sales_invoice",
        "supplier_invoice",
        "credit_note",
        "supplier_credit_note",
    ]
    assert definitions["movement_create_propose"].input_schema["properties"][
        "movement_type"
    ]["enum"] == [
        "opening_stock",
        "receipt",
        "shipment",
        "transfer",
        "return",
        "supplier_return",
        "adjustment",
    ]
    free_invoice = definitions["supplier_invoice_free_record_propose"].input_schema
    assert set(free_invoice["required"]) == {
        "supplier_id",
        "number",
        "currency",
        "gross_amount",
        "lines",
    }
    assert set(free_invoice["properties"]["lines"]["items"]["required"]) == {
        "quantity",
        "unit_price",
        "gross_amount",
    }
    credit = definitions["sales_credit_record_propose"].input_schema
    assert set(credit["properties"]["lines"]["items"]["required"]) == {
        "invoice_line_id",
        "quantity",
        "gross_amount",
    }


def test_operational_and_finance_closed_schemas_are_complete_without_probing():
    definitions = {tool.name: tool.input_schema for tool in MCP_TOOL_CATALOG}
    assert definitions["shipment_notice_record_propose"]["properties"]["direction"][
        "enum"
    ] == ["inbound", "outbound"]
    assert definitions["shipment_notice_record_propose"]["properties"]["purpose"][
        "enum"
    ] == [
        "customer_delivery",
        "supplier_delivery",
        "customer_return",
        "supplier_return",
    ]
    dispatch = {
        branch["properties"]["purpose"]["const"]: branch
        for branch in definitions["shipment_dispatch_propose"]["oneOf"]
    }
    receive = {
        branch["properties"]["purpose"]["const"]: branch
        for branch in definitions["shipment_receive_propose"]["oneOf"]
    }
    assert set(dispatch) == {"customer_delivery", "supplier_return"}
    assert set(receive) == {"supplier_delivery", "customer_return"}
    assert dispatch["customer_delivery"]["properties"]["movements"]["items"][
        "properties"
    ]["movement_type"] == {"type": "string", "const": "shipment"}
    assert dispatch["supplier_return"]["properties"]["movements"]["items"][
        "properties"
    ]["movement_type"] == {"type": "string", "const": "supplier_return"}
    assert receive["supplier_delivery"]["properties"]["movements"]["items"][
        "properties"
    ]["movement_type"] == {"type": "string", "const": "receipt"}
    assert receive["customer_return"]["properties"]["movements"]["items"]["properties"][
        "movement_type"
    ] == {"type": "string", "const": "return"}
    assert definitions["supply_assign_propose"]["properties"]["purpose"]["enum"] == [
        "customer_demand",
        "stock_replenishment",
    ]
    assert definitions["return_disposition_propose"]["properties"]["disposition"][
        "enum"
    ] == ["restock", "quarantine_repair", "scrap_loss", "return_to_supplier"]
    settlement = definitions["finance_settlement_propose"]
    assert settlement["properties"]["mode"]["enum"] == [
        "payment",
        "allocate_credit",
        "refund_credit",
    ]
    assert set(settlement["required"]) == {
        "mode",
        "document_id",
        "expected_revision",
        "amount",
    }
    assert "allocation_amount" in settlement["properties"]["mode"]["description"]
    assert "invoice_id" in settlement["properties"]["mode"]["description"]


def test_new_external_agent_surfaces_use_opaque_ids_and_refuse_foreign_records(
    session, business
):
    from reality.services import core
    from reality.services.finance.accounts import list_accounts
    from reality.tools.application import approve_and_execute_proposal

    definitions = {tool.name: tool for tool in MCP_TOOL_CATALOG}
    identity_fields = {
        "invoice_credit_context": ["invoice_id"],
        "supplier_invoice_free_record_propose": ["supplier_id"],
        "finance_dunning_context": ["invoice_ids"],
        "finance_dunning_notice": ["notice_id"],
        "finance_dunning_record_propose": ["invoice_ids"],
        "finance_dunning_reverse_propose": ["notice_id"],
        "proposal_reject": ["proposal_id"],
    }
    for tool_name, field_names in identity_fields.items():
        properties = definitions[tool_name].input_schema["properties"]
        for field_name in field_names:
            identity_schema = properties[field_name]
            if identity_schema["type"] == "array":
                assert identity_schema["items"]["type"] == "string"
            else:
                assert identity_schema["type"] == "string"

    tenant = business.tenant.id
    foreign = create_tenant(session, "Foreign external-agent boundary")
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "INV-OPAQUE-257",
        business.customer.id,
        "50.00",
        document_date="2026-01-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    with pytest.raises(NotFound):
        dispatch_tool(
            session,
            foreign.id,
            "invoice_credit_context",
            {"invoice_id": invoice.id},
            allowed_access=("read",),
        )
    with pytest.raises(NotFound):
        dispatch_tool(
            session,
            foreign.id,
            "finance_dunning_context",
            {
                "invoice_ids": [invoice.id],
                "level": 1,
                "notice_date": "2026-09-23",
                "fee_amount": "0",
                "reason": "Boundary proof",
                "number": "DN-OPAQUE-257",
            },
            allowed_access=("read",),
        )
    assert (
        dispatch_tool(
            session,
            foreign.id,
            "finance_dunning_notices",
            {},
            allowed_access=("read",),
        )
        == []
    )
    with pytest.raises(NotFound):
        dispatch_tool(
            session,
            foreign.id,
            "supplier_invoice_free_record_propose",
            {
                "supplier_id": business.supplier.id,
                "number": "FOREIGN-SINV-257",
                "currency": "EUR",
                "gross_amount": "1.00",
                "lines": [
                    {
                        "description": "Foreign refusal",
                        "quantity": "1",
                        "unit_price": "1.00",
                        "gross_amount": "1.00",
                    }
                ],
            },
            allowed_access=("propose",),
        )

    prepared = dispatch_tool(
        session,
        tenant,
        "finance_dunning_record_propose",
        {
            "invoice_ids": [invoice.id],
            "level": 1,
            "notice_date": "2026-09-23",
            "fee_amount": "0",
            "reason": "Boundary proof",
            "number": "DN-OPAQUE-257",
            "expected_revision": list_accounts(session, tenant)["revision"],
        },
        allowed_access=("propose",),
    )
    executed = approve_and_execute_proposal(session, tenant, prepared["proposal_id"])
    notice_id = json.loads(executed.output)["id"]
    for tool_name, arguments, access in (
        ("finance_dunning_notice", {"notice_id": notice_id}, "read"),
        (
            "finance_dunning_reverse_propose",
            {
                "notice_id": notice_id,
                "reason": "Foreign refusal",
                "expected_revision": list_accounts(session, foreign.id)["revision"],
            },
            "propose",
        ),
        (
            "proposal_reject",
            {"proposal_id": prepared["proposal_id"], "rejected": True},
            "confirm",
        ),
    ):
        with pytest.raises(NotFound):
            dispatch_tool(
                session,
                foreign.id,
                tool_name,
                arguments,
                allowed_access=(access,),
            )


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


def test_proposal_rejection_is_a_controlled_non_model_tool():
    definitions = {tool.name: tool for tool in MCP_TOOL_CATALOG}
    rejection = definitions["proposal_reject"]

    assert rejection.access == "confirm"
    assert rejection.input_schema["required"] == ["proposal_id", "rejected"]
    assert rejection.input_schema["properties"]["rejected"] == {
        "type": "boolean",
        "const": True,
    }


def test_mcp_rejection_requires_explicit_decision_and_preserves_tenant_scope(
    session, business
):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-24",
    )
    prepared = dispatch_tool(
        session,
        business.tenant.id,
        "reservation_propose",
        {"commitment_id": commitment.id},
        allowed_access=("propose",),
    )
    values = {"proposal_id": prepared["proposal_id"], "rejected": True}

    with pytest.raises(ValueError, match="explicit authorized decision"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_reject",
            {**values, "rejected": False},
            allowed_access=("confirm",),
        )
    with pytest.raises(NotFound):
        dispatch_tool(
            session,
            "ten_other",
            "proposal_reject",
            values,
            allowed_access=("confirm",),
        )

    rejected = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_reject",
        values,
        allowed_access=("confirm",),
    )
    replay = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_reject",
        values,
        allowed_access=("confirm",),
    )
    assert rejected == replay
    assert rejected["status"] == "rejected"
    assert rejected["business_effect"] == "none"


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
    stored = record_by_id(session, Secret, settings.api_key_secret_id)
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
    assert record_by_id(session, Secret, first_id).status == "revoked"
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
    assert record_by_id(session, Secret, second_id).status == "revoked"


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
        inventory_page = json.loads(inventory.content[0].text)
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
        assert "requires_confirmation" in str(proposal_result)
        pending = await server.call_tool("proposals_awaiting_approval", {})
        assert proposal.id in str(pending)
        confirmed = await server.call_tool(
            "proposal_approve_and_execute",
            {
                "proposal_id": proposal.id,
                "approved": True,
                "review_token": json.loads(proposal.input)["_delivery_review"]["token"],
            },
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
    assert verified.claims["reality_principal"].authentication_kind == "manual"
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
