# Verification

Validated on 2026-09-15 on main e03a78e1 plus this feature.

- Initial browser proofs failed on missing collapse control and heading integration before their implementation.
- Browser acceptance PASS: 200px/60px widths, 140px content expansion, keyboard toggle, preserved navigation names and active state, retained chat draft, profile popover, company switcher, preference persistence, four languages and labeled 390px mobile drawer.
- Sidebar preference storage failure: expanded fallback and usable toggle.
- Custom tooltips: native titles absent, dark tooltip visible on hover and focus, correct positioning beyond the sidebar, Escape/scroll dismissal.
- Heading row: at most 36px; expanded/collapsed/mobile and tooltip screenshots visually reviewed.
- Frontend contract suite: 180 tests passed.
- Localization audit: en/de/nl/es PASS, zero missing/invalid strings.
- Prettier, TypeScript/Vite production build, git diff --check and specification policy: PASS. Existing bundle-size advisory remains.
- Local Docker web rebuilt and verified on port 8080.

Final review: one navigation tree and unchanged targets, no content/chat remount, desktop preference isolated from mobile styling, profile and company access retained. No schema, business service, command or catalog changes; backend and migration checks do not apply.

Browser reproduction: set UNIFIED_BASE_URL, PLAYWRIGHT_MODULE and optionally PLAYWRIGHT_EXECUTABLE, then run node apps/web/scripts/collapsible-navigation-browser.mjs.

Rebased onto main 9a01c2d2 before PR creation. Sidebar browser acceptance, all 185 frontend contract tests, four-language localization audit, TypeScript/Vite build and spec policy passed again.
