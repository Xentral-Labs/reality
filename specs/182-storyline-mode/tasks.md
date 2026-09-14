# Tasks: Storyline Mode

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/storyline-package.md,
contracts/storyline-api.md.
**Gate**: Product scope, assumption A and the schema accepted by the owner on 2026-09-12.
Implementation starts after analysis (T004) has no critical finding.

Format: `[ID] [P?] [Story] [FR-…] Description with exact paths`. `[P]` = can run in parallel
with its neighbours. Tests come before the code they prove.

## Phase 0: Decisions and research

- [x] T001 [FR-014] Play the seven chapters by hand against the services in a throwaway practice company (order, purchase order and short receipt, hold and refused dispatch, overpayment, reorder) and record the real exception ids, the fields each command needs and the due-date behaviour in `specs/182-storyline-mode/research.md` §R8.
- [x] T002 [FR-014] Verify in `packages/reality-core/src/reality/services/delivery_actions.py` whether a party hold refuses a dispatch at prepare or at confirm and what the review returns; record the chapter 3 shape in `research.md` §R8.
- [x] T003 [FR-014] Record the owner's answer to the open decision (assumption A or dunning and period close first) in `plan.md` and, if needed, amend FR-014 in `spec.md` and create the follow-up specs' stubs with `python3 scripts/next_feature_number.py`.
- [x] T004 Run cross-artifact analysis over spec, plan, data-model, contracts and tasks; resolve critical findings in place and note the rest in `specs/182-storyline-mode/quickstart.md`.

## Phase 1: Foundations (blocking)

- [x] T005 [P] [FR-005] Failing tests for `fact.recorded_at` (set on observe, backfill, index) in `packages/reality-core/tests/test_storyline_delta.py` and migration up/down for `0058_storyline` in `packages/reality-core/tests/test_migrations.py`.
- [x] T006 [P] [FR-002] [FR-019] Failing package contract tests in `packages/reality-core/tests/test_storyline_package.py`: shape, catalog names, `$ref`/`$seed`/`$chapter` resolution, raw-id refusal, relative dates, default branch, bounds, all errors collected (SC-008), every built-in validates (FR-017).
- [x] T007 [P] [FR-004] Failing recorder tests in `packages/reality-core/tests/test_storyline_trace.py`: scope, three producers, per-entry bound with truncation flag, 2 000-entry ring, inert for business tenants, tenant scope.
- [x] T008 [FR-005] Schema from `data-model.md` in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0058_storyline.py` (batched backfill, guarded downgrade).
- [x] T009 [FR-002] [FR-019] Implement `packages/reality-core/src/reality/storyline/package.py` and `references.py` (contract, four validation passes, JSON Schema export); add `storylines/` to the wheel in `packages/reality-core/pyproject.toml` like `config/`.
- [x] T010 [FR-004] Implement `packages/reality-core/src/reality/storyline/recorder.py`; wrap the four dispatcher functions in `tools/application.py`; view middleware in `web/app.py` (analysis M2); Copilot and MCP reads are covered by the dispatcher wrappers.
- [x] T011 [P] [FR-005] Forward mode `after_sequence` in `services/core.py:timeline_activity` and `web/api.py` timeline route, with a test in `packages/reality-core/tests/test_storyline_delta.py`.
- [x] T012 [P] [FR-007] `load_catalog_labels()` in `packages/reality-core/src/reality/catalogs.py` with its test in `tests/test_storyline_package.py`; `application-reference` stays unchanged (analysis M4), the tenant `tool-reference` route (T019) is the single surface.
- [x] T013 [FR-014] Author `packages/reality-core/storylines/order-to-close.storyline.yaml` (fourteen default-path chapters and four alternatives per research R8 and analysis C2, three branch points, four languages, backdated seed from T001); T006's built-in test passes.

**Checkpoint**: package validates, trace records, delta primitives exist, story is authored.

## Phase 2: User Story 1 — Play one chapter and see what it did (P1)

- [x] T014 [US1] [FR-001] [FR-003] Failing run tests in `packages/reality-core/tests/test_storyline_runs.py`: start creates a practice run with storyline key and seeded refs, resume returns the same run, production tenants refused, quota errors unchanged, seed failure rolls back to `initialization_failed` with the failing entry.
- [x] T015 [US1] [FR-003] [FR-005] Failing chapter tests in `test_storyline_runs.py`: prepare records marker and exception snapshot, validates input against the MCP schema, confirm and reject go through the Playground services, a chapter cannot run twice, read chapters complete without a proposal.
- [x] T016 [US1] [FR-005] Failing delta tests in `test_storyline_delta.py`: events after marker, facts after `marker_at`, records from receipt, raised and cleared from snapshots with rule label and `clears_through`, graph nodes and new edges, truncated range reported.
- [x] T017 [US1] [FR-001] [FR-003] Implement `services/storyline.py` start/resume/seed (`storyline` preset in `playground/catalog.py:find_preset`, seed history under `_profile_scope`, refs into `initialization_progress`), and the storyline branch in `services/playground.py:prepare_step` with marker capture.
- [x] T018 [US1] [FR-005] Implement `packages/reality-core/src/reality/storyline/delta.py`.
- [x] T019 [US1] [FR-001] [FR-003] [FR-004] [FR-005] Router `packages/reality-core/src/reality/web/storyline_api.py` (tenant scope routes of contracts/storyline-api.md) registered in `web/app.py`; HTTP tests in `packages/reality-core/tests/test_storyline_library_api.py` for auth, tenant scope, error mapping.
- [x] T020 [P] [US1] [FR-006] Web contract tests in `apps/web/scripts/storyline-contract.test.mjs`: `readSelection`/`selectionUrl` round trip for `/app/storyline`, unknown params dropped, `unifiedPath`, no `src/playground` (product boundary stays green).
- [x] T021 [P] [US1] [FR-006] [FR-007] [FR-008] Browser script `apps/web/scripts/storyline-browser.mjs` (mocked API): idle → preview → confirm, protocol lists calls with expandable explanation and docs link, delta items open Inspector, Facts and Exceptions routes, 1440 px and 390 px in en/de/nl/es with overflow 0 and no page errors; `test:storyline-browser` in `apps/web/package.json`.
- [x] T022 [US1] [FR-006] Destination in `apps/web/src/unified/routing.ts`, `entryRouting.ts`, `UnifiedApp.tsx`, `pageIntroduction.ts`; `dock="none"` and nav item in `Shell.tsx`; API functions in `apps/web/src/api.ts`.
- [x] T023 [US1] [FR-006] [FR-003] `StorylinePage.tsx`, `StorylineNarrator.tsx`, `storylineState.ts`: chapter list with `aria-current="step"`, situation, prepare through the run API, the prepared proposal's review rendered in the narrator with confirm and reject through the storyline routes (analysis C1), refused preparations shown as the chapter's outcome, expected against observed findings, explanation.
- [x] T024 [US1] [FR-006] `StorylineStage.tsx`: the view a chapter names, read through the shared live reads (`readLiveView`), rows that name a record of the delta marked, count in the stage header, one click to the full page. Mounting the whole page component was dropped: its register header portals into the shell header (research R6).
- [x] T025 [US1] [FR-004] [FR-005] [FR-007] [FR-008] `StorylineProtocol.tsx`: trace list with access chips, input and result, tool explanation from `tool-reference`, docs link through `languageHref`; delta groups with links; polling with the HomePulse guards.
- [x] T026 [US1] [FR-015] Strings for en/de/nl/es in `apps/web/src/localization.tsx` with ERP vocabulary; `npm run i18n:audit` green.

**Checkpoint**: chapter 1 of the built-in storyline plays in the browser with a truthful protocol.

## Phase 3: User Story 2 — Follow the whole story (P1)

- [x] T027 [US2] [FR-009] [FR-014] Failing scenario test `packages/reality-core/tests/scenarios/test_storyline_order_to_close.py`: the default path and every branch alternative through the service; the reference chapter writes a Fact that the delta lists (analysis H3); the reserve chapter clears the at-risk finding the order raised; the dispatch chapter is refused with the hold as reason and keeps its step; the overpayment chapter settles 1 180 of 1 300, leaves 120 available credit, clears the overdue receivable and raises the unmatched financial event; the billing chapter clears shipped-not-billed; the month-end review lists exactly the remaining findings; SC-002 completeness (every event, Fact, record and finding in the tenant appears in exactly one chapter's delta or the seed).
- [x] T028 [US2] [FR-009] Failing resume tests in `test_storyline_runs.py`: after re-login the run resumes at the first chapter not done; earlier chapters' trace and delta readable from stored markers.
- [x] T029 [US2] [FR-009] [FR-014] Implement resume derivation and chapter state read in `services/storyline.py`; fix the storyline file from what T027 proves.
- [x] T030 [US2] [FR-008] [FR-009] Browser section in `storyline-browser.mjs`: reload mid-story resumes; earlier chapter opens read-only protocol; each delta item type opens its surface.

## Phase 4: User Story 3 — Branches (P2)

- [x] T031 [US3] [FR-010] Failing tests in `test_storyline_runs.py`: branch choice stored in `storyline_state`, next chapter from the branch, default branch without a choice, earlier chapters read-only and never replayed.
- [x] T032 [US3] [FR-010] Implement branch route and next-chapter resolution in `services/storyline.py` and `web/storyline_api.py`; branch cards in `StorylineNarrator.tsx` (service and scenario proof; the browser fixture plays a story without branches, the branch cards are exercised by the scenario test through the same routes).

## Phase 5: User Story 6 — Library, export, import (P2)

- [x] T033 [US6] [FR-017] [FR-018] [FR-019] Failing HTTP tests in `test_storyline_library_api.py`: library lists built-ins and own imports only, download round-trips unchanged (SC-007 first half), import refuses unknown names with all errors and stores nothing, size bound before parsing and non-YAML/JSON bodies refused, replace on same key and version asks and keeps old runs, delete of built-in is 405, warning for commands the person may not confirm, and (US6-5, analysis M10) a chapter whose command a viewer principal may not confirm is refused by the ordinary authorization and shown as the chapter's outcome.
- [x] T034 [US6] [FR-018] [FR-020] Implement account routes in `web/storyline_api.py` and library service in `services/storyline.py`; runs keep their version when a newer package is imported.
- [x] T035 [US6] [FR-017] Docs: `apps/docs/scripts/generate-catalog-reference.py` writes `content/storylines/index.md`, `content/de/storylines/index.md`, `content/public/storylines/*.storyline.yaml` and `storyline.schema.json`; sidebar label in `.vitepress/config.mts` (EN and DE); extend the CI stale-output guard in `.github/workflows/quality.yml` and `Makefile`; docs contracts green.
- [x] T036 [US6] [FR-018] `StorylineLibrary.tsx` with download (Blob, `RegisterTable` precedent) and import (`<input type="file">`, raw-body POST, `ItemImportPanel` precedent), error list rendering; browser section; strings in four languages.
- [x] T037 [US6] [FR-016] Entry points: home card for sandbox and demo companies in `apps/web/src/unified/HomePage` (or the home component in use), link from the docs Tool Usage `order_to_cash` process page; `retirement-browser.mjs` still green for `/playground`.
- [x] T038 [US6] Scenario: export the built-in, import under another key, play it, assert the same end state as T027 (SC-007).

## Phase 6: User Story 4 — Free play (P2)

- [x] T039 [US4] [FR-011] (tests live in `test_storyline_runs.py`; the Copilot path is the same `create_change_proposal` wrapper) Failing tests in `test_storyline_trace.py`: a proposal confirmed outside a chapter (web route and `run_read_tool` path) is recorded with its own marker; delta for a free-play marker; Copilot proposal in the practice company recorded.
- [x] T040 [US4] [FR-011] [FR-012] Failing tests in `test_storyline_runs.py`: precondition check names the missing Fact and offers restart; restart creates a new practice company under quota and keeps the old one.
- [x] T041 [US4] [FR-011] [FR-012] Implement preconditions, free-play markers and restart in `services/storyline.py`; "Free play" and "Back to the story" in `StorylinePage.tsx`; browser section.

## Phase 7: User Story 5 — Presentation mode (P3)

- [x] T042 [US5] [FR-013] Presentation timer in `storylineState.ts` (prepare, confirm, advance; pause on any interaction; default branch); browser section asserting that the timed run issued the same ordered prepare, confirm and branch calls as the manual section (SC-003, analysis M8); a language switch mid-run re-renders texts without changing the trace (edge case).

## Phase 8: User Story 7 — Record a run as a draft (P3)

- [x] T043 [US7] [FR-021] Failing tests in `packages/reality-core/tests/test_storyline_export.py`: three free-play commands export in order, seed ids become `$ref`, created records become `$chapter`, dates become offsets, texts marked missing, unsupported command emitted in place; the draft validates except for missing texts; filled draft imports and plays (SC-009).
- [x] T044 [US7] [FR-021] Implement `packages/reality-core/src/reality/storyline/export.py` and the draft route; "Export as storyline draft" in the library of `StorylinePage.tsx`.

## Phase 9: Verification and review

- [x] T045 Update `docs/features/learning-playground.md` (storyline section), `docs/WEB_SPEC.md` (Storyline destination and dock rule), `docs/DATA_MODEL.md` (new columns and tables), `docs/DEMO_SPEC.md` (pointer to the storyline file).
- [x] T046 Run `make spec-check`, Ruff and the complete backend suite on isolated PostgreSQL; migration up and down on `postgres_database`; record output in `quickstart.md`.
- [x] T047 Run `apps/web` build, `i18n:audit`, contract tests and the storyline, retirement, unified-inspector and unified-activity browser scripts; record output in `quickstart.md`.
- [x] T048 Regenerate docs, run docs contracts and build; record output in `quickstart.md`.
- [x] T049 Review the final diff against spec, Constitution and shortest true links; confirm no page in `apps/web/src` is named playground; update task markers only with green evidence.

## Dependencies and strategy

T001–T004 → Phase 1 → US1 → US2 → (US3 ‖ US6 ‖ US4) → US5 → US7 → Phase 9. Phase 1 tasks
marked `[P]` run in parallel; T013 depends on T001 and T009. US1 is the MVP and is
independently demonstrable after T026. US6 can start after T009 and T019 in parallel with US2
if a second implementer is available; its browser work waits for T022. No deployment is
implied by any task; migrations are not run on the owner's live environment.

## Requirement coverage

| Requirement | Test tasks | Implementation tasks |
| --- | --- | --- |
| FR-001 | T014, T019 | T017, T019 |
| FR-002 | T006 | T009 |
| FR-003 | T014, T015 | T017, T019, T023 |
| FR-004 | T007, T039 | T010, T019, T025 |
| FR-005 | T005, T011, T016 | T008, T011, T018, T019, T025 |
| FR-006 | T020, T021 | T022, T023, T024 |
| FR-007 | T012, T021 | T012, T025 |
| FR-008 | T021, T030 | T025 |
| FR-009 | T027, T028, T030 | T029 |
| FR-010 | T031 | T032 |
| FR-011 | T039, T040 | T041 |
| FR-012 | T040 | T041 |
| FR-013 | T042 | T042 |
| FR-014 | T001, T002, T027 | T003, T013, T029 |
| FR-015 | T021 (four languages), T026 | T026, T036 |
| FR-016 | T037 | T037 |
| FR-017 | T006, T033 | T009, T035 |
| FR-018 | T033, T036 | T034, T036 |
| FR-019 | T006 | T009 |
| FR-020 | T033 | T034 |
| FR-021 | T043 | T044 |
| SC-001 | T021 | T023 |
| SC-002 | T027 | T018, T029 |
| SC-003 | T042 | T042 |
| SC-004 | T006 | T009 |
| SC-005 | T021 | T022–T026 |
| SC-006 | T016 (timing assertion on the practice company) | T018 |
| SC-007 | T033, T038 | T034 |
| SC-008 | T006, T033 | T009, T034 |
| SC-009 | T043 | T044 |

## Autoplay refresh regression (FR-013)

- [x] T901 Add a Home-entry/delayed trial-refresh browser regression and observe failure.
- [x] T902 Keep mounted children during successful background refresh; run browser, build, contract and spec checks.
