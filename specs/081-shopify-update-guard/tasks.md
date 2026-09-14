# Tasks: Shopify Update Guard

**Input**: spec.md, plan.md and supporting artifacts.
**Gate**: Approved bounded scope; all Constitution rows PASS; no clarifications.

## Phase 1: Specification and Design

- [x] T001 Record approved scope and requirements review in spec.md and checklists/requirements.md.
- [x] T002 Pass Constitution Check and document design in plan.md, research.md and data-model.md.
- [x] T003 Analyze spec.md, plan.md and tasks.md for requirement coverage and conflicts.

## Phase 2: US1 — Preserve Operational Reality

- [x] T004 [US1] [FR-001] [FR-002] [FR-003] [DR-001] Add failing state-preservation and consecutive-version tests in packages/reality-core/tests/test_shopify_update_guard.py.
- [x] T005 [US1] [FR-001] [FR-002] [FR-003] [DR-001] Guard new Shopify interpretations and remove destructive replacement in packages/reality-core/src/reality/services/core.py.

## Phase 3: US2 — Review and Retry

- [x] T006 [US2] [FR-004] [FR-005] [FR-007] [DR-002] Add review, HTTP, batch and synchronous-helper tests in packages/reality-core/tests/test_shopify_update_guard.py.
- [x] T007 [US2] [FR-004] [FR-005] [FR-007] [DR-002] Handle terminal review and safe explanations in packages/reality-core/src/reality/services/core.py.

## Phase 4: US3 — Preserve Intake Guarantees

- [x] T008 [US3] [FR-006] [DR-002] Update old replacement expectations and first-version recovery tests in packages/reality-core/tests/test_shopify_and_explain.py; cover tenant boundaries in packages/reality-core/tests/test_shopify_update_guard.py.
- [x] T009 [US3] [FR-006] Align docs/features/shopify_ingestion.md, docs/ERP_MONTH.md, specs/005-source-ingestion/spec.md and relevant public integration/lifecycle guides with the guard.

## Final Phase: Verification and Review

- [x] T010 Run focused tests, make test, make lint and make spec-check; record results here.
- [x] T011 Run make web-build, make site-build and make docs-build; record results here.
- [x] T012 Review final diff against spec.md and Constitution, including no migration and rollback implications in plan.md.

## Dependencies and Strategy

T001 → T002 → T003. Write T004, T006 and T008 tests before T005/T007 code.
US1 protects the business state; US2 makes that protection visible and repeatable;
US3 proves compatibility. T009 follows the reviewed policy. Verification and final
review finish the feature. Independent build targets may run in parallel; service
edits remain sequential. No parallel agents are needed.

## Requirement Coverage

| Requirement | Test tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001 | T004 | T005 |
| FR-002 | T004 | T005 |
| FR-003 | T004 | T005 |
| FR-004 | T006 | T007 |
| FR-005 | T006 | T007 |
| FR-006 | T008 | T009 |
| FR-007 | T006 | T007 |
| DR-001 | T004 | T005 |
| DR-002 | T006, T008 | T007 |

## Verification Evidence

- Regression proof before implementation: 16 failed, 8 passed, exposing automatic
  replacement and missing review behavior. Four new fixtures initially reused an
  upstream timestamp; corrected them to represent updates rather than conflicts.
- Focused guard, Shopify and interpretation coverage suite: 24 passed.
- Complete backend suite: 508 passed, 7 skipped (including migrations and PostgreSQL
  concurrency tests). Test databases were isolated and removed by the harness.
- make lint and make spec-check: passed.
- make web-build: passed; 80 contract tests and all four locale audits passed.
- make site-build: passed; 48 tests and all four locale audits passed.
- make docs-build: passed; 37 tests and static rendering passed.
- git diff --check: passed. Existing web bundle-size warning remains non-failing.
- Final review: no schema, no operational document fields, no raw exception leakage,
  source stream remains latest accepted input, and completed review cannot reapply.
  The updated contracts explicitly preserve historical interpretations and defer
  initial cancellation interpretation and full amendment semantics.
- Pre-implementation analysis: 9/9 functional/domain requirements covered by tests
  and implementation/documentation tasks; 12 tasks; no critical findings.
- Spec-quality checklist passed. No extension hooks are configured.
- No release checklist, production data, or deployment was changed. Human merge
  authorization is not implied by this implementation review.
