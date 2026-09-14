# Validation
From packages/reality-core run PYTHONPATH=src ../../.venv/bin/pytest -q tests/test_unified_business_journey.py.
For real UI proof set PLAYWRIGHT_MODULE and PLAYWRIGHT_EXECUTABLE to installed Playwright/Chrome, then run PYTHONPATH=src ../../.venv/bin/pytest -q -s tests/browser/unified_business_journey.py. Set JOURNEY_ARTIFACTS to an output directory to retain logs/screenshots/results. The runner owns a disposable PostgreSQL database plus dedicated API and Vite processes; it must not use localhost5177/8007 or shared tenant data.
After bounded repairs run complete backend and frontend gates; record verified results and findings here.

## Findings during real-browser validation
- The linked service story passes for partial and full refund variants.
- Harness setup corrections: evidence collection uses /evidence-documents; scope the Actions menu to the banner because table columns also use Actions; reversal confirmation correctly uses its existing Confirm reversal label. These are harness corrections, not product defects.
- Product defect (FR-002/005): the real refund reversal review labels both REF-127 and CR-127 balances as Open invoice amount. These are a refund and credit, not invoices. Replace the overly narrow amount/intro labels with financial-posting wording in FinancialReversalCard.tsx, translate all four languages, and assert the correct labels in the real journey. No business calculation changes. Reproduction screenshot: /private/tmp/reality-127-browser/error.png.

The added real-browser label regression failed as expected (0 correct labels instead of 2) in /private/tmp/reality-127-label-red.log before the wording repair. The correction changes presentation only; balances and posting behavior are unchanged.

## Verified result — 2026-09-08
- Shared-tool journey: partial and full refund variants passed. Complete backend: 1689 passed, 7 existing skips in 443.00s (`/private/tmp/reality-127-backend-full.log`).
- Explicit real-browser journey: one passed in 115.91s. All eight actual form stages review, confirm, persist and reload verified evidence. Final stock 14 / reserved 4 / delivery open 4; invoice open 0; credit 125 after refund 75 and 200 after refund reversal. Original refund proof remains verified and allocation inactive.
- Actual credit Inspector opened; database assertions verify invoice→order and credit→invoice links. Source-stated invoice/credit amounts are preserved. UI screenshots reviewed for the real reversal and credit evidence, plus localized reversal layouts.
- Test identity is an ordinary owner in a disposable migrated PostgreSQL database. API, Vite and browser process groups are owned/terminated by the runner; database cleanup passed. No shared company records or credentials used, no external bank or AI provider execution.
- Production web build, 131 UI contracts, 100 i18n tests, 1,681 keys in four languages, formatting, lint/spec/diff and existing 16-view reversal browser passed.
- Scoped repair: financial reversal copy uses Open amount and financial posting wording for credits/refunds as well as invoices. No service/business logic, schema or migration changes.
- Artifacts: `/private/tmp/reality-127-browser-final/` contains API/migration/web/browser logs, every stage review/receipt screenshot, final Inspector and result.json. Failing wording proof is retained under `/private/tmp/reality-127-browser-red/`.
- Local development UI receives the wording change through Vite; no API restart, deployment, merge or legacy retirement required/performed.
