from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.mcp import auth as auth_module
from reality.mcp.app import create_mcp_app
from reality.mcp.auth import create_mcp_access_token
from reality.mcp.config import MCPRuntimeSettings, configured_mcp_url


def test_sdk_supports_target_protocol_revision():
    from mcp_types import LATEST_PROTOCOL_VERSION

    assert LATEST_PROTOCOL_VERSION == "2026-07-28"


def test_runtime_settings_keep_public_endpoint_and_listener_separate():
    settings = MCPRuntimeSettings.from_environ(
        {
            "MCP_URL": "http://localhost:9001/",
            "MCP_BIND_HOST": "0.0.0.0",
            "MCP_BIND_PORT": "8001",
        }
    )

    assert settings.public_url == "http://localhost:9001/"
    assert settings.bind_host == "0.0.0.0"
    assert settings.bind_port == 8001
    assert settings.authorization_issuer == "http://127.0.0.1:8000"


def test_runtime_settings_keep_authorization_issuer_separate():
    settings = MCPRuntimeSettings.from_environ(
        {
            "MCP_URL": "https://mcp.example.test/",
            "MCP_AUTHORIZATION_ISSUER": "https://api.example.test",
        }
    )

    assert settings.public_url == "https://mcp.example.test/"
    assert settings.authorization_issuer == "https://api.example.test"


def test_runtime_settings_require_https_in_production():
    try:
        MCPRuntimeSettings.from_environ(
            {"REALITY_ENV": "production", "MCP_URL": "http://mcp.runreality.ai/"}
        )
    except ValueError as error:
        assert "HTTPS" in str(error)
    else:  # pragma: no cover - communicates the expected failure clearly
        raise AssertionError("Production accepted an insecure MCP_URL")


def test_dedicated_runtime_is_http_only_authenticated_and_has_probes(
    session, business, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(auth_module, "Session", factory)
    _, clear_token = create_mcp_access_token(session, business.tenant.id, "HTTP client")
    settings = MCPRuntimeSettings(
        public_url="http://localhost:8001/",
        bind_host="127.0.0.1",
        bind_port=8001,
    )
    runtime = create_mcp_app(settings=settings, session_factory=factory)
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }

    with TestClient(runtime) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready"}
        metadata = client.get("/.well-known/oauth-protected-resource").json()
        assert metadata["resource"] == "http://localhost:8001/"
        assert metadata["authorization_servers"] == ["http://127.0.0.1:8000"]
        assert client.post("/", json=initialize).status_code == 401
        response = client.post(
            "/",
            json=initialize,
            headers={
                "Authorization": f"Bearer {clear_token}",
                "Accept": "application/json, text/event-stream",
                "Host": "localhost:8001",
            },
        )

    assert response.status_code == 200
    assert response.json()["result"]["serverInfo"]["name"] == "Reality"


def test_http_tools_list_serializes_complete_shipment_execution_contracts(
    session, business, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(auth_module, "Session", factory)
    _, clear_token = create_mcp_access_token(
        session, business.tenant.id, "Schema client"
    )
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/",
            bind_host="127.0.0.1",
            bind_port=8001,
        ),
        session_factory=factory,
    )
    headers = {
        "Authorization": f"Bearer {clear_token}",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
    }
    with TestClient(runtime) as client:
        initialized = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2026-07-28",
                    "capabilities": {},
                    "clientInfo": {"name": "schema", "version": "1"},
                },
            },
        )
        assert initialized.status_code == 200
        response = client.post(
            "/",
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )

    tools = {
        row["name"]: row["inputSchema"] for row in response.json()["result"]["tools"]
    }
    from reality.mcp.catalog import MCP_TOOL_REGISTRY

    for name in ("business_records_discover", "inventory_read", "reservation_propose"):
        assert tools[name] == MCP_TOOL_REGISTRY[name].input_schema
    settlement = tools["finance_settlement_propose"]
    assert "$ref" not in json.dumps(settlement)
    reduction = settlement["properties"]["reduction"]["anyOf"][0]
    assert reduction["required"] == ["amount", "reason_category", "reason"]
    assert reduction["properties"]["reason_category"]["enum"] == [
        "early_payment_discount",
        "agreed_deduction",
        "accepted_small_remainder",
        "bad_debt",
        "payment_fee",
    ]

    for name, purposes in {
        "shipment_dispatch_propose": {"customer_delivery", "supplier_return"},
        "shipment_receive_propose": {"supplier_delivery", "customer_return"},
    }.items():
        branches = tools[name]["oneOf"]
        assert {row["properties"]["purpose"]["const"] for row in branches} == purposes
        assert all(
            {"purpose", "counterparty_id", "movements"} == set(row["required"])
            for row in branches
        )
        assert all(
            {"item_id", "quantity"}
            <= set(row["properties"]["movements"]["items"]["required"])
            for row in branches
        )


def test_http_runtime_rejects_unknown_shipment_fields_before_dispatch(
    session, business, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(auth_module, "Session", factory)
    _, clear_token = create_mcp_access_token(
        session, business.tenant.id, "Strict client"
    )
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/",
            bind_host="127.0.0.1",
            bind_port=8001,
        ),
        session_factory=factory,
    )
    headers = {
        "Authorization": f"Bearer {clear_token}",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
    }
    arguments = {
        "purpose": "customer_delivery",
        "counterparty_id": business.customer.id,
        "movements": [
            {
                "item_id": business.item.id,
                "quantity": "1",
            }
        ],
    }

    with TestClient(runtime) as client:
        for field, invalid_arguments in (
            ("unexpected_top_level", arguments | {"unexpected_top_level": True}),
            (
                "unexpected_nested",
                arguments
                | {
                    "movements": [
                        arguments["movements"][0] | {"unexpected_nested": True}
                    ]
                },
            ),
        ):
            response = client.post(
                "/",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "shipment_dispatch_propose",
                        "arguments": invalid_arguments,
                    },
                },
            )

            result = response.json()["result"]
            assert result["isError"] is True
            message = result["content"][0]["text"]
            assert field in message
            assert "Party not found" not in message


def test_readiness_is_safe_when_database_is_unavailable():
    class BrokenSession:
        def __enter__(self):
            raise RuntimeError("postgresql://secret@database/reality")

        def __exit__(self, *_args):
            return None

    settings = MCPRuntimeSettings(
        public_url="http://localhost:8001/",
        bind_host="127.0.0.1",
        bind_port=8001,
    )
    runtime = create_mcp_app(settings=settings, session_factory=BrokenSession)

    with TestClient(runtime) as client:
        assert client.get("/healthz").status_code == 200
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert "secret" not in response.text


def test_manual_token_survives_authorization_outage_without_anonymous_fallback(
    session, business, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(auth_module, "Session", factory)
    record, clear_token = create_mcp_access_token(
        session, business.tenant.id, "Existing integration", ["exceptions_list"]
    )
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/",
            bind_host="127.0.0.1",
            bind_port=8001,
            authorization_issuer="https://authorization-unavailable.example",
        ),
        session_factory=factory,
    )
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2026-07-28",
            "capabilities": {},
            "clientInfo": {"name": "existing", "version": "1"},
        },
    }
    headers = {
        "Authorization": f"Bearer {clear_token}",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
    }
    with TestClient(runtime) as client:
        assert client.post("/", json=initialize, headers=headers).status_code == 200
        invalid = client.post(
            "/", json=initialize, headers={**headers, "Authorization": "Bearer invalid"}
        )
        assert invalid.status_code == 401
        record.revoked_at = auth_module.now()
        session.commit()
        assert client.post("/", json=initialize, headers=headers).status_code == 401


def test_public_mcp_address_does_not_validate_runtime_only_configuration():
    assert (
        configured_mcp_url(
            {
                "REALITY_ENV": "production",
                "MCP_URL": "https://mcp.example.test/",
                "MCP_AUTHORIZATION_ISSUER": "not-an-issuer",
                "MCP_BIND_PORT": "not-a-port",
            }
        )
        == "https://mcp.example.test/"
    )


def test_production_runtime_uses_canonical_api_origin_as_issuer():
    settings = MCPRuntimeSettings.from_environ(
        {
            "REALITY_ENV": "production",
            "MCP_URL": "https://mcp.example.test/",
            "API_URL": "https://api.example.test/",
        }
    )
    assert settings.authorization_issuer == "https://api.example.test"


@pytest.mark.parametrize(
    "url", ["http://mcp.example.test/", "https://mcp.example.test/path", "invalid"]
)
def test_public_mcp_address_retains_production_origin_validation(url):
    with pytest.raises(ValueError):
        configured_mcp_url({"REALITY_ENV": "production", "MCP_URL": url})


def test_production_runtime_rejects_insecure_api_issuer_fallback():
    with pytest.raises(ValueError, match="HTTPS"):
        MCPRuntimeSettings.from_environ(
            {
                "REALITY_ENV": "production",
                "MCP_URL": "https://mcp.example.test/",
                "API_URL": "http://api.example.test",
            }
        )


def test_production_runtime_discovery_advertises_canonical_api_issuer():
    settings = MCPRuntimeSettings.from_environ(
        {
            "REALITY_ENV": "production",
            "MCP_URL": "https://mcp.example.test/",
            "API_URL": "https://api.example.test",
        }
    )
    with TestClient(create_mcp_app(settings=settings)) as client:
        metadata = client.get("/.well-known/oauth-protected-resource").json()
    assert metadata["authorization_servers"] == ["https://api.example.test"]
    assert metadata["resource"] == "https://mcp.example.test/"


def test_http_read_returns_deterministic_evidence_summary(
    session, business, monkeypatch
):
    from reality.services.core import record_movement

    movement = record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    from reality.mcp import server as server_module

    monkeypatch.setattr(server_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    _, clear_token = create_mcp_access_token(
        session, business.tenant.id, "Read evidence test"
    )
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/", bind_host="127.0.0.1", bind_port=8001
        ),
        session_factory=factory,
    )
    headers = {
        "Authorization": f"Bearer {clear_token}",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
    }
    with TestClient(runtime) as client:
        response = client.post(
            "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "business_records_discover",
                    "arguments": {"family": "movement", "query": "return"},
                },
            },
        )
    assert response.status_code == 200
    result = response.json()["result"]
    assert not result.get("isError", False)
    value = json.loads(result["content"][0]["text"])
    assert value["records"][0]["id"] == movement.id
    assert value["records"][0]["item_name"] == business.item.name
    assert value["records"][0]["item_sku"] == business.item.sku
    assert value["summary"]["selection_record_count"] == 1
    assert value["summary"]["counts_by_type"] == {"return": 1}
    assert "customer return (return): 1 records" in value["summary"]["observation"]
    assert value["summary"]["complete_matching_selection"] is True
    assert value["metadata"]["persistence"]["business_writes"] is False


def test_http_existing_tools_expose_evidence_boundaries(session, business, monkeypatch):
    from test_mcp_read_contract import order

    _, _, _, commitments = order(session, business)
    commitment = next(c for c in commitments if c.type == "customer_delivery")
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    from reality.mcp import server as server_module

    monkeypatch.setattr(server_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    _, clear_token = create_mcp_access_token(
        session, business.tenant.id, "Read evidence test"
    )
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/", bind_host="127.0.0.1", bind_port=8001
        ),
        session_factory=factory,
    )
    headers = {
        "Authorization": f"Bearer {clear_token}",
        "Accept": "application/json, text/event-stream",
        "Host": "localhost:8001",
    }
    cases = [
        ("capability_catalog", {}),
        ("fulfillment_readiness", {"commitment_id": commitment.id}),
        ("fulfillment_queue", {}),
        ("fulfillment_blockers", {}),
    ]
    with TestClient(runtime) as client:
        values = {}
        for name, arguments in cases:
            response = client.post(
                "/",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": name,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                },
            )
            assert response.status_code == 200
            result = response.json()["result"]
            assert not result.get("isError", False)
            values[name] = json.loads(result["content"][0]["text"])
    assert (
        values["capability_catalog"]["external_agent_runtime"]["schedule"] == "unknown"
    )
    meaning = values["fulfillment_readiness"]["payment_interpretation"]
    assert meaning["payment_evidence"]["status"] == "not_evaluated"
    assert meaning["shipment_constraint"]["status"] == "not_required"
    cause = values["fulfillment_readiness"]["unfulfilled_cause"]
    assert cause["status"] == "unknown"
    assert (
        values["fulfillment_queue"]["records"][0]["lines"][0]["unfulfilled_cause"]
        == cause
    )
    assert all(
        b["blocker_kind"] == "derived_readiness_condition"
        for b in values["fulfillment_blockers"]["records"]
    )


def test_http_executed_decision_discovery_uses_existing_read_grant(
    session, business, monkeypatch
):
    from test_business_decision_discovery import executed_reservation

    from reality.mcp import server as server_module

    document, _, proposal = executed_reservation(session, business)
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    monkeypatch.setattr(server_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    _, allowed = create_mcp_access_token(
        session,
        business.tenant.id,
        "Discovery reader",
        allowed_tools=["business_records_discover"],
    )
    _, denied = create_mcp_access_token(
        session, business.tenant.id, "Context reader", allowed_tools=["company_context"]
    )
    runtime = create_mcp_app(
        settings=MCPRuntimeSettings(
            public_url="http://localhost:8001/", bind_host="127.0.0.1", bind_port=8001
        ),
        session_factory=factory,
    )
    with TestClient(runtime) as client:

        def call(token, name, arguments):
            return client.post(
                "/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                    "Host": "localhost:8001",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                },
            )

        arguments = {"family": "executed_decision", "document_id": document.id}
        response = call(allowed, "business_records_discover", arguments)
        assert response.status_code == 200
        result = response.json()["result"]
        assert not result.get("isError", False)
        value = json.loads(result["content"][0]["text"])
        assert value["records"][0]["proposal_id"] == proposal.id
        assert (
            value["metadata"]["decision_coverage"]["historical_completeness"]
            == "unknown"
        )
        nullable = call(
            allowed,
            "business_records_discover",
            {"family": "executed_decision", "document_id": None, "record_id": None},
        )
        assert nullable.status_code == 200
        assert not nullable.json()["result"].get("isError", False)
        for token, name, args in [
            (denied, "business_records_discover", arguments),
            (
                allowed,
                "proposal_execute",
                {"proposal_id": proposal.id, "confirmed": True},
            ),
        ]:
            refused = call(token, name, args)
            assert refused.status_code == 200
            assert refused.json()["result"]["isError"] is True
