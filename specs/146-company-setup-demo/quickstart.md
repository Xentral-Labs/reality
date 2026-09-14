# Validation Guide: Company Setup and Demo Data

Status: approved and implemented locally on 2026-09-09. Acceptance uses disposable PostgreSQL and synthetic accounts. No live deployment was performed.

## Creation acceptance

1. Prepare verified active and pending accounts, a saved access-application company name, an invited account, existing companies and enabled/disabled practice-entry configurations.
2. Open first setup, then every Companies → New company entry. Exercise empty ordinary, empty Sandbox, demo Sandbox and forbidden combinations. Confirm exactly once; no selection or cancel creates a company. Existing membership/invitation enters its company directly.
3. Verify the first name prefill is editable, personal/volume questions do not repeat, and application copy explains that those details did not create a company.
4. Lose the creation response, reload and repeat the same request. Reopen the same result; changed choices with same key conflict even across ordinary/Sandbox requests. Empty has no synthetic business rows. Failed or partial profile never opens as ready.
5. Active users open exact App tenant; pending users only the exact Playground cockpit. Production APIs remain denied to pending users. Existing companies/lessons/history remain unchanged.

## Canonical fixture and execution

Verify `contracts/demo-profile.md` against actual public/service reads: counts, all ten cases, local stock, supply dates/units, source/evidence links and the two 42-day windows. Inspect EUR/USD separately and source business dates versus actual ingestion timestamps. Compare identical version/anchor fixtures from both entry points. Validate manifest size and capability-gap declarations.

Provision execution fixture with explicit separate request. Inspect one-unit available/unreserved state, prepare proposal, review actual effect, separately confirm and read receipt/status/stock. No setup step may reserve or simulate success. Repeat into a fresh isolated tenant while preserving analysis and old execution evidence.

## Continuous source

1. Confirm connection prerequisites in empty Sandbox; verify only the listed minimal master data exists and no history/stock appears. Reject ordinary/execution/incompatible populated tenants.
2. Connect a ready canonical Sandbox; status is stopped. Start 60 orders/hour and use the controlled-clock harness for ten intervals. Run real scheduler and worker processes against the disposable database; browser closure is irrelevant to delivery.
3. Verify ten distinct normal imported orders, lossless payloads and source/intake/document links. Replays produce no duplicate commitments. No stock/reservation/shipment/payment is created by an arrival.
4. Pause/stop with pending and executing work, then resume/restart. Pending work is visibly cancelled; in-flight work may finish. No paused-period backlog; new Start-after-Stop gets a new run ID.
5. Inject interpretation failure/backlog 20, revoked actor, disconnected source and archived company. Verify safe retained outcomes, visible throttling, current authorization and explicit recovery. Foreign requests return not-found/refusal without effects. Baseline and execution tenant remain unchanged.

## Required gates

`make lint`, complete `make test`, `make spec-check`, `make site-build`, `make web-build`, `make docs-build`, migration upgrade/downgrade/constraint proof, Docker scheduler/worker acceptance and browser review in four languages, both themes, mobile/desktop and keyboard. Record real results here before marking implementation tasks or release checklist complete. No live deployment is authorized by this guide.

## Evidence — 2026-09-09

- Full backend suite: **1538 passed, 9 skipped in 305.29s (0:05:05)** (`../../.venv/bin/pytest -q`, same complete suite as `make test`); includes legacy imports, compact lessons, migration roundtrip, schema constraints, setup concurrency, history, supervised reservation and spec 147 regressions.
- Frontend contract suite: 120 passed, including both new setup/source contract files (also added to the normal web i18n test gate).
- Real Chromium acceptance: 16 passed: English/German/Dutch/Spanish × light/dark × 1280×900/390×844. Exercises editable first-name prefill, empty default, demo/Sandbox coupling, required field, keyboard access, response-loss reload recovery, exact destination, later modal/cancel, source preview/connect-stopped and separately confirmed Start. Harness: `apps/web/scripts/company-setup-browser.mjs`; HTTP fixtures isolate presentation testing from the PostgreSQL proofs. Screenshots: `/private/tmp/reality-146-browser`; reviewed German dark mobile form and English light desktop integration.
- Source acceptance includes ten real imported orders at controlled intervals for active and pending owners, both empty and canonical tenants; lineage/count/page reads, immutable retries and unchanged baseline; failure cap 20; explicit rate/disconnect/reconnect; owner revocation and profile incompatibility.
- Existing compact Playground browser regression: PASS against the production build; six separately reviewed/confirmed fixture operations, reload context, tabs, inspectors, both themes and cockpit viewport. The harness expects production effect behavior; use the preview build, not React development Strict Mode.
- Container acceptance uses locally built `reality-scheduler:spec146` and `reality-worker:spec146`, independent processes and disposable PostgreSQL, including Demo Data delivery with no browser. All nine container checks passed (26.69s).
- Build gates: web (TypeScript/Vite/i18n), site and docs passed. Existing Vite chunk-size advisory remains; it is not a failed build.
- Final requirement coverage: 24/24 FR/DR, 9/9 success criteria mapped, 40 tasks; no unresolved critical/high Spec Kit findings. See review.md for scope and implementation refinements.

Reproduce browser acceptance with the Vite server on port 5186 and `PLAYWRIGHT_MODULE` pointing to an installed Playwright module, then `node apps/web/scripts/company-setup-browser.mjs`. Run container acceptance from `packages/reality-core` with `REALITY_CONTAINER_SMOKE=1 REALITY_CONTAINER_IMAGE_TAG=spec146 ../../.venv/bin/pytest tests/test_scheduled_worker_deployment.py -q` after building both Dockerfiles from the repository root. Containers do not migrate on startup; apply migration 0046 once before any later authorized rollout.

Final gates: `make lint`, `make spec-check`, `make site-build`, `make web-build`, `make docs-build` and `git diff --check` passed. The nine conditional skips remain explicit; Docker acceptance is separately enabled and all nine container checks pass. Earlier red fixture/catalog assertions were corrected and the complete suite rerun. No deployment, merge or operational reservation was performed outside disposable tests.

## Live-creation refinement acceptance

The confirmed request can select Live simulation in both creation entries. Verify that it returns the same ready tenant with a connected/running source at 60/hour without additional browser connection/start calls. Retrying after an injected Start failure reuses the baseline and leaves no partial connection; replay after a later Pause preserves Pause. Empty/ordinary/execution and non-boolean live flags are rejected. No schema changes were required.

Observed red proof: three new service cases failed with unsupported `live_simulation` before implementation. Focused service/API/legacy connection checks: 17 passed. Chromium matrix: 16 passed, including later live creation as one request and unchanged separate manual source controls. Web build, four-language audit, lint, spec policy and docs build pass. Full regression result is recorded after completion below.

Final live-creation regression: **1545 passed, 9 skipped in 306.06s (0:05:06)**. All T041–044 checks are green. Browser matrix 16/16 and web/lint/spec/docs gates PASS. This supersedes the earlier 40-task verification with 44 completed tasks and FR-021 coverage. No live deployment or merge.

## Combined unified-app and local rollout evidence — 2026-09-09

This section supersedes earlier statements that no local deployment occurred; the
owner explicitly authorized the port-8080 update. The active checkout and safe local
commands are documented in `docs/LOCAL_STACK.md`. No remote deployment or Git commit
was performed.

- Complete combined backend suite: **1913 passed, 9 skipped in 311.43s**.
- Focused setup, scoped presentation, invitation cleanup and access regressions: 18 passed.
- Unified frontend contracts: 40 passed; formatting, four-language audit (1140/1140),
  TypeScript/Vite, site, docs, lint and spec-policy gates passed. Site dependencies
  reuse the root installation with an identical lockfile.
- All seven matching application/migration/background images built successfully.
- Both restored-backup rehearsal and actual local migration preserved every existing
  row in 62 tables, including 38 tenants; four additive infrastructure tables were
  created. Head: `0047_merge_demo_lot_expiry`. Private backups remain outside Git.
- API and MCP healthy; all six selected runtime services running with zero restarts;
  scheduler and worker logs show successful idle sweeps. Database and object-storage
  containers were not recreated.
- Actual port-8080 asset hashes match the combined build; health 200, protected setup
  options 401 without a session, and live-creation schema present.

Browser fixtures do not create companies in the live database. Real setup, canonical
seed, automatic connection/start, tenant isolation and later Pause are separately
proven by PostgreSQL tests. The nine conditional suite skips remain explicit; earlier
container acceptance is recorded above and is not claimed as a rerun here.

Final browser acceptance against **http://127.0.0.1:8080**: 16/16 combinations PASS
(English/German/Dutch/Spanish, light/dark, desktop/mobile), including distinct company
cards, scoped action grouping, type/state badges, confirmed live creation, recovery and
opening the unified Sandbox. No separate connect/start browser requests are sent.
The same matrix passed against preview port 5190 before rollout. Screenshot review
confirmed the company boundaries and contained management footer. T045–050 complete.

FR-023 completed: the updated browser assertion first failed against the old form (0 vs 3 goal-choice radios). The new preview build passes 16 language/theme/viewport combinations, including default choice, one fieldset, demo-only toggle, clearing live intent on selection change, live request mapping and recovery. Desktop screenshot reviewed. Forty frontend contracts, formatting, i18n audit, TypeScript/Vite, spec policy and docs build pass. Only the local web image/container was updated; backend, database and scheduler remain unchanged. No backend/migration rerun was required for this presentation-only refinement.

FR-024 / T054 complete: red proof demonstrated the disabled button prevented feedback. Forty frontend contracts, formatting, four-language audit, TypeScript/Vite, spec policy and docs build passed. Sixteen browser combinations passed empty/whitespace rejection with no setup request, inline invalid state, focused field, correction, retained demo/live choices and successful creation/recovery. Only the local web container was updated; backend and database unchanged.

FR-025/T055 complete: prior ready menu failed the new auto-open regression. The updated build passed 16 browser combinations covering direct automatic entry, failed-opening receipt recovery after reload, one creation request and destination confirmation. Forty frontend contracts, formatting/i18n, TypeScript/Vite, spec policy and docs build pass. Local web image/container updated; backend, source state and database unchanged.

## FR-026–029 final acceptance — 2026-09-09

UX review produced compact state/control groups, persisted-time activity and a header badge. User steering moved Demo Data to its own Company navigation destination. Initial regressions reproduced the Sandbox report denial and missing recent-read mode; an older test enforcing the superseded analytics denial was updated while preserving reference-workspace restrictions. Direct-entry regression additionally caught the outer route allowlist and is now green.

- Full backend: **1914 passed, 9 skipped in 343.80s**; focused read/API/security checks: 76 passed.
- Web: 41 contracts, formatting, four-language audit, TypeScript/Vite, lint, spec policy and docs build PASS.
- Dedicated page: 16 browser combinations PASS: four English functional cases and twelve localized visual cases; menu placement/visibility, standalone route, no widget in Integrations, polling, stale retention, input/confirmation preservation and confirmed controls checked. Spanish mobile badge overflow fixed and verified; badge has accessible description.
- Existing creation/recovery browser matrix: 16 PASS before navigation refinement; direct dedicated-page routing/navigation is covered by the final matrix and entry contract.
- Existing Demo Firma 1 Live verified through the deployed API image with SET TRANSACTION READ ONLY: Reports/contributors both 34 open, latest snapshot 25 of 26 imports in chronological order, running source, zero pending/failed. Simulation continued during work.
- Matching local API/MCP/background images and web updated. API/MCP healthy; scheduler/worker running without restarts. Port 8080 serves the tested dedicated-page build and API exposes recent mode. No schema migration, source restart command or business mutation was performed by verification.

T056–059 complete. No unresolved critical/high review finding. Reviewer-owned checklist markers unchanged; no remote deployment.

### FR-030 Sandbox Exceptions correction

The seeded demo and authorized practice HTTP tests initially failed on the
ordinary-only read guard (HTTP400). The correction changes only the two admission
checks in `attention_reads.py` to scoped tenant reads; no frontend or schema change.
Focused verification: 81 tests passed across company setup, playground API,
attention reads, unified operations API and reference workspace. Full suite: 1925 passed, 9 skipped in 443.52 seconds. Lint/spec/diff checks passed.
Matching local core images were updated without a migration or data reset. The
exact tenant from the reported URL returned 105 findings (50 on the first page)
and a readable finding detail in a strictly read-only transaction. API/MCP are
healthy, scheduler/worker running, all with zero restarts; the port8080 health
proxy responds successfully. No frontend change was required. Evidence: local
`/tmp/reality-attention-full.log` and `/tmp/reality-attention-focused.log`.
