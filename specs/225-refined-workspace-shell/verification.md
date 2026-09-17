# Verification: Refined workspace shell

## Environment and scope

Worktree `/private/tmp/reality-225`, branch `225-refined-workspace-shell`, based on
`origin/main` at `5130b476`. Original checkout changes were not imported or modified.
Local Vite preview used port 5225. Browser fixtures contain synthetic records and
make no real business writes. Chromium only; Safari/Firefox are not claimed.

## Test-first evidence

The new acceptance script failed before implementation at `60 !== 48` for the
content header. Final acceptance checks verify actual geometry and interactions,
not only source text.

## Required checks

- Spec policy and Ruff: PASS.
- Web formatting, 232 Node contract tests, four-language audit (1896 strings per
  language), TypeScript and production bundle: PASS, including the final rerun.
- Generated documentation catalog check: PASS, no generated diffs. Initially the
  isolated checkout lacked the docs formatter dependency; linking the installed
  dependencies restored the generator's normal formatting step.
- `git diff --check`: PASS.
- `scripts/ci_backend_changes.py`: `changed=false`, matching the web-only scope.

## Browser acceptance

- Refined shell: company placement, 48px aligned headers, description Escape/focus,
  chat draft retention, company isolation, Activity, populated action popover,
  profile theme toggle, standalone chat, short-height profile and 32 combinations
  of four languages, four widths and two themes. Touch targets cover collapsed
  navigation, utilities, company/status controls, chat controls and action entries.
  Final mobile action-dismissal and touch-menu rerun: PASS.
- Collapsible navigation: PASS; keyboard, tooltips, profile/company access, stored
  preference, blocked-storage fallback, draft preservation and mobile behavior.
- Live simulation: PASS; eligibility, all non-running/error states, timeout/recovery,
  hidden-page behavior, reduced motion and stale-company response suppression.
- Page introductions: PASS; 46 desktop/mobile route layouts and three translations,
  with unavailable business reads and accessible description disclosures.
- Title counts: PASS; 18 registers, zero/filter/error recovery, nested catalog,
  navigation and mobile actions. Lower technical disclosure is exercised by keyboard
  because the existing fixed footer can intercept a pointer click there.
- Action discovery with `LAUNCHER_ONLY=1`: PASS; catalog navigation/search, launcher
  dispatch, failed-catalog recovery and mobile bounds; zero business writes. Old
  finance toolbar assertions remain available in the full script, outside this scope.

## Optional backend diagnostic

An additional parallel PostgreSQL run was interrupted after the first failure to
inspect it: **1448 passed, 1 failed, 2 skipped** in 597 seconds. The failure was
`tests/scenarios/test_international_demo.py::test_canonical_profile_counts_and_cases`
with `JobError("handler_timeout")`. The unchanged test then passed alone in 12.35s.
This supports a load-related timeout but does not prove the entire backend suite
passes. No backend implementation, fixture or timeout was changed. The full backend
suite is neither required by the CI changed-path gate nor claimed complete here.

## Visual review

Inspected German desktop light/dark, 1024px dark, mobile dark and collapsed-rail
screenshots. Shell headers align, company/global controls have separate homes and
long company names truncate without page overflow. Theme screenshots disable CSS
transitions to capture the settled appearance. Artifacts are in
`/private/tmp/reality-225-browser/`. No production deployment or merge performed.

## Activities consolidation follow-up (2026-09-17)
- Navigation contract: observed expected old-label failure, then 5/5 passed.
- `gmake web-build spec-check lint docs-catalog-check`: PASS, including formatting,
  232 Node tests, all four translation catalogs, TypeScript and production build.
  Existing large-chunk build warning remains non-blocking.
- Refined shell browser: PASS, 32 localized layouts plus rail, touch, company and
  keyboard checks. Explicitly checks one translated Activities navigation link,
  absence from bottom utilities, unchanged history URL and embedded reader.
- Shared activity browser: PASS through Home, including paging, failed read retry,
  stale response/tenant isolation, inspection, retained page selection, focus and
  16 localized layouts; no business writes or browser errors.
- German desktop screenshot visually reviewed: Activities replaces Event history;
  bottom utilities contain Actions/Profile only. Screenshots remain under
  `/private/tmp/reality-225-browser/`.
- `git diff --check`: PASS. Backend unchanged; no exclusive endpoint exists to remove.
  Full backend suite was not rerun for this frontend-only follow-up.

## Action translation regression verification
- New executable-catalog translation regression failed on exactly five missing keys
  per non-English language before implementation; all three language tests now pass.
- `gmake web-build spec-check lint docs-catalog-check`: PASS; 235 tests, four language
  audits, formatting, TypeScript, production build and generated catalog consistency.
- Refined shell browser: PASS, including all five German labels and translated
  package search at 320/390/1024/1440px, plus the existing 32-layout matrix.
- `git diff --check`: PASS. No backend changes or backend suite needed.

## Command palette presentation verification
- `gmake web-build spec-check lint docs-catalog-check`: PASS; 235 tests, all four
  translation audits, formatting, TypeScript and production build. Updated the
  superseded lower-utility placement contract; shortcut symbols have explicit
  reviewed invariant entries, with German Strg notation translated.
- Refined shell browser: PASS, both keyboard modifiers, initial search focus,
  query reset, Escape focus return, centered bounds, mobile keyboard access with
  closed navigation, existing tenant/draft checks and 32 localized layouts.
- Action discovery launcher browser: PASS, action form invocation, modal shortcut
  precedence, catalog error/retry, translated search and mobile bounds; zero writes.
- Visually inspected German desktop dark and mobile light palette screenshots.
  Artifacts: `/private/tmp/reality-225-browser/command-palette-de.png` and
  `/private/tmp/action-discovery-screens/mobile-menu-de.png`. Menu screenshots avoid
  full-page resizing, which intentionally dismisses the palette.
- `git diff --check`: PASS. No backend changes; future command features remain deferred.

## Quiet shell boundaries verification
- `gmake web-build spec-check lint docs-catalog-check`: PASS (235 tests, translation
  audits, formatting, TypeScript, production build and generated-doc consistency).
- Existing refined shell browser: PASS, including 32 language/theme/viewport layouts
  and keyboard/menu geometry. German desktop light screenshot reviewed: no header
  rules or sidebar border; content/chat divider remains.
- Diff review confirms active-tab indicator and all content separators unchanged.
- `git diff --check`: PASS. No backend changes or new tests required.

## Sidebar head grouping verification
- Updated placement contracts fail before implementation and pass afterwards.
- `gmake web-build spec-check lint docs-catalog-check`: PASS, including 235 tests,
  formatting, translation audits, TypeScript, build and generated catalog consistency.
- Refined shell browser: PASS, 32 localized layouts, touch targets, company and palette
  access, keyboard focus and preserved drafts.
- Collapsible navigation browser: PASS, new head placement, no visible Daily work
  heading, rail, mobile, keyboard, profile, persistence and localization.
- German desktop light and collapsed-rail screenshots visually reviewed; artifacts
  in `/private/tmp/reality-225-browser/` and `/private/tmp/reality-203-browser/`.
- `git diff --check`: PASS. No backend behavior changed.

## Unified tab header verification
- `gmake web-build spec-check lint docs-catalog-check`: PASS; 235 tests, formatting,
  all language audits, TypeScript, production build and generated-doc consistency.
- Page-introduction browser: PASS, 46 desktop/mobile routes and three translations,
  shared header placement, retained information and active tab styling, menu bounds
  and Escape dismissal where actions exist.
- Title-count browser: PASS, 18 registers, active-tab placement, zero/filtered/error
  states, tab transitions, nested documents, title-only navigation and mobile counts.
  Populated action menus verified across available registers; German sales menus
  verified at 1440/390px, with screenshots reviewed for alignment and containment.
- Refined shell browser: PASS, 32 localized layouts, company/draft isolation, palette,
  keyboard and touch behavior.
- Visual examples: `/private/tmp/reality-225-tabs-de-1440.png` and
  `/private/tmp/reality-225-tabs-de-390.png`. No second tab/action row remains.
- `git diff --check`: PASS. Existing large-chunk warning remains non-blocking; no
  backend code or business calculations changed.

## Commitments header regression verification
- Placement contract failed before implementation, then passed.
- `gmake web-build spec-check lint docs-catalog-check`: PASS, 235 tests, formatting,
  translation audits, TypeScript, production build and catalog consistency.
- Daily-work browser: PASS for three queues across English/German, light/dark and
  desktop/mobile (24 queue/layout combinations). Header tabs/count placement, side
  switching/reload, pagination, inline preview, filters and zero business writes verified.
- German desktop screenshot reviewed: customer/supplier tabs and counts share the
  header, with no second direction strip. Artifacts in `/private/tmp/reality-work-lists/`.
- `git diff --check`: PASS. No backend changes.

## Inbox consolidation verification
- New membership test failed before implementation; final frontend suite: 236/236 PASS.
- `gmake web-build spec-check lint docs-catalog-check`: PASS, including formatting,
  all supported translations, TypeScript, production build and generated catalog check.
- Daily-work browser: PASS, 24 queue/layout combinations in English/German, both themes
  and desktop/mobile. Direct Inbox tab clicks, tenant preservation, sidebar default,
  removal of old links, no aggregate badge, side/reload behavior, paging, previews,
  filters and zero business writes verified.
- Page-introduction browser: PASS, 46 desktop/mobile layouts and three translations.
- Title-count browser: PASS, 18 registers, nested views, filtered/error/zero counts
  and mobile menu bounds.
- German desktop screenshot reviewed in `/private/tmp/reality-work-lists/`: one Inbox
  navigation entry, three primary tabs and subordinate direction controls.
- `git diff --check`: PASS. No backend or confirmation behavior changed.

## Empty standalone chat history verification
- `gmake web-build spec-check lint docs-catalog-check`: PASS, including 236 tests,
  formatting, translation audits, TypeScript, production build and generated docs.
- New empty-chat-history browser: PASS for empty layout, first-session stability,
  explicit history opening/closing, draft preservation, saved-history revisit, mobile,
  in-place company switching, archived-only history and retry after initial read failure.
  No browser errors. Final overlay availability handling covered by a repeated run.
- Empty desktop screenshot `/private/tmp/reality-empty-chat.png` reviewed: history
  column absent, centered welcome/composer and independent New chat toolbar action.
- `git diff --check`: PASS. No backend changes.
