# Verification

Validated on 2026-09-15 against main 6e8a422d plus this change.

- Docker TypeScript/Vite production build: PASS (existing bundle-size advisory).
- Composer browser acceptance against the Docker bundle: PASS. Covers all three starters, editable draft and focus, no implicit submission, draft protection, historical-message hiding, four UI languages, keyboard use, desktop/mobile overflow and existing composer regressions.
- Independent /app/chat page: PASS; all three starters render and selection fills its composer. Desktop screenshot visually reviewed.
- Frontend contract suite: 177 tests passed.
- Localization audit: PASS for en/de/nl/es, zero missing or invalid translations.
- Changed frontend files: Prettier PASS; git diff --check PASS.
- Specification policy: PASS.

The initial missing-button acceptance failed before implementation. No backend, schema or catalog changes require additional migration or generated-reference checks.

For Docker acceptance, set UNIFIED_BASE_URL=http://127.0.0.1:8080 and PLAYWRIGHT_MODULE to the installed Playwright index.mjs, then run node apps/web/scripts/unified-chat-composer-browser.mjs. PLAYWRIGHT_EXECUTABLE can select an installed Chromium-compatible browser.
