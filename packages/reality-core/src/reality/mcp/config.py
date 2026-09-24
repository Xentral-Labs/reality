from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class MCPRuntimeSettings:
    """Validated public and listener configuration for the HTTP-only MCP runtime."""

    public_url: str
    bind_host: str
    bind_port: int
    authorization_issuer: str = "http://127.0.0.1:8000"

    @classmethod
    def from_environ(
        cls, environ: Mapping[str, str] = os.environ
    ) -> MCPRuntimeSettings:
        public_url = (environ.get("MCP_URL") or "http://localhost:8001/").strip()
        parsed = urlparse(public_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("MCP_URL must be an absolute HTTP URL.")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("MCP_URL must use the origin root without an extra path.")
        if (
            environ.get("REALITY_ENV", "").lower() in {"production", "prod"}
            and parsed.scheme != "https"
        ):
            raise ValueError("MCP_URL must use HTTPS in production.")

        authorization_issuer = (
            environ.get("MCP_AUTHORIZATION_ISSUER") or "http://127.0.0.1:8000"
        ).strip().rstrip("/")
        issuer = urlparse(authorization_issuer)
        if issuer.scheme not in {"http", "https"} or not issuer.netloc:
            raise ValueError("MCP_AUTHORIZATION_ISSUER must be an absolute HTTP URL.")
        if issuer.path not in {"", "/"} or issuer.query or issuer.fragment:
            raise ValueError("MCP_AUTHORIZATION_ISSUER must use the origin root.")
        if (
            environ.get("REALITY_ENV", "").lower() in {"production", "prod"}
            and issuer.scheme != "https"
        ):
            raise ValueError("MCP_AUTHORIZATION_ISSUER must use HTTPS in production.")

        bind_host = (environ.get("MCP_BIND_HOST") or "127.0.0.1").strip()
        if not bind_host:
            raise ValueError("MCP_BIND_HOST must not be empty.")
        try:
            bind_port = int(environ.get("MCP_BIND_PORT") or "8001")
        except ValueError as error:
            raise ValueError("MCP_BIND_PORT must be an integer.") from error
        if not 1 <= bind_port <= 65535:
            raise ValueError("MCP_BIND_PORT must be between 1 and 65535.")

        return cls(
            public_url=public_url.rstrip("/") + "/",
            bind_host=bind_host,
            bind_port=bind_port,
            authorization_issuer=authorization_issuer,
        )


def configured_mcp_url(environ: Mapping[str, str] = os.environ) -> str:
    """Return the exact independently configured public MCP endpoint."""

    return MCPRuntimeSettings.from_environ(environ).public_url
