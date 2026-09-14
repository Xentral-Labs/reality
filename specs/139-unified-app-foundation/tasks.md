# Tasks: Unified App Foundation

**Input:** Approved `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/foundation.md`.
**Gate:** Constitution design check passes; resolve critical analysis findings and reviewer-owned requirements questions before implementation. Completion markers below describe implementation and technical verification only. Owner visual acceptance and rollout authorization remain separate; reviewer-owned checklists are unchanged.

All paths are repository-relative. All repository content remains English. Existing runtime paths and explicitly planned new files are distinguished in plan.md. Test tasks precede implementation; record a failing proof where practical, then run the independent journey after each story.

## Phase 1 — Setup and foundation

- [X] T001 Prepare an isolated feature checkout preserving current user work; run baseline gates from `Makefile` and record environment, PostgreSQL/browser availability and results in `specs/139-unified-app-foundation/quickstart.md`.
- [X] T002 Add service/tool-based stock-20/commitment-12 fixtures and multi-line, revised, corrected and two-company variants in `packages/reality-core/tests/unified_fixtures.py`.
- [X] T003 Add required Node/browser harness entry points to `apps/web/package.json` and an executable journey skeleton using existing harness conventions in `apps/web/scripts/unified-app-browser.mjs`; fail explicitly if browser prerequisites are missing rather than count a skipped run as acceptance.

## Phase 2 — US1: Coherent shell and company context

Goal: new design entry without old styles or unauthorized context. Independent proof: two companies, empty company, foreign deep link, pending practice-only account, reload/back-forward.

- [X] T004 [US1] [FR-001 FR-002 FR-003 FR-022 FR-023 DR-003] Add failing route/admission/context-generation and legacy compatibility proofs in `apps/web/scripts/unified-app-contract.test.mjs`, `apps/web/scripts/unified-app-browser.mjs` and `packages/reality-core/tests/test_unified_app_api.py`.
- [X] T005 [US1] [FR-001 FR-003 FR-022 FR-023] Isolate the old ProductApp and its styles in `apps/web/src/legacy/LegacyProductApp.tsx`; keep `apps/web/src/App.tsx` as lazy authenticated dispatch with internal VITE_UNIFIED_APP routing and preserve `apps/web/src/Auth.tsx` practice admission.
- [X] T006 [US1] [FR-001 FR-002 DR-003] Build new navigation/URL state, scoped requests, company switch and compatibility navigation in `apps/web/src/unified/Shell.tsx`, `routing.ts`, `useCompanyContext.ts` and `UnifiedApp.tsx`.
- [X] T007 [US1] [FR-003 FR-023] Document exact new/legacy route behavior, unchanged practice policy and no permanent Old/New control in `docs/WEB_SPEC.md` and `docs/WEB_UX_MATRIX.md`; preserve semantic assertions when relocating legacy-source contract checks in `apps/web/scripts/product-boundary.test.mjs`.

## Phase 3 — US2: Authoritative Home

Goal: actual position, attention and pending decisions with honest unavailable states. Independent proof: Home agrees with authoritative reads and drill-down preserves scope.

- [X] T008 [US2] [FR-004 FR-005 FR-016 DR-004] Add failing dashboard sample-scope, unavailable-provider/read, decimal and post-action invalidation assertions in `packages/reality-core/tests/test_unified_app_api.py` and `apps/web/scripts/unified-app-browser.mjs`.
- [X] T009 [US2] [FR-004 FR-005 DR-004] Add sample/completeness metadata to existing dashboard reads in `packages/reality-core/src/reality/web/api.py` without deriving totals from bounded samples or adding new KPI arithmetic.
- [X] T010 [US2] [FR-004 FR-005 FR-016 DR-004] Build `apps/web/src/unified/HomePage.tsx` and typed scope/read states in `apps/web/src/api.ts`; preserve filters, expose existing setup paths and independently invalidate dependent reads after recorded actions.

## Phase 4 — US3: Delivery work and explanation

Goal: one revision/correction-aware case accessible after fulfillment. Independent proof: stock 20/commitment 12 → reserve 12 → ship 5 → remaining 7, plus linked evidence.

- [X] T011 [US3] [FR-006 FR-007 FR-008 FR-016 DR-001 DR-002 DR-004 DR-005] Add failing effective quantity/date, correction-aware inspector, item/location scope, bounded history/page and closed-case tests in `packages/reality-core/tests/test_unified_delivery_reads.py` and `test_unified_app_api.py`.
- [X] T012 [US3] [FR-006 FR-007 FR-016 DR-001 DR-002 DR-004 DR-005] Implement shared effective delivery composition in `packages/reality-core/src/reality/services/delivery_reads.py`; correct effective-value filtering/sorting before pagination in `packages/reality-core/src/reality/web/read_models.py` using existing core authority helpers.
- [X] T013 [US3] [FR-006 FR-007 FR-008 DR-001 DR-003 DR-005] Expose scoped list/detail and cursor history in `packages/reality-core/src/reality/web/api.py`, supply the same bounded read snapshot to existing contextual Chat tools in `packages/reality-core/src/reality/services/core.py`, and delegate commitment inspector semantics to the same service.
- [X] T014 [US3] [FR-006 FR-007 FR-008 FR-016] Build `apps/web/src/unified/DeliveryWorkPage.tsx`, `DeliveryCase.tsx` and `Inspector.tsx`; preserve opaque selected identity, list filters, multiple lines/reservations and closed-case access.
- [X] T015 [US3] [FR-006 FR-007 FR-008 DR-001 DR-002 DR-005] Exercise linked source/evidence/history, unavailable references and partial/final fulfillment in `apps/web/scripts/unified-app-browser.mjs`; record the independent journey in `specs/139-unified-app-foundation/quickstart.md`.

## Phase 5 — US5: Exact review, single execution and recovery

US5 precedes shared-card integration because the card must consume a sound backend lifecycle.

- [X] T016 [US5] [FR-011 FR-012 FR-013 FR-014 FR-015 FR-020 DR-003 DR-006] Add failing prepare replay, stale review, edited authority, rejection, shipment verification, historical reservation proof and unknown-result tests in `packages/reality-core/tests/test_unified_delivery_actions.py` and `test_application_tools.py`.
- [X] T017 [US5] [FR-014 FR-015 DR-003 DR-006] Add true multi-connection duplicate/different-proposal stock competition, cross-entry direct-writer interference, hold/revision/correction race and connection-loss tests in `packages/reality-core/tests/test_postgresql_integration.py` and `test_unified_delivery_actions.py`.
- [X] T018 [US5] [FR-014 FR-015 DR-003 DR-006] Implement the tenant transaction guard in `packages/reality-core/src/reality/services/business_locks.py` and apply a documented complete writer list in `services/core.py`; retain existing reservation capping and lock from final review validation through the domain effect commit.
- [X] T019 [US5] [FR-011 FR-012 FR-013 FR-014 FR-020 DR-004 DR-006] Implement typed request identity, immutable versioned review and exact state/token checks in `packages/reality-core/src/reality/services/delivery_actions.py`; connect ordinary-company reservation/shipment proposal creation and approval in `tools/application.py`, stripping reserved metadata before handlers.
- [X] T020 [US5] [FR-013 FR-015 FR-020 DR-006] Extend `packages/reality-core/src/reality/tools/application.py` execution-status verification with immutable correlated reservation/shipment evidence and safe settlement; retain original review and legacy receipt fields; do not infer failure from absent evidence.
- [X] T021 [US5] [FR-011 FR-012 FR-013 FR-014 FR-015 FR-020] Add prepare/detail/review adapters and token-aware approval payloads in `packages/reality-core/src/reality/web/api.py`; validate session/company before optional chat annotation and prevent duplicate approval messages or misleading failed-action responses after a recorded effect.
- [X] T022 [US5] [FR-012 FR-014 FR-023 DR-003 DR-006] Make legacy review in `apps/web/src/legacy/LegacyProductApp.tsx`, MCP in `mcp/catalog.py` and shared approval tools carry required review authority; preserve old pending proposal IDs and non-delivery command behavior. Verify that direct CLI commands use the guarded shared services; the repository has no CLI proposal-approval command.
- [X] T023 [US5] [FR-013 FR-015 FR-020] Build scoped `apps/web/src/unified/useProposal.ts` and `DecisionsPage.tsx` with direct detail recovery, original review, explicit unresolved outcomes and independently refreshed observations.

## Phase 6 — US4: Shared card and all three entries

Goal: reservation and shipment use one precise form/review/result flow. Independent proof: six tool/entry combinations with equivalent inputs.

- [X] T024 [US4] [FR-009 FR-010 FR-011 FR-012 FR-019 DR-003] Add six entry/action parity and missing/ambiguous/foreign/tracked-reference scenarios in `packages/reality-core/tests/test_unified_delivery_actions.py` and `apps/web/scripts/unified-app-browser.mjs`.
- [X] T025 [US4] [FR-009 FR-010 FR-019] Implement command-backed discovery/business descriptions and bounded allowed reference choices via `packages/reality-core/src/reality/web/application_catalog.py`, `tools/application.py` and typed contracts in `apps/web/src/api.ts`; no unrestricted command gateway.
- [X] T026 [US4] [FR-009 FR-010 FR-011 FR-012 FR-019] Build `apps/web/src/unified/ActionCard.tsx` and `ActionLauncher.tsx` with exact quantity strings, visible references, prerequisites, capped-allocation preview, fresh review after edit and separate confirmation per dependent action.
- [X] T027 [US4] [FR-009 FR-011 FR-012 FR-016 FR-020] Connect case, shell launcher and Decisions entry/result handling through the same card/controller in `apps/web/src/unified/DeliveryCase.tsx`, `Shell.tsx`, `DecisionsPage.tsx` and `UnifiedApp.tsx`; closing a panel must not imply rejection.

## Phase 7 — US6: Company Chat and contextual assistance

Goal: persistent authorized conversations, contextual answers and the same actual proposals. Independent proof: global/case question, action review, reload, provider failure and hostile foreign ID.

- [X] T028 [US6] [FR-017 FR-018 FR-013 DR-003] Add failing context annotation/legacy-message compatibility, server binding, provider timeout and six-entry Chat integration cases in `packages/reality-core/tests/test_chat_confirmation.py`, `test_unified_app_api.py` and `apps/web/scripts/unified-app-browser.mjs`.
- [X] T029 [US6] [FR-017 FR-018 DR-003] Implement optional validated commitment context and historical annotation using existing Chat persistence/provider assembly in `packages/reality-core/src/reality/services/core.py` and `web/api.py`; retain plain legacy messages and reject forged internal metadata.
- [X] T030 [US6] [FR-009 FR-013 FR-017 FR-018] Build `apps/web/src/unified/ChatPage.tsx` and `CaseAssistant.tsx` around existing sessions/messages and the shared ActionCard; display historical context, retain failed questions, keep safe Markdown and avoid duplicate successful sends/approval notices.
- [X] T031 [US6] [FR-017 FR-018 FR-023] Extend existing ordinary-company and unchanged sandbox regression assertions in `packages/reality-core/tests/test_chat_confirmation.py` and `test_playground_chat.py`; run the independent conversation/recovery journey and record evidence in `specs/139-unified-app-foundation/quickstart.md`.

## Phase 8 — US7: Complete the design and accessible states

Goal: coherent real product at both viewports, four languages and both themes. Independent proof: Home, Chat, case, review and result with keyboard-only operation.

- [X] T032 [US7] [FR-021 FR-022 FR-005] Add viewport/theme/language/keyboard/focus/long-label and unsafe-content scenarios in `apps/web/scripts/unified-app-browser.mjs` and `unified-app-contract.test.mjs`.
- [X] T033 [US7] [FR-021 FR-022 FR-005] Complete shared br-* controls and responsive states in `apps/web/src/unified/`, `apps/web/src/tailwind.css` and existing `apps/web/src/localization.tsx`/`localization-core.ts` catalogs; use no legacy global component CSS or synthetic success states.
- [X] T034 [US7] [FR-021 FR-022] Perform actual desktop/mobile light/dark and en/de/nl/es visual/keyboard review; store evidence references and owner acceptance status in `specs/139-unified-app-foundation/quickstart.md` against `design/reference.html`.

## Phase 9 — Full verification and reviewed rollout

- [X] T035 Run all six entry/action combinations, canonical partial/final shipment and all negative-state journeys; verify every FR/DR and SC in `specs/139-unified-app-foundation/quickstart.md` with no skipped mandatory gate counted as success.
- [X] T036 Run `make spec-check`, `make lint`, complete PostgreSQL suite and existing affected inventory/revision/correction/holds/proposal/practice regressions from `Makefile`; record results in `specs/139-unified-app-foundation/quickstart.md`.
- [X] T037 Run `make web-build`, all frontend contracts and the new browser journey via `apps/web/package.json`; run `make docs-build` plus `make site-build` if its boundary changed, recording results in `specs/139-unified-app-foundation/quickstart.md`.
- [X] T038 Review token-aware legacy rollback, shared-lock coverage, query bounds, original review retention and no-schema diff against `specs/139-unified-app-foundation/plan.md` and `contracts/foundation.md`; record reviewer decisions and resolve findings before enabling rollout.
- [X] T039 Update `docs/WEB_SPEC.md`, `docs/WEB_UX_MATRIX.md`, applicable public guidance under `apps/docs/` and `docs/V0_CHECKLIST.md` only after required evidence passes; keep legacy/practice retirement outside this feature and rerun affected documentation/spec gates after these edits.

## Dependencies and implementation strategy

T001–T003 establish the test environment. US1 creates the new-design foundation; US2 can show existing authoritative reads without waiting for mutations. US3 service work precedes its adapters/UI. US5 establishes shared guard → preparation/review → status recovery → adapters → review UI. US4 then integrates the cards; US6 completes the third Chat entry. US7 and the final verification finish the approved increment.

Critical path: setup → US1 → US3 → US5 → US4 → US6 → US7 → final verification. US2 may proceed after US1 and independent backend contract setup. A skeleton or US1 alone is an intermediate demonstration, not completion of the approved scope.

Parallel opportunities, after common prerequisites: US1 browser fixtures and backend admission assertions; US2 Home rendering and service-sample tests; US3 read-service tests and presentational case layout; US5 preparation tests and separate concurrency tests; US4 launcher and card styles after the contract; US6 provider tests and Chat presentation after common authority; US7 independent language/theme review. Do not parallelize writes to shared `api.py`, `core.py`, `application.py` or localization files without dividing ownership. No `[P]` tasks are advertised as unconditionally independent.

## Requirement Coverage

The mapping below covers both a test and implementation task for all 29 requirements. Final T035–T039 apply to all requirements and SC-001–SC-008 in addition to these focused proofs.

| Requirement | Test tasks | Implementation tasks | Status |
| --- | --- | --- | --- |
| FR-001 | T004 | T005, T006 | Technical proof recorded in quickstart.md |
| FR-002 | T004 | T006 | Technical proof recorded in quickstart.md |
| FR-003 | T004 | T005, T007 | Technical proof recorded in quickstart.md |
| FR-004 | T008 | T009, T010 | Technical proof recorded in quickstart.md |
| FR-005 | T008, T032 | T009, T010, T033 | Technical proof recorded in quickstart.md |
| FR-006 | T011, T015 | T012, T013, T014 | Technical proof recorded in quickstart.md |
| FR-007 | T011, T015 | T012, T013, T014 | Technical proof recorded in quickstart.md |
| FR-008 | T011, T015 | T013, T014 | Technical proof recorded in quickstart.md |
| FR-009 | T024 | T025, T026, T027, T030 | Technical proof recorded in quickstart.md |
| FR-010 | T024 | T025, T026 | Technical proof recorded in quickstart.md |
| FR-011 | T016, T024 | T019, T021, T026, T027 | Technical proof recorded in quickstart.md |
| FR-012 | T016, T024 | T019, T021, T022, T026, T027 | Technical proof recorded in quickstart.md |
| FR-013 | T016, T028 | T019, T020, T021, T023, T030 | Technical proof recorded in quickstart.md |
| FR-014 | T016, T017 | T018, T019, T021, T022 | Technical proof recorded in quickstart.md |
| FR-015 | T016, T017 | T018, T020, T021, T023 | Technical proof recorded in quickstart.md |
| FR-016 | T008, T011 | T010, T012, T014, T027 | Technical proof recorded in quickstart.md |
| FR-017 | T028, T031 | T029, T030 | Technical proof recorded in quickstart.md |
| FR-018 | T028, T031 | T029, T030 | Technical proof recorded in quickstart.md |
| FR-019 | T024 | T025, T026 | Technical proof recorded in quickstart.md |
| FR-020 | T016 | T019, T020, T021, T023, T027 | Technical proof recorded in quickstart.md |
| FR-021 | T032, T034 | T033 | Technical proof recorded in quickstart.md |
| FR-022 | T004, T032, T034 | T005, T033 | Technical proof recorded in quickstart.md |
| FR-023 | T004, T031 | T005, T007, T022 | Technical proof recorded in quickstart.md |
| DR-001 | T011, T015 | T012, T013 | Technical proof recorded in quickstart.md |
| DR-002 | T011, T015 | T012 | Technical proof recorded in quickstart.md |
| DR-003 | T004, T016, T017, T024, T028 | T006, T013, T018, T022, T029 | Technical proof recorded in quickstart.md |
| DR-004 | T008, T011 | T009, T010, T012, T019 | Technical proof recorded in quickstart.md |
| DR-005 | T011, T015 | T012, T013 | Technical proof recorded in quickstart.md |
| DR-006 | T016, T017 | T018, T019, T020, T022 | Technical proof recorded in quickstart.md |


## Completion evidence

Implementation uses existing shared service/tool authority and no schema changes.
`quickstart.md` records commands, browser matrix, actual API proof and failures that
were resolved. `architecture-review.md` records the guard, compatibility and
recovery review. T034 records technical visual review with owner acceptance still
pending; it does not claim owner approval. Final suite/status recording for T036
and T039 is complete: 1470 passed, 7 pre-existing retired-UI skips; all required
frontend, documentation and static gates pass.
