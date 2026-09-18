# Validation Guide: Global Command Palette

This is the run guide for the planned implementation. New test/benchmark files named below do not exist yet and have not passed. Do not treat planning completion as feature acceptance.

## Prerequisites

- Existing Python 3.12+ development environment with the shared core's dev dependencies installed.
- PostgreSQL 17/UTF8 test server, with permission to create isolated disposable databases. Set `TEST_POSTGRES_ADMIN_URL` as required by `tests/conftest.py`; never target a production database.
- Node 22 and the existing frontend dependencies installed.
- For browser proofs, the existing harness requires `PLAYWRIGHT_MODULE` pointing to an installed Playwright module; optionally set `PLAYWRIGHT_EXECUTABLE`. Run the Vite preview/dev server and set `UNIFIED_BASE_URL` (the existing harness defaults to `http://localhost:5225`). Missing browser prerequisites must fail visibly, not skip acceptance.
- Apply the new Alembic revision to disposable integration/benchmark databases. Do not run migrations at API/scheduler/worker startup. Metadata-created test fixtures must explicitly install the same SQL support functions.

## Focused backend proofs after implementation

From `packages/reality-core`:

```sh
../../.venv/bin/pytest tests/test_global_search_matching.py tests/test_global_search_service.py tests/test_global_search_access.py tests/test_global_search_web.py tests/test_global_search_worklists.py tests/test_global_search_migration.py tests/test_global_search_benchmark.py
```

Expected: all-family exact/prefix/token/typo coverage including off-page/closed records, stable bounded continuation, duplicate identities preserved, canonical payment/shipment mapping, report-owner checks, tenant/lesson isolation and source/business tables unchanged by search. SQL/Python/browser fixture normalization must agree. Migration upgrade/downgrade/re-upgrade preserves existing data.

## Frontend proofs after implementation

From `apps/web`:

```sh
npm run test:contracts
npm run build
npm run i18n:audit
node scripts/command-palette-browser.mjs
```

Expected: all launch kinds work with keyboard and touch; active selection survives delayed results; no stale-company result appears; exact detail opens even outside current pagination/status filters; reload/Back preserve record/report targets; no mutation or chat send occurs merely by selecting a hit. Historical templates still require date inputs. Recents/favorites show only reauthorized labels and clear on logout. See [UI contract](contracts/ui.md).

Synthetic browser routes prove interaction behavior only. Real-API browser smoke scenarios must additionally prove the same target IDs, permissions and no-write behavior against PostgreSQL.

## Manual acceptance tour

1. Open from expanded sidebar, collapsed rail and mobile drawer; confirm current company and input focus.
2. Search by a partner name, SKU, exact duplicate invoice number, old settled invoice, order external reference and shipment tracking number. Open each exact record and its existing source/Reality links.
3. Search an action and open its form; cancel. Confirm no business write. Repeat for a capability without a direct Web form and verify the clearly labeled details/chat path.
4. Open each named worklist; inspect filters/freshness. Compare membership with the canonical reader, including both financial sides, unknown due dates and partial payments.
5. Open a private report and a snapshot template; verify owner scope and required date input.
6. Pin a target, open another through ordinary navigation, reopen palette and reload. Rename/revoke one target and verify re-resolution; test blocked local storage.
7. Type rapidly while delaying responses; change company mid-search; verify old results never appear. Fail private-report search and verify local report templates/calculated views remain usable with partial status. Retry restores group ordering. Search a fixture with more than twelve candidates: prove four per visible group/twelve overall, Show all for a wholly omitted group, and at most fifty merged Reports hits per page without duplicates/loss. Return restores the preceding filter/refinement.
8. Hand a question into chat with an existing draft; inspect visible/removable record context, preserve draft and confirm no send. Switch company explicitly and verify reset.
9. Repeat keyboard/focus paths at 200% zoom and mobile size, with all four supported UI languages; perform a screen-reader smoke check of active result and status announcements.

## Performance gate after implementation

Add the planned `benchmarks/global_search/runner.py` using the existing disposable-database guard convention (database name starts `reality_benchmark_`, explicit confirmation, reject nonempty unrelated databases). Its planned CLI:

```sh
python -m benchmarks.global_search.runner --records 100000 --users 10 --seed 235 --confirm-disposable --output /private/tmp/reality-235-search-performance.json
```

Run from `packages/reality-core` with the benchmark-specific `REALITY_DATABASE_URL` already configured and migrations applied. The runner must seed the declared family mix, execute deterministic named search cases, collect query plans and report workload identity, p50/p95/max and separately defined cold/warm runs. It must not pretend a new connection clears database/OS caches; report first-touch runs and genuinely controlled cold-cache runs distinctly.

Against the disposable real API/Web instance, run the planned browser companion:

```sh
node scripts/command-palette-performance.mjs
```

Run from `apps/web` with `UNIFIED_BASE_URL` and browser prerequisites configured. The script supplies 100ms network RTT and ten independent authenticated searching contexts, measuring last-keystroke-to-visible-result latency including debounce/queue time. Required p95: field interactive <=200ms; static results <=300ms; record results <=1.5s. Report host specs, PostgreSQL version, revision/content digest, query distribution, ten-user concurrency and cache methodology. A provider error/timeout is a failed observation, not a sample to drop. Use at least 100 measured observations per search case per warm/cold regime.

If the target fails, retain the failing evidence and optimize the chosen complete query path; do not cap candidates or declare partial implementation done.

## Full repository verification

From repository root, run required gates after implementation:

```sh
make spec-check
make lint
make test
make web-build
make docs-catalog-check
```

Also run frontend `format:check`, `test:contracts`, `i18n:audit`, the focused/regression browser scripts listed in plan.md, and migration tests. If catalog metadata changes, run `make docs-generate`, include generated pages and `apps/docs/.vitepress/data/tool-usage.json`, and run docs formatting/tests/build. Catalog entries require resource membership and German ERP labels.

The current host blocks `make` until its Xcode license is accepted. For specification-only validation, the identical underlying command is `python3 scripts/check_spec_policy.py`. This workaround does not substitute for later backend/frontend/browser checks.

## Evidence and completion

Record commands, actual outcomes, test counts, benchmark artifacts, migration evidence and manual accessibility observations in `verification.md` during implementation. Tasks and acceptance criteria remain incomplete while any required check is red or unrun. The final review must compare implementation with spec, this plan and shortest true relationship boundaries.

## Existing local development stack: required migration

The Web/API reload code does not migrate an existing database. Before trying this
feature on port 8080, install its reviewed database support explicitly:

```bash
docker compose exec -T api alembic current
docker compose exec -T api alembic upgrade 0066_global_search_support
```

A database still on 0062 lacks the search SQL functions and returns 503 for every
provider. Restarting the browser or API does not install them. Do not add migration
execution to API, scheduler or worker startup. Once migrated, close/reopen the
palette or retry the query; no application restart is required.
