---
description: "Requirement-traceable CEO contribution analytics template tasks"
---

# Tasks: CEO Contribution Analytics Templates

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/templates.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/244-ceo-contribution-templates/spec.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/244-ceo-contribution-templates/plan.md`
- [x] T003 Run Spec Kit analysis and resolve all CRITICAL findings across `specs/244-ceo-contribution-templates/`

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001] [FR-010] Add failing exact-key and EN/DE catalog assertions in `packages/reality-core/tests/test_reporting_graph_declaration.py`
- [x] T005 [P] [US1] [FR-002] [FR-005] [FR-006] [DR-001] [DR-002] [DR-004] Add failing overview execution and incomplete-coverage tests in `packages/reality-core/tests/test_contribution_graph_reporting.py`
- [x] T006 [P] [US2] [FR-007] [FR-008] Add failing month/channel grouping tests in `packages/reality-core/tests/test_contribution_graph_reporting.py`
- [x] T007 [P] [US3] [FR-009] Add failing leakage ordering and unknown-margin tests in `packages/reality-core/tests/test_contribution_graph_reporting.py`
- [x] T008 [P] [US1] [FR-003] [FR-004] [DR-003] Add failing context-free adoption/no-execution contract test in `apps/web/scripts/analysis-chat-workflow.test.mjs`

## Phase 3: Executive Overview (P1)

- [x] T009 [US1] [FR-011] Extend load-time template validation without weakening runtime context enforcement in `packages/reality-core/src/reality/services/analytics/graph_model.py`
- [x] T010 [US1] [FR-001] [FR-002] [FR-005] [FR-006] [FR-010] Declare the localized overview template in `packages/reality-core/config/reporting_graph.yaml`
- [x] T011 [US1] [FR-003] [FR-004] [DR-003] Preserve selector-first browser adoption in `apps/web/src/unified/analytics/GraphSteps.tsx` and `apps/web/src/unified/analytics/GraphTemplates.tsx` only if failing proof requires a change
- [x] T012 [US1] Run the independent overview acceptance story from `specs/244-ceo-contribution-templates/quickstart.md`

## Phase 4: Trend and Channel Comparison (P2)

- [x] T013 [US2] [FR-001] [FR-005] [FR-007] [FR-010] Declare the localized monthly template in `packages/reality-core/config/reporting_graph.yaml`
- [x] T014 [US2] [FR-001] [FR-005] [FR-008] [FR-010] Declare the localized sales-channel template in `packages/reality-core/config/reporting_graph.yaml`
- [x] T015 [US2] Run the independent monthly/channel acceptance stories from `specs/244-ceo-contribution-templates/quickstart.md`

## Phase 5: Margin Leakage (P3)

- [x] T016 [US3] [FR-001] [FR-005] [FR-009] [FR-010] Declare the localized margin-leakage template in `packages/reality-core/config/reporting_graph.yaml`
- [x] T017 [US3] Run the independent leakage acceptance story from `specs/244-ceo-contribution-templates/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T018 [FR-012] Run existing graph declaration, traversal, contribution, and web template regression tests
- [ ] T019 Run `make spec-check`, `make lint`, and the complete backend PostgreSQL suite
- [x] T020 Run relevant web tests, i18n audit, and `make web-build`
- [x] T021 Confirm no migration, generated Tool Usage refresh, or catalog membership update is required
- [x] T022 Review final diff against Constitution and all FR/DR requirements

## Dependencies

- Phase 2 follows T003 and precedes implementation.
- US1 establishes safe context-free declaration validation before US2 and US3 declarations.
- US2 and US3 are independently testable after US1's validation support.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) |
|---|---|---|
| FR-001, FR-010 | T004 | T010, T013, T014, T016 |
| FR-002, FR-005, FR-006 | T005 | T010 |
| FR-003, FR-004 | T008 | T009, T011 |
| FR-007, FR-008 | T006 | T013, T014 |
| FR-009 | T007 | T016 |
| FR-011 | T004-T007 | T009 |
| FR-012 | T018-T020 | T021-T022 |
| DR-001, DR-002, DR-004 | T005-T007 | T010, T013, T014, T016 |
| DR-003 | T008 | T009, T011 |

## Implementation Strategy

Deliver US1 first as the minimum useful template and safety contract, then add the two comparative templates and the leakage template. Tests precede each declaration. No task is complete until its acceptance evidence is green.
