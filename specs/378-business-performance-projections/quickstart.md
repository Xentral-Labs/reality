# Verification (spec 378)

Prerequisites: local disposable PostgreSQL on port 54329; repository Python virtualenv and Web dependencies. No real company data or deployment required.

Run `make spec-check lint business-annotations-check`, then `cd packages/reality-core && ../../.venv/bin/pytest tests/test_business_projection.py tests/test_projection_jobs.py tests/test_clock_sensitivity.py tests/test_migrations.py tests/test_application_catalog.py`. Full required backend regression: `make test`. Migration tests upgrade head, inspect indexes, downgrade to 0145, re-upgrade and refuse cache removal with unfinished shared jobs.

Web gates: `make web-build`; generated catalog: `make docs-generate` and `make docs-catalog-check` after generated files are committed. Browser: run local Vite on 5177 and `PLAYWRIGHT_MODULE=<installed-playwright/index.mjs> PLAYWRIGHT_EXECUTABLE=/usr/bin/chromium UNIFIED_BASE_URL=http://127.0.0.1:5177 node apps/web/scripts/business-live-browser.mjs` from its script directory as appropriate.

Current evidence:
- Meaningful first failure: missing business projection service; oracle tests failed before implementation.
- Final focused shared projection/clock/migration-metadata run: 43 passed (168.60 s). Separately, complete migration/catalog integration ran 68 passed/one stale catalog-count assertion; that assertion was corrected, and the final metadata/catalog proof passed two tests. Migration roundtrip and unfinished-job downgrade guard pass.
- The final dedicated Business suite passed 18 tests (81.60 s), including a one-statement read that forbids Reality derivation and leaves pending mutations unflushed. This includes missing/empty message-ID counter/detail semantics against the unchanged oracle. The full backend regression is pending.
- `make web-build` passed formatting, 463 Web tests, all four localization audits (2865/2865 keys), TypeScript and Vite. Vite reports the existing large-bundle warning.
- Chromium Business proof passes existing counts/dialogs/Inspector/inert correspondence/stale retention/mobile/read-only behavior plus order/mail cursor paging, filter reset, delayed/failed processing and unavailable cold rebuild.
- `make spec-check lint business-annotations-check` passes (650 described functions, 115 described tests, no outstanding annotation preparation).
- `make docs-catalog-check` passes reproducibility against the committed generated output. Documentation formatting, all 145 contract tests and VitePress build pass after updating the two catalog-count expectations.
- Synthetic read/rebuild/shared-role measurements, raw results and the million-order plan are in [benchmark.md](benchmark.md). Final 10,000-order read p95 is 186.92 ms; short shared-role booking lag remains above ten seconds. Sustained simultaneous bookings/viewers and million-order capacity are open acceptance items.

No deployment or real company data was touched. SC-004 remains open; this is a draft follow-up for review. Do not mark completion/release gates green while required checks remain pending. Interrupted early full-suite attempts are not passing verification. A parallel migration-fixture run exhausted the disposable PostgreSQL default lock table; the final four-worker run uses max_locks_per_transaction=512 in the local test container only. Benchmark measurements used its earlier default 64. Final full regression results will replace this pending entry.
