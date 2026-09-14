# Research: Deployable Application Layout

## Decision: applications and shared code have different ownership roots

**Decision**: Use `apps/web`, `apps/api`, `apps/mcp`, and
`packages/reality-core`.

**Rationale**: Application directories answer “what is deployed?” while the package
directory answers “what behavior is shared?”. This mirrors the existing runtime
architecture and prevents the API name from claiming ownership of domain behavior.

**Alternatives considered**:

- Rename `backend/` to `api/`: rejected because MCP, CLI, services, migrations, and
  tests are not API-owned.
- Duplicate Python trees under API and MCP: rejected because it violates the shared
  service boundary and creates drift.
- Keep the current structure and only add documentation: rejected because explicit
  independently buildable application ownership is the requested outcome.

## Decision: one installable Python workspace moves intact

**Decision**: Move the complete current Python workspace—including `src`, tests,
migrations, catalogs, fixtures, package metadata, and Alembic configuration—to
`packages/reality-core` without changing `reality.*` imports or the distribution name.

**Rationale**: Resource lookup, editable installs, migration commands, tests, and
package data already form a coherent workspace. Moving it intact is lower risk than
splitting operational resources across new roots in the same refactor.

**Alternatives considered**:

- Move only `src/reality`: rejected because catalog and fixture packaging plus Alembic
  working-directory rules would require new abstractions with no business value.
- Rename the Python distribution/import package: rejected as unrelated churn.

## Decision: thin application-specific images

**Decision**: API and MCP each own a Dockerfile under `apps/`; both use the repository
root build context and install `packages/reality-core`. Runtime commands and exposed
ports remain application-specific.

**Rationale**: Independent image definitions make deployment ownership explicit while
retaining one source release. Root context is necessary to read both the app
Dockerfile and shared package without copying code.

**Alternatives considered**:

- One shared Dockerfile selected only by Compose command: works technically but keeps
  image ownership ambiguous.
- Independently versioned core wheel registry: deferred until release cadence proves a
  need; it adds publication and compatibility overhead.

## Decision: Web is an application, not a homepage

**Decision**: Rename `frontend/` to `apps/web`.

**Rationale**: The directory contains the complete Operations Cockpit and Business
Reality Inspector, not merely marketing pages. `web` remains accurate as product
scope grows.

## Decision: atomic cutover with stale-path enforcement

**Decision**: Update Compose, CI, Make, Spec Policy, Docker ignores, README, active
architecture/contracts, and coverage ownership in the same change. Add a deterministic
layout test and current-path scan.

**Rationale**: Temporary compatibility symlinks or dual paths hide incomplete moves
and create two supported layouts. Git preserves history across renames without them.

**Alternatives considered**:

- Compatibility symlinks: rejected because they weaken the stable ownership contract.
- Multi-release migration: rejected because repository paths are not a public runtime
  API and all consumers live in this monorepo.
