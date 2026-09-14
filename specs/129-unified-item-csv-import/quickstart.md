# Validation

Run from the feature worktree. Backend commands use `PYTHONPATH=src` in
`packages/reality-core` and the root `.venv/bin/pytest`.

## Verified feature checks

- New service/API/concurrency regressions plus existing source-ingestion/demo-file suites: **24 passed**. New test family has 16 cases including parameterized invalid files.
- Explicit real browser runner: `PYTHONPATH=src ../../.venv/bin/pytest -q tests/browser/unified_item_csv_import.py -s` — **1 passed in 91.85s**. Requires `PLAYWRIGHT_MODULE` and `PLAYWRIGHT_EXECUTABLE`; uses disposable PostgreSQL and dedicated API/Vite processes.
- Browser proof: ordinary member; real BOM/semicolon CSV and manual mapping; lost preparation response and recovery; lost confirmation response and read-only recovery; reload/bookmark; exact bytes from original download; persisted item/source receipt; foreign artifact rejection; cancellation creates no third item.
- Real browser screenshot review: desktop English review and German 390px dark recorded result inspected; no horizontal page overflow. Automated checks cover English, German, Dutch and Spanish at 390px/1440px; item Inspector opens from the verified receipt.
- Existing source browser: **passed**, including 48 localized layouts and no-write evidence navigation.
- Web build passed; **131** contracts, **100** i18n tests and **1723** translation keys in each supported language passed. Prettier check passed.
- Root lint, spec-policy and diff whitespace checks passed.

Artifacts: `/private/tmp/reality-129-real-browser`, `/private/tmp/reality-129-real.log`,
`/private/tmp/reality-129-focused.log`, `/private/tmp/reality-129-sources-browser.log`
and `/private/tmp/reality-129-*.log`. No shared company data was imported.
The browser harness was corrected to wait for the deliberately aborted preparation
request before removing interception; mapping controls received explicit accessible
names. The final real browser run passed without browser errors.

## Full regression gate

Complete backend command: `PYTHONPATH=src ../../.venv/bin/pytest -q` — **1705 passed, 7 existing skips in 586.82s**. Core source/tests remained frozen during the run. Log: `/private/tmp/reality-129-backend-full.log`. All required gates are green. The production build retains its existing advisory about chunks larger than 500 kB.
