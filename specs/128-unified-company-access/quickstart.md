# Validation
Run npm run test:company-access-browser in apps/web with PLAYWRIGHT_MODULE and PLAYWRIGHT_EXECUTABLE configured and unified Vite running. All HTTP calls are intercepted; no real mail or business data changes. Run npm run test:settings-browser for preferences and owner summary regression.
Run PYTHONPATH=src ../../.venv/bin/pytest -q from packages/reality-core against isolated PostgreSQL fixtures. Run web build, contracts, i18n audit/tests, format check; root make lint, make spec-check and git diff --check.
Manually open /app/settings?settings_view=company and access in light/dark and mobile. Do not submit a real invitation without an intended recipient.

## Verified 2026-09-08
- Initial browser proof failed at missing Company name input: /private/tmp/reality-128-browser-red.log.
- Final stateful browser passed: /private/tmp/reality-128-browser-final.log. Artifacts: /private/tmp/reality-128-browser (25 screenshots). Reviewed desktop invitation review, mobile German dark review and desktop company details. All HTTP intercepted; no real invitations or companies created.
- Existing settings browser passed including 48 localized responsive light/dark screenshots: /private/tmp/reality-128-settings-browser.log.
- Full unchanged backend suite: 1689 passed, 7 existing skips, 372.32 seconds; /private/tmp/reality-128-backend-full.log.
- Build, 131 UI contracts, 100 i18n tests, 1689 static keys in all four languages, format, lint, spec policy and diff whitespace checks passed.
- Browser harness correction: a revoke/removal wait originally matched both review and list email; scoped to list rows. Acceptance proof waits for the actual selected-company Home and Analytics card, not only its URL.
- Final review: exact returned tenant selection, existing API-only writes, unknown-result/recovery behavior, removal owner guard, disabled review controls and company draft cleanup checked. No schema or backend runtime change. Existing creation transaction gap remains explicitly documented.
