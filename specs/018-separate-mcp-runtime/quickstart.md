# Quickstart: Validate the Separate HTTP MCP Runtime

This guide describes the end-to-end evidence required after implementation. Commands
may be refined in tasks when the final process entry point is named.

## Prerequisites

- PostgreSQL is running and migrations are current.
- One tenant owner can sign in to Web/API settings.
- The dedicated MCP runtime is configured with a local public endpoint such as
  `http://localhost:8001/` and a separate listener on port `8001`.
- Web/API and MCP use the same application release and database schema.

## 1. Start independent runtimes

Start Web/API and MCP as separate processes or through the complete Compose profile.

Expected:

- Web/API health succeeds on its port.
- MCP `/healthz` and `/readyz` succeed on the MCP port.
- stopping MCP does not stop Web/API;
- Web/API does not answer the MCP initialize protocol at `/mcp/`.

## 2. Create a restricted credential

In company Agents & AI settings:

1. confirm that the displayed endpoint equals the configured dedicated MCP URL;
2. create a credential allowing only `exceptions_list`;
3. copy the one-time clear token.

Expected: settings never display the clear token again, and the token remains bound to
the selected tenant and allowlist.

## 3. Connect over HTTP

Configure an MCP client with the displayed URL and bearer token. Initialize the
session, list tools, and call `exceptions_list`.

Expected:

- the authorized read returns tenant-scoped structured data;
- `inventory_read` is denied for this restricted token;
- no command or client configuration uses stdio.

## 4. Verify revocation and tenant isolation

Revoke the token in company settings and repeat the request. Then create a new
restricted token and attempt to reference an opaque record belonging to another test
tenant.

Expected:

- the revoked token fails on its next protected request;
- the foreign record is rejected or behaves as not found;
- neither response reveals the other tenant or its data.

## 5. Verify proposal safety

Create a token limited to a proposal tool, call it with valid tenant-owned arguments,
and inspect pending proposals through the normal application view.

Expected:

- one durable proposal is visible;
- no reservation, ingestion, or other operational mutation occurred;
- disconnecting before the response does not execute the proposal;
- execution still needs separately authorized explicit approval.

## 6. Verify Copilot and catalog parity

Run a representative internal Copilot read and proposal request, then run the registry
parity suite.

Expected:

- Copilot starts no subprocess and imports no stdio client;
- model schemas derive from the canonical registry;
- direct Copilot dispatch and HTTP MCP return equivalent normalized results;
- every registry tool binds exactly once with the expected schema and access mode.

## 7. Verify failure isolation

Keep Web/API serving a representative read while restarting MCP. Separately simulate
database unavailability for the MCP readiness check.

Expected:

- Web/API remains alive during the MCP restart;
- MCP liveness distinguishes a running process;
- MCP readiness becomes unavailable while required dependencies are unavailable and
  recovers afterward;
- health output contains no secret or tenant data.

## 8. Run repository gates

Run the focused HTTP MCP tests first, followed by the complete backend suite, lint,
spec policy, frontend build/tests, and Compose smoke validation.

Expected: all gates pass, documentation contains no supported stdio path, and the
README describes the implemented rather than planned topology after cutover.

## Verified evidence — 2026-08-31

- Focused MCP/configuration/API suite: `47 passed, 2 skipped`.
- Complete PostgreSQL-backed backend suite after rebasing onto feature 019:
  `175 passed, 7 skipped`.
- Frontend localization tests: `9 passed`; all four language audits passed.
- Frontend production build passed (the existing large-chunk advisory remains non-blocking).
- Spec Policy passed and `docker compose config --quiet` passed.
- Current runtime/source/documentation scan found no supported stdio client, server,
  CLI command, or mounted Web/API MCP route.
- Compose declares independent Web/API and MCP processes with health/readiness wiring;
  an isolated live Compose stack passed migrations and all container health checks.
- Live endpoint checks returned MCP `healthz=ok`, `readyz=ready`, unauthenticated MCP
  initialization `401`, and no Web/API MCP protocol route (`405`).
- With the MCP container stopped, Web/API remained healthy; after MCP restart its
  readiness and Docker health both recovered to green.
- The isolated smoke stack and its test volumes were removed afterward, and the
  previously running `reality-db-1` container was restored.
- PostgreSQL pool acquisition is bounded by an executable one-second timeout proof.
- No Alembic migration or business schema change was introduced.
