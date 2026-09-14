# Verification guide

## Prerequisites
Use repository .venv, installed web/docs Node dependencies and the local isolated PostgreSQL test server on port54329. Never use production for tests. Background schema approval was supplied by the owner on 2026-09-12.

## Commands
1. `make spec-check`
2. `.venv/bin/pytest packages/reality-core/tests/test_application_catalog.py packages/reality-core/tests/test_http_boundary.py`
3. `.venv/bin/pytest packages/reality-core/tests/test_projection_jobs.py packages/reality-core/tests/test_materialized_projections.py packages/reality-core/tests/test_projection_job_migration.py`
4. `make lint && make test`
5. `make web-build` and `cd apps/web && npm run test:inspector-browser`
6. `make docs-generate && make docs-build`; verify regeneration is deterministic. Run catalog stale-output check against the final committed diff when committing is authorized.
7. Run any affected financial/workspace browser stories and migration tests before completion.

## Stories to prove
Open/reopen/search directory; expand details. Commit multiple changes without browser, scheduler dispatch then worker success, stored read with builders forbidden. Stop worker and verify old data with notice. Retry interrupted job; commit during calculation; roll back mutation; isolate tenants. Bootstrap missing/version-old cache. Advance clock without business events. Inspect live price result without projection writes. Record timings and actual gate outcomes below.

## Evidence
Baseline catalog: 0.972–1.365s per uncached build, 357,630-byte JSON. Implementation gate outcomes follow below.

Pre-implementation review 2026-09-12: 11/11 requirements mapped to tests and implementation across 29 tasks; no remaining critical finding after owner schema approval. Existing baseline: 35 catalog/projection tests passed in 15.52s; spec policy passed. Architecture checklist remains reviewer-owned; owner explicitly instructed proceeding with all implementation after reviewing the schema proposal. No extension hooks configured.

Catalog implementation: 44 catalog/HTTP tests passed (43.17s). Measured cold runtime initialization 846.92ms, warm reads 7.53ms / 12.04ms / 7.30ms (>98% improvement). Focused Inspector browser path passes metadata search, absent collapsed bodies, keyboard disclosure and read-only data. The older all-Inspector script assumes retired navigation; use its new PROJECTION_ONLY=1 path for this feature.

Initial background test-first proof failed on missing projection_jobs module. After implementation, 9 new service/schema tests passed in 6.14s. Broader compatibility checks correctly exposed prior refresh-on-read expectations; those tests now explicitly materialize before verifying stored results. No global automatic test refresh is installed.


Review and extended verification (2026-09-12):
- Real scheduler/worker, repeatable-read concurrent writer, atomic rollback/failure, terminal recovery and HTTP compatibility proofs passed (25 tests, 31.73s). A continuous-demo fairness regression failed first and passed after alternating eligible work classes using retained run history.
- Migration/internal-job tests including downgrade refusal with preserved history, retry identity, version/missing-checkpoint bootstrap and pending-write read purity: 21 passed in 9.58s. That complete run includes the healthy real child-process publication story, below the 30s target. Clock eligibility uses a controlled +61s observation without business events.
- Final dependency review added a real commitment-hold regression: supply/demand incorrectly remained ready before adding its dependency; all 19 projection-job tests then passed in 21.67s.
- Compatibility suite: 203 passed initially; four remaining checks identified explicit tenant-isolation fixture materialization, six newly registered service operations, and benchmark capture of CTE-based paginated SELECTs. Those adaptations preserve the bounded SQL/tenant assertions.
- Browser Inspector: focused PROJECTION_ONLY=1 path passed search over unopened definitions, keyboard disclosure and initial/pending/failed/recovered read-only results; screenshot `/private/tmp/reality-179-browser/projection-ready.png` inspected.
- Finance browser: initial absence of a cache exposed the generic table's misleading empty state; the table is now withheld until a completed generation exists. The full finance script passed all freshness states, paging/filter/totals/preview/retry behavior and 48 localized responsive screenshots. Its language fixture now supplies explicit `lang`, matching the existing shared-browser language contract instead of assuming profile changes override the stored preference.
- `make web-build` passed formatting, localization contracts, four-language coverage and production compilation. `make docs-build` passed generated-reference contracts, formatting, Node tests and VitePress build. Existing chunk-size advisories remain non-failing.
- Raw spec policy and package-scoped Ruff checks passed. Generated docs were checked by hashing all generated vocabulary pages/data before and after regeneration; identical output. The git-based stale-output command is designed for committed generated changes and would report this intentionally uncommitted feature diff.

Logs are in `/private/tmp/reality179-*.log`; they are local verification evidence, not production measurements. No migration was applied to a running application database, and no deployment or merge was performed.

Final backend verification: complete PostgreSQL suite passed with **2,315 passed, 9 skipped** in 385.62s (`pytest -q -n 4`). After the final dependency/documentation review, the affected projection/migration/catalog/HTTP/benchmark suite passed **72 tests** in 54.03s. Package-scoped Ruff, spec policy and whitespace review passed.

Final browser and review completion:
- Payment entry browser passed customer/supplier entry, exact-amount review, confirmation, edit/rejection, decision/Copilot reopening and 16 localized responsive views. Fixture maintenance uses the canonical action-discovery fixture, a complete invoice row, explicit language, a waited-for action disclosure, decision-row expansion and the shared Copilot dock on Finance. It does not change product behavior or bypass confirmation.
- Both edited financial browser scripts passed Prettier checks. Finance and Inspector freshness proofs are green; final documentation regeneration hashes remain identical.
- Final diff review found no remaining critical requirement or Constitution issue. Schema remains exactly the owner-approved nullable internal actor/check/partial index, with no new table or authority. Stored reads cannot flush pending writes; explicit live v2 reads and pricing remain canonical. Backend, frontend, browser, migration, documentation and spec gates have green evidence above. All 29 implementation tasks are complete. Human merge/release review remains separate; no merge or deployment was requested.

## Public read-mode reference verification (2026-09-12)

Documentation-only clarification of FR-010/FR-011. The generated reference and
interactive explorer now label concrete catalog view/projection and read-only MCP
queries as stored, live or parameterized live. Source review covered the Inspector,
warehouse stock, specialized projection pages, financial flow variants and MCP
page/legacy dispatch. No runtime read path, business rule or schema changed.

- The new generated-reference contracts failed before metadata was implemented.
- `make docs-build`: 4 Python reference tests and 57 Node documentation tests passed;
  formatting and the VitePress production build passed.
- Python adapter tests exercise the actual five MCP handlers with default, page and
  legacy arguments, checking which live/stored service receives the tenant.
- `make spec-check` and `git diff --check`: passed.
- Final consistency review: FR-010/FR-011 map to T030–T033 and the reference/adapter
  contracts. No unresolved scope questions or critical consistency findings. Existing
  Constitution Check remains applicable; the follow-up changes documentation only.
- Browser checks passed for all four explorer tabs plus inventory/pricing mode details,
  in English/German at 375/1280 px in light/dark themes. Reviewed mobile and desktop
  screenshots; no page errors or horizontal overflow. The preview was restarted after
  rebuilding to clear stale asset references before the successful full run.
