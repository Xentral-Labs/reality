# Idea: Separate MCP runtime without a second business backend

**Status:** Brainstorming — not approved, not an implementation specification

## Problem

Reality currently exposes remote MCP by mounting the MCP ASGI application below
`/mcp` in the main web backend. A local `stdio` MCP server already starts as a separate
process, while the internal Copilot starts such a process for a chat interaction.

If Reality becomes one component of a larger enterprise agent, MCP becomes a distinct
machine-to-machine entry point with different traffic, session, authentication,
timeout, scaling, and exposure characteristics from the human-facing Web/API server.
Keeping both protocols in one process may couple failures and deployments even though
they share the same business behavior.

The opposite mistake would be to create a second business backend: duplicated tools,
authorization, ORM writes, projections, or domain rules would make MCP behave
differently from Web, CLI, API, and Chat.

## Proposed direction

Run MCP as a separate process and deployable adapter while keeping it in the same
repository and Python application for the first step:

```text
enterprise agent / MCP clients
              |
              v
      separate MCP runtime
              |
              v
  canonical application tools/services
              |
              v
 PostgreSQL / Business Events / Projections

browser / API clients
              |
              v
       Web/API runtime
              |
              +---- same application tools/services
```

This is initially a **runtime and deployment boundary**, not a new bounded context or
independent business service.

The MCP runtime may import the same application package and use the same disciplined
repositories and database. It must not call the Web UI, reproduce application rules,
or add MCP-only write paths. A later internal service API remains an option only when
independent ownership or stronger isolation proves its cost worthwhile.

## Three levels of separation

Keep the decision explicit:

| Level | Shape | Recommendation now |
|---|---|---|
| Process separation | Separate MCP and Web/API processes from one codebase, application layer, and database | Yes |
| Package separation | MCP adapter is an isolated package/module depending inward on application contracts | Yes, incrementally |
| Service separation | MCP calls a versioned internal API and cannot access application persistence directly | Not yet |
| Product separation | Independent MCP business model, database, tools, or rules | No |

Process separation provides most immediate operational benefits without introducing a
network hop between MCP and the application layer.

## Invariants

- MCP remains an adapter to the canonical application-tool registry.
- MCP, Web, API, CLI, and Chat invoke the same application services.
- No MCP handler performs direct ORM writes.
- MCP never owns alternative Facts, Commands, Business Events, or Projections.
- Every call is tenant-scoped through authenticated token authority; a caller cannot
  select or override the tenant in tool arguments.
- Tool allowlists, proposal creation, confirmation, and execution rules remain shared.
- Mutation tools propose first. Approval and execution require separately authorized
  application actions.
- Source → Evidence → Reality traceability remains identical across adapters.
- OperationContext is accepted or generated at the MCP boundary and propagated
  through commands, events, jobs, logs, and responses.
- Deployment topology must not change observable tool semantics.

## Runtime responsibilities

### Separate MCP runtime owns

- MCP protocol negotiation and Streamable HTTP session lifecycle;
- bearer-token extraction and MCP-specific protocol responses;
- transport security, request limits, timeouts, and MCP rate limits;
- conversion between MCP tool schemas/results and canonical application tool calls;
- MCP health/readiness endpoints and structured transport logs;
- operation/invocation context at the MCP entry boundary;
- graceful shutdown of active protocol sessions.

### Shared application layer owns

- canonical tool definitions and input/output contracts;
- tenant-scoped authorization decisions beyond transport authentication;
- reads, proposals, confirmation, execution, and audit behavior;
- business validation and transaction boundaries;
- repositories, Source/Evidence/Reality, Business Events, and projections;
- token creation/revocation services and durable authorization records;
- operation participation at durable business boundaries.

### Web/API runtime continues to own

- browser sessions and human-facing API authentication;
- settings UI and administrative endpoints for creating/revoking MCP tokens;
- normal Web/API routes, OpenAPI documentation, and frontend hosting concerns;
- human review and confirmation UI.

Token administration may remain in the Web/API runtime while token verification occurs
in MCP. Both must use the same shared token service and database records.

## Connection to the application core

### Recommended first step: in-process application imports

The MCP runtime imports the canonical application tools and opens normal
tenant-disciplined database sessions. This preserves transactions, keeps latency low,
and avoids inventing an internal API solely because two processes exist.

The dependency direction is:

```text
MCP transport -> application tool contract -> services -> repositories
```

Application services must not import MCP transport types.

### Possible later step: internal application API

Move to a private versioned API only if at least one proven requirement exists:

- MCP and core have independent release ownership or languages;
- database credentials must be removed from the MCP network zone;
- application services require centralized concurrency or transaction control;
- MCP must scale in an environment unable to import the backend package;
- multiple external adapters need the same remote application boundary;
- operational evidence shows direct shared-database deployment is the limiting risk.

If introduced, that API exposes application commands and queries, not database-shaped
CRUD. It carries tenant authority, tool permission, confirmation identity, idempotency,
and OperationContext explicitly.

## Authentication and authorization

The existing hashed, revocable, tenant-scoped MCP tokens with explicit tool allowlists
remain the basis. Separation must preserve these properties:

1. The MCP runtime verifies the bearer token through the shared verifier.
2. The token subject establishes exactly one tenant.
3. Every tool call rechecks the token's current revocation and tool permission as
   required by the security contract.
4. Tool arguments cannot provide a different tenant or widen permissions.
5. Token clear text is never stored or sent to the Web/API runtime for routine
   verification.
6. Logs record safe token identity/prefix or token record ID, never the bearer secret.
7. Rate limits may apply per token, tenant, tool category, and runtime instance without
   becoming business authorization.

If token verification uses shared PostgreSQL initially, readiness must report database
connectivity. Caching verification requires an explicit revocation-latency contract;
it must not be added implicitly for performance.

## Tool catalog and contract ownership

There must be one canonical application-tool catalog from which MCP schemas are
derived. The MCP process must not maintain a hand-copied list that can drift.

The catalog should make visible:

- stable tool name and version;
- mode: read, propose, or confirm;
- application service/handler;
- input and structured output contracts;
- required permissions and tenant behavior;
- operation-context behavior;
- deprecation and compatibility rules.

Startup should fail clearly when the MCP adapter cannot bind a catalogued tool or when
it exposes an unknown handler. Contract tests should invoke equivalent tools through
the direct application registry and MCP and compare their observable results.

## Internal Copilot relationship

The internal Copilot currently uses MCP as a discipline boundary so model calls use
the same registered tools. Separation creates two reasonable modes:

1. **Production remote mode:** Copilot connects to the separate MCP runtime using a
   short-lived or service-bound tenant authorization.
2. **Local/test stdio mode:** Copilot or developer tooling starts the same MCP adapter
   over `stdio` without exposing a network port.

Do not keep spawning a full server per chat turn in production if a managed MCP
runtime exists. Connection/session reuse, cancellation, timeout, and token authority
must be explicit. The Copilot must not gain approval permissions merely because it is
an internal client.

The enterprise agent and internal Copilot should see the same tool semantics, while
their tokens and allowlists may differ.

## Deployment and routing

Possible topology:

```text
public gateway
  +-- /api/*  -> Web/API runtime
  +-- /mcp/*  -> MCP runtime
```

Keeping the external `/mcp/` URL stable allows the process split without forcing
clients to reconfigure immediately. Alternatively, MCP may receive a dedicated host
such as `mcp.example.com` when isolation, certificates, or scaling justify it.

The MCP runtime needs its own:

- process command and container/service definition;
- liveness and dependency-aware readiness checks;
- concurrency, request-body, session, and timeout limits;
- structured logs, metrics, distributed traces, and OperationContext;
- graceful termination window for active sessions;
- deployment rollback and compatible schema expectations.

Database migrations remain owned and run once by the backend release workflow, not by
every MCP replica. MCP startup checks compatibility but does not race to migrate.

## Failure and scaling behavior

- MCP overload or protocol-session exhaustion must not consume all Web/API capacity.
- Database exhaustion can still affect both runtimes; use explicit pool budgets and
  observe combined connection limits.
- A failed MCP instance must not corrupt an application transaction; normal database
  transaction boundaries remain authoritative.
- Client disconnect or timeout does not imply that a committed mutation was rolled
  back. The returned OperationContext and proposal/action IDs support reconciliation.
- Long-running work is queued through normal jobs; MCP should return a durable
  reference instead of holding a session indefinitely.
- Scale MCP horizontally only when the selected transport's session routing and shared
  state behavior are understood. Do not assume stateless HTTP semantics.
- Health must distinguish process alive, protocol ready, database reachable, token
  verifier usable, and application catalog loaded.

## Migration path

1. Keep the current tool catalog, auth verifier, and application handlers unchanged.
2. Introduce an explicit MCP runtime entry point for authenticated Streamable HTTP.
3. Add standalone health/readiness and configuration validation.
4. Run it beside the mounted MCP route in development and execute parity tests.
5. Route a test endpoint or host to the separate runtime.
6. Verify tenant isolation, revocation, tool allowlists, proposals, OperationContext,
   disconnect behavior, and equivalent application results.
7. Move production `/mcp/` routing to the separate runtime.
8. Remove the MCP mount and session-manager lifecycle from the Web/API application.
9. Retain `stdio` as a local/developer adapter backed by the same catalog.
10. Update Web settings to render the configured public MCP URL rather than deriving it
    from the backend URL.

Removal of the old mount happens only after routing and compatibility verification. A
process split must not silently change token URLs, tool names, or client configuration.

## Smallest useful slice

1. Start the existing remote MCP server as an independent process.
2. Keep shared database-backed token verification and canonical application tools.
3. Add one read-tool and one proposal-tool parity story against mounted and standalone
   runtimes.
4. Propagate one caller OperationContext through MCP, application service, Business
   Event/proposal audit, and response.
5. Provide separate readiness and bounded database pool configuration.
6. Point a local reverse proxy or test client at the standalone runtime.
7. Prove revocation, wrong-tenant access, forbidden tool, client cancellation, and
   backend/database failure behavior.
8. Only then remove the `/mcp` mount from the Web/API process.

Out of scope for the first slice: a separate MCP repository, a second database,
duplicated application APIs, independent business rules, a new token model, changing
the MCP tool surface, or introducing a message bus solely for the process split.

## Questions to resolve before specification

1. Is the first production topology one host with path routing or a dedicated MCP
   hostname?
2. Which Streamable HTTP session state requires affinity or shared storage when MCP is
   horizontally scaled?
3. Should internal Copilot use remote MCP in production or an in-process application
   tool client while preserving the same catalog contract?
4. What are the database pool budgets for Web/API, MCP, and workers together?
5. How quickly must token revocation take effect, and is verifier caching allowed?
6. Which health dependencies block readiness versus appear only as degraded status?
7. How are public MCP URL changes rolled out without breaking configured enterprise
   agents?
8. Which operational evidence would justify a later internal application API and
   removal of database access from the MCP runtime?

## Promotion trigger

Move this idea into a numbered Spec Kit feature after selecting the target deployment
topology, internal Copilot connection mode, session-scaling expectation, database pool
budget, and public URL migration. The specification should focus on observable parity,
security, isolation, availability, and migration behavior. The plan must preserve one
canonical application core and avoid turning process separation into duplicated
business architecture.
