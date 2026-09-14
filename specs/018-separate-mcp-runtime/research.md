# Research: Separate MCP Runtime

## Decision 1: Separate process, shared application core and database

**Decision**: Run remote MCP as its own HTTP process from the existing backend package.
It imports the same canonical application tools and uses the existing tenant-scoped
repositories and PostgreSQL records.

**Rationale**: This isolates protocol lifecycle, traffic, deployment, and resource
budgets without introducing a second business authority or an unnecessary internal
network hop.

**Alternatives considered**:

- Keep MCP mounted in Web/API: rejected because it couples machine sessions and failure
  lifecycle to human/API traffic.
- Create an internal HTTP application API: rejected for the first slice because it adds
  network authentication, versioning, latency, and failure modes without independent
  ownership or security-zone evidence.
- Separate repository/database: rejected because it would duplicate business rules,
  tokens, proposals, and traceability.

## Decision 2: HTTP-only MCP, including local development

**Decision**: Remove every stdio and fixed-tenant MCP entry point. Production, local
development, tests, and external clients use authenticated Streamable HTTP.

**Rationale**: The owner requires one supported access mode. One authenticated
transport reduces ambiguous tenant authority, divergent startup behavior, and
documentation/test surface.

**Alternatives considered**:

- Retain stdio for developers: rejected by the approved scope.
- Retain fixed-tenant unauthenticated localhost HTTP: rejected because it preserves the
  same alternate authority model under another transport.

## Decision 3: Internal Copilot dispatches tools in process

**Decision**: The internal Copilot stops being an MCP client and uses the canonical
exposed-tool registry directly with the tenant already authorized by the Chat service.

**Rationale**: Existing MCP bearer tokens are intentionally hash-only and cannot be
recovered. Making the multi-tenant Web/API process call MCP over HTTP would require a
new retrievable service-token lifecycle, rotation, and tenant delegation model. Direct
registry dispatch keeps the same schemas, handlers, proposal rules, and tenant scope
without a network hairpin.

**Alternatives considered**:

- Issue and vault a per-tenant internal MCP token: rejected as new security/data scope
  with no user value for an in-process caller.
- Give Copilot a broad platform token: rejected because it violates tenant least
  authority.
- Keep spawning stdio: rejected by the HTTP-only requirement and process overhead.

## Decision 4: One canonical exposed-tool binding registry

**Decision**: Consolidate exposed name, description, input contract, access mode, and
handler adapter into one registry. HTTP MCP registration, settings metadata, allowlist
validation, parity tests, and internal Copilot tool schemas derive from it.

**Rationale**: The current metadata catalog and manually decorated server handlers can
drift. Runtime separation increases the cost of that drift, so the boundary must fail
closed when catalog and registrations disagree.

**Alternatives considered**:

- Keep two lists and add only a name assertion: rejected because input schema and access
  mode could still diverge.
- Generate business application tools from MCP: rejected dependency direction; MCP is
  an adapter and must depend inward.

## Decision 5: Dedicated ASGI application with separate liveness/readiness

**Decision**: Add one MCP HTTP application owning the SDK session-manager lifespan,
protocol endpoint, liveness endpoint, and dependency-aware readiness endpoint.

**Rationale**: A separate process needs probes that distinguish a running process from
one unable to authenticate or execute tools. The installed MCP SDK supports custom
HTTP routes and an ASGI lifespan around its session manager.

**Alternatives considered**:

- Use only process/container status: rejected because database or registry failure
  would appear healthy.
- Put health endpoints in Web/API: rejected because they would measure the wrong
  runtime.

## Decision 6: Public URL and bind address are separate configuration

**Decision**: `MCP_URL` is the exact advertised endpoint. Separate bind host/port
settings control the listener. Local public default is on port 8001; production
requires an externally valid secure URL.

**Rationale**: Public scheme/host/path determine client and resource-security metadata,
while containers normally bind an internal address. Conflating them breaks reverse
proxy deployments.

**Alternatives considered**:

- Infer MCP URL from API_URL: rejected because the runtimes and domains are
  intentionally independent.
- Infer bind address from MCP_URL: rejected because external DNS/TLS does not describe
  the container listener.
- Allow any forwarded host: rejected because it weakens transport host/origin checks.

## Decision 7: No schema migration; preserve immediate revocation

**Decision**: Reuse MCPAccessToken and ChangeProposal unchanged. Verify current token
state for protected calls and retain the current `last_used_at` audit update.

**Rationale**: The feature changes runtime topology, not credential or proposal
semantics. Caching would introduce a new revocation-latency contract.

**Alternatives considered**:

- Add an MCP-owned token store: rejected as duplicated authority.
- Cache token verification: deferred until measured load proves the database write/read
  cost and a revocation SLA is approved.

## Decision 8: Controlled cutover, no permanent dual serving

**Decision**: Prove parity with the dedicated runtime, move stable URL routing, then
remove the Web mount and stdio paths. Rollback restores the prior image and route as a
unit.

**Rationale**: Temporary parity validation reduces migration risk, but permanent dual
serving makes session ownership, observability, and incident diagnosis ambiguous.

**Alternatives considered**:

- Big-bang removal without parity: rejected because existing clients and tokens need
  evidence of compatibility.
- Keep both endpoints indefinitely: rejected because it defeats lifecycle separation.
