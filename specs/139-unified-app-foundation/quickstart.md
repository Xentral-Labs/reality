# Validation guide: Unified App Foundation

## Current evidence

- Owner approved the design-first foundation scope on 2026-09-07.
- Implementation lives in `/private/tmp/reality-139`, branch `139-unified-app-foundation`, based on `58dce63`. The original checkout and user work are preserved.
- The new frontend remains opt-in (`VITE_UNIFIED_APP=1`). No deployment, merge, legacy retirement or practice deletion has occurred.
- Full PostgreSQL run: **1470 passed, 7 skipped**. The seven skips are existing retired server-rendered UI tests in `test_integrations.py`, `test_ai_mcp.py` and `test_tenant_lifecycle.py`; they are not foundation acceptance substitutes.
- Focused foundation regressions: **20 passed**, including separate-connection hold/revision/correction interference and connection loss; `/private/tmp/reality-139-final-focused.log`.
- Frontend contracts: **122 passed**. Web build, four-language audit, documentation build, Ruff and spec policy pass.
- The browser harness exercises six action/entry combinations, final fulfillment, Inspector safety, contextual Chat, native-dialog keyboard focus, unresolved outcomes and failed observations. Fixture browser evidence is separate from actual PostgreSQL business proof.
- Local authenticated live-API browser proof passed: Home → delivery → prepare with no effect → explicit confirmation → reservation 12 with physical stock 20 → Inspector.
- Owner visual acceptance remains **pending**. Technical visual review and test success do not imply owner approval or rollout authorization.

### Local review URL

Open `http://localhost:5177/app/home`. On 2026-09-08 the owner requested the same
users and tenants as the existing local app on port 8080. The frontend still proxies
the newer API on port 8007; that API now uses the existing `reality_test` database,
object storage and encryption configuration. Use localhost on both ports to share
the existing session cookie. Business changes are visible in both presentations.
The supplied existing owner login was verified on both ports, with identical user
identity, default company and all five accessible companies. No password reset or
user/tenant copy was needed. Evidence: `/private/tmp/reality-shared-login-check.log`.

Local runtime launcher: `.venv/bin/python /private/tmp/reality-139-shared-api.py`
from `/private/tmp/reality-139`. It obtains configuration from `reality-api-1`
without printing credentials, maps Docker database/object-storage addresses to
localhost, and runs the new API on 8007. Log: `/private/tmp/reality-139-shared-api.log`.
Database migration heads matched before connection; no migration was performed.
The launcher does not provision or promote an administrator account.

**Spec impact: none** — owner-requested local runtime configuration using existing
supported database/authentication settings; no application contract or source-code
behavior change. The earlier implementation proofs above used the separate
`reality_unified_preview_107` database with Northstar sample data. That database is
preserved but is no longer the active preview. Its old company-specific URLs should
be replaced with the shared URL above.

## Environment

Use Python 3.12+, the repository virtual environment and the existing PostgreSQL test configuration from `packages/reality-core/tests/conftest.py` / `docs/TEST_STRATEGY.md`. PostgreSQL is mandatory. Install frontend dependencies from the existing lockfile and use the documented development compose workflow.

Create an isolated feature checkout for implementation, preserving this specification and the user's other work. Verify the existing browser harness setup (including PLAYWRIGHT_MODULE/PLAYWRIGHT_EXECUTABLE when required by local scripts) rather than adding an unreviewed test stack. Missing browser access means visual acceptance remains pending, not passed.

## Focused proof commands after test files are added

```bash
cd packages/reality-core
../../.venv/bin/pytest tests/test_unified_delivery_reads.py tests/test_unified_delivery_actions.py tests/test_unified_app_api.py
../../.venv/bin/pytest tests/test_application_tools.py tests/test_chat_confirmation.py tests/test_postgresql_integration.py
```

The new browser command `npm run test:unified-browser` and contract entry are added by T003 in `apps/web/package.json`. Run them against the documented fixture and real API environments; a fixture-only browser pass cannot substitute for PostgreSQL business-story proof.

## Main acceptance journey

1. Use existing services/tools to prepare an authorized company, customer, item/location, opening stock 20 and a customer commitment for 12. Enter source-stated amounts explicitly if fixture creation requires them; do not compute missing source totals.
2. Enable VITE_UNIFIED_APP for the review build. Open Home and the delivery via Your work. Confirm selected company, source/evidence links and exact units.
3. Prepare reservation 12. Before confirmation stock/commitment records are unchanged. Confirm once: physical 20, reserved 12, available 8, open 12.
4. Prepare shipment 5. Review exact target/quantity and confirm separately: physical 15, reserved 7, available 8, fulfilled 5, open 7.
5. Inspect immutable original reservation evidence after consumption: its original applied quantity remains 12 while current reserved is 7.
6. Confirm final shipment 7 through a new review: physical 8, reserved 0, available 8, open 0. Open work no longer includes it, but the case and receipts remain linked.
7. Run equivalent isolated stories for both actions through case, global launcher and company Chat: six action/entry combinations.

## Negative and boundary journeys

- Prepare then edit quantity/location/target; the old token cannot authorize changed intent.
- Reject: no effect. Close a panel: no implicit rejection. Reload: same pending identity returns.
- Confirm twice or in two tabs: one effect; two different proposals competing for one stock pool cannot overallocate.
- Competing ordinary API/CLI/MCP writer changes stock, hold, revision or correction; stale review is refused under the shared guard.
- Lose the response after execution: recovery returns actual correlated evidence without calling the handler again.
- Fail after claim without sufficient evidence: unresolved remains explicit. No-event alone must not become a safe-retry signal.
- Fail observation refresh after a recorded effect: receipt remains visible; refresh never repeats execution.
- Use two companies with identical customer/item labels, foreign IDs and delayed prior-company responses; no data/authority crosses context.
- Open a pending practice-only account and an archived saved run through existing paths; new company bootstrap/mutation is not granted.
- Verify revisions, corrected shipments, multiple locations/units, paginated work and incomplete history without aggregating samples into totals.
- Disable provider or return unsafe Markdown: retained question/error, safe rendering, deterministic forms remain available.
- Reopen saved plain legacy conversations and new case-annotated conversations without modifying historical context.

## Visual review matrix

Review Home, global Chat, selected delivery, action review, verified result and unresolved/error state at 390 px and 1440 px, light/dark, en/de/nl/es. Test keyboard focus, mobile navigation, long reference labels, company switch and return from technical inspection. Genuine tables may scroll inside their frame; page-wide clipping is not accepted.

Compare hierarchy and case behavior with `design/reference.html`. Do not copy mocked values or accept a screenshot as execution proof. Record browser, viewport, language, theme, state, evidence path and reviewer outcome.

## Final required commands from repository root

```bash
make spec-check
make lint
make test
make web-build
cd apps/web && npm run test:contracts && npm run test:unified-browser
```

Run `make docs-build` for updated public documentation and `make site-build` if its boundary changes. Current CI is `.github/workflows/quality.yml`. After final documentation/status edits, rerun affected gates. Do not mark tasks or V0 complete while required checks fail or are skipped.

## Rollback exercise

Create an in-scope reviewed proposal, disable the new presentation switch and reopen it through token-aware compatibility handling. Original review and result remain accessible. Never roll back the backend to one that bypasses new review authority or strands new proposal formats. No practice/data deletion is part of this exercise.

## Execution log

| Date | Stage | Command/evidence | Result |
| --- | --- | --- | --- |
| 2026-09-07 | Planning | Owner scope approval | Approved |

| 2026-09-07 | Baseline | Existing suite before compatibility adaptations | 1449 passed, 7 skipped; one new-family spec registration failure fixed |
| 2026-09-07 | Full backend | `PYTHONPATH=src ../../.venv/bin/pytest -q` | 1465 passed, 7 existing skips; `/private/tmp/reality-139-backend-verified.log` |
| 2026-09-07 | Frontend contracts | `npm run test:contracts` | 122 passed; `/private/tmp/reality-139-contracts-verified.log` |
| 2026-09-07 | Frontend build | `make web-build` | Passed; `/private/tmp/reality-139-web-final-checked.log` |
| 2026-09-07 | Documentation | `make docs-build` | Passed; `/private/tmp/reality-139-docs-verified.log` |
| 2026-09-07 | Static/spec | `make lint spec-check`, `git diff --check` | Passed |
| 2026-09-07 | Live API browser | Isolated authenticated Chrome journey | Passed; `/private/tmp/reality-139-live-browser.log` |
| 2026-09-07 | Browser matrix | `npm run test:unified-browser` | Passed (all 80 matrix captures plus recovery); final rerun log `/private/tmp/reality-139-browser-complete.log` |

### Browser evidence

Chrome headless, actual React application, HTTP fixtures: `/private/tmp/reality-139-browser/`.
The matrix captures **Home, Chat, case, review and result** for each combination of
`en/de/nl/es`, `light/dark` and `390/1440`: 80 named PNGs. Each variant asserts no
page-wide horizontal overflow and keyboard opening/Escape focus restoration.
Additional images cover contextual Chat at both sizes, unknown outcome and failed
observation. `live-*.png` are the separate real-API proof, not intercepted fixtures.

Visual review found and fixed mobile header overflow, dialog focus restoration,
Spanish operational status wording and an opaque-ID-only context chip. Structure,
contrast and control reachability were reviewed against the frozen reference;
owner design acceptance is still pending.

### Requirement evidence map

| Requirements | Executable evidence |
| --- | --- |
| FR-001–003, FR-022–023 | `unified-app-contract.test.mjs`, shell browser journey, existing admission/practice regressions |
| FR-004–005, DR-004 | `test_unified_app_api.py`, Home scope and failure browser journeys |
| FR-006–008, FR-016, DR-001–002, DR-005 | `test_unified_delivery_reads.py`, partial/final browser journey, lossless Inspector proof |
| FR-009–012, FR-019–020 | Six entries in `unified-delivery-browser.mjs`, shared action and existing tracked-reference tests |
| FR-013–015, DR-003, DR-006 | `test_unified_delivery_actions.py`, PostgreSQL duplicate-claim migration test, token-aware API/MCP regressions, unknown/observation browser proof |
| FR-017–018 | Context service/API tests, saved conversation regressions, company Chat/provider-failure and case-assistant browser journeys |
| FR-021–022 | Language audit, 80-image matrix, keyboard and viewport assertions |

SC-001/002/005/007 are covered by the shared delivery/action proofs. SC-004 uses
case metrics, inventory workspace and result Inspector links. SC-006 has technical
browser evidence; owner acceptance remains separately pending. SC-003 is the
spec/task coverage mapping. SC-008 is the bounded route contract with no later-module
placeholders or live fixture data.


Review gallery: `/private/tmp/reality-139-browser/index.html`. The final complete-suite rerun, including all added regressions, is logged at `/private/tmp/reality-139-final-suite.log`.

Final complete-suite result: **1470 passed, 7 skipped in 242.71 seconds**.
All seven skips are the pre-existing retired server-rendered UI tests described
above. The final run includes all added concurrency and connection-loss tests.
Final frontend delta verification also passes, including the explicit unverified
receipt notice and preserved shipment location during editing; its browser run
uses `UNIFIED_SKIP_MATRIX=1` because the full unchanged matrix already passed.
The full matrix was not skipped in `/private/tmp/reality-139-browser-complete.log`.

### Subsequent workspace coverage

Specs113 and114 add Orders & deliveries and Facts to the unified navigation.
Their verification evidence is recorded in their own quickstarts. Supporting
advanced routes and Playground remain available pending separate rollout and
retirement acceptance; the original foundation results above are historical.
