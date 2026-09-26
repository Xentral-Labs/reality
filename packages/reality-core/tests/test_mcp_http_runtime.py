from __future__ import annotations

from fastapi.testclient import TestClient
from reality.mcp import auth as auth_module
from reality.mcp.app import create_mcp_app
from reality.mcp.auth import create_mcp_access_token
from reality.mcp.config import MCPRuntimeSettings
from sqlalchemy.orm import sessionmaker


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
