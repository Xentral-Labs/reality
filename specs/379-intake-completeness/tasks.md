# Tasks: Essential intake completeness

## Setup and review

- [x] T001 Review approved scope, Constitution and existing intake contracts; record analysis in specs/379-intake-completeness/analysis.md.

## User Story 1: ambiguous money

- [x] T002 [US1] Add failing omission/null/blank currency and bank direction/date proofs with raw/no-effect assertions in packages/reality-core/tests/test_intake_completeness.py (FR-001/002/008, DR-001/003).
- [x] T003 [US1] Add pure required-value policy in packages/reality-core/src/reality/domain/intake_completeness.py and coded refusal translation/catalog in services/core.py and config/service_refusals.json.
- [x] T004 [US1] Apply essential monetary checks in services/shopify_intake.py, services/artifact_intake.py and services/file_interpreters.py; keep complete fixture/examples truthful (FR-001/002/008).

## User Story 2: incomplete orders

- [x] T005 [US2] Add failing omission/zero price, review-gap and file-date/local-midnight/header-conflict proofs in tests/test_intake_completeness.py (FR-003/004/005, DR-001/002).
- [x] T006 [US2] Preserve omitted prices and expose shared order gaps in services/core.py, services/shopify_intake.py, services/intake.py and services/artifact_intake.py; add file mapping fields and render shared issues/Unknown in apps/web/src/unified/CompletenessIssues.tsx, OrderCard.tsx and IntakeBatchReview.tsx with the existing order-entry browser proof (FR-003/004/005).

## User Story 3: simulator and units

- [x] T007 [US3] Add failing simulator source/date/register/replay and unsupported sales-unit proofs in tests/scenarios/test_live_company.py and tests/test_intake_completeness.py (FR-006/007).
- [x] T008 [US3] Author complete simulator orders in services/live_company.py and enforce stock-unit promise meaning through shared domain/services (FR-006/007).

## Verification and review

- [x] T009 Document the shared rule matrix in docs/features/intake-completeness.md and update source/simulator contracts and specs/SPEC_COVERAGE_MATRIX evidence; generate catalogs (FR-009).
- [ ] T010 Run affected and complete required backend/frontend/docs/spec gates; record measured verification in specs/379-intake-completeness/verification.md (all FR/DR, SC-003).
- [ ] T011 Review final diff, create/attach the PR and resolve every failing CI job on its current head; record actual status without merging.

## Dependencies and implementation strategy

T001 precedes tests. T002/T005/T007 are written and observed failing before implementation. Domain T003 precedes services T004/T006/T008. Documentation T009 follows final behavior; T010 and T011 are completion gates. Tests can be run independently, but edits to shared service files are sequential. No delegated agent work is required.
