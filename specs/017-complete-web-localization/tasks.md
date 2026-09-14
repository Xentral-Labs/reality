---
description: "Requirement-traceable implementation tasks for complete Web localization"
---

# Tasks: Complete Web Localization

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed, specification approved, and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the implementation they prove. Generated
`frontend/dist/` files are not source deliverables.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Record the 2026-08-31 owner approval and confirm zero clarification markers in `specs/017-complete-web-localization/spec.md`
- [x] T002 Confirm every Constitution Check row and post-design re-evaluation remain PASS in `specs/017-complete-web-localization/plan.md`
- [x] T003 Validate the logical entities and audit behavior against `specs/017-complete-web-localization/data-model.md` and `specs/017-complete-web-localization/contracts/localization-audit.md`
- [x] T004 Run `$speckit-analyze` across `specs/017-complete-web-localization/spec.md`, `plan.md`, and `tasks.md`; resolve every CRITICAL finding before implementation

## Phase 2: Foundational Failing Proof

**Purpose**: Establish deterministic tests and commands before changing the audit or catalogs.

- [x] T005 [P] [US2] [FR-001] [FR-003] [FR-004] [FR-005] [FR-006] Add failing Node tests for source discovery, four-language results, missing/blank entries, invariants, and deterministic output in `frontend/scripts/i18n-audit.test.mjs`
- [x] T006 [P] [US3] [FR-007] [FR-008] [FR-009] [DR-001] [DR-002] [DR-003] [DR-004] Add failing tests for English fallback, preference independence, invariant identity, and unchanged business/source samples in `frontend/scripts/localization-contract.test.mjs`
- [x] T007 [US2] [FR-011] Add explicit focused localization test and strict audit commands to `frontend/package.json`
- [x] T008 [US2] [FR-001] [FR-003] [FR-004] Run the focused test commands and record the expected initial failures in `specs/017-complete-web-localization/quickstart.md`

**Checkpoint**: The tests fail for the documented missing multi-language discovery and coverage behavior, not because of test harness errors.

---

## Phase 3: User Story 2 - Detect Translation Gaps Before Release (Priority: P1)

**Goal**: Produce a strict, deterministic completeness result for every advertised language.

**Independent Test**: Complete fixtures pass; missing, blank, unapproved English-equal, and newly discovered strings fail with language/source details in one run.

### Tests

- [x] T009 [US2] [FR-001] [FR-005] Add temporary controlled discovery fixtures in `frontend/scripts/i18n-audit.test.mjs` covering nested source files, JSX text, supported attributes, accessibility text, and excluded dynamic/business values
- [x] T010 [P] [US2] [FR-002] [FR-003] [FR-004] Add complete and incomplete temporary four-language catalog fixtures in `frontend/scripts/i18n-audit.test.mjs`
- [x] T011 [P] [US2] [FR-006] Add temporary approved-invariant and unapproved-English-equal fixtures in `frontend/scripts/i18n-audit.test.mjs`

### Implementation

- [x] T012 [US2] [FR-001] [FR-005] Extract reusable recursive source discovery and candidate classification into `frontend/scripts/i18n-audit-lib.mjs`
- [x] T013 [US2] [FR-002] [FR-003] [FR-004] Implement independent `en`, `de`, `nl`, and `es` completeness results with stable missing/invalid details in `frontend/scripts/i18n-audit-lib.mjs`
- [x] T014 [US2] [FR-006] Replace broad prose exemptions with a narrow, reasoned invariant registry in `frontend/scripts/i18n-invariants.mjs` and enforce it from `frontend/scripts/i18n-audit-lib.mjs`
- [x] T015 [US2] [FR-011] Refactor `frontend/scripts/i18n-audit.mjs` into the strict production entry point defined by `specs/017-complete-web-localization/contracts/localization-audit.md`
- [x] T016 [US2] [FR-001] [FR-003] [FR-004] [FR-005] [FR-006] [FR-011] Run `npm run test:i18n` in `frontend/` and make all User Story 2 regression tests pass

**Checkpoint**: The audit contract is independently proven against fixtures even while production catalogs may still fail strict completeness.

---

## Phase 4: User Story 1 - Work in a Complete Selected Language (Priority: P1)

**Goal**: Complete all product-owned interface text for English, German, Dutch, and Spanish without changing protected business content.

**Independent Test**: Every discovered production string is covered in all four languages or explicitly invariant, and representative selected-language states contain no avoidable English fallback.

### Tests

- [x] T017 [US1] [FR-002] Run the strict production audit and record the exact starting missing/invalid counts per language in `specs/017-complete-web-localization/quickstart.md`
- [x] T018 [P] [US1] [FR-008] [FR-009] [DR-001] [DR-002] [DR-003] [DR-004] Extend `frontend/scripts/localization-contract.test.mjs` with production catalog, Source/Evidence/ID preservation, and language-versus-locale/timezone cases
- [x] T019 [P] [US1] [FR-010] Create the four-language desktop/mobile acceptance matrix in `specs/017-complete-web-localization/checklists/visual-review.md`

### Implementation

- [x] T020 [US1] [FR-002] Complete all required German entries in `frontend/src/localization.tsx`
- [x] T021 [US1] [FR-002] Complete all required Dutch entries in `frontend/src/localization.tsx` after T020 to avoid overlapping catalog edits
- [x] T022 [US1] [FR-002] Complete all required Spanish entries in `frontend/src/localization.tsx` after T021 to avoid overlapping catalog edits
- [x] T023 [US1] [FR-008] [DR-001] [DR-002] [DR-004] Encode explicit untranslated original-content and stable-domain boundaries in `frontend/src/localization.tsx` and `frontend/scripts/i18n-invariants.mjs`
- [x] T024 [US1] [FR-009] [DR-003] Preserve independent language, locale, and timezone behavior while organizing catalog/runtime helpers in `frontend/src/localization.tsx`
- [x] T025 [US1] [FR-009] [FR-010] Record the affected paths in `specs/017-complete-web-localization/checklists/visual-review.md`; correct the landing language control in `frontend/src/LandingPage.tsx` and `frontend/src/landing.css`, then preserve landing-to-auth language continuity through `frontend/src/Auth.tsx`, `frontend/src/LandingPage.tsx`, `frontend/src/localization-core.ts`, and `frontend/scripts/localization-contract.test.mjs`
- [x] T026 [US1] [FR-002] [FR-008] [FR-009] [FR-010] [DR-001] [DR-002] [DR-003] [DR-004] Run the strict production audit, localization contract tests, build, and representative User Story 1 review; record results in `specs/017-complete-web-localization/quickstart.md`

**Checkpoint**: User Story 1 is independently usable in all four languages, with original business content and preference boundaries unchanged.

---

## Phase 5: User Story 3 - Fall Back Safely Without Hiding Debt (Priority: P2)

**Goal**: Keep runtime pages usable for unexpected lookups while strict audit still rejects required missing coverage.

**Independent Test**: Unknown runtime text renders canonical English, but an inventoried missing entry fails the strict audit.

### Tests

- [x] T027 [US3] [FR-007] Add unknown, empty, and internal-key fallback cases to `frontend/scripts/localization-contract.test.mjs`
- [x] T028 [P] [US3] [FR-004] [FR-006] Add a regression proving runtime fallback cannot make an inventoried missing translation pass in `frontend/scripts/i18n-audit.test.mjs`

### Implementation

- [x] T029 [US3] [FR-007] Keep canonical English fallback explicit and prevent blank/internal-key output in `frontend/src/localization.tsx`
- [x] T030 [US3] [FR-004] [FR-006] Keep audit completeness independent from runtime fallback in `frontend/scripts/i18n-audit-lib.mjs`
- [x] T031 [US3] [FR-004] [FR-006] [FR-007] Run the independent fallback-versus-debt scenario and record the passing result in `specs/017-complete-web-localization/quickstart.md`

**Checkpoint**: Runtime resilience and release-time completeness are both proven without weakening either contract.

---

## Phase 6: User Story 4 - Close the Approved Baseline Gap with Evidence (Priority: P2)

**Goal**: Change `016/FR-013` from Documented gap to Verified as-is only after objective proof passes.

**Independent Test**: Baseline and coverage matrix cite passing per-language evidence and no unrelated gap status changes.

### Tests and Evidence Gate

- [x] T032 [US4] [FR-012] Verify all tasks T005–T031 and all four-language automated/visual evidence are green before editing baseline status; record the gate in `specs/017-complete-web-localization/checklists/requirements.md`
- [x] T033 [P] [US4] [FR-012] Add a policy regression that recognizes the verified localization evidence and remaining unrelated gaps in `backend/tests/test_spec_policy.py`

### Documentation Implementation

- [x] T034 [US4] [FR-012] Change only `016/FR-013` from Documented gap to Verified as-is and cite Spec 017 evidence in `specs/016-web-product/spec.md`
- [x] T035 [P] [US4] [FR-012] Remove only the localization gap and record four-language evidence in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T036 [US4] [FR-012] Run the independent baseline-closure review and record owner acceptance in `specs/017-complete-web-localization/checklists/requirements.md`

**Checkpoint**: The approved baseline truthfully reflects the completed localization evidence while all other gaps remain visible.

---

## Final Phase: Cross-Cutting Review

- [x] T037 Run `$speckit-analyze` again and resolve all CRITICAL findings across `specs/017-complete-web-localization/`
- [x] T038 Run `python3 scripts/check_spec_policy.py` and the focused policy tests in `backend/tests/test_spec_policy.py`
- [x] T039 Run the complete required backend PostgreSQL suite and Ruff checks without folding unrelated fixes into the feature PR
- [x] T040 Run `npm run test:i18n`, `npm run i18n:audit`, and `npm run build` in `frontend/`
- [x] T041 Complete the desktop/mobile four-language matrix in `specs/017-complete-web-localization/checklists/visual-review.md`
- [x] T042 Review the final diff against all FR/DR requirements, Source → Evidence → Reality, original-content losslessness, tenant/service boundaries, and no-schema scope in `specs/017-complete-web-localization/checklists/requirements.md`
- [x] T043 Update task checkboxes and final evidence in `specs/017-complete-web-localization/tasks.md` and `quickstart.md` only after every required check is green

## Dependencies

```text
Phase 1 gates
  └─ Phase 2 failing proof
      └─ US2 audit enforcement
          ├─ US1 complete selected languages
          │   └─ US3 safe fallback without hidden debt
          │       └─ US4 baseline evidence closure
          └────────────────────────────────────────┘
                              └─ Final review
```

- US2 precedes US1 because a trustworthy inventory is required to prove catalog completion.
- US1 and US3 share localization boundaries; US3 is accepted after complete catalogs prove normal behavior.
- US4 is strictly blocked by every automated and visual requirement from US1–US3.
- Final review is blocked by all four independently accepted stories.

## Parallel Opportunities

- T005 and T006 can proceed in parallel because they create separate test files.
- T009, T010, and T011 can prepare independent fixture groups in parallel.
- T018 and T019 can proceed while the initial production audit evidence is collected.
- T020, T021, and T022 are sequenced because all three edit
  `frontend/src/localization.tsx`; splitting catalogs is not justified for this feature.
- T033 and T035 can proceed in parallel only after T032 confirms the evidence gate.
- Backend gates and visual review can run alongside frontend automated gates after implementation stabilizes.

## Implementation Strategy

### MVP: Trustworthy Audit (US2)

Complete T001–T016 first. This produces a valuable, independently testable gate even
before the production catalogs are complete and makes remaining work measurable.

### Incremental Delivery

1. Prove the audit detects gaps across all source and language dimensions.
2. Complete production catalogs and selected-language UX (US1).
3. Prove runtime fallback cannot hide release debt (US3).
4. Close baseline evidence only after all proof is green (US4).
5. Run final cross-cutting review and create one focused PR.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T005, T009, T016 | T012, T015 | Complete |
| FR-002 | T010, T017, T026 | T013, T020–T022 | Complete |
| FR-003 | T005, T010, T016 | T013, T015 | Complete |
| FR-004 | T005, T010, T028, T031 | T013, T015, T030 | Complete |
| FR-005 | T005, T009, T016 | T012, T015 | Complete |
| FR-006 | T005, T011, T028, T031 | T014, T023, T030 | Complete |
| FR-007 | T006, T027, T031 | T029 | Complete |
| FR-008 | T006, T018, T026 | T023 | Complete |
| FR-009 | T006, T018, T026 | T024 | Complete |
| FR-010 | T019, T026, T041 | T025 | Complete |
| FR-011 | T007, T016, T040 | T015, `.github/workflows/quality.yml` review in T042 | Complete |
| FR-012 | T032, T033, T036 | T034–T035 | Complete |
| DR-001 | T006, T018, T026 | T023, T042 | Complete |
| DR-002 | T006, T018, T026 | T023, T042 | Complete |
| DR-003 | T006, T018, T026 | T024, T042 | Complete |
| DR-004 | T006, T018, T026 | T023, T042 | Complete |

## Format Validation

- All 43 tasks use checkbox, sequential task ID, optional parallel marker, story label
  where applicable, requirement reference where applicable, and exact file path or
  executable command context.
- Every FR and DR appears in at least one test/evidence task and one implementation or
  documentation/review task.
