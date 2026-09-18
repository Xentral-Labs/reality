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

## FR-015 continuous register surfaces
- `gmake web-build spec-check lint docs-catalog-check`: PASS, including 236 Node tests, localization audit, TypeScript and Vite. Existing bundle-size advisory only.
- `register-footer-browser.mjs`: PASS for populated open items/payments/journal at 1440px and 390px, chat toggles, aligned table/footer, independent scrolling, selection controls, healthy freshness, compact empty state and no page overflow. Updated obsolete shell selectors and completed fixture view metadata. Initial run encountered a stale description selector before the new geometry assertion, so no meaningful test-first failure is claimed.
- `page-title-counts-browser.mjs`: PASS, 18 registers plus tab, zero/error, nested navigation and mobile checks.
- `projection-freshness-browser.mjs`: PASS, in-flight, unchanged/newer outcomes, backlog and four languages.
- Visually inspected `/private/tmp/content-heading-screens/finance-0-1440.png` and `/private/tmp/reality-register-empty-dark.png`; footer and toolbar align and mobile empty guidance remains readable.
- Backend suite not rerun: presentation-only changes, no API/service/schema modifications.

## FR-016 sidebar simulation removal
`gmake web-build spec-check lint` PASS: 236 tests, formatting, all four localization audits, TypeScript, Vite, spec policy and Ruff. Existing bundle-size advisory only. Focused `live-simulation-header-browser.mjs` PASS for desktop, collapsed/mobile absence, zero indicator polling and retained tenant-scoped simulation route. Updated shell absence assertion failed before removal and passes afterward. No backend/schema changes; backend suite not rerun.

## Inbox Welcome (FR-017–018), 2026-09-18

- Scope authorized by the owner: dissolve Home into Inbox Welcome, prioritize company
  activity and choose three supporting operational links. Spec/plan/tasks reviewed
  before implementation: two requirements, three mapped tasks, no critical findings.
- Test-first: daily-work membership/fresh-entry tests failed before implementation
  (home was outside Inbox); all four focused tests pass afterward.
- `gmake spec-check lint web-build docs-catalog-check`: PASS. Web gate includes
  formatting, all 275 contract tests, all four-language translation audits and
  TypeScript/Vite production build. Generated documentation has no remaining diff.
- Home live browser: English/light/desktop complete polling, stale/error recovery,
  hidden-tab suspension, company isolation, ranges and drilldown passed. The pointer
  test initially hit an existing subpixel partial bucket on mobile; hover coverage
  now uses the preceding complete bucket. `HOVER_ONLY=1` full 16-case language/theme/
  desktop-mobile matrix passes, including independent dashboard loading, first
  Welcome tab, active Inbox, no Home entry, content order and no writes.
- Visually reviewed German desktop/mobile screenshots in
  `/private/tmp/reality-graph-browser/`: activity first, three compact queue links,
  shared header navigation, readable themes and no horizontal overflow.
- Final scope review: HomePulse and application services untouched, no schema or
  permissions changes. Existing landing and queue URLs preserve tenant context.
  Backend and migration runs are not required for this adapter-only change.

### Final styling and status refinement

- Owner-requested FR-019 removes enclosing cards, reduces heading/body spacing,
  reuses neutral local tabs and gives unconfirmed readiness a theme-aware caution
  triangle. A loader marks checking; ready retains the checkmark.
- Final full `home-live-browser.mjs`: PASS, all 16 language/theme/viewport cases,
  including polling, stale recovery, warning icon, period preferences and
  company switching. Desktop/mobile screenshots reviewed after the flat restyle.
- Final `daily-work-browser.mjs`: PASS, all eight language/theme/viewport cases,
  all three queues, filters/paging/previews, Welcome default, three shortcuts,
  back/reload, tenant preservation and zero writes.
- German mobile fourth-tab overflow was traced to the absolutely positioned
  screen-reader count label; position: relative on the existing count wrapper
  contains it in the scroll strip. The unchanged overflow assertion now passes.
- Final gates after all changes: `gmake spec-check lint web-build docs-catalog-check`
  PASS (275 frontend tests, four-language audit, production build, formatting and
  generated catalog consistency). `git diff --check` PASS. T041–T045 complete.

## FR-020 compact standalone chat navigation — 2026-09-18

The owner approved History disclosure followed by New chat directly in the existing
header. Pre-implementation analysis: FR-020 maps to T046–T048; 100% incremental
coverage, no unresolved clarification or critical consistency/Constitution findings.
The adapted browser fixture initially failed on the original icon-only action's
missing label; the shared action contract failed before explicit inline presentation.

Browser acceptance passes direct access without a menu, History second-click closing,
Escape/Close focus, outside dismissal, drafts, stable conversation bounds,
new/session/archive actions, archived-only access, read retry, tenant isolation and
41-session scrolling. English/German/Dutch/Spanish headers fit at 320px, including
the page title. Reviewed desktop, mobile and translated screenshots. At <=360px,
labels use compact spacing and New chat omits its decorative plus; labels remain.

`gmake web-build` passes all 275 contracts, formatting, four-language audit, TypeScript
and Vite. Spec policy, Ruff and generated docs checks pass. Existing chunk-size
advisory only. Backend/schema/migration checks are inapplicable to this web-only
change. Final review preserves the default action menu on other pages, dock controls,
tenant-scoped services, confirmation and source authority.

PR verification repeated on origin/main at 5746db5e in the isolated PR worktree:
full web-build, spec-check, lint, docs-catalog-check and the browser matrix all pass.
