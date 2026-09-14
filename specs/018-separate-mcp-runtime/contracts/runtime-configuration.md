# Contract: MCP Runtime Configuration

## Public endpoint

`MCP_URL` is the exact URL copied into an MCP client and shown in company settings.

Contract:

- absolute HTTP URL for local development;
- secure HTTPS URL in production;
- uses the dedicated origin root without an additional endpoint path;
- independent from `API_URL` and `APP_URL`;
- drives resource-server metadata and narrow allowed external host/origin checks;
- never interpreted as the process bind address.

Local example: `MCP_URL=http://localhost:8001/`

Production example: `MCP_URL=https://mcp.runreality.ai/`

## Listener

`MCP_BIND_HOST` and `MCP_BIND_PORT` configure only the runtime listener. The local
default host is loopback; Compose explicitly binds `0.0.0.0`. The default port is
`8001`. Bind values are not shown to clients and do not establish tenant authority.

## Database and pool budget

The MCP runtime receives `REALITY_DATABASE_URL` like other application processes and
uses generic, separately configured bounded pool size, overflow, and acquisition
timeout values. Implementation must use a shared engine-settings function rather than
adding MCP-only engine construction.

Validation rejects invalid or unbounded values. Deployment documents the maximum
aggregate connections across Web/API, MCP, workers, migrations, and operator tools.

## Proxy contract

- TLS may terminate at a trusted reverse proxy/load balancer.
- The MCP runtime safely observes the configured public scheme and host for protocol
  metadata and host/origin validation.
- Proxy routing sends only the MCP endpoint and probes to the MCP runtime.
- `/api/*` and browser routes continue to target their existing owners.
- Wildcard allowed hosts/origins are not an acceptable production fix.

## Invalid configuration

The MCP runtime fails startup with a safe, actionable message when the public URL,
endpoint path, listener, or required database configuration is invalid. Company
settings do not fall back to `API_URL` after feature 018 is complete.
