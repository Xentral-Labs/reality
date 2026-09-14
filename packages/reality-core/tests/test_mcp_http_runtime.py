from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.mcp import auth as auth_module
from reality.mcp.app import create_mcp_app
from reality.mcp.auth import create_mcp_access_token
from reality.mcp.config import MCPRuntimeSettings


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
