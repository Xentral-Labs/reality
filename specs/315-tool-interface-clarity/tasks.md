# Tasks: Tool interface clarity

## Phase 1: Specification and Design Gates

- [x] T001 Record accepted scope and requirements review in `specs/315-tool-interface-clarity/spec.md` and `checklists/requirements.md`.
- [x] T002 Complete Constitution PASS design and three-operation audit in `specs/315-tool-interface-clarity/plan.md` and `research.md`.
- [x] T003 Analyze spec/plan/tasks and record coverage evidence in `specs/315-tool-interface-clarity/verification.md` before implementation.

## Phase 2: User Story 1 - Category clarity

- [x] T004 [US1] [FR-001, FR-002, FR-005] Add failing shared-guide tests in `apps/docs/scripts/test_interface_guide_reference.py` and `apps/docs/scripts/docs-contract.test.mjs`.
- [x] T005 [US1] [FR-001, FR-002, FR-005] Define guide metadata and render shared manual terminology in `apps/docs/scripts/generate-catalog-reference.py`; consume it in `apps/docs/.vitepress/theme/components/ToolUsage.vue`.

## Phase 3: User Story 2 - Follow the operation

- [x] T006 [US2] [FR-003, FR-004, DR-001] Add example identity, optional quantity and relationship tests in `apps/docs/scripts/test_interface_guide_reference.py`, `apps/docs/scripts/docs-contract.test.mjs` and `apps/docs/scripts/tool-interface-render.test.mjs`.
- [x] T007 [US2] [FR-003, FR-004, DR-001] Render catalog-resolved example links and explicit operation relationships in `apps/docs/scripts/generate-catalog-reference.py` and `apps/docs/.vitepress/theme/components/ToolUsage.vue`.

## Phase 4: User Story 3 - Consolidation and audit

- [x] T008 [US3] [FR-005, FR-006, DR-001] Review shared terminology proof and audit against source paths; record outcome in `specs/315-tool-interface-clarity/verification.md`; retain deliberate adapter differences documented in `research.md`.

## Final Phase: Verification and Review

- [x] T009 Generate all catalog output with `make docs-generate` and verify repeatability for `apps/docs/content/tool-usage/`, `apps/docs/content/de/tool-usage/` and `apps/docs/.vitepress/data/tool-usage.json`.
- [x] T010 Run spec gate, lint, complete documentation Python/Node tests, format and production build; record results and scoped gate rationale in `specs/315-tool-interface-clarity/verification.md`.
- [x] T011 Review final diff against FR/DR and stable registry identifiers; update `specs/315-tool-interface-clarity/tasks.md` only after required checks pass.

## Dependencies and Implementation Strategy

T001–T003 gate all implementation. Tests precede their changes. US2 follows shared guide metadata from US1; US3 reviews both. The Python and Node test authoring can run independently; edits to shared generator/Vue files remain sequential. Deliver the guide first, then relationship presentation, then generation and review. No domain/service/tool behavior changes are necessary.

## Requirement Coverage

| Requirement | Test/review tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001, FR-002 | T004, T010 | T005, T009 |
| FR-003, FR-004 | T006, T010 | T007, T009 |
| FR-005 | T004, T008 | T005, T009 |
| FR-006 | T008, T011 | T002, T008 |
| DR-001 | T006, T008, T011 | T002, T007 |

## Phase 5: User Story 4 — Business-object offerings

- [x] T012 [US4] [FR-007, FR-008, FR-009] Add object/count/search/detail/technical preservation tests in `apps/docs/scripts/tool-interface-render.test.mjs`.
- [x] T013 [US4] [FR-007, FR-008, FR-009, DR-001] Restore separate View/Projection lists and explain their technical links in `apps/docs/.vitepress/theme/components/ToolUsage.vue`; update `docs/WEB_SPEC.md`.
- [x] T014 [US4] [FR-007, FR-008, FR-009, DR-001] Run documentation tests/build, catalog and spec gates; review and record evidence in `specs/315-tool-interface-clarity/verification.md`.

Dependencies: T012 before T013 before T014. Existing design remains unchanged outside US4.

## Phase 6: User Story 5 — Canonical category vocabulary

- [x] T015 [US5] [FR-010, FR-011] Add failing category-label and localized-control tests in `apps/docs/scripts/tool-interface-render.test.mjs`, `apps/docs/scripts/docs-contract.test.mjs` and `apps/web/scripts/model-terminology.test.mjs`.
- [x] T016 [US5] [FR-010, FR-011, DR-001] Update shared labels in `apps/docs/scripts/generate-catalog-reference.py`, `apps/docs/.vitepress/theme/components/ToolUsage.vue`, `apps/web/src/localization.tsx`, `apps/web/scripts/i18n-invariants.mjs` and `docs/WEB_SPEC.md`; regenerate docs.
- [x] T017 [US5] [FR-010, FR-011, DR-001] Run docs/frontend tests, builds, localization/spec gates and scoped review; record evidence in `specs/315-tool-interface-clarity/verification.md`.

Dependencies: T015 precedes T016; T017 verifies both. Preserve separate View/Projection lists and the no-push/no-PR instruction.

## Phase 7: User Story 6 — Complete entry navigation

- [x] T018 [US6] [FR-012, FR-013] Add failing membership/badge/search assertions in `apps/docs/scripts/tool-interface-render.test.mjs`.
- [x] T019 [US6] [FR-012, FR-013, DR-001] Add all related Agent Tools and Web Actions to resource navigation and type every row in `apps/docs/.vitepress/theme/components/ToolUsage.vue`; update `docs/WEB_SPEC.md`.
- [x] T020 [US6] [FR-012, FR-013, DR-001] Verify docs suite/build and spec gate; record evidence in `specs/315-tool-interface-clarity/verification.md`.

Dependencies: T018 before T019 before T020; may share final documentation checks with T017.

- [x] T021 [FR-014] Extend shared guide in `apps/docs/scripts/generate-catalog-reference.py` and Vue/manual consumption; add test-first assertions in `apps/docs/scripts/tool-interface-render.test.mjs`, regenerate and verify documentation tests/build/spec.

- [x] T022 [FR-015] Update sidebar contract tests in `apps/docs/scripts/docs-contract.test.mjs`, revise bilingual development guides and `.vitepress/config.mts`, split exception guide while retaining routes, and verify Docs tests/build/spec.

- [x] T023 [FR-016] Review implementation-backed examples, update bilingual guides and add Agent Tool/Web Action tutorials with nested navigation; add docs contract proof, run Docs tests/build/spec and record review findings/evidence.

## Phase 8: User Story 7 — Systematic extension handbook

- [x] T024 [US7] [FR-017–FR-021] Add failing bilingual handbook/navigation/outline/legacy-anchor assertions in `apps/docs/scripts/docs-contract.test.mjs` and executable training-registry proof in `apps/docs/scripts/test_interface_guide_reference.py`.
- [x] T025 [US7] [FR-017, FR-018] Recompose bilingual overview/sidebar; create `views.md`, `projections.md`, `first-extension.md`, `reference.md` and `api-cli.md` under `apps/docs/content/{,de/}development/`; retain `derived-views.md` compatibility links.
- [x] T026 [US7] [FR-019, FR-020, DR-001] Recompose implementation chapters to one learning structure using actual inventory/reservation templates, exercises, verification and common mistakes; consolidate common contracts in reference.
- [x] T027 [US7] [FR-021] Run complete Docs Node/Python tests, production build, scoped formatting, spec and source/registry verification; inspect desktop/mobile if a browser becomes available.
- [x] T028 [US7] [FR-017–FR-021, DR-001] Review content mapping, tutorial feasibility and limitations; record evidence in `specs/315-tool-interface-clarity/verification.md` and update task status only for passing gates.

Dependencies: T024 gates T025/T026; T027 verifies both before T028. No business runtime edits. The approved proposed plan is the architecture/design authority; all Constitution rows PASS. No unresolved clarification or critical analysis finding.

T027 visual condition: no enabled browser was available; automated checks are green and this limitation is recorded explicitly in verification.md. An independent reader trial is not claimed. Earlier unrelated T014/T020 gates remain unchanged.


## Phase 9: Complete vendor integration guidance

- [x] T029 [FR-022/023] Add fail-first bilingual vendor structure, navigation, coverage and actual-registry status checks in apps/docs/scripts/docs-contract.test.mjs.
- [x] T030 [FR-022/023] Add six integrations vendor pages and shared coverage/acceptance contract, connect sidebar/connector/pilot links and correct stale Shopify update status.
- [x] T031 [FR-022/023] Run complete Docs Node/Python suites, build, scoped formatting/lint/spec/whitespace and source verification.
- [x] T032 [FR-022/023, DR-001] Review source authority, cutover, expected story, implementation gaps and external citations; record evidence and limitations.

Pre-implementation requirements/design/task analysis: all requirements covered, approved scope, Constitution PASS, no critical finding. T029 gates T030; T031 gates T032. No live upstream or runtime changes.


## Phase 10: Responsive documentation width

- [x] T033 [FR-024] Extend theme layout contract checks for article/outline/table behavior, observe failure before CSS changes.
- [x] T034 [FR-024] Update apps/docs/.vitepress/theme/custom.css using existing outline dropdown and responsive table wrapping, preserving specialized layouts.
- [x] T035 [FR-024, DR-001] Verify full Docs suites/build, scoped formatting/spec/whitespace, review responsive behavior and record visual availability.

Requirements/design/task review: FR-024 fully mapped, approved scope, Constitution PASS, no unresolved questions or critical findings. T033 gates T034; T035 gates completion. No new component or business runtime.

## Integration acquisition guidance

- [x] T036 [FR-025] Add bilingual acquisition guidance regression check and observe failure.
- [x] T037 [FR-025] Add officially sourced initial/event/polling guidance and recommended intervals to Shopify/Xentral chapters.
- [x] T038 [FR-025] Verify Docs suites/build, formatting/spec checks and review source semantics.

Requirements/design/task review: approved scope, Constitution PASS, no unresolved questions or critical findings. T036 gates T037; T038 gates completion.

## Operating modes

- [x] T039 [FR-026] Add and fail observation-mode documentation checks.
- [x] T040 [FR-026] Explain both observation modes and implement clarified third mode with examples/boundaries.
- [x] T041 [FR-026] Verify documentation and record final review, disclosing independent workspace failures.

## Mode-scoped coverage

- [x] T042 [FR-027] Add and fail bilingual mode-scoped coverage checks.
- [x] T043 [FR-027] Update matrices and scope/acceptance/acquisition framing for narrow observation and selected C decisions.
- [x] T044 [FR-027] Verify and review, recording independent suite failures if they persist.

## Progressive example ERP chapter

- [x] T045 [FR-028] Add and fail bilingual staged-chapter/navigation/knowledge-boundary check.
- [x] T046 [FR-028] Write example chapter and teaching links, review numeric examples and capture boundaries.
- [x] T047 [FR-028] Verify required Docs gates and record remaining independent failures.

## Agent-centered example chapter

- [x] T048 [FR-029] Add and fail bilingual per-stage agent framing check.
- [x] T049 [FR-029] Rewrite chapter around agent capabilities and bounded autonomous loop.
- [x] T050 [FR-029] Verify docs gates and record unrelated suite failures.

## Source concept chapter

- [x] T051 [FR-030] Update navigation check and add bilingual concept/title/anchor test; observe failure.
- [x] T052 [FR-030] Rewrite chapter introduction, move sidebar entry, clarify technical example title and update link labels.
- [x] T053 [FR-030] Regenerate advisor knowledge, verify Docs gates and record review.

- [x] T054 [FR-030] Correct concept-first data-source navigation after user review, fail updated navigation checks first, verify and record results.

## Source revision explanation

- [x] T055 [FR-031] Add and fail bilingual source-stream/revision semantic checks.
- [x] T056 [FR-031] Explain source capture/versions and interpreter-specific changes using actual code contracts.
- [x] T057 [FR-031] Regenerate derived knowledge and verify/review required Docs checks.
