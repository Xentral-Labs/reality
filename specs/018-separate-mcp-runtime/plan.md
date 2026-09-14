# Implementation Plan: Separate MCP Runtime

**Branch**: `[018-separate-mcp-runtime]` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)
**Status**: Approved by owner on 2026-08-31

**Language**: English for all repository artifacts and review evidence.

## Summary

Move authenticated remote MCP from the Web/API application into a dedicated HTTP-only
ASGI runtime with its own public URL, bind configuration, health/readiness, process
lifecycle, database-pool budget, and Compose service. Preserve one shared application
core and one tenant/token/proposal model. Replace the internal Copilot's per-message
`stdio` subprocess with an in-process client of the same canonical tool registry used
to register HTTP MCP tools. Remove every fixed-tenant and `stdio` MCP entry point after
HTTP parity, security, and routing tests pass.

No business schema or migration is required. The deployment contract changes from one
Web/API process serving `/api` and `/mcp` to separate Web/API and MCP processes sharing
the same package, PostgreSQL records, application services, and release migration.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript only for existing settings display contracts
**Primary Dependencies**: FastAPI/Starlette ASGI, Uvicorn, MCP SDK 1.x Streamable HTTP, SQLAlchemy 2, PostgreSQL, Pydantic v2, Typer, httpx, React/Vite
**Storage**: Existing PostgreSQL business database and MCP credential records; no new tables or object-storage use
**Testing**: pytest unit/contract/ASGI integration and business stories; Compose health smoke test; frontend API/build regression; spec policy
**Project Type**: Modular-monolith application package with independently deployed Web/API, MCP, worker, and static frontend runtimes
**Constraints**: HTTP-only MCP; no `stdio`; one canonical tool registry; token subject is tenant authority; immediate database-backed revocation; proposal-before-mutation; no direct adapter ORM writes; public URL distinct from bind address; migrations run once outside runtime replicas
**Scale/Scope**: One independently restartable MCP process locally and one-or-more deployment replicas only after stateless session compatibility is proven; explicit combined PostgreSQL connection budget across Web/API, MCP, and workers

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Runtime separation does not change business records; MCP tools continue through canonical application services and existing trace results | PASS |
| Reality owns operational state | No document or transport status is added; proposals and Reality records remain authoritative | PASS |
| Proven schema only | `data-model.md` records no schema change; existing MCPAccessToken and ChangeProposal are reused | PASS |
| Tenant + shared service boundaries | Token subject establishes tenant; one tool dispatcher calls shared services; no MCP ORM writes | PASS |
| Spec/test traceability | FR/DR groups map to named contract, ASGI, security, lifecycle, Copilot, and documentation tests below | PASS |
| Explainable web behavior | Settings continue to display the exact MCP URL and token state; business traces remain shared | PASS |
| Smallest coherent design | One codebase/database and direct internal dispatcher avoid a new internal API, token vault lifecycle, broker, or second service model | PASS |

Post-design re-evaluation: all gates remain PASS. The design introduces an operational
process boundary only; it does not introduce an additional business authority or
storage system.

## Repository Structure and Layer Changes

```text
backend/src/reality/
├── agent/
│   └── mcp_chat.py              # remove stdio subprocess; use canonical dispatcher
├── cli/
│   └── app.py                   # remove `reality mcp` fixed-tenant entry point
├── db/
│   └── core.py                  # configurable bounded pool, no schema change
├── mcp/
│   ├── app.py                   # new dedicated HTTP ASGI app + health/readiness
│   ├── auth.py                  # shared current-token verifier remains authoritative
│   ├── catalog.py               # canonical exposed-tool metadata and binding registry
│   └── server.py                # authenticated HTTP registration/dispatch only
├── tools/
│   └── application.py           # canonical application handlers remain business path
└── web/
    ├── api.py                   # display shared configured MCP public URL
    └── app.py                   # remove MCP construction, lifespan and mount

backend/tests/
├── test_ai_mcp.py               # token/admin/Copilot regressions, no stdio path
├── test_mcp_http_runtime.py      # new dedicated ASGI, health, auth, parity stories
├── test_http_boundary.py        # Web/API no longer serves MCP
└── test_master_data_api.py      # exact independent MCP_URL settings contract

compose.yml                      # independent `mcp` service and health dependency
.env.example                     # public URL, bind, and pool configuration
backend/Dockerfile               # document/expose separate runtime port as needed
frontend/nginx.conf              # stop proxying `/mcp/` to Web/API
README.md                        # current/target topology becomes implemented topology
docs/WEB_SPEC.md                 # dedicated HTTP-only MCP product boundary
docs/CLI_SPEC.md                 # remove stdio/`reality mcp` contract
docs/ARCHITECTURE.md             # runtime topology and dependency direction
docs/decisions/0005-frontend-backend-object-storage.md  # superseded deployment route
backend/config/command_catalog.yaml                     # remove obsolete transport input if unused
```

**Files/layers affected**: Transport and deployment code depend inward on the shared
tool/application layer. `reality.mcp.app` owns only HTTP lifecycle and health;
`reality.mcp.server` adapts the single registry; `reality.web.app` no longer imports
MCP. The internal Copilot consumes the same registry in process and retains its
already-authorized tenant from the Chat service. No dependency points from application
services back to MCP transport types.

## Design

### Reality flow

This feature does not create or alter Source, Evidence, Fact, Commitment, Reservation,
Movement, LedgerEntry, Business Event, or Projection records. A read tool returns the
same derived and traceable result as today. A mutating tool creates the same
tenant-scoped ChangeProposal; only the existing separately authorized confirmation
executes the underlying application tool.

```text
external MCP request
  -> authenticated token subject (tenant)
  -> canonical exposed-tool binding
  -> shared application tool/service
  -> existing Source/Evidence/Reality and projection trace
```

The MCP runtime does not copy business results or audit records into its own store.

### Service and adapter flow

External clients use only authenticated Streamable HTTP:

```text
MCP client
  -> MCP_URL (dedicated origin root `/`)
  -> dedicated MCP ASGI runtime
  -> database-backed token verifier
  -> current per-tool allowlist check
  -> canonical MCP binding registry
  -> application tool/service
```

The binding registry is the single definition of each exposed MCP tool's stable name,
description, input contract, access mode, and handler adapter. Both FastMCP
registration and settings/catalog presentation derive from it. Startup and tests fail
if a catalog entry cannot bind or the registered server surface differs.

Internal Copilot no longer speaks MCP or spawns a child process. Its model-tool loop
uses the same registry to present schemas and dispatch calls in process with the Chat
service's authorized tenant. It cannot call confirmation tools unless the shared
registry/access policy explicitly permits them; existing provider failures continue to
degrade to a safe assistant response.

The HTTP application owns `/`, `/healthz`, and `/readyz`. Liveness checks process
availability without business dependencies. Readiness checks database access, token
verification prerequisites, and tool-registry integrity and returns a bounded,
non-sensitive 503 result when unavailable. The MCP SDK session-manager lifespan is
owned solely by this application.

### Configuration contract

- `MCP_URL` is the exact externally reachable dedicated origin. The protocol is served
  at `/` without a redundant path suffix. It is
  advertised in company settings and used for MCP resource/security metadata.
- `MCP_BIND_HOST` and `MCP_BIND_PORT` control only the internal listener; local defaults
  are `127.0.0.1` and `8001`, while Compose binds explicitly to `0.0.0.0`.
- `API_URL` and `APP_URL` remain independent public origins.
- Generic validated database-pool settings are set separately per runtime; the MCP
  values form an explicit bounded share of the combined connection budget.
- Production configuration rejects an unsafe or malformed MCP public URL and an
  endpoint containing any path beyond `/`. Local HTTP is allowed for localhost.
- The reverse proxy must preserve the expected external host/scheme or use an explicit,
  narrow trusted-proxy contract; allowed hosts are never widened to `*`.

See [contracts/runtime-configuration.md](contracts/runtime-configuration.md) and
[contracts/http-boundary.md](contracts/http-boundary.md).

### Data and migration impact

No Alembic migration and no new business entity are planned. Existing
`MCPAccessToken` records remain the sole credential authority, and existing
`ChangeProposal` records remain the mutation boundary. Token clear text remains
non-recoverable after creation. The MCP process uses the same released schema but never
runs migrations on replica startup.

Engine/pool configuration changes are runtime configuration only. The plan preserves
the current per-verification `last_used_at` write for semantic compatibility; its load
impact is recorded as a capacity follow-up rather than silently adding a cache that
would weaken immediate revocation.

### Failure, security, and tenant behavior

- Missing, malformed, or revoked bearer tokens receive an authentication failure
  without tenant or tool data.
- Token subject is the only tenant authority. Tool inputs cannot select a tenant.
- Tool permission is checked on every call, including an already initialized client
  after revocation or allowlist reduction.
- Cross-tenant opaque IDs use existing not-found behavior.
- Health endpoints expose no credentials, tenant IDs, catalog secrets, query results,
  or exception traces.
- A client disconnect after durable proposal creation does not undo the proposal.
  Reconciliation uses the proposal reference/list; retry behavior must not execute the
  business mutation implicitly.
- MCP failure or restart does not share a process lifecycle with Web/API. PostgreSQL
  remains shared, so pool budgets and total connection limits are observable deployment
  constraints rather than claimed failure isolation.
- Multi-replica support is not claimed until Streamable HTTP session behavior is proven
  under the chosen deployment routing. The first slice uses one runtime replica.

## Test Strategy and Traceability

Tests are added or changed before the corresponding runtime changes and observed
failing where practical.

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-004 | ASGI/story | Dedicated app serves the configured origin root; Web app returns no MCP protocol route; independent lifespan/restart smoke | MCP is mounted and started by Web/API today |
| FR-005–FR-006 | contract | Every canonical registry entry equals the registered HTTP tool name, schema, access mode, and direct-dispatch result | Catalog metadata and decorated handlers are duplicated today |
| FR-007–FR-010 | ASGI/security | Valid restricted token succeeds; absent, malformed, revoked, wrong-tool and changed-allowlist calls fail on next request | Tests target the Web-mounted route and fixed-tenant builder |
| FR-011–FR-012 | business story | Reservation/source-ingest calls create proposals only; separate approval retains current rules; adapter has no direct write path | Dedicated runtime/dispatcher does not exist |
| FR-013–FR-016 | unit/ASGI/deployment | Liveness survives mocked dependency failure; readiness returns 503; separate pool config validates; Compose health uses MCP readiness | No standalone health/readiness or pool budget exists |
| FR-017–FR-018 | contract/deployment | Old/new parity fixture before cutover; settings returns exact configured MCP_URL; final routing reaches MCP service only | URL falls back to backend and Nginx routes MCP there |
| FR-019, FR-023 | repository/ASGI | No stdio import, CLI command, module mode, docs contract, or test path remains; local client uses authenticated HTTP | Multiple stdio entry points exist |
| FR-020 | business story | Simulated disconnect after proposal creation is reconciled without implicit execution or duplicate mutation | Current HTTP disconnect behavior lacks dedicated story |
| FR-021–FR-022 | documentation | README and contracts accurately identify current implemented topology after cutover | README currently describes target as future state |
| FR-024 | unit/story | Copilot uses canonical in-process registry, never subprocess; tenant and proposal permissions remain bounded | Copilot spawns stdio server per message |
| DR-001–DR-006 | architecture/story | Cross-adapter result/trace comparison, tenant not-found tests, proposal audit, dependency-direction review | Separation and registry consolidation not present |

Full validation includes focused MCP tests, backend suite, spec policy, lint, frontend
API/build regression, and a Compose smoke run that restarts MCP while Web/API remains
healthy.

## Rollout and Rollback

1. Add the canonical binding registry, dedicated authenticated HTTP app, config
   validation, health/readiness, and tests while the current mount still exists only in
   controlled development parity coverage.
2. Add the separate Compose/deployment service with its own listener, health check,
   pool budget, and stable external `MCP_URL` routing.
3. Run all tool-schema/result/security parity tests plus token revocation and proposal
   stories against the dedicated endpoint.
4. Move local and target reverse-proxy routing for the stable MCP URL to the dedicated
   process; verify that settings advertises the same URL.
5. Remove the Web mount and MCP lifespan from Web/API, remove the frontend proxy rule,
   delete fixed-tenant/stdio entry points, and move internal Copilot to direct registry
   dispatch in the same reviewed release.
6. Verify no `/mcp/` protocol traffic reaches Web/API and the dedicated readiness probe
   is green before declaring cutover complete.

Rollback uses the previous application image and routing configuration together. No
database rollback is required because there is no schema/data migration. A rollback
must restore the prior Web mount only with the prior compatible image; permanent dual
serving is not retained because it obscures which runtime owns sessions. Existing MCP
tokens remain valid across forward and rollback deployments.

## Review Risks

- Tool metadata and actual registered schemas currently live in two places; an
  incomplete consolidation could silently remove or widen a tool.
- FastMCP owns a session-manager lifespan even in stateless HTTP mode; constructing the
  ASGI app more than once or failing to run its lifespan can break requests.
- `MCP_URL` drives both client metadata and allowed host/origin checks; incorrect proxy
  host preservation can make a healthy runtime reject legitimate clients.
- Replacing internal stdio must not give Copilot confirmation authority or create a
  parallel dispatcher with subtly different schemas/results.
- Token verification updates `last_used_at` on every request; a larger independent MCP
  workload may amplify database writes and connection pressure.
- Separate processes isolate lifecycle and CPU but still share PostgreSQL; poor pool
  budgets could degrade both runtimes.
- Removing the mounted path before independent routing and parity validation would
  create an avoidable client outage.
- Documentation contracts currently promise mounted MCP and stdio; leaving any of them
  stale would falsely advertise unsupported access.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
