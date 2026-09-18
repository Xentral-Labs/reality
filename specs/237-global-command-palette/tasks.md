---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Global Command Palette

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [search contract](contracts/search.md), [UI contract](contracts/ui.md), [quickstart.md](quickstart.md).
**Created**: 2026-09-18
**Gate**: Constitution design rows PASS; scope accepted; read-only consistency analysis follows generation. No implementation starts with unresolved critical findings.
**Status**: Implementation in progress; completed gates and foundation carry evidence in verification.md.

All repository artifacts are English. Task paths are repository-relative unless explicitly prefixed by `specs/237-global-command-palette/`. Tests are mandatory for this feature and precede the code they prove. `[P]` means only that the marked tasks in the same phase may run independently after prerequisites; it does not authorize parallel edits to shared files or automatically spawn agents.

## Format and evidence rules

`- [x] T001 [P?] [USn?] [FR/DR/SC references] Action with exact file path`

Each requirement maps separately to test and implementation work below. Record red/green proof in verification.md as implementation proceeds. References to future files describe planned outputs, not existing code or passed checks. Migration numeric prefixes are assigned at implementation time to avoid colliding with concurrent feature migrations.

## Phase 1: Specification, Design and Setup Gates

Complete these gates before behavior changes. Existing unrelated changes in this checkout must remain intact. The generated reviewer checklist remains reviewer-owned; do not mark it as implemented.

- [x] T001 [SC-002] Record the accepted scope, pre-implementation architecture review and current checkout boundary in `specs/237-global-command-palette/review.md`; read Constitution, workflow and Web contracts, retain every PASS row in `plan.md`, and run the read-only Spec Kit analysis after task generation. Do not implement while critical findings remain. No automatic commit/merge is authorized.
- [x] T002 [SC-002] Establish disposable PostgreSQL, Python, Node and browser prerequisites from `specs/237-global-command-palette/quickstart.md`; record exact commands and baseline failures in `specs/237-global-command-palette/verification.md`, without changing unrelated tests or treating missing prerequisites as passes.

## Phase 2: Foundational Contracts and Database Support

Tests precede code. No new business table/field is allowed. This phase supplies shared types and matching support; user-story integration follows.

- [x] T003 [FR-007, FR-008, FR-021, DR-004] Add the shared four-language matching corpus in `packages/reality-core/tests/fixtures/global_search_matching.json` and failing pure tests in `packages/reality-core/tests/test_global_search_matching.py`: raw/normalized exact references, diacritics, short IDs, prefix/tokens, every single-edit kind, no fuzzy identifiers, stable identity and deterministic ordering.
- [x] T004 [FR-007, FR-008, FR-021, DR-004] Implement allowlisted request/result/target contracts, matching tiers and reference normalization in `packages/reality-core/src/reality/domain/search.py`; reject unknown fields/invalid bounds and use opaque physical identity. Match the corpus from T003; preserve original display values.
- [x] T005 [DR-005, SC-003] Add failing SQL parity and upgrade/downgrade/re-upgrade tests in `packages/reality-core/tests/test_global_search_migration.py`; prove unchanged existing business rows, UTF8 requirement, exact function/index ownership and no runtime-startup DDL.
- [x] T006 [FR-007, FR-008, DR-005, SC-003] Implement versioned normalization/single-edit SQL support in `packages/reality-core/src/reality/db/search_sql.py`; inventory existing indexes and add the reviewed, nonredundant support migration under `packages/reality-core/migrations/versions/` with suffix `_global_search_support.py`, assigning its actual revision from the then-current head. Record the final filename in `specs/237-global-command-palette/data-model.md`; never alter a versioned indexed function in place.
- [x] T007 [DR-005] Install identical search support explicitly in metadata-created test fixtures in `packages/reality-core/tests/conftest.py`; keep migration proof independent and preserve PostgreSQL isolation/rollback. Do not add an API/worker/scheduler startup installer.

## Phase 3: US1 — Navigate and Start Existing Work (P1)

Goal: search destinations/capabilities and open existing forms/reports with keyboard. Independent acceptance: US1.1–4, including unauthorized destinations, no-mutation cancellation and historical template input. This is the first demoable slice, not completion of the feature.

- [ ] T008 [P] [US1] [FR-001, FR-002, FR-003, FR-017, FR-020, SC-006] Add failing destination/capability/report launch and route tests in `apps/web/scripts/command-palette-targets.test.mjs`; cover canonical deduplication, owner/demo eligibility, unknown targets, clean route state, Tools query/disclosure, calculated-reader availability and no fabricated form.
- [ ] T009 [P] [US1] [FR-001, FR-002, FR-003, FR-010, FR-017, SC-004, SC-006] Add US1 browser scenarios in `apps/web/scripts/command-palette-browser.mjs`: shared shortcut/pointer entry, basic arrow/Enter/Escape, modal precedence, correct destination, no business write on form open/cancel and required template dates. Observe failures before implementation.
- [ ] T010 [US1] [FR-002, FR-003, FR-008, FR-017, FR-020] Expose necessary existing resource synonyms/launch metadata in `packages/reality-core/src/reality/catalogs.py` and `packages/reality-core/config/resource_catalog.yaml`; build local entries from navigation and unified capability/report metadata in `apps/web/src/unified/commandPaletteEntries.ts`. Do not add a parallel command inventory or use catalog presence as permission.
- [ ] T011 [US1] [FR-001, FR-002, FR-003, FR-010] Introduce `apps/web/src/unified/CommandPalette.tsx` and connect `ActionLauncher.tsx` through the existing portal/provider; implement focused/reset input, current company, explicit outcomes and basic keyboard launch with existing confirmation flows.
- [ ] T012 [US1] [FR-002, FR-003, FR-017, FR-020] Implement typed target dispatch in `apps/web/src/unified/commandPaletteTargets.ts`; extend `routing.ts` and `useCompanyContext.ts` with route-backed capability/calculated-report/saved-report/template selections and mutual exclusion/reset rules. Wire the existing `UnifiedApp.tsx` form path; do not execute on selection.
- [ ] T013 [US1] [FR-003, FR-017, FR-020] Hydrate route-backed capability/calculated-report selections in `apps/web/src/unified/ToolCatalog.tsx` and `RealityInspectorPage.tsx`; seed query and exact disclosure, reuse existing reader/details availability and preserve report freshness.
- [ ] T014 [US1] [FR-002, FR-017] Hydrate saved-report/template targets in `apps/web/src/unified/AnalyticsPage.tsx` and `analytics/GraphTemplates.tsx` with existing owner-checked `graphApi.report` and editor/input flows; preserve unsaved drafts, Back/reload and explicit historical dates. Reuse existing report listing until US2 supplies unified report search.
- [ ] T015 [US1] [FR-001, FR-002, FR-003, FR-017, FR-020, SC-004, SC-006] Run US1 target/browser proofs and existing action-discovery/tool-catalog/report/snapshot regressions; record commands and results in `specs/237-global-command-palette/verification.md`. A fixture-only browser pass does not prove backend authorization.

## Phase 4: US2 — Find the Exact Business Record (P1)

Goal: complete bounded record search and exact opening independent of list pages. Independent acceptance: US2.1–6 against PostgreSQL, with every mapped family, duplicate references, historical records and a second tenant.

- [ ] T016 [P] [US2] [FR-004, FR-005, FR-009, DR-001, DR-002, DR-004, DR-005, SC-001] Add failing all-family search fixtures and service tests in `packages/reality-core/tests/test_global_search.py`: each allowed field, >50 positions, closed/inactive/settled objects, multi-role partner, duplicate numbers, source versions, payment cash IDs and multiple tracking packages. Assert unchanged source/Reality rows and bounded continuation without candidate truncation.
- [ ] T017 [P] [US2] [FR-004, FR-005, FR-011, FR-014, FR-017, DR-003, SC-002] Add failing membership/owner/lesson/resolution tests in `packages/reality-core/tests/test_global_search_access.py`: cross-tenant joins, revoked membership, private reports, forged hints/cursors, unknown targets and safe non-disclosure; test trusted-local mode separately from absent browser authentication.
- [ ] T018 [P] [US2] [FR-004, FR-009, FR-011, FR-012, DR-003] Add failing thin-adapter tests in `packages/reality-core/tests/test_global_search_web.py` for read-only query/resolve POST, limits, missing/invalid principal, no autoflush/commit, empty query, cursor mismatch, timeout and safe provider errors.
- [ ] T019 [US2] [FR-004, FR-005, FR-009, DR-001, DR-004, SC-001, SC-004] Extend `apps/web/scripts/command-palette-browser.mjs` with every exact native/Inspector target off the loaded list page, settled/inactive defaults, duplicate disambiguation, filtered continuation, Back/reload, inbound shipment direction and source trace navigation; add group-budget fixtures with more than twelve candidates, an entirely omitted group, duplicate report representations and interleaved local/private report pages, proving four/twelve preview and fifty merged-page limits with no lost lookahead.
- [ ] T020 [US2] [FR-004, FR-005, DR-002, DR-004] Extract canonical payment cash-entry eligibility from `_payment_rows` in `packages/reality-core/src/reality/services/core.py` into a reusable selector without changing accounting semantics; retain `cash_entry_ids` bounded hydration and prove existing payment regressions.
- [ ] T021 [US2] [FR-004, FR-005, FR-007, FR-008, FR-009, DR-003, DR-004, DR-005] Implement explicit per-family SQL selectors/ranking/keyset continuation in `packages/reality-core/src/reality/db/search.py`; constrain every joined alias by tenant, use tracking EXISTS and canonical provider assignment, apply complete predicates before LIMIT, and never search arbitrary payload values.
- [ ] T022 [US2] [FR-004, FR-005, FR-011, FR-012, FR-014, FR-017, DR-001, DR-002, DR-003] Implement `search_company` and bounded `resolve_search_targets` in `packages/reality-core/src/reality/services/global_search.py`; reuse membership/lesson/report policy, hydrate authorized labels/roles/origins in batches, omit expensive optional derived state, and return safe unavailable results without business effects.
- [ ] T023 [US2] [FR-004, FR-009, FR-011, FR-012, DR-003] Add thin query/resolve transports and explicit lesson-safe eligibility integration in `packages/reality-core/src/reality/web/api.py`, and typed calls in `apps/web/src/api.ts`; retain existing authentication/CSRF semantics and separate read-only POST from business mutation authorization.
- [ ] T024 [US2] [FR-004, FR-005, FR-006, FR-009, FR-011, FR-012] Connect provider search, basic query-generation guards, broad filters distinct from Records-family refinements and eleven visible groups, hidden-group affordances and bounded single-group pagination in `apps/web/src/unified/CommandPalette.tsx` and `commandPaletteEntries.ts`; deduplicate by physical identity and preserve exact-hit ranking when merging metadata/providers. Apply four/twelve preview caps per visible group/overall; combine Reports sources using cursor/lookahead state before the fifty-row page cap, retain Show all for wholly omitted groups, and restore the prior filter on return.
- [ ] T025 [US2] [FR-002, FR-005, DR-001, DR-004] Add exact Inspector kind/ID selection and native record mapping in `apps/web/src/unified/routing.ts`, `commandPaletteTargets.ts`, `useCompanyContext.ts` and `InspectorRecordsPage.tsx`; reuse existing Inspector and clear all targets on company switch; never use query text as identity.
- [ ] T026 [US2] [FR-002, FR-005] Render existing selected partner/item/location/order detail independently of loaded rows in `apps/web/src/unified/MasterDataPage.tsx` and `OrdersPage.tsx`; preserve original register behavior, multi-role partner identity, closed/inactive access and unsaved-state handling.
- [ ] T027 [US2] [FR-002, FR-005, DR-002, DR-004] Open exact invoice/credit/payment/shipment details independently of status/pagination in `apps/web/src/unified/FinancePage.tsx` and `ShipmentsRegister.tsx`; reuse native details/Inspector, cash-entry payment IDs and opaque shipment IDs; serialize shipment direction in `routing.ts`.
- [ ] T028 [US2] [FR-004, FR-005, FR-009, DR-001, DR-002, DR-003, DR-004, DR-005, SC-001] Run US2 service/access/API/browser proofs, payment regressions and exact-target navigation regressions; record actual family coverage and failure evidence in `specs/237-global-command-palette/verification.md`.

## Phase 5: US3 — Fluent, Accessible and Resilient Search (P1)

Goal: deterministic multilingual ranking and stable interaction under loading/failure. Independent acceptance: US3.1–7, including keyboard-only operation and simulated delayed providers. Requires the US1/US2 integration; static matching can be proved independently.

- [ ] T029 [P] [US3] [FR-007, FR-008, FR-021, SC-005] Add `apps/web/scripts/command-palette-ranking.test.mjs` consuming `packages/reality-core/tests/fixtures/global_search_matching.json`; prove reference tiers, translations/synonyms, context tie-breaks and defined typo/diacritic behavior for local entries and provider merges.
- [ ] T030 [P] [US3] [FR-001, FR-006, FR-009, FR-010, FR-011, FR-012, FR-021, SC-004] Extend `apps/web/scripts/command-palette-browser.mjs` with IME/auto-repeat, keyboard secondary controls, selection disappearance, higher-ranked late insertion, provider errors/retry (including failed private reports alongside healthy templates/calculated views), query/company races, modal precedence, four languages, touch and 200% zoom; assert utility controls do not consume hit limits and group retry resets incomplete pagination.
- [ ] T031 [US3] [FR-007, FR-008, FR-021] Complete shared-corpus browser matching and stable ranking in `apps/web/src/unified/commandPaletteEntries.ts`; keep original values, raw exact precedence and same-tier context/recency only. SQL behavior must remain corpus-equivalent.
- [ ] T032 [US3] [FR-006, FR-009, FR-010, FR-011, FR-012] Complete accessible combobox/listbox state and asynchronous orchestration in `apps/web/src/unified/CommandPalette.tsx`: 150ms debounce, max three provider requests, scope+generation checks, identity-stable active result, no nested interactive options, provider-scoped partial errors/retries within visible groups, and query-preserving group pagination with prior-filter restoration; keep successful sources in a partially unavailable Reports group accessible.
- [ ] T033 [US3] [FR-001, FR-010, FR-021] Add all new copy in `apps/web/src/localization.tsx` and responsive/focus/touch styles in `apps/web/src/tailwind.css`; retain 44px targets, visible company and viewport-contained layout without changing unrelated shell styling.
- [ ] T034 [US3] [FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-021, SC-004, SC-005] Run ranking/browser/accessibility proofs and record a screen-reader smoke observation plus four-language outcomes in `specs/237-global-command-palette/verification.md`; keep missing checks explicitly pending.

## Phase 6: US4 — Recent, Favorite and Contextual Work (P2)

Goal: useful bounded empty state without retained business labels. Independent acceptance: US4.1–4 with reload, revocation, company/user changes and storage failure. Depends on exact resolution and launch contracts.

- [ ] T035 [P] [US4] [FR-013, FR-014, DR-003] Add failing preference tests in `apps/web/scripts/command-palette-preferences.test.mjs` for 20/20 limits, 4/4/2 suggestions, reference-only storage, pin overflow, malformed versions, denied storage, transient vs denied resolution, rename, logout and user/company isolation.
- [ ] T036 [US4] [FR-013, FR-014, FR-015, DR-003] Extend `apps/web/scripts/command-palette-browser.mjs` and `command-palette-targets.test.mjs` for successful ordinary-navigation recents, canceled/failed opens, reauthorized labels, cross-tab logout and allowlisted contextual targets with form cancellation/no write.
- [ ] T037 [US4] [FR-013, FR-014, DR-003] Implement reference-only versioned storage and validated resolution in `apps/web/src/unified/commandPalettePreferences.ts`; deduplicate and cap collections, reject favorite overflow without eviction, retain hidden references on transient errors and use in-memory fallback when storage is denied.
- [ ] T038 [US4] [FR-013, FR-014] Wire successful page/record/report open acknowledgments, management expansion and bounded empty-state suggestions in `apps/web/src/unified/CommandPalette.tsx`, `commandPaletteTargets.ts` and `UnifiedApp.tsx`; failed/canceled actions and typed queries never create recents.
- [ ] T039 [US4] [FR-014, DR-003] Clear feature storage/rendered data on logout/session loss and cross-tab notification in `apps/web/src/unified/ProfileMenu.tsx`, `apps/web/src/Auth.tsx`, `unified/useCompanyContext.ts` and `commandPalettePreferences.ts`; reauthorize before labels are displayed after any scope change.
- [ ] T040 [US4] [FR-015, FR-003, DR-003] Extend the typed existing actionTarget contract in `apps/web/src/unified/ActionLauncher.tsx`, `UnifiedApp.tsx` and `commandPaletteTargets.ts`; allow only service-eligible receipt/release/correction/credit/refund/reversal targets, display the named record and preserve execution-time validation and confirmation.
- [ ] T041 [US4] [FR-013, FR-014, FR-015, DR-003] Run preference/contextual/browser proofs including company/session regressions; record outcomes and remaining checks in `specs/237-global-command-palette/verification.md`.

## Phase 7: US5 — Worklists, Chat, Help and Company Switching (P2)

Goal: task phrases open canonical lists or explicit handoffs. Independent acceptance: US5.1–4; finance/blocker membership is proved by PostgreSQL services, not synthetic browser data.

- [ ] T042 [P] [US5] [FR-016, DR-002] Add failing `packages/reality-core/tests/test_command_palette_worklists.py` for outstanding/overdue both sides, canonical dates/unknown due/partial/settled cases, filter-before-count/paging, open inbound/outbound commitments, blocker membership/freshness, exceptions and pending decisions.
- [ ] T043 [P] [US5] [FR-016, FR-018, FR-019, FR-020, DR-003, SC-006] Extend `apps/web/scripts/command-palette-browser.mjs` for every named worklist and visible scope, explicit company chooser/reset, chat draft append with removable record context/no send, existing usage limits and help/Tools query handoff.
- [ ] T044 [US5] [FR-016, DR-002] Add canonical overdue filtering in `packages/reality-core/src/reality/services/finance/worklists.py` using existing aging/outstanding semantics at one evaluation instant; delegate `web/read_models.py` and `web/api.py` filters to it before pagination/count. Do not create a new financial rule or Document state.
- [ ] T045 [US5] [FR-016, DR-002] Expose financeOverdue and named worklist selections in `apps/web/src/api.ts`, `unified/routing.ts`, `FinancePage.tsx`, `commandPaletteEntries.ts` and `commandPaletteTargets.ts`; use existing daily-work destinations and the canonical fulfillment-blockers report with visible scope/freshness, never a hold-only approximation.
- [ ] T046 [US5] [FR-018, FR-003, DR-003] Extend the existing `reality:open-chat` handoff and visible/removable context in `apps/web/src/unified/ChatPage.tsx`, `Shell.tsx` and `commandPaletteTargets.ts`; append bounded editable drafts, retain company scope and existing usage/confirmation, and never send automatically.
- [ ] T047 [US5] [FR-019, FR-020, FR-006, DR-003] Add accessible-company chooser/results and allowlisted help/Tools shortcuts in `apps/web/src/unified/CommandPalette.tsx`, `commandPaletteEntries.ts` and `commandPaletteTargets.ts`; use `useCompanyContext.ts` switching and preserve query only for the intended destination, never old-company action state.
- [ ] T048 [US5] [FR-016, FR-018, FR-019, FR-020, DR-002, DR-003, SC-006] Run US5 worklist/browser proofs plus existing finance-aging, daily-work, chat/analysis and company regression suites; record results in `specs/237-global-command-palette/verification.md`.

## Phase 8: Performance, End-to-End Verification and Review

All five stories remain required. No done markers until their own required checks pass. Timing failures must lead to evidence-driven optimization, not dropped samples or approximate candidate caps.

- [ ] T049 [SC-001, SC-002, SC-004, SC-006, DR-001, DR-002, DR-003, DR-004, DR-005] Add complete cross-company business-story/no-write proofs in `packages/reality-core/tests/test_global_search_story.py` and a real-API mode in `apps/web/scripts/command-palette-browser.mjs`; verify exact detail identities and service-owned form/report behavior rather than relying only on mocked HTTP.
- [ ] T050 [FR-021, SC-003] Add a failing benchmark harness contract in `packages/reality-core/tests/test_global_search_benchmark.py` for disposable database guards, deterministic all-family mix, ten users, named query corpus, no silently dropped errors and reproducible timing output.
- [ ] T051 [FR-021, SC-003] Implement `packages/reality-core/benchmarks/global_search/runner.py` and package initialization with the planned CLI/guarded disposable dataset, 100k total searchable records, all mapped families and second-tenant isolation, cold/warm definition, query-plan and hardware/content-digest evidence; reuse existing benchmark guard conventions without touching inventory-cost benchmark work.
- [ ] T052 [FR-021, SC-003] Implement `apps/web/scripts/command-palette-performance.mjs` against the real disposable API/Web: ten authenticated contexts, 100ms RTT, at least 100 observations per case/regime, last-keystroke timing including debounce/queue and opening latency. Include all providers, common-prefix, typo and exact cases; count failures as failed samples.
- [ ] T053 [FR-021, SC-003] Run backend and browser workload from `specs/237-global-command-palette/quickstart.md`; collect cold/warm p50/p95/max and query plans in `verification.md`, optimize only measured paths in `packages/reality-core/src/reality/db/search.py`/`services/global_search.py`, rerun affected correctness proofs, and require all latency budgets to pass.
- [ ] T054 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, DR-001, DR-002, DR-003, DR-004, DR-005, SC-002] Update `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md` and new `docs/features/command-palette.md` with final implemented behavior and traceability. Run catalog generation when metadata changes; include `apps/docs/content/tool-usage/` output and `apps/docs/.vitepress/data/tool-usage.json`. Preserve unrelated edits; do not claim unverified acceptance.
- [ ] T055 [SC-001, SC-002, SC-004, SC-005, SC-006, DR-005] Run spec policy, Ruff, complete PostgreSQL pytest suite including migration upgrade/downgrade, frontend formatting/contracts/build/i18n, focused and impacted browser regressions, and catalog/docs freshness plus relevant docs tests/build; record actual results in `specs/237-global-command-palette/verification.md`. Missing dependencies or red tests block completion.
- [ ] T056 [SC-002, DR-001, DR-002, DR-003, DR-004, DR-005] Review the final diff, migration lock/write impact, rollback, every acceptance scenario and requirement-to-evidence mapping in `specs/237-global-command-palette/review.md`; update `tasks.md` and status/checklists only for green verified work. No merge, deployment or business-data reset is implicit.

## Dependencies and Execution Order

- Gate T001–T002 precedes code. Foundation T003–T007 precedes the first integration slice; every test precedes its proving code.
- US1 T008–T015 -> US2 T016–T028 -> US3 T029–T034 -> US4 T035–T041 -> US5 T042–T048 -> final T049–T056 is the safe serial sequence.
- US2 selectors/service depend on T004/T006/T007; T020 payment selector precedes T021 query implementation, which precedes T022 service and T023 adapter. T024–T027 depend on those contracts.
- US3 ranking test T029 is independent from browser test T030. US4 preference tests T035 can be prepared once resolution contracts exist. US5 service test T042 is independent from browser test T043. These are testing opportunities, not permission to race shared UI/API files.
- Early performance risk check: T050–T051 may be pulled forward after T022 to measure database matching before broad UI integration; T052 requires the working palette and real authentication paths. Full acceptance T053 remains after all providers/stories exist.
- US1/US2 exact route tests precede later context/recents integration. US4 and US5 both modify the shared launch/chat/navigation seams and should be integrated serially.
- Verification tasks never skip earlier red tests. Final review depends on all story proofs and the complete required suite.

## Parallel Examples by Story

- US1: T008 pure target tests and T009 browser fixture scenarios use separate files; run after foundation.
- US2: T016 service fixtures, T017 access negatives and T018 Web contracts are separate files; agree on shared fixture identities before edits. T019 shares the browser file and remains serial.
- US3: T029 ranking corpus consumer and T030 browser race/accessibility scenarios may be authored independently after US2.
- US4: T035 pure storage tests may run alongside review of existing contextual action eligibility, but T036 browser changes and T038–T040 shared integration are serial.
- US5: T042 canonical worklist service tests and T043 browser handoff scenarios are independent; implementation T044–T047 is serial around shared API/route files.

## Implementation Strategy

Deliver US1 as the first internal demonstrable slice, then US2 record search and exact navigation, US3 resilient interaction, US4 personal/context shortcuts, and US5 task-oriented handoffs. This ordering is incremental verification, not scope reduction: all P1 and P2 stories and final performance/security checks are required before feature completion. Read-only analysis/review must not be mistaken for completed implementation.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Verification / review | Status |
|---|---|---|---|---|
| FR-001 | T008, T009, T030 | T011, T033 | T015 | Pending |
| FR-002 | T008, T009 | T010, T011, T012, T014, T025, T026, T027 | T015 | Pending |
| FR-003 | T008, T009 | T010, T011, T012, T013, T040, T046 | T015 | Pending |
| FR-004 | T016, T017, T018, T019 | T020, T021, T022, T023, T024 | T028 | Pending |
| FR-005 | T016, T017, T019 | T020, T021, T022, T024, T025, T026, T027 | T028 | Pending |
| FR-006 | T030 | T024, T032, T047 | T034 | Pending |
| FR-007 | T003, T029 | T004, T006, T021, T031 | T034 | Pending |
| FR-008 | T003, T029 | T004, T006, T010, T021, T031 | T034 | Pending |
| FR-009 | T016, T018, T019, T030 | T021, T023, T024, T032 | T028, T034 | Pending |
| FR-010 | T009, T030 | T011, T032, T033 | T034 | Pending |
| FR-011 | T017, T018, T030 | T022, T023, T024, T032 | T034 | Pending |
| FR-012 | T018, T030 | T022, T023, T024, T032 | T034 | Pending |
| FR-013 | T035, T036 | T037, T038 | T041 | Pending |
| FR-014 | T017, T035, T036 | T022, T037, T038, T039 | T041 | Pending |
| FR-015 | T036 | T040 | T041 | Pending |
| FR-016 | T042, T043 | T044, T045 | T048 | Pending |
| FR-017 | T008, T009, T017 | T010, T012, T013, T014, T022 | T015 | Pending |
| FR-018 | T043 | T046 | T048 | Pending |
| FR-019 | T043 | T047 | T048 | Pending |
| FR-020 | T008, T043 | T010, T012, T013, T047 | T015, T048 | Pending |
| FR-021 | T003, T029, T030, T050 | T004, T031, T033, T051, T052 | T034, T053 | Pending |
| DR-001 | T016, T019, T049 | T022, T025 | T028, T056 | Pending |
| DR-002 | T016, T042, T049 | T020, T022, T027, T044, T045 | T028, T048, T056 | Pending |
| DR-003 | T017, T018, T035, T036, T043, T049 | T021, T022, T023, T037, T039, T040, T046, T047 | T028, T041, T048, T056 | Pending |
| DR-004 | T003, T016, T019, T049 | T004, T020, T021, T025, T027 | T028, T056 | Pending |
| DR-005 | T005, T016, T049 | T006, T007, T021 | T028, T055, T056 | Pending |
| SC-001 | T016, T019, T049 | — | T028, T055 | Pending |
| SC-002 | T017, T049 | T054 | T001, T002, T055, T056 | Pending |
| SC-003 | T005, T050 | T006, T051, T052 | T053 | Pending |
| SC-004 | T009, T019, T030, T049 | — | T015, T034, T055 | Pending |
| SC-005 | T029 | — | T034, T055 | Pending |
| SC-006 | T008, T009, T043, T049 | — | T015, T048, T055 | Pending |

## Generation Notes

No extension hooks are configured. Generation does not check off tasks or the reviewer-owned requirements checklist. The active feature is explicitly scoped to 235 for scripts, independent of the existing Git branch. The subsequent read-only analysis reports findings without editing these artifacts.

## Visual refinement continuation

- [x] T057 [US3] [FR-010, FR-012, FR-021] Add status rendering proofs for aggregated loading, mixed success/failure and independently retryable details; implement compact status and stable palette layout in CommandPalette.tsx, CommandSearchStatus.tsx and scoped CSS.
- [x] T058 [US3] [FR-010, FR-021] Verify desktop/narrow layout and actual typing, run frontend contracts/build/i18n, and record visual evidence without changing prior incomplete release gates.

- [x] T059 [US2] [FR-005, FR-021] Add regression coverage and repair off-page selected order/master detail presentation using shared preview containment; preserve exact readers/actions.
- [x] T060 [US2] [FR-005, FR-021] Audit palette destination renderers/families, verify live layouts and run frontend contracts/build/i18n; record absent fixtures and remaining limitations explicitly.

- [x] T061 [US3] [FR-010, FR-021] Match palette icons/type/tab/surface treatment to existing app styling, preserving layout; run existing frontend checks and inspect live.
