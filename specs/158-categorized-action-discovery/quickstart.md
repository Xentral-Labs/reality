# Validation Guide

From the active worktree run `make spec-check`, `make lint`, `make test`, and
`make web-build`. Run the new browser script against a separate Vite server using
`BASE_URL`, `PLAYWRIGHT_MODULE`, and optional `PLAYWRIGHT_EXECUTABLE`.

Open Inspector → Actions → Action catalog. Expand Warehouse → Movements, inspect
both entry types, search a hidden command, clear search, and check restored branches.
Repeat at 390px and in German. Open every Warehouse tab on an empty register; inspect
its local action menu. Check Finance customer and supplier directions on all tabs;
supplier contexts must not launch customer-only credit or refund flows. Opening menus
and forms must not send business mutation requests. Use existing form regressions for
confirmation, stale state, tenant and retry behavior.

## Fixture and repeatable checks

Production classification is `packages/reality-core/config/action_discovery.json`.
After command/action catalog changes, regenerate the portable web reference fixture
with `.venv/bin/python scripts/update_action_discovery_fixture.py`, then format
`apps/web/scripts/fixtures/action-reference.json` with the web Prettier command.
Backend tests reject stale fixture content; web tests read classification directly
from production JSON and require no Python installation.

Use `apps/web/scripts/action-discovery-browser.mjs` with `BASE_URL` for the new
browser proof. Existing `unified-*-browser.mjs` action regressions use
`UNIFIED_BASE_URL`. Both use an installed Playwright module/executable and intercepted
API fixtures. See `verification.md` for final results and full-suite rerun details.
