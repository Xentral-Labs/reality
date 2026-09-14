# Verification — 2026-09-10

The following initial results describe the deployed integration worktree. Isolated
PR verification against main is recorded separately below.

## Scope and review

All 67 current Commands and 13 workspace Actions have one primary category path.
The original inventory had 65 Commands; the concurrent Finance work added two.
The shared discovery catalog exposes 18 existing form variants and 10 management
links. No generic command executor, business service changes or migration were added.
See `inventory.md` for the complete screen/placement review and deliberate exclusions.

## Automated gates

- `make spec-check`: passed.
- `make lint`: passed.
- `make web-build`: passed, including 68 web tests, all four translation catalogs
  (1,184/1,184 each), TypeScript and production build. Existing bundle-size warning remains.
- Complete PostgreSQL run from `packages/reality-core`:
  `../../.venv/bin/pytest -q -n 4 --tb=short` — 2,012 passed, 9 skipped,
  3 failed during concurrent source edits. Two HTTP catalog tests held the old YAML
  filename during the JSON transition; one concurrent Finance regression held an older
  implementation. All three were rerun successfully with the final discovery tests:
  14 passed. The full run itself did not exit successfully; the focused final rerun did.
- Discovery coverage includes malformed catalog rejection, exact command coverage,
  fixture freshness, fallback grouping, localization/search and context/access rules.
- `git diff --check`: passed.

## Browser verification

Production assets with intercepted API fixtures passed the action-directory test:
keyboard disclosures, ancestor search expansion and clearing, counts, empty results,
German mobile layout, popup viewport bounds, all Warehouse tabs, Finance flow/tab
combinations, payment direction, catalog failure/retry and zero mutation requests
when opening navigation or forms. Desktop and mobile screenshots were inspected.

Existing browser regressions passed for holds, receipt/release, correction/reversal,
opening stock, order entry and invoice entry. These cover existing confirmation,
rejection, stated amounts, lost-response recovery, localization and company isolation
in proportion to each workflow. Outdated fixture navigation and unrelated Home read
responses were updated to match the current integrated application.

Evidence logs are under `/private/tmp/discovery-*.log`; directory screenshots are
under `/private/tmp/action-discovery-screens/`. Browser business responses were
synthetic; these tests did not create business records in the user's companies.

## Local rollout

Matching API, MCP, invitation worker, scheduler, worker and web images were built
from the active integration worktree with the root environment file. No migration
was run for this feature. The existing database was already at
`0049_settlement_reduction_roles` from the concurrent Finance work. Runtime catalog
validation inside the rebuilt API reports 67 Commands and 28 navigation entries.

All six application services are running; API and MCP health checks passed. The
same directory/context browser proof passed against deployed assets on port8080,
with zero business writes. Final spec policy, Ruff and changed-script formatting
checks passed after documentation and fixture updates. Existing intentional
integration changes were retained; no commit or branch switch was performed.

## Isolated PR branch

Base: main `2bc3a65`. The branch includes only action discovery and its existing-form
integration. Separate Finance services, account/settlement Commands, management links,
and credit-balance routes were excluded. Coverage is 60 Commands, 13 Actions,
18 form variants and eight management destinations.

- Spec policy and Ruff passed.
- Catalog/discovery/HTTP boundary tests: 52 passed in 17.45 seconds.
- Web gate: 69 tests passed, translation audit, TypeScript and production build passed.
- Final context-only adjustment: seven discovery unit tests passed.
- Full PostgreSQL suite for this isolated branch is delegated to the required PR CI
  check; the earlier integration-suite result is not an isolated-branch result.
- Final discovery backend tests: 11 passed in 2.96 seconds.
- Isolated production-browser directory/context proof passed: search, keyboard,
  localized mobile layout, Warehouse and supported Finance routes, recovery and
  zero business writes. Evidence: `/private/tmp/discovery-pr-browser.log`.
