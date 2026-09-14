# Feature Specification: Deployable Application Layout

**Feature Branch**: `021-deployable-app-layout`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Make deployable Web, API, and MCP units obvious and independently buildable while retaining one shared application core."

## Context and Intent

### Problem

Reality already operates Web, API, and MCP independently, but the repository still
groups the complete Python application under `backend/` and the browser product under
`frontend/`. A new contributor cannot identify deployable units from the top-level
layout, and API/MCP container ownership appears coupled even though their runtime
lifecycles are separate. Renaming `backend/` to `api/` would be misleading because it
also owns the shared domain, services, tools, CLI, migrations, fixtures, and tests.

### Scope

- Make every currently deployed process visible under one `apps/` boundary.
- Put the shared Python application package under a neutral `packages/` boundary.
- Give API and MCP explicit, independent image definitions that consume the same core.
- Preserve current commands, migrations, tests, public URLs, runtime behavior, and
  business semantics while updating all build, CI, documentation, and developer paths.
- Keep one source of truth for domain rules, repositories, application services,
  canonical tools, events, and projections.

### Non-Goals

- Splitting Reality into independently versioned repositories or Python distributions.
- Duplicating services, models, repositories, configuration, or tests per adapter.
- Changing database schema, public API/MCP contracts, authentication, tenant behavior,
  user-visible Web behavior, or AWS topology.
- Adding placeholder applications that are not deployable today.

### Existing Contracts

- [Architecture](../../docs/ARCHITECTURE.md)
- [Web product](../../docs/WEB_SPEC.md)
- [CLI contract](../../docs/CLI_SPEC.md)
- [Deployment boundary ADR](../../docs/decisions/0005-frontend-backend-object-storage.md)
- [Separate MCP runtime](../018-separate-mcp-runtime/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify deployable units immediately (Priority: P1)

As a contributor or operator, I can inspect the repository root and immediately see
the Web, API, and MCP applications, their build definitions, and the shared core they
consume.

**Why this priority**: The layout must communicate the actual runtime architecture
without requiring source-code archaeology or misleading names.

**Independent Test**: Inspect the repository tree and README, then map every Compose
service to exactly one application directory and the shared core package.

**Acceptance Scenarios**:

1. **Given** a new checkout, **When** a contributor lists top-level application and
   package directories, **Then** Web, API, MCP, and the shared Reality core have
   unambiguous names and documented ownership.
2. **Given** the API and MCP applications, **When** their build definitions are
   inspected, **Then** each has an explicit image boundary and both consume the same
   shared Python package rather than copied business code.
3. **Given** a repository search, **When** obsolete `backend/` and `frontend/` ownership
   claims are checked, **Then** no active build, CI, command, or current-state document
   relies on the retired layout.

### User Story 2 - Build and operate applications independently (Priority: P1)

As an operator, I can build, start, stop, and diagnose API and MCP independently while
their shared release remains compatible with migrations and Web.

**Why this priority**: Directory clarity is valuable only if the deployment units are
real and independently verifiable.

**Independent Test**: Build both images from their application definitions, start the
complete stack, stop MCP while API remains healthy, and verify MCP recovery.

**Acceptance Scenarios**:

1. **Given** the repository build context, **When** API and MCP images are built, **Then**
   each image contains the same release of the shared core and its own runtime command.
2. **Given** a healthy stack, **When** MCP is stopped or restarted, **Then** API remains
   healthy and MCP readiness recovers independently.
3. **Given** an incompatible or incomplete directory move, **When** quality gates run,
   **Then** stale paths or missing build inputs fail deterministically before merge.

### User Story 3 - Keep one coherent developer workflow (Priority: P2)

As a developer or coding agent, I can install, test, migrate, build, and run Reality
using documented commands after the move without learning adapter-specific business
implementations.

**Why this priority**: A professional layout must improve comprehension without making
the common development loop fragile.

**Independent Test**: Follow the README from a clean checkout through Python install,
migration, backend tests, frontend tests/build, and Compose validation.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** the documented setup commands are followed,
   **Then** all package, migration, test, Web, API, and MCP paths resolve successfully.
2. **Given** CLI, API, MCP, and internal Copilot calls, **When** representative reads and
   proposals run, **Then** they still invoke the same application services and preserve
   tenant and confirmation behavior.

### Edge Cases

- A build cache contains files from the retired directory layout.
- A CI path filter or Spec Policy coverage row still names the retired location.
- Alembic is invoked from the repository root versus the shared package directory.
- Editable Python installation and Docker installation resolve resources differently.
- A generated frontend artifact or Python cache appears during the move.
- An ignored local `.env` must remain local while example paths change.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST group every current deployable application under an
  explicit application boundary with stable names `web`, `api`, and `mcp`.
- **FR-002**: The repository MUST place shared Python domain, service, repository, tool,
  event, projection, CLI, migration, fixture, and test assets under one neutral shared
  core boundary rather than an adapter-named directory.
- **FR-003**: API and MCP MUST each have an explicit independently buildable image
  definition and runtime command.
- **FR-004**: API and MCP image builds MUST consume the same shared core source and MUST
  NOT copy or fork business behavior between application directories.
- **FR-005**: Web MUST remain an independently buildable static application and MUST
  continue to access business behavior only through API contracts.
- **FR-006**: Compose MUST map each deployable service to its named application build
  definition while preserving independent health, readiness, ports, dependencies, and
  bounded database pools.
- **FR-007**: Local setup, migration, test, lint, frontend, Docker, and CI commands MUST
  work from documented paths after the move.
- **FR-008**: Current-state documentation and repository policy MUST reject stale active
  references to the retired `backend/` and `frontend/` layout, excluding historical
  specifications and migration explanations that are explicitly labeled historical.
- **FR-009**: The move MUST preserve public Web, API, and MCP URLs and all observable
  protocol, authentication, authorization, proposal, and confirmation behavior.
- **FR-010**: The move MUST preserve the PostgreSQL migration chain without adding a
  schema migration or changing stored business data.
- **FR-011**: Release and rollback instructions MUST treat application layout and shared
  core paths as one atomic repository release so mixed old/new filesystem layouts are
  not presented as supported.
- **FR-012**: The root README MUST let a new contributor identify all deployable units,
  the shared core, and the commands for building and running them without inspecting
  implementation source.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality is unchanged; the filesystem move MUST NOT
  alter records, provenance, shortest true links, or derived-state ownership.
- **DR-002**: CLI, API, Web, MCP, Chat, and workers MUST continue to converge on the same
  application services and canonical tools with no direct adapter ORM writes.
- **DR-003**: Every business query, mutation proposal, confirmation, and persistence
  operation MUST retain existing tenant scope and cross-tenant non-disclosure behavior.
- **DR-004**: Human-facing application and directory names MUST remain deployment
  metadata only and MUST NOT become business identity or stored domain state.

## Success Criteria *(mandatory)*

- **SC-001**: A reviewer can map 100% of current Compose application services to one
  named `apps/` directory and the shared Python dependency in under two minutes.
- **SC-002**: API, MCP, and Web build independently from a clean checkout with no copied
  domain/service modules across application directories.
- **SC-003**: The complete existing backend and frontend test/build gates pass after the
  move with zero behavioral expectation changes.
- **SC-004**: A repository scan reports zero stale active build, CI, command, or
  current-state documentation references to the retired layout.
- **SC-005**: Every FR and DR has an acceptance scenario, an implementation task, and
  executable proof or an explicit reviewed documentation proof.

## Assumptions and Dependencies

- `apps/web`, `apps/api`, `apps/mcp`, and `packages/reality-core` are the approved stable
  names; `homepage` is rejected because Web contains the full product, not only a page.
- The repository remains a monorepo with one release version and one shared lockstep
  compatibility boundary.
- Python import paths remain `reality.*`; only repository ownership paths change.
- Tests stay with the shared core because they prove shared application behavior.
- Alembic migrations, fixtures, catalogs, and package metadata stay with the shared core
  to preserve resource resolution and keep the move mechanical.
- No new dependency or database is required.

## Open Questions

None. Product scope and stable directory names were approved by the owner on 2026-08-31.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005 | US1 scenarios 1–3; US2 scenario 1 | Repository layout and independent image build tests |
| FR-006–FR-007 | US2 scenarios 1–3; US3 scenario 1 | Compose validation, complete backend/frontend gates |
| FR-008 | US1 scenario 3 | Spec Policy active-path scan |
| FR-009–FR-010 | US2 scenarios 1–2; US3 scenario 2 | Existing contract suites and migration tests |
| FR-011–FR-012 | US1 scenario 1; US3 scenario 1 | README/release documentation review |
| DR-001–DR-004 | US3 scenario 2 | Existing business-story, tenancy, and adapter-equivalence suites |
