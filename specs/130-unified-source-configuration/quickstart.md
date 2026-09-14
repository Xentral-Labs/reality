# Verification

Run from the feature worktree; web commands in apps/web. Browser prerequisites:
`PLAYWRIGHT_MODULE` points to the installed Playwright module, `PLAYWRIGHT_EXECUTABLE`
to Chrome. No shared company data is changed by the stateful HTTP browser fixtures.

- `npm run test:source-configuration-browser`: source creation, normalized review,
  cancel/duplicate, source/type flag changes, bookmark reload, lost response and failed
  current-state checks, foreign selection, received-record routing, 25-type pagination,
  double-click prevention and company switch while the POST response is held. Four
  languages at 390px and 1440px with actual data-theme=dark; screenshots disable CSS
  transitions. Includes empty declarations and initial-read failure/retry.
- `npm run test:sources-browser`: passed, including 48 localized evidence layouts.
- `PYTHONPATH=src ../../.venv/bin/pytest -q -s tests/browser/unified_item_csv_import.py`
  in packages/reality-core: **1 passed in 62.60s**. Actual CSV bytes/review/confirmation,
  recovery and download against isolated migrated PostgreSQL plus private API/Vite.
- `npm run test:contracts`: **131 passed**.
- `npm run test:i18n`: **100 passed**.
- `npm run i18n:audit`: **1746 keys per language**, all four passed.
- `npm run build` and `npm run format:check`: passed. Existing chunk-size advisory remains.
- `make lint`, `make spec-check` and `git diff --check`: passed.

Logs: `/private/tmp/reality-130-*.log`; screenshots:
`/private/tmp/reality-130-browser`. Desktop initial layout and German 390px dark
configuration inspected. The initial test failed at absent Register source before
implementation. A later browser-harness reload was corrected to await the known
response; an early reload correctly retained the unresolved marker. No backend source
or tests changed in this feature.

## Final gates
Complete backend `PYTHONPATH=src ../../.venv/bin/pytest -q`: **1705 passed, 7 existing skips in 430.64s**. Final source configuration browser passed including empty declaration and initial-read retry cases; final format check passed. All planned checks are green. Frontend is served by the existing local Vite process at http://localhost:5177/app/data-sources; no API restart is needed because backend code is unchanged.
