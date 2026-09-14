# Validation

From apps/web: `npm run test:contracts`, `npm run i18n:audit`, `npm run build`, `npm run format:check`.
Run `node scripts/integrations-catalog-browser.mjs` with PLAYWRIGHT_MODULE, PLAYWRIGHT_EXECUTABLE and UNIFIED_BASE_URL pointing to the built app. Test selection, review, edit, removal, reload, scope, cancellation, error handling, translations and mobile layout using intercepted API fixtures. Run existing sources browser regression. From root run `python3 scripts/check_spec_policy.py` and `git diff --check`.

## Evidence — 2026-09-08

- Red proof: Add integration missing on baseline (`/private/tmp/integrations-red.log`).
- Browser journey passes: ten providers, search/category, field validation, save/reload/edit/remove, multiple instances, user/company isolation, cancelled edits/focus restore, unavailable and corrupt storage, preparation during source-read errors, zero API mutations; 16 catalog screenshots (four languages, two sizes, two themes). `/private/tmp/integrations-browser.log`.
- Existing sources browser regression passes with 48 localized screenshots: original payload, exact evidence, pagination/filter/retry/company reset, no writes. `/private/tmp/integrations-sources-browser.log`.
- Frontend: 39 contract tests; build; localization audit 1083 keys in four languages; formatting; spec policy; diff whitespace pass. Existing bundle-size warning unchanged.
- Visual review: desktop draft cards and catalog, German mobile catalog, dark catalog.
- Local web Docker container rebuilt on port 8080; no backend/schema/volume changes.
- Final review: preparation calls sessionStorage only, uses scoped validated draft keys; existing services and source register remain unchanged. No constitutional or scope exceptions.

### FR-007 footer regression
Baseline browser proof fails because neither source tab has a bottom footer (`/private/tmp/footer-red.log`). The corrected browser suite passes footer ordering and single-control assertions for Received data/Documents, existing navigation and 48 localized screenshots (`/private/tmp/footer-browser.log`). Production build, 39 contract tests, formatting, four-language audit, spec policy and diff checks pass. Desktop Documents screenshot reviewed. Web container rebuilt on port 8080.

### FR-008 source-centered navigation and details
- Six targeted service tests pass, covering lossless source payload, document/party/item links, event-to-subject navigation, tenant exclusion and bounded results.
- Full backend run: 1783 passed, 7 skipped; 13 migration tests initially failed because the suite was launched from the repository root rather than the package directory (`Config("alembic.ini")`). Rerunning all 13 migration tests from packages/reality-core passed. Logs: `/private/tmp/source-details-full-tests.log`, `/private/tmp/source-migrations-tests.log`, `/private/tmp/source-details-tests.log`.
- Source browser suite passes: two primary tabs, linked-record dialog traversal, original payload, retained contextual document URLs and 48 localized screenshots. `/private/tmp/source-details-browser.log`.
- Frontend build, 39 contracts, four-language audit, formatting, changed Python Ruff checks, spec policy and whitespace pass. Web/API rebuilt on existing ports. No migrations, provider calls or business mutations introduced.
- Reviewed final source-link query predicates and navigation: explicit tenant and source FKs only; no inferred links or claim of creation.
