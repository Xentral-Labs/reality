# Implementation Plan: Deployable Application Layout

**Branch**: `021-deployable-app-layout` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Move the browser product to `apps/web`, add explicit `apps/api` and `apps/mcp`
container definitions, and move the complete installable Python workspace to
`packages/reality-core`. Keep Python imports and package identity unchanged. Update
Compose, CI, Make, Spec Policy, documentation, and all active paths atomically. This
is a filesystem and deployment-boundary refactor with no business/schema change.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: One monorepo; three current deployables; one shared Python package;
approximately 300 moved files and path-only contract updates

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Files move unchanged; complete business-story suite proves the chain | PASS |
| Reality owns operational state | No domain fields, states, or derivations change | PASS |
| Proven schema only | No model or Alembic change | PASS |
| Tenant + shared service boundaries | One `reality` package remains the only service/repository authority for all adapters | PASS |
| Spec/test traceability | FR/DR map to layout policy, builds, Compose, and existing behavior suites | PASS |
| Explainable web behavior | Web source moves mechanically; UI and trace behavior remain unchanged | PASS |
| Smallest coherent design | One shared package plus thin deployable definitions; no service extraction or duplicate packages | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
apps/
  api/Dockerfile                  # Web/API image definition only
  mcp/Dockerfile                  # MCP image definition only
  web/                            # React/Vite static application and nginx config
packages/
  reality-core/
    pyproject.toml
    src/reality/                  # domain, services, tools, adapters
    migrations/                   # one PostgreSQL migration chain
    config/                       # executable catalogs
    fixtures/
    tests/                        # shared/core and adapter contract proof
    alembic.ini
```

**Files/layers affected**: `backend/` moves atomically to
`packages/reality-core/`; `frontend/` moves atomically to `apps/web/`; API and MCP
Dockerfiles become thin build definitions under `apps/`; root Compose/Make/CI/scripts
and current documentation adopt the new paths. Dependency direction remains
`domain <- services <- tools <- adapters`.

## Design

### Reality flow

No business record or relationship changes. Source → Evidence → Reality paths are
proved by the same tests after their owning filesystem path moves.

### Service and adapter flow

Both `apps/api` and `apps/mcp` images install `packages/reality-core`. Web calls API;
CLI and internal Copilot remain entry points of the shared package. Application
directories contain no business modules.

### Data and migration impact

No schema change and no migration. The Alembic directory moves with the shared
package, preserving revision contents, ordering, and runtime resource paths.

### Failure, security, and tenant behavior

All behavior is inherited unchanged from the same Python package. Existing tenancy,
MCP authorization, Web/API authentication, proposal/confirmation, and business-story
suites are required gates. Stale active paths are rejected by repository policy.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-005 | repository policy/build | `packages/reality-core/tests/test_repository_layout.py` | Old layout currently exists and deployable definitions are not explicit |
| FR-006–FR-007 | integration/config | Compose config, CI workflow, Make targets, full builds | Commands currently resolve old paths |
| FR-008 | policy | `packages/reality-core/tests/test_repository_layout.py`, Spec Policy | Active docs and scripts contain old ownership paths |
| FR-009–FR-010 | regression/integration | complete backend suite, migration suite, MCP/Web contract tests | Mechanical move must prove zero behavior/schema drift |
| FR-011–FR-012 | documentation review | README and deployment contract assertions | Current README describes backend/frontend roots |
| DR-001–DR-004 | business stories/tenancy | complete existing suite after move | Import/resource/path mistakes would break shared behavior proof |

## Rollout and Rollback

Merge as one atomic monorepo change. Build all three applications and run migrations
from the new shared path before deployment. Do not support mixed old/new repository
paths. Roll back by reverting the commit and rebuilding all images from the prior
layout; database rollback is unnecessary because migration contents do not change.

## Review Risks

- CI and policy path globs can silently omit moved files if not updated first.
- Docker build contexts can accidentally exclude catalogs, fixtures, or migrations.
- Alembic relative paths can depend on the process working directory.
- Historical specifications may legitimately describe old paths; active-path scans
  must distinguish historical evidence from current commands/contracts.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
