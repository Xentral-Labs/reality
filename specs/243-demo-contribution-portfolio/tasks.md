---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Demo Contribution Portfolio

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/demo-portfolio.md`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be written in English.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/243-demo-contribution-portfolio/spec.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/243-demo-contribution-portfolio/plan.md`
- [x] T003 Run `$speckit-analyze` against `specs/243-demo-contribution-portfolio/spec.md`, `plan.md`, and `tasks.md` and resolve all CRITICAL findings

## Phase 2: Failing Business Proof

- [x] T004 [US1] [FR-001] [FR-002] [FR-005] [FR-008] Add a failing six-outcome portfolio, classifications, exact-values, and discovery-reference story in `packages/reality-core/tests/test_demo_costing_profile.py`
- [x] T005 [US2] [FR-003] [FR-004] [FR-010] [DR-001] [DR-002] [DR-003] [DR-004] Add failing source-lineage, reviewed-category, tenant-scope, and exact selling-cost reconciliation assertions in `packages/reality-core/tests/test_demo_costing_profile.py`
- [x] T006 [US3] [FR-006] [FR-007] [FR-011] Extend failing regression assertions for missing cost, late cost/return, and continuous Demo Data boundaries in `packages/reality-core/tests/test_demo_costing_profile.py`
- [x] T007 [US1] [FR-009] [DR-004] Add failing replay count and stable portfolio identity assertions in `packages/reality-core/tests/test_demo_costing_profile.py`

## Phase 3: User Story 1 — Varied Complete Outcomes (P1)

**Goal**: A fresh canonical demo company exposes six named complete contributions spanning healthy, lower, and negative DB2.

**Independent test**: Run the focused profile test and inspect exact classifications and shared contribution results for all named complete cases.

- [x] T008 [US1] [FR-001] [FR-002] [FR-008] [FR-009] [DR-004] Increment the canonical profile identity, retain version compatibility, and define stable idempotent portfolio scenario vocabulary in `packages/reality-core/src/reality/demo/international.py`, `packages/reality-core/src/reality/playground/catalog.py`, and `packages/reality-core/src/reality/services/demo_data.py`
- [x] T009 [US1] [FR-001] [FR-004] [DR-001] [DR-002] Author the bounded acquisition lot, five ordinary sales, issue movements, invoices, and postings in `packages/reality-core/src/reality/services/demo_profile.py`
- [x] T010 [US1] [FR-004] [FR-005] [FR-010] [DR-003] [DR-005] Create one tenant-scoped inventory review and five exact commercial matches through existing profile cost actions in `packages/reality-core/src/reality/services/demo_profile.py`
- [x] T011 [US1] [FR-001] [FR-002] [FR-005] [FR-008] Store stable opaque portfolio references in the existing `costing_cases` manifest in `packages/reality-core/src/reality/services/demo_profile.py`
- [x] T012 [US1] Run the independent complete-outcome acceptance story in `packages/reality-core/tests/test_demo_costing_profile.py` and record evidence in `specs/243-demo-contribution-portfolio/quickstart.md`

## Phase 4: User Story 2 — Selling-Cost Composition (P2)

**Goal**: Complete examples explain distinct direct and allocated cost bridges from DB1 to DB2.

**Independent test**: Query all complete cases and reconcile every evidenced or reviewed-zero category to exact DB2.

- [x] T013 [US2] [FR-003] [FR-004] [DR-001] [DR-002] Author and post scenario-specific selling-cost source lines in `packages/reality-core/src/reality/services/demo_profile.py`
- [x] T014 [US2] [FR-003] [FR-004] [DR-003] Assign direct and allocated parts and complete all category dispositions through existing cost actions in `packages/reality-core/src/reality/services/demo_profile.py`
- [x] T015 [US2] [FR-003] [FR-005] Complete the selling-cost reconciliation acceptance story in `packages/reality-core/tests/test_demo_costing_profile.py`

## Phase 5: User Story 3 — Truthful Gaps and Later Knowledge (P3)

**Goal**: Complete examples remain clearly distinct from missing and later-known cost stories.

**Independent test**: Query the missing and late-return cases and prove unknown remains unknown while later reviewed knowledge stays separately traceable.

- [x] T016 [US3] [FR-006] [FR-007] Preserve existing missing-cost and late-cost/return manifest identities and service behavior in `packages/reality-core/src/reality/services/demo_profile.py`
- [x] T017 [US3] [FR-011] [DR-005] Preserve continuous Demo Data eligibility and missing-cost semantics while asserting the portfolio remains canonical-profile-only in `packages/reality-core/src/reality/services/demo_data.py` and `packages/reality-core/tests/test_demo_costing_profile.py`
- [x] T018 [US3] Complete missing/late/continuous boundary acceptance tests in `packages/reality-core/tests/test_demo_costing_profile.py`

## Phase 6: Documentation and Cross-Cutting Review

- [x] T019 [P] [FR-012] Update the durable international-v3 portfolio contract and arithmetic in `docs/features/company-setup-demo.md` and `specs/146-company-setup-demo/contracts/demo-profile.md`
- [x] T020 [P] [FR-012] Add the varied demo portfolio example to the bilingual ERP guide and a situation-led DB1/DB2 tool playbook under `apps/docs/content/{,de/}agent-playbooks/contribution-margin.md`, including sidebar navigation
- [x] T021 [P] [FR-012] Extend documentation contract assertions in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T021A [P] [FR-012] Group DB1/DB2 tools and exceptions under the bilingual `Contribution margin` business resource in `packages/reality-core/config/resource_catalog.yaml` and regenerate Tool Usage
- [x] T021B [P] [FR-012] Group the same capabilities under a translated `Contribution margin` topic in the application Tools catalog and verify its exact membership
- [x] T022 [FR-001-FR-012] [DR-001-DR-005] Update executable evidence mapping in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T023 Run `make spec-check` and audit requirement coverage across `specs/243-demo-contribution-portfolio/`
- [x] T024 Run Ruff and the focused `packages/reality-core/tests/test_demo_costing_profile.py` PostgreSQL suite
- [ ] T025 Run the complete backend PostgreSQL suite and record results in `specs/243-demo-contribution-portfolio/quickstart.md`
- [x] T026 Run Docs format, tests, and build plus Web build, i18n audit, and contract tests; record results in `specs/243-demo-contribution-portfolio/quickstart.md`
- [x] T027 Confirm no migration exists or is required and review version-3 rollback in `specs/243-demo-contribution-portfolio/plan.md`
- [x] T028 Review the final diff against the Constitution, all FR/DR requirements, and shortest true links; then mark completed tasks in `specs/243-demo-contribution-portfolio/tasks.md`

## Dependencies

- Phase 1 blocks all implementation.
- Phase 2 tests must be added and observed failing before Phases 3-5 implementation.
- User Story 1 establishes the shared portfolio acquisition and commercial matches required by User Story 2.
- User Story 3 is behavior-preserving and may be verified after User Story 1, independently of selling-cost implementation details.
- Documentation tasks T019-T022 may proceed after exact scenario values stabilize.

## Parallel Opportunities

- T019, T020, and T021 affect separate documentation files and may run in parallel after scenario values are final.
- Test cases are intentionally kept in one file and must be edited sequentially.
- Profile implementation tasks share one service file and must be executed sequentially.

## Implementation Strategy

1. Establish failing portfolio and replay proofs.
2. Deliver the P1 acquisition, invoice, inventory-review, and commercial-match slice.
3. Add P2 selling-cost evidence, assignments, and contribution reviews.
4. Re-run P3 gap and continuous-data boundaries.
5. Update durable contracts and public handbook only after exact executable values pass.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T004, T012 | T008-T011 | Complete |
| FR-002 | T004, T012 | T008-T011 | Complete |
| FR-003 | T005, T015 | T013-T014 | Complete |
| FR-004 | T005, T015 | T009-T010, T013-T014 | Complete |
| FR-005 | T004-T005, T012, T015 | T010-T011 | Complete |
| FR-006 | T006, T018 | T016 | Complete |
| FR-007 | T006, T018 | T016 | Complete |
| FR-008 | T004, T012 | T008, T011 | Complete |
| FR-009 | T007 | T008-T011 | Complete |
| FR-010 | T005 | T010 | Complete |
| FR-011 | T006, T017-T018 | T016-T017 | Complete |
| FR-012 | T021, T026 | T019-T022 | Complete |
| DR-001 | T005 | T009, T013 | Complete |
| DR-002 | T005 | T009, T013 | Complete |
| DR-003 | T005 | T010, T014 | Complete |
| DR-004 | T005, T007 | T008, T011 | Complete |
| DR-005 | T005, T017 | T010, T017 | Complete |
