# Verification

2026-09-16. User-approved central fix. Two requirements mapped to three tasks, no unresolved clarifications or Constitution findings.

- Browser regression before CSS: failed with left=0, right=0; no horizontal overflow.
- After the shared rule: desktop (1440px) and mobile (390px) passed for ready, pending, failed and uninitialized states. Both insets are 16px; refresh works; no notice overflow.
- Nested padded and standalone contexts retain 0px additional horizontal margin. The mobile test closes the existing chat overlay before interacting with the underlying notice.
- `gmake spec-check web-build`: passed, including formatting, 203 frontend tests, all four localization audits, TypeScript and production build. Existing bundle-size advisory only. Updated browser script formatting separately passed after closing the test overlay.
- Manual diff review: one four-line shared CSS rule; no page-specific production changes, copy, runtime logic or business/data changes. Backend tests not needed for this CSS-only correction.

Reproduce the focused browser check with `NOTICE_SPACING_ONLY=1` and the existing UNIFIED_BASE_URL/Playwright environment variables for `apps/web/scripts/unified-finance-browser.mjs`.
