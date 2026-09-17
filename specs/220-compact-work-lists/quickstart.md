# Validation

Start Vite with `npm run dev -- --port 5193` in apps/web. Set PLAYWRIGHT_MODULE to the installed Playwright index.mjs and PLAYWRIGHT_EXECUTABLE if needed, then run `node scripts/daily-work-browser.mjs` there. Screenshots are written to /private/tmp/reality-work-lists.

Run `npm run test:contracts`, `npm run build`, `npm run i18n:audit` in apps/web and `make spec-check` at the repository root. Verify 44px wide rows, stacked narrow rows, aligned metadata, working previews, filters and pagination, and zero mutation requests.

## Verification Evidence — 2026-09-17

- Pre-implementation browser proof failed as expected: old wide row height 68px, required 44px.
- Updated browser fixture passed all 24 page combinations (three queues, EN/DE, light/dark, desktop/mobile), including geometry, keyboard preview, filtering, paging, overflow and zero writes.
- Screenshots reviewed for all three desktop queues and the narrow dark commitment list; aligned columns, metadata and readable stacked rows confirmed.
- Frontend contract suite: 219 passed, zero failures. Updated the existing exception-toolbar structural assertion to recognize its new shared class.
- Production build and four-language localization audit passed. Build retains its existing large-chunk advisory.
- Spec policy passed via `python3 scripts/check_spec_policy.py`, the exact Make target command; macOS `make` itself is blocked by the unaccepted Xcode license.
- Changed frontend files pass Prettier; `git diff --check` passes.
- Final review: no API, domain, service, persistence, permissions or confirmation changes. No catalog generation needed because no catalog/schema vocabulary changed.
