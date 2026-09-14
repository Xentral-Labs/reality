# Analytics implementation evidence

On 2026-09-13 the owner accepted the product scope and the concrete
architecture/schema design. CHK001–009 passed, and consistency analysis found
coverage for all 25 FR/DR requirements with no unresolved clarification or critical
cross-artifact issue.

## Delivered behavior

The implementation provides one strict analytical definition and read-only
PostgreSQL execution capability shared by the application layer, MCP, CLI and Web.
It covers the 30-question assessment through exact results or explicit restricted
answers, provides contributor navigation and bounded CSV export, and adds the
Overview, Explore and My reports workspace. Private report changes use the existing
proposal/confirmation mechanism with trusted tenant and owner context. Agent handoff
uses a typed visible attachment in the existing chat.

The only new business table stores tenant- and owner-scoped report definitions. It
does not store analytical results or introduce a second database. Migration 0060 was
verified through upgrade/downgrade guards in disposable PostgreSQL databases and was
also applied to the owner-approved local development database.

## Automated verification

- `../../.venv/bin/pytest -q -n 4 --tb=short` from `packages/reality-core`:
  **2420 passed, 9 skipped in 383.02 s**. One pre-existing SQLAlchemy cleanup warning
  was emitted by `test_storyline_library_api.py`; no test failed.
- The nine focused Analytics test modules passed again after final formatting:
  **53 passed in 6.14 s**.
- The 29 migration cases that had first been invoked from the wrong working directory
  were rerun from `packages/reality-core`: **29 passed in 28.57 s**.
- The strict 10,000-source replay timing test passed alone without benchmark load:
  **1 passed in 13.31 s** against its 60-second bound.
- `make lint`, `make spec-check` and `git diff --check` passed.
- Web contracts and localization: **128 passed**; the TypeScript/Vite production
  build passed with **1965 modules**. Vite reports its existing large-chunk advisory.
- Public Site: **61 passed** and production build passed.
- `make docs-generate` completed; `make docs-build` passed its 4 generator unit tests,
  Prettier check, **61 documentation tests**, and VitePress build. Generated bilingual
  Tool Usage pages and `apps/docs/.vitepress/data/tool-usage.json` are retained.
- Analytics browser acceptance passed draft/executed-result separation, localized
  errors, chart, contributors, private save/reopen/rename/duplicate/delete, CSV,
  mobile width and English/German/Dutch/Spanish. Screenshots are local evidence at
  `/private/tmp/reality-185-browser/desktop.png` and `mobile.png`.
- The existing chat-composer browser acceptance passed reference attachment, text,
  voice teardown, keyboard, immediate echo and send-failure retention.

The broad legacy `unified-shell-chat-browser.mjs` still asserts a 56 px header while
the current shell renders 60 px at its hard-coded server URL. It fails at that
pre-existing pixel assertion before reaching chat behavior. The current shell layout
contracts, all Web contract tests, the dedicated chat-composer run and the Analytics
handoff browser path pass. This unrelated stale assertion was not changed as part of
Analytics.

## Performance evidence

`packages/reality-core/benchmarks/analytics/run.py` created an isolated database and
loaded **100 orders × 1,000 lines = 100,000 order lines** through the normal
`create_manual_order` service. After `ANALYZE`, it executed eight representative
Q01/Q04/Q06/Q07/Q08/Q09/Q22/Q23 definitions once as the first observation and 20 warm
times each, for **168 runs**. The first-observation p95 was **2.053 s**, warm p95 was
**1.940 s**, and the slowest run was **2.725 s**. This passes SC-005's p95 below five
seconds and every-run bound below 30 seconds.

The benchmark reports 18 customer/week groups, 20 customer comparison groups, 100
product groups, 500 weekly-product groups, 4,950 product pairs, 2,000 customer-product
price groups, 500 purchase-week groups and 1,000 supplier-product groups. Every
captured plan parameterizes tenant scope; the selective product/week plan uses an
index. “First observation” means the first analytical query after ordinary intake
and PostgreSQL `ANALYZE`; PostgreSQL and operating-system caches were not forcibly
flushed. The machine-readable local result is
`/private/tmp/reality185-benchmark.json`. The runner now preserves this method and
always removes its `reality_benchmark_analytics_*` database, including after failure.

## Final review

All FR-001–FR-019, DR-001–DR-006 and SC-001–SC-007 have implementation and acceptance
evidence. The implementation keeps PostgreSQL as the sole database, applies tenant
scope in repositories, derives analytical observations at read time, reuses the
application tools for Web/CLI/agent, and requires confirmation only for private report
mutations. No merge or deployment was performed.

## Chart guidance correction — 2026-09-13

- FR-010/FR-016: distinguish missing grouping, mixed currencies, mixed units and
  both; every message names the required setting and asks for explicit re-execution.
- Test-first proof: 8 blocker cases failed against the generic message; 2 compatible
  chart cases passed. After correction, all 10 rendered component cases pass across
  bar and line charts. Rendering also exposed a React SVG title warning; a single
  template string preserves the tooltip text and removes the warning.
- `npm run test:contracts`: PASS, 150 tests.
- `npm run build`: PASS (existing large-bundle advisory).
- `make spec-check` and `git diff --check`: PASS.
- `npm run i18n:audit`: FAIL outside this correction: 12 missing keys per de/nl/es
  in concurrently added `CompanyDangerZone.tsx`. All four new chart guidance keys
  have en/de/nl/es coverage. T040 remains open until the global gate passes.
- Final correction diff review: no data/API/schema/catalog changes; partition
  boundaries, loaded-row bounds, selected measure and table fallback preserved.
  Unrelated concurrent company-management changes were not edited.

## Recognizable Explorer controls — 2026-09-13

- Root cause: `br-input` had no CSS definition. The Explorer now uses shared
  `br-control` fields, native selectors with decorative chevrons, and a bordered
  keyboard-operable Filters disclosure. Scoped CSS reserves chevron space against
  legacy unlayered styles; the date grid fits its available container width.
- Browser test-first proof: the dataset control failed with a 0px border before
  implementation. Dataset/sort controls now pass the 1px border and >=44px target
  checks. Native keyboard type-ahead changes sorting; Enter opens/closes Filters.
- Full `analytics-browser.mjs`: PASS, including existing explicit-run, error,
  charts, contributors, saved reports, CSV, mobile overflow and four-language flow.
- Visually inspected desktop, 390px mobile and dark-mode screenshots under
  `/private/tmp/reality-185-browser/`; dark control colors asserted after the CSS
  transition settles. No page-level horizontal overflow.
- `npm run test:contracts`: PASS (150); `npm run build`: PASS;
  `npm run i18n:audit`: PASS (en/de/nl/es); `make spec-check`: PASS;
  `git diff --check`: PASS. The earlier unrelated translation failure is resolved.
- Final review: no services, schema, data values or execution semantics changed.
  Existing business and migration suites are unaffected by this presentation fix.

## Direct chart selection — 2026-09-13

Supersedes narrowing guidance for mixed partitions. Charts default to the first
loaded currency/unit partition and provide native pressed-state buttons to switch.
The selection only filters displayed rows; no values or totals are recomputed.
Ten rendered tests pass (currency, unit, combined, unknown, partitions beyond 50,
missing grouping and compatibility, for bar/line). Browser tests prove immediate
EUR rendering, USD row isolation and switching for both chart types with no extra
query. Existing browser lifecycle, mobile, dark and localization checks pass.
Desktop screenshot reviewed. Frontend contracts: 150 PASS. Localization: all four
languages PASS. Spec/diff checks PASS. Docker TypeScript/Vite build PASS and local
web container rebuilt for port 8080. No backend/schema/catalog change.

## Dedicated analysis chat — 2026-09-13

- Browser test failed before implementation because the explicit new-chat action
  was absent. After implementation, analytics browser flow PASS: existing chat,
  creation failure retains draft, successful creation switches to one new session,
  no automatic message, first send includes its analysis definition, and history
  returns to untouched old messages with no attachment leaking into that session.
- Existing chat composer browser regression PASS (draft attachment, dictation,
  keyboard send, immediate echo, failure retention and conversation switching).
- Frontend contracts: 150 PASS; localization: en/de/nl/es PASS; TypeScript/Vite
  build PASS; spec policy and diff checks PASS.
- Existing shell-chat browser regression FAILS before chat interactions on its
  fixed shell-header height assertion: expected 56px, current layout is 60px.
  This change does not edit shell header/layout. T046 verification remains open
  because the complete required regression set is not green.
- Final diff review: shared existing session API, no direct persistence/business
  mutations, no automatic sends, creation lock, preserved failures, stale-session
  send guard, session-bound attachments and tenant-keyed unmount retained.
- Local deployment: `docker compose -f compose.yml up -d --build --no-deps web`
  succeeded. Full analytics browser fixture flow also PASS against the actual
  production frontend bundle at `http://127.0.0.1:8080`.

## Isolated PR verification — 2026-09-13

Prepared `fix/analytics-controls-chart-chat` directly from main (`9f0f695`) in a
separate worktree. Excludes the unrelated company danger-zone commit and its
translations. Removes obsolete intermediate currency-narrowing translations.
On this exact isolated tree: frontend contracts PASS (144 tests), production Web
build PASS, en/de/nl/es localization audit PASS, spec policy PASS, diff check PASS.
Earlier 150-test evidence included six unrelated company lifecycle tests. The
known shell-header assertion remains documented; PR is draft pending that gate.

PR #252 CI follow-up: frontend-quality found Prettier wrapping differences in the
chart test and localization additions. Applied Prettier to both files; the full
`npm run format:check` now passes. Formatting only; no behavior changes.
