# Feature Specification: Separate MCP Runtime

**Feature Branch**: `[018-separate-mcp-runtime]`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Run remote MCP on its own public URL and runtime while preserving one shared Reality application core, and document the application topology clearly in the README."

## Context and Intent

### Problem

Remote MCP currently shares the Web/API runtime and public backend route even though
machine clients have different authentication, session, timeout, scaling, and failure
characteristics from browser and API traffic. Reality is intended to participate as a
component of a larger enterprise agent, so external agents need a stable, dedicated
MCP endpoint that can be operated independently without creating a second set of
business rules.

Splitting the process incorrectly would be worse than keeping it mounted: a duplicate
tool catalog, separate tenant logic, direct persistence writes, or alternative proposal
behavior would make MCP a second business backend. The feature must create an
operational boundary while preserving one canonical application boundary.

The repository documentation also needs to distinguish the static Web client, Web/API
runtime, remote MCP runtime, shared application core, workers, PostgreSQL, and object
storage so operators and contributors understand which component owns each concern.

### Scope

- Give authenticated remote MCP clients a dedicated, configurable public URL.
- Run remote MCP independently from the Web/API runtime while preserving the existing
  tool behavior and tenant authority.
- Keep MCP token administration in the normal company settings experience.
- Preserve the canonical application-tool and service path for MCP, Web, API, CLI, and
  Chat.
- Provide independent MCP health and readiness outcomes suitable for deployment and
  incident diagnosis.
- Offer MCP exclusively through authenticated HTTP, including local development.
- Remove all `stdio` MCP entry points and migrate internal consumers away from
  process-spawned `stdio` sessions.
- Migrate from the mounted MCP route without silently breaking configured clients.
- Document the current and intended runtime topology, storage responsibilities, URLs,
  and request paths in the repository README.

### Non-Goals

- Creating a separate MCP repository, business domain, database, or source of truth.
- Adding an internal network API between MCP and the shared application core solely
  for process separation.
- Changing the public MCP tool names, business inputs, structured results, or
  read/propose/confirm semantics.
- Replacing the existing tenant-scoped, revocable token model or human confirmation
  workflow.
- Giving the internal Copilot broader permissions or approval authority.
- Adding a message broker, distributed cache, or horizontally shared MCP session store
  without a separately proven requirement.
- Retaining an unauthenticated, fixed-tenant, or `stdio` MCP compatibility mode.
- Implementing the broader enterprise OperationContext feature beyond preserving any
  context already supported by application contracts.
- Changing Source, Evidence, Reality, Business Event, or projection semantics.

### Existing Contracts

- [`docs/ideas/separate-mcp-runtime.md`](../../docs/ideas/separate-mcp-runtime.md)
- [`specs/014-agent-interaction/spec.md`](../014-agent-interaction/spec.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md), especially the AI and MCP boundary
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/decisions/0005-frontend-backend-object-storage.md`](../../docs/decisions/0005-frontend-backend-object-storage.md)
- [`docs/CLI_SPEC.md`](../../docs/CLI_SPEC.md)
- [`AGENTS.md`](../../AGENTS.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect an enterprise agent to a dedicated MCP endpoint (Priority: P1)

As a tenant administrator, I can copy one stable MCP URL from company settings, create
a tenant-scoped token, and connect an external enterprise agent without routing its MCP
session through the human Web/API runtime.

**Why this priority**: A dedicated, usable client boundary is the purpose of the
feature and the prerequisite for all operational separation benefits.

**Independent Test**: Configure a dedicated public MCP URL, create a restricted token,
connect an MCP client, list its permitted tools, and execute a read tool successfully
while the Web/API MCP mount is not serving the request.

**Acceptance Scenarios**:

1. **Given** a tenant administrator and a configured dedicated MCP endpoint, **When**
   the administrator opens MCP settings, **Then** the exact externally reachable URL
   is displayed and can be copied without deriving it from the Web/API URL.
2. **Given** a valid tenant-scoped token with permission for one read tool, **When** an
   MCP client connects to the dedicated endpoint and calls that tool, **Then** it
   receives the same tenant-scoped result as the canonical application tool.
3. **Given** an unavailable Web/API runtime but an available MCP runtime and shared
   application dependencies, **When** an already-authorized MCP client performs a read
   that does not require Web administration, **Then** the MCP request can still
   complete.
4. **Given** the documented local developer profile, **When** a developer starts the
   stack and connects an MCP client, **Then** the client uses the local authenticated
   HTTP endpoint and the same canonical tool behavior as production.
5. **Given** a command, module invocation, or internal Copilot path that previously
   started MCP over `stdio`, **When** feature 018 is complete, **Then** that path is
   removed or uses the authenticated HTTP endpoint and no `stdio` transport remains.

### User Story 2 - Preserve tenant and mutation safety across the split (Priority: P1)

As a tenant administrator and reviewer, I need MCP tokens, tool allowlists, proposals,
and approvals to retain exactly the same security behavior after MCP moves to its own
runtime.

**Why this priority**: Process isolation is unacceptable if it weakens tenant scope,
authorization, or the proposal-before-mutation invariant.

**Independent Test**: Exercise valid, revoked, malformed, wrong-tool, and cross-tenant
token cases against the dedicated endpoint, then create a mutation proposal and prove
that no operational mutation occurs until a separately authorized confirmation.

**Acceptance Scenarios**:

1. **Given** an absent, malformed, or revoked token, **When** a client calls the MCP
   endpoint, **Then** access is denied without revealing tenant or business data.
2. **Given** a valid token lacking permission for a requested tool, **When** the tool is
   called, **Then** the call is denied even if the tool appeared in another tenant's or
   client's catalog.
3. **Given** a token bound to tenant A, **When** its client supplies an identifier from
   tenant B or attempts to select tenant B, **Then** the record behaves as not found or
   the request is rejected without disclosure.
4. **Given** a mutation-oriented MCP tool, **When** it is called successfully, **Then**
   it creates only a reviewable proposal and no business mutation occurs before a
   separately authorized approval.
5. **Given** a token revoked through Web/API settings, **When** it is used for a later
   MCP call, **Then** it no longer authorizes the call according to the existing
   immediate revocation contract.

### User Story 3 - Operate and diagnose MCP independently (Priority: P2)

As an operator, I can deploy, monitor, restart, and scale the MCP boundary separately
from Web/API traffic and can distinguish an alive process from one unable to serve
authenticated application tools.

**Why this priority**: The split creates value only when it provides observable failure
and capacity isolation rather than an additional opaque process.

**Independent Test**: Observe MCP liveness and readiness during normal operation and
while separately making the database, token verifier, or tool catalog unavailable;
restart MCP without restarting Web/API and verify clean recovery.

**Acceptance Scenarios**:

1. **Given** a started MCP runtime with all required dependencies, **When** an operator
   checks readiness, **Then** it reports ready independently from Web/API health.
2. **Given** an alive MCP process whose business database or token verifier is
   unavailable, **When** readiness is checked, **Then** it reports not ready while
   liveness continues to distinguish the process from a crash.
3. **Given** an MCP restart or deployment, **When** Web/API users continue working,
   **Then** normal Web/API traffic remains available and does not share the MCP process
   lifecycle.
4. **Given** an MCP client disconnect or timeout around a proposal call, **When** the
   client reconnects, **Then** it can reconcile the outcome using returned or durable
   proposal/operation references without assuming rollback or repeating a mutation.

### User Story 4 - Migrate clients without semantic drift (Priority: P2)

As an administrator or integration owner, I can move from the backend-mounted MCP
route to the dedicated endpoint with a controlled compatibility check and without
unexpected tool or authorization changes.

**Why this priority**: A process split must not strand configured enterprise agents or
silently change what their credentials can do.

**Independent Test**: Run a representative read and proposal tool against the old and
new routes, compare observable outputs and security behavior, switch the configured
public URL, and verify that only the dedicated runtime serves the final endpoint.

**Acceptance Scenarios**:

1. **Given** the mounted and dedicated endpoints during a controlled transition,
   **When** the parity suite calls every catalogued MCP tool it is authorized to use,
   **Then** tool names, schemas, modes, tenant behavior, and observable application
   results match.
2. **Given** a dedicated endpoint that has passed parity and security checks, **When**
   routing is switched, **Then** company settings display the dedicated URL and new
   clients need no knowledge of the Web/API address.
3. **Given** completion of the migration, **When** the Web/API runtime starts, **Then**
   it does not start or mount the remote MCP session runtime.
4. **Given** an incompatible or unavailable dedicated endpoint, **When** migration
   validation runs, **Then** the old route is not removed and the failure is visible to
   operators.

### User Story 5 - Understand the application topology (Priority: P3)

As a contributor or operator, I can read the repository README and understand how
frontend, Web/API, MCP, workers, PostgreSQL, and object storage relate, which public URL
reaches each boundary, and which components share application rules.

**Why this priority**: Clear topology prevents accidental duplication of business
logic and incorrect deployment assumptions.

**Independent Test**: Give the README to a reviewer unfamiliar with the change and
verify that they can identify every runtime, storage owner, public entry point, and the
shared application path without inspecting source code.

**Acceptance Scenarios**:

1. **Given** the repository README, **When** a contributor reviews its architecture
   section, **Then** it clearly distinguishes deployable runtimes from shared code and
   storage.
2. **Given** the feature is specified but not yet implemented, **When** the README is
   read, **Then** it distinguishes current local behavior from the planned separate MCP
   deployment and does not claim unfinished behavior exists.
3. **Given** production deployment guidance, **When** an operator identifies public
   URLs, **Then** frontend, Web/API, and MCP URLs are independently configurable and
   their responsibilities are unambiguous.

### Edge Cases

- The dedicated public MCP URL is absent, empty, malformed, uses an unsafe production
  scheme, contains an inconsistent path, or differs from the externally routed host.
- A reverse proxy forwards a different host or scheme from the configured public MCP
  URL.
- The MCP process is alive while PostgreSQL, token verification, or the tool catalog is
  unavailable.
- Web/API token administration succeeds immediately before or after MCP checks token
  revocation.
- A client holds a long-lived session while its token is revoked or its allowlist is
  reduced.
- A token authorizes a tool removed or renamed between compatible deployments.
- The MCP client disconnects after a proposal is durably created but before receiving
  its response.
- MCP and Web/API together exhaust the shared database connection budget even though
  their process capacity is isolated.
- A deployment starts multiple MCP replicas without compatible session behavior.
- The old mounted route and dedicated route accidentally serve simultaneously after
  migration completion.
- A local developer attempts to connect without first creating an authenticated MCP
  credential.
- An old client configuration attempts to start or connect through `stdio` after the
  migration.
- An operator confuses the MCP public URL with the internal bind address.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support a dedicated, explicitly configured public URL for
  authenticated remote MCP that is independent of the Web/API public URL.
- **FR-002**: Company settings MUST display the effective external MCP URL exactly as
  clients should configure it. The dedicated MCP origin MUST serve the protocol at its
  root and MUST NOT require a redundant `/mcp/` suffix.
- **FR-003**: Remote MCP MUST be operable in a process lifecycle independent from the
  Web/API runtime.
- **FR-004**: After migration completion, the Web/API runtime MUST NOT mount, start, or
  manage the remote MCP session runtime.
- **FR-005**: The dedicated MCP runtime MUST expose the canonical MCP tool catalog
  without a separately maintained duplicate catalog.
- **FR-006**: Every MCP tool MUST retain the same name, input contract, access mode,
  tenant behavior, and observable application result across the process split.
- **FR-007**: The dedicated runtime MUST authenticate remote calls with the existing
  hashed, revocable, tenant-scoped MCP credentials.
- **FR-008**: The authenticated credential subject MUST determine the tenant; MCP tool
  input MUST NOT select, override, or widen tenant authority.
- **FR-009**: The dedicated runtime MUST enforce the credential's current explicit tool
  allowlist on every protected tool call.
- **FR-010**: Revoking an MCP credential through company settings MUST prevent its
  subsequent use according to the existing revocation behavior, without requiring a
  separate MCP credential store.
- **FR-011**: Mutation-oriented MCP tools MUST continue to create proposals only, and
  business mutation MUST require the existing separately authorized confirmation.
- **FR-012**: MCP tools MUST execute through canonical application tools and services;
  the MCP boundary MUST NOT perform direct business persistence writes or alternative
  business validation.
- **FR-013**: The MCP runtime MUST report liveness independently from readiness to serve
  authenticated application tools.
- **FR-014**: Readiness MUST fail visibly when required application dependencies,
  credential verification, or the canonical tool catalog cannot support calls.
- **FR-015**: Operators MUST be able to restart or deploy MCP without restarting the
  Web/API runtime, and an MCP runtime failure MUST NOT directly terminate Web/API.
- **FR-016**: MCP and Web/API MUST have separately configurable resource and connection
  budgets so independent processes do not imply unlimited shared-database use.
- **FR-017**: The migration MUST include an observable parity check before the mounted
  route is removed.
- **FR-018**: The system MUST preserve a stable externally configured MCP URL during
  routing changes unless an administrator intentionally changes that URL.
- **FR-019**: MCP MUST be exposed exclusively through authenticated HTTP in production,
  local development, tests, and internal MCP-consuming application paths.
- **FR-020**: Client disconnects, timeouts, and retries MUST NOT bypass proposal,
  confirmation, idempotency, or durable outcome reconciliation rules.
- **FR-021**: The README MUST document the deployable runtime boundaries, shared
  application core, storage responsibilities, request paths, public URL configuration,
  current local topology, and planned dedicated MCP topology.
- **FR-022**: Documentation MUST distinguish implemented behavior from the target state
  until migration completion.
- **FR-023**: The feature MUST remove `stdio` MCP commands, module entry points,
  process-spawn behavior, configuration guidance, and transport-specific tests that
  would imply continued support.
- **FR-024**: If the internal Copilot continues to use MCP, it MUST connect through the
  authenticated HTTP boundary with tenant authority no broader than its intended tool
  access; it MUST NOT spawn a local MCP subprocess.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality is unchanged by this transport/runtime
  feature; every MCP result and proposal MUST retain the same shortest true trace
  exposed by the canonical application service.
- **DR-002**: MCP credentials, tool definitions, proposals, actions, Business Events,
  and operation references remain authoritative in their existing shared records; the
  process boundary MUST NOT duplicate them in an MCP-owned business store.
- **DR-003**: Every credential lookup, tool call, proposal, confirmation, and trace read
  MUST enforce tenant scope through shared services and disciplined repositories.
- **DR-004**: Web, API, CLI, Chat, and HTTP MCP MUST converge on the same
  application-tool behavior; transports MUST NOT become alternative rule engines.
- **DR-005**: Human-readable URLs, tool labels, credential prefixes, and business
  numbers MUST NOT become internal identity or authorization.
- **DR-006**: Any operation/invocation context supported at the MCP boundary MUST be
  passed through shared application contracts and MUST NOT be copied into arbitrary
  domain fields or treated as business identity.

### Key Entities

- **MCP Endpoint Configuration**: The externally reachable MCP address presented to
  clients, distinct from internal process binding and the Web/API address.
- **MCP Runtime**: The independently operated protocol boundary that authenticates
  clients and adapts canonical application tools without owning business rules.
- **MCP Access Credential**: Existing hashed, revocable, tenant-scoped authority with
  an explicit tool allowlist; clear text is shown only when created.
- **Canonical Tool Definition**: Shared tool name, contract, access mode, and handler
  used consistently by MCP and other application adapters.
- **Readiness Result**: Operational evidence that the MCP boundary and required shared
  dependencies can currently serve authenticated tool calls.
- **Change Proposal**: Existing durable preview of a requested mutation that remains
  inert until separately authorized execution.

## Success Criteria *(mandatory)*

- **SC-001**: An administrator can copy the dedicated MCP URL, issue a restricted
  credential, and complete an authorized read from a newly configured external client
  in under five minutes without using the Web/API URL as the MCP endpoint.
- **SC-002**: One hundred percent of catalogued MCP tools pass contract-parity checks
  for names, inputs, access modes, tenant outcomes, and application results before the
  mounted route is removed.
- **SC-003**: All tested absent, malformed, revoked, wrong-tool, and cross-tenant
  credential cases are denied without disclosed business data.
- **SC-004**: All tested mutation-oriented MCP calls create no operational mutation
  before a separately authorized confirmation.
- **SC-005**: Operators can restart the MCP boundary while an independent Web/API
  health check and representative read remain available throughout the MCP restart.
- **SC-006**: MCP liveness and readiness identify process failure and required-
  dependency failure as different observable states in every defined failure scenario.
- **SC-007**: After routing migration, all external MCP test traffic reaches the
  dedicated boundary and no remote MCP session is served by the Web/API runtime.
- **SC-008**: A reviewer unfamiliar with the implementation can use the README alone to
  correctly identify all deployable runtimes, both storage responsibilities, shared
  application behavior, and the current versus target MCP topology.
- **SC-009**: Every FR and DR has an acceptance scenario and executable proof or a
  reviewed documentation check identified during planning.
- **SC-010**: Repository and end-to-end checks find zero supported MCP startup,
  connection, documentation, or internal-consumer paths using `stdio`; every exercised
  MCP client uses authenticated HTTP.

## Assumptions and Dependencies

- The target production topology uses a dedicated MCP hostname or otherwise independent
  public URL; the exact domain is deployment-specific.
- The public MCP URL is configuration, not derived from the Web/API URL. The local
  default may use a separate localhost port.
- MCP and Web/API initially share the same application package, PostgreSQL business
  database, credential records, and migrations.
- Database migrations remain a single release responsibility and are not independently
  run by every MCP process.
- Existing remote tokens and allowlists remain compatible unless a later migration
  requirement explicitly changes them.
- Token revocation remains effective without an unspecified long-lived cache.
- Local development uses the same authenticated HTTP MCP contract as production, with
  a local public URL and locally issued tenant-scoped credentials.
- Horizontal MCP scaling is not required to complete the first slice; the runtime must
  nevertheless avoid claiming safe multi-replica behavior until session semantics are
  proven.
- The enterprise OperationContext Idea is not yet an approved implementation feature;
  this split preserves compatible context fields but does not implement that whole
  concept.
- Deployment routing and TLS termination are environment responsibilities, while the
  application validates and advertises its externally reachable MCP URL.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-004 | US1.1–US1.3, US4.2–US4.3 | Dedicated endpoint, independent lifecycle, and removed-mount integration stories |
| FR-005–FR-006 | US1.2, US4.1 | Full tool-catalog parity contract suite |
| FR-007–FR-010 | US2.1–US2.3, US2.5 | Remote credential, revocation, allowlist, and tenant-boundary tests |
| FR-011–FR-012 | US2.4, US4.1 | Proposal-only mutation and shared-tool parity tests |
| FR-013–FR-016 | US3.1–US3.3 | Liveness/readiness, restart isolation, and resource-configuration checks |
| FR-017–FR-018 | US4.1–US4.4 | Migration parity, routing, rollback, and stable-URL evidence |
| FR-019, FR-023–FR-024 | US1.4–US1.5 | HTTP-only transport, removed-stdio, and internal-client migration tests |
| FR-020 | US3.4 | Disconnect/timeout reconciliation tests |
| FR-021–FR-022 | US5.1–US5.3 | README topology review checklist |
| DR-001–DR-006 | US1–US5 | Shared-service, trace, identity, context, and tenant architecture review plus cross-adapter tests |
| SC-001–SC-010 | All | End-to-end acceptance report and requirement coverage audit |
