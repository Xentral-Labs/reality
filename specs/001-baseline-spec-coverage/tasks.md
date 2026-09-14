---
description: "Requirement-traceable tasks for the existing-system specification baseline"
---

# Tasks: Existing-System Specification Baseline

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed; specification and plan approved; no unresolved clarification

All task descriptions, review notes, and resulting repository artifacts are written in
English. Product code and schema are read-only evidence throughout this feature.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner approval and Reviewed status in `specs/001-baseline-spec-coverage/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/001-baseline-spec-coverage/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL finding across `specs/001-baseline-spec-coverage/`

## Phase 2: Foundational Coverage Infrastructure

- [x] T004 [FR-001] Create the thirteen-row capability index in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T005 [P] [FR-001] Inventory all durable feature and cross-cutting contracts in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T006 [P] [FR-001] Inventory every table from `backend/config/data_model.yaml` in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T007 [P] [FR-001] Inventory backend test families and skipped-proof limitations in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T008 [P] [FR-001] Inventory public service/tool and adapter/UI capability families in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T009 [FR-002] Assign every coverage entry to one primary baseline or cross-cutting authority in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T010 [FR-003] Extend deterministic baseline structure and language validation from `specs/001-baseline-spec-coverage/contracts/baseline-spec-template.md` in `scripts/check_spec_policy.py`
- [x] T011 [FR-001] [FR-002] Add coverage-policy regression tests in `backend/tests/test_spec_policy.py`

## Phase 3: User Story 1 — Find the Authority for Existing Behavior (P1)

**Goal**: Every existing capability has one discoverable, evidence-backed baseline owner.

**Independent Test**: Every contract, catalog table, test family, and public capability
row maps to exactly one primary baseline or an explicit cross-cutting/excluded entry.

- [x] T012 [P] [US1] [FR-003] [FR-011] Draft tenant/access baseline and checklist in `specs/003-tenant-access/`
- [x] T013 [P] [US1] [FR-003] [FR-011] Draft master-data baseline and checklist in `specs/004-master-data/`
- [x] T014 [US1] [FR-004] [FR-005] Classify and link foundation evidence in `specs/003-tenant-access/spec.md` and `specs/004-master-data/spec.md`
- [x] T015 [P] [US1] [FR-003] [FR-011] Draft source-ingestion baseline and checklist in `specs/005-source-ingestion/`
- [x] T016 [P] [US1] [FR-003] [FR-011] Draft documents/evidence baseline and checklist in `specs/006-documents-evidence/`
- [x] T017 [US1] [FR-004] [FR-005] Classify and link Source/Evidence proof in `specs/005-source-ingestion/spec.md` and `specs/006-documents-evidence/spec.md`
- [x] T018 [P] [US1] [FR-003] [FR-011] Draft commitments/holds baseline and checklist in `specs/008-commitments-holds/`
- [x] T019 [P] [US1] [FR-003] [FR-011] Draft inventory/execution baseline and checklist in `specs/009-inventory-execution/`
- [x] T020 [US1] [FR-004] [FR-005] Classify and link operational Reality proof in `specs/008-commitments-holds/spec.md` and `specs/009-inventory-execution/spec.md`
- [x] T021 [P] [US1] [FR-003] [FR-011] Draft order-to-cash baseline and checklist in `specs/010-order-to-cash/`
- [x] T022 [P] [US1] [FR-003] [FR-011] Draft procure-to-pay baseline and checklist in `specs/011-procure-to-pay/`
- [x] T023 [P] [US1] [FR-003] [FR-011] Draft ledger/finance baseline and checklist in `specs/012-ledger-finance/`
- [x] T024 [US1] [FR-004] [FR-005] Classify and link end-to-end financial proof in `specs/010-order-to-cash/spec.md`, `specs/011-procure-to-pay/spec.md`, and `specs/012-ledger-finance/spec.md`
- [x] T025 [P] [US1] [FR-003] [FR-011] Draft explain/projections baseline and checklist in `specs/013-explain-projections/`
- [x] T026 [P] [US1] [FR-003] [FR-011] Draft agent-interaction baseline and checklist in `specs/014-agent-interaction/`
- [x] T027 [P] [US1] [FR-003] [FR-011] Draft demo/scenarios baseline and checklist in `specs/015-demo-scenarios/`
- [x] T028 [US1] [FR-004] [FR-005] Classify and link explanation/interaction proof in `specs/013-explain-projections/spec.md`, `specs/014-agent-interaction/spec.md`, and `specs/015-demo-scenarios/spec.md`
- [x] T029 [US1] [FR-003] [FR-011] Draft Web product baseline and checklist in `specs/016-web-product/`
- [x] T030 [US1] [FR-004] [FR-005] Classify Web and shared-service equivalence proof in `specs/016-web-product/spec.md`
- [x] T031 [US1] [FR-002] [FR-006] Reconcile all primary owners, exclusions, gaps, and skipped tests in `docs/SPEC_COVERAGE_MATRIX.md`

## Phase 4: User Story 2 — Review Current Reality Without Losing Uncertainty (P1)

**Goal**: The owner can distinguish proven behavior, gaps, future intent, and decisions.

**Independent Test**: A sample of every evidence status has correct evidence; no Draft
spec is presented as Reviewed and every material ambiguity has a decision record.

- [x] T032 [US2] [FR-004] [FR-006] Validate evidence statuses in `specs/003-tenant-access/spec.md`, `specs/004-master-data/spec.md`, `specs/005-source-ingestion/spec.md`, `specs/006-documents-evidence/spec.md`, `specs/008-commitments-holds/spec.md`, `specs/009-inventory-execution/spec.md`, `specs/010-order-to-cash/spec.md`, `specs/011-procure-to-pay/spec.md`, `specs/012-ledger-finance/spec.md`, `specs/013-explain-projections/spec.md`, `specs/014-agent-interaction/spec.md`, `specs/015-demo-scenarios/spec.md`, and `specs/016-web-product/spec.md`
- [x] T033 [US2] [FR-007] Record all contract/implementation/test contradictions in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T034 [US2] [FR-008] Prepare at most three owner questions per review batch in the exact baseline checklist paths listed by T012-T013, T015-T016, T018-T019, T021-T023, T025-T027, and T029
- [x] T035 [US2] [FR-008] [FR-009] Record owner answers in English and update requirement statuses in each reviewed baseline `spec.md`
- [x] T036 [US2] [FR-009] Update each completed checklist at the exact baseline paths created by T012-T013, T015-T016, T018-T019, T021-T023, T025-T027, and T029 from Draft to Reviewed
- [x] T037 [US2] [FR-010] Replace duplicated cross-cutting rules with canonical links in the exact thirteen baseline spec paths named by T032
- [x] T038 [US2] [FR-013] Verify English language and terminology consistency across `specs/` and `docs/SPEC_COVERAGE_MATRIX.md`

## Phase 5: User Story 3 — Start the Next Change Spec-First (P2)

**Goal**: A contributor can locate authority and start a future change without reading implementation first.

**Independent Test**: A representative change drill locates its baseline, cross-cutting
contracts, affected requirements, and review gates in under five minutes.

- [x] T039 [US3] [DR-001] [DR-002] Audit Source → Evidence → Reality and stored/derived declarations across all baseline specs in `specs/`
- [x] T040 [US3] [DR-003] [DR-004] Audit tenant, shared-service, opaque-ID, and shortest-link declarations across all baseline specs in `specs/`
- [x] T041 [US3] [DR-005] Audit Web explanation paths in applicable specs and `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T042 [US3] [SC-006] Record a representative future-change discovery drill in `specs/001-baseline-spec-coverage/quickstart.md`
- [x] T043 [US3] [FR-001] [FR-002] Verify final discovery navigation from `docs/SPEC_COVERAGE_MATRIX.md` to every baseline and authority

## Final Phase: Cross-Cutting Verification

- [x] T044 [FR-001] [FR-011] Run the complete coverage/spec-policy suite from `scripts/check_spec_policy.py` and `backend/tests/test_spec_policy.py`
- [x] T045 [FR-012] Confirm isolated baseline commits contain no changes under `backend/src/`, `backend/migrations/`, or `frontend/src/`
- [x] T046 Run Ruff and the complete PostgreSQL suite using `make lint` and `make test`
- [x] T047 Run frontend build and translation audit using `make frontend-build` and `cd frontend && npm run i18n:audit`
- [x] T048 Review final artifacts against `.specify/memory/constitution.md` and `specs/001-baseline-spec-coverage/spec.md`
- [x] T049 Update final counts, review dates, and evidence gaps in `docs/SPEC_COVERAGE_MATRIX.md`

## Dependencies and Execution Order

```text
T001-T003
   ↓
T004-T011 foundational inventory/policy
   ↓
US1: T012-T031 baseline creation
   ↓
US2: T032-T038 owner review and uncertainty resolution
   ↓
US3: T039-T043 future-change discovery proof
   ↓
T044-T049 final verification
```

Foundation specs T012-T014 precede all later owner reviews. Within each evidence batch,
drafting tasks marked `[P]` may proceed in parallel, but classification/reconciliation
waits for all drafts in that batch. US2 depends on all US1 drafts so terminology and
status decisions remain consistent. US3 depends on reviewed baseline links.

## Parallel Examples

- T005-T008 inventory different evidence families in parallel.
- T012 and T013 draft the two foundation baselines in parallel.
- T015/T016, T018/T019, T021-T023, and T025-T027 are parallel drafting batches.
- Product code is never edited in parallel with baseline work.

## Implementation Strategy

The first independently useful increment is US1 through the foundation batch:
`docs/SPEC_COVERAGE_MATRIX.md`, `003-tenant-access`, and `004-master-data`. Present that
batch to the owner before proceeding. Continue batch-by-batch, retaining Draft status
until questions are answered. US2 converts reviewed scope and decisions into durable
English baselines. US3 proves the resulting system guides future spec-first work.

## Requirement Coverage

| Requirement | Validation task(s) | Documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T011, T031, T043-T044 | T004-T009 | Complete |
| FR-003–FR-006 | T032, T044 | T012-T031 | Complete |
| FR-007–FR-010 | T033, T036-T037 | T034-T035 | Complete |
| FR-011–FR-013 | T038, T044-T045 | T012-T030 | Complete |
| DR-001–DR-002 | T039, T048 | T012-T030 | Complete |
| DR-003–DR-004 | T040, T048 | T012-T030 | Complete |
| DR-005 | T041, T048 | T014, T017, T020, T024, T028, T030 | Complete |
| SC-001–SC-007 | T042-T049 | All baseline tasks | Complete |
