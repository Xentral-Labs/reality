# Quickstart: Validate Deployable Application Layout

Red phase completed before the move: all five repository-layout tests failed against
the retired tree, image ownership, Compose mapping, active paths, and commands.

## 1. Inspect ownership

From the repository root, confirm `apps/api`, `apps/mcp`, `apps/web`, and
`packages/reality-core` exist and that retired `backend/` and `frontend/` roots do not.

Expected: each current Compose application maps to an explicit application directory;
API and MCP contain no copied business modules.

## 2. Install and test the shared core

Create the project virtual environment, install
`./packages/reality-core[dev]`, and run pytest from `packages/reality-core`.

Expected: the complete PostgreSQL-backed suite passes, including migrations, tenancy,
MCP, API, CLI, Source/Evidence/Reality, proposals, and projections.

Result: PASS — 180 passed and 7 environment-dependent tests skipped using two workers.

## 3. Build Web

Install locked dependencies in `apps/web`, run localization tests/audit, and build the
production bundle.

Expected: all current languages pass and static assets build successfully.

Result: PASS — 9 localization contract tests passed; English, German, Dutch, and
Spanish audits passed with 775/775 keys; the production bundle built successfully.

## 4. Validate independent images

Render Compose configuration, build API and MCP images independently, and inspect
their configured commands.

Expected: each image installs the same shared core checkout; API runs on 8000 and MCP
runs on 8001 with its existing health/readiness endpoints.

Result: PASS — Compose configuration validated; API, MCP, and Web images built from
their explicit Dockerfiles. Image inspection confirmed distinct API/MCP commands and
ports while both package the same `business-reality` shared core.

## 5. Run complete stack and failure isolation

Start the complete Compose stack. Confirm Web, API, and MCP health. Stop MCP and prove
API remains healthy; restart MCP and prove readiness recovers.

Expected: independent lifecycle behavior matches feature 018.

Result: PASS — Web and API health, MCP liveness/readiness, MCP stop with API remaining
healthy, and MCP restart/readiness recovery were proven in an isolated Docker network.

## 6. Run path and policy gates

Run Spec Policy, the repository layout test, shared-core Ruff, the full shared-core
suite, web-app gates, and a current-path scan.

Expected: no active command, build, CI, or current-state documentation depends on the
retired layout, and no schema migration is introduced.

Result: PASS — 12 focused layout/policy tests, Ruff, Spec Policy, `git diff --check`,
and the active-path scan passed. Migration files are pure renames with no content
change. The initial red phase produced five expected layout-test failures before the
move; the same repository contract is now green.
