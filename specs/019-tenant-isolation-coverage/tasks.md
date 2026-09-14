---
description: "Requirement-traceable implementation tasks for complete tenant isolation coverage"
---

# Tasks: Complete Tenant Isolation Coverage

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed, specification and plan approved, and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, catalog content, tests, and repository
artifacts MUST be written in English. Tests precede the implementation they prove.
PostgreSQL is the only business test database.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [X] T001 Record the 2026-08-31 owner approvals and confirm zero clarification markers in `specs/019-tenant-isolation-coverage/spec.md` and `plan.md`
- [X] T002 Confirm every Constitution Check row and post-design re-evaluation remain PASS in `specs/019-tenant-isolation-coverage/plan.md`
- [X] T003 Validate the evidence entities and catalog semantics against `specs/019-tenant-isolation-coverage/data-model.md` and `contracts/tenant-isolation-catalog.md`
- [X] T004 Run `$speckit-analyze` across `specs/019-tenant-isolation-coverage/spec.md`, `plan.md`, and `tasks.md`; resolve every CRITICAL finding before implementation

## Phase 2: Foundational Failing Proof and Harness

**Purpose**: Establish catalog failure semantics and the shared two-tenant graph before
claiming family coverage.

- [X] T005 [FR-001] [FR-002] [FR-003] [FR-009] [FR-010] Add failing complete, missing, duplicate, stale, invalid-classification, empty-evidence, and broad-exemption catalog cases in `backend/tests/test_application_catalog.py`
- [X] T006 [FR-001] [FR-008] [FR-010] Add failing callable, indirect-operation, projection-registry, tool-registry, and canonical-catalog drift cases in `backend/tests/test_application_catalog.py`
- [X] T007 [P] [DR-001] [DR-002] [DR-005] Add a failing asymmetric Source → Evidence → Reality two-tenant fixture contract in `backend/tests/tenant_isolation/conftest.py` and `backend/tests/tenant_isolation/test_families.py`
- [X] T008 [FR-001] [FR-002] Add the initial contract-shaped `backend/config/tenant_isolation_catalog.yaml` with no unsupported verified claims so T005–T007 fail for coverage rather than parsing
- [X] T009 [FR-001] [FR-002] [FR-008] [FR-009] [FR-010] Implement reusable catalog loading, schema validation, and deterministic discovery helpers in `backend/src/reality/catalogs.py` and `backend/tests/tenant_isolation/coverage.py`
- [X] T010 [DR-001] [DR-002] [DR-005] Implement the reusable populated, overlapping-identity, asymmetric two-tenant graph in `backend/tests/tenant_isolation/conftest.py`

**Checkpoint**: Invalid catalog fixtures fail precisely; the production catalog still
reports every uncovered family and cannot yet satisfy the baseline.

---

## Phase 3: User Story 1 - Keep One Company's Data Isolated (Priority: P1)

**Goal**: Prove foreign reads are non-disclosing and foreign records contribute nothing
to collections or aggregates across the complete public read surface.

**Independent Test**: Exercise every cataloged record-read, collection, and aggregate
family with both tenants populated; foreign IDs equal unknown IDs and foreign sentinels/
measures contribute zero.

### Tests

- [X] T011 [US1] [FR-004] Add foreign-ID-versus-unknown-ID cases for detail, Source/Evidence, Reality, finance, integration, chat, and projection read families in `backend/tests/tenant_isolation/test_families.py`
- [X] T012 [US1] [FR-005] [DR-002] Add overlapping-name/code/external-ID collection and search exclusion cases in `backend/tests/tenant_isolation/test_families.py`
- [X] T013 [US1] [FR-005] Add asymmetric inventory, commitment, finance, event, timeline, usage, and projection aggregate cases in `backend/tests/tenant_isolation/test_families.py`
- [X] T014 [US1] [DR-001] [DR-005] Add local lineage traversal, foreign cross-stage denial, and unchanged Source payload assertions in `backend/tests/tenant_isolation/test_families.py`
- [X] T015 [P] [US1] [FR-007] Add representative read-tool and API tenant-context propagation cases in `backend/tests/test_application_tools.py` and `backend/tests/test_master_data_api.py`

### Implementation and Evidence

- [X] T016 [US1] [FR-001] [FR-002] [FR-003] Classify and map every record-read, collection, and aggregate operation with named evidence in `backend/config/tenant_isolation_catalog.yaml`
- [X] T017 [US1] [FR-004] [FR-005] [FR-011] Correct only read, collection, aggregate, or projection leaks proven by T011–T015 in the affected shared file under `backend/src/reality/services/`, or record that no defect was found; record each exact outcome in `specs/019-tenant-isolation-coverage/quickstart.md`
- [X] T018 [US1] [FR-003] [FR-004] [FR-005] Run the complete User Story 1 family slice and record discovered/covered counts and results in `specs/019-tenant-isolation-coverage/quickstart.md`

**Checkpoint**: Every public read family is independently proven without relying on an
adapter-only filter.

---

## Phase 4: User Story 2 - Reject Cross-Tenant Writes and Links (Priority: P1)

**Goal**: Prove every public mutation or tenant-owned relationship rejects foreign IDs
atomically and without disclosure.

**Independent Test**: Execute every cataloged mutation/relationship family under Tenant
A with controlled Tenant B inputs; both tenant graphs and event streams are unchanged.

### Tests

- [X] T019 [US2] [FR-006] [DR-002] Add master-data, pricing, source/integration, and artifact foreign-relationship cases in `backend/tests/tenant_isolation/test_families.py`
- [X] T020 [US2] [FR-006] [DR-001] Add document, commitment, reservation, tracking, movement, hold, and correction foreign-relationship cases in `backend/tests/tenant_isolation/test_families.py`
- [X] T021 [US2] [FR-006] Add ledger, payment, allocation, chat, proposal, import, and projection-refresh foreign-input cases in `backend/tests/tenant_isolation/test_families.py`
- [X] T022 [US2] [FR-006] Add reusable before/after row, Business Event, quantity, balance, and record-state snapshots for failed mutations in `backend/tests/tenant_isolation/coverage.py` and assert them from `backend/tests/tenant_isolation/test_families.py`
- [X] T023 [P] [US2] [FR-007] Add shared application-tool proposal/confirm/reject and representative API mutation context cases in `backend/tests/test_application_tools.py` and `backend/tests/test_master_data_api.py`

### Implementation and Evidence

- [X] T024 [US2] [FR-001] [FR-002] [FR-003] Classify and map every mutation, relationship, and tenant-aware boundary operation with named evidence in `backend/config/tenant_isolation_catalog.yaml`
- [X] T025 [US2] [FR-006] [FR-011] Correct only mutation/relationship leaks proven by T019–T023 at the affected shared service boundary under `backend/src/reality/services/` or `backend/src/reality/tools/application.py`, or record that no defect was found; record each exact outcome in `specs/019-tenant-isolation-coverage/quickstart.md`
- [X] T026 [US2] [FR-003] [FR-006] Run the complete User Story 2 family slice and record atomicity and no-side-effect evidence in `specs/019-tenant-isolation-coverage/quickstart.md`

**Checkpoint**: Every foreign write/link fails before commit with no state change in
either tenant.

---

## Phase 5: User Story 3 - Detect Coverage Drift (Priority: P1)

**Goal**: Make exhaustive isolation evidence durable as public services, projections,
tools, and catalogs evolve.

**Independent Test**: The current catalog validates; controlled uncovered, stale,
duplicate, invalid, unproven, and overbroad-exemption fixtures fail with stable details.

### Tests

- [X] T027 [US3] [FR-008] [FR-010] Complete controlled discovery fixtures for newly added tenant-aware and indirect-context operations in `backend/tests/test_application_catalog.py`
- [X] T028 [US3] [FR-008] [FR-010] Complete projection, application-tool, command-catalog, and projection-catalog drift fixtures in `backend/tests/test_application_catalog.py`
- [X] T029 [US3] [FR-009] Add approved global-admin and rejected missing/broad exemption cases in `backend/tests/test_application_catalog.py`
- [X] T030 [US3] [FR-003] Add evidence-reference uniqueness, existence, classification compatibility, per-operation execution coverage, and deterministic ordering cases in `backend/tests/test_application_catalog.py`

### Implementation and Evidence

- [X] T031 [US3] [FR-001] [FR-002] [FR-008] [FR-010] Complete production discovery and catalog drift enforcement in `backend/src/reality/catalogs.py` and `backend/tests/tenant_isolation/coverage.py`
- [X] T032 [US3] [FR-003] [FR-009] Classify explicit indirect-context and global/platform-administrative operations with authority, reason, and evidence in `backend/config/tenant_isolation_catalog.yaml`
- [X] T033 [US3] [FR-008] Integrate tenant-isolation catalog validation into the existing catalog/policy regression path in `backend/tests/test_application_catalog.py`
- [X] T034 [US3] [FR-008] [FR-009] [FR-010] Run the independent drift/exemption scenarios and record final family/operation/projection/tool counts in `specs/019-tenant-isolation-coverage/quickstart.md`

**Checkpoint**: A future uncovered public business operation cannot pass the normal
backend quality suite.

---

## Phase 6: User Story 4 - Close the Baseline Gap with Objective Evidence (Priority: P2)

**Goal**: Change only `003/FR-012` after all complete isolation evidence is green.

**Independent Test**: Baseline and coverage matrix cite the complete catalog and passing
family evidence while every unrelated documented gap remains unchanged.

### Evidence and Policy Gate

- [X] T035 [US4] [FR-012] Verify T005–T034, full catalog coverage, family proofs, adapter evidence, and zero unresolved isolation defects before baseline edits; record the gate in `specs/019-tenant-isolation-coverage/checklists/requirements.md`
- [X] T036 [P] [US4] [FR-012] Add a policy regression recognizing verified `003/FR-012` evidence and preserving every unrelated gap in `backend/tests/test_spec_policy.py`

### Documentation Implementation

- [X] T037 [US4] [FR-012] Change only `003/FR-012` from `Documented gap` to `Verified as-is` and cite Spec 019 evidence in `specs/003-tenant-access/spec.md`
- [X] T038 [P] [US4] [FR-012] Remove only `003/FR-012`, update verified/gap counts, and record tenant-isolation evidence in `docs/SPEC_COVERAGE_MATRIX.md`
- [X] T039 [US4] [FR-012] Run the independent baseline-closure diff review and record owner acceptance in `specs/019-tenant-isolation-coverage/checklists/requirements.md`

---

## Final Phase: Cross-Cutting Review

- [X] T040 Run `$speckit-analyze` again and resolve all CRITICAL findings across `specs/019-tenant-isolation-coverage/`
- [X] T041 Run `python3 scripts/check_spec_policy.py` and the focused policy tests in `backend/tests/test_spec_policy.py`
- [X] T042 Run Ruff for every changed Python file and the complete backend PostgreSQL suite from `backend/`
- [X] T043 Review the final diff against FR-001–FR-012, DR-001–DR-006, Source → Evidence → Reality, non-disclosure, atomicity, shared-service boundaries, lossless payloads, and no-schema scope in `specs/019-tenant-isolation-coverage/checklists/requirements.md`
- [X] T044 Update final task checkboxes, requirement coverage, counts, commands, defects, and evidence in `specs/019-tenant-isolation-coverage/tasks.md` and `quickstart.md` only after all required checks are green

## Dependencies

```text
Spec/plan approval
  └─ Catalog failure semantics + two-tenant harness
      ├─ US1 complete read/collection/aggregate proof
      ├─ US2 complete mutation/relationship proof
      └─ US3 discovery/registry/exemption drift gate
             └─ US4 baseline closure
                    └─ Final cross-cutting review
```

- T005–T010 block all story claims.
- US1 and US2 may use the same graph after T010 but edit the same catalog and are
  therefore completed sequentially.
- US3 finalizes catalog completeness after US1/US2 operations and evidence are mapped.
- US4 is strictly blocked by every automated requirement and unresolved defect.

## Parallel Opportunities

- T005 and T006 are sequential because both extend the catalog test module; T007 can
  proceed in parallel because it owns the tenant-isolation fixture files.
- T011–T014 are sequential within the shared family test module; T015 can proceed in
  parallel because it owns adapter test modules.
- T019–T022 are sequential within the shared isolation test files; T023 can proceed in
  parallel because it owns adapter test modules.
- T027–T030 are sequential because they extend the same catalog test module.
- T036 and T038 touch separate files only after T035 passes.

## Implementation Strategy

### MVP: Trustworthy Coverage Gate

Complete T001–T010 and T027–T033 first in implementation order only after preserving
test-first dependencies. This proves drift detection even before all production families
are green, but does not permit baseline closure.

### Incremental Delivery

1. Prove catalog validation fails correctly and build the shared two-tenant graph.
2. Complete read, collection, aggregate, and lineage proof (US1).
3. Complete mutation, relationship, and atomicity proof (US2).
4. Complete discovery, registry, and exemption drift enforcement (US3).
5. Close `003/FR-012` only after owner-reviewed evidence (US4).

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T005–T006, T027–T028 | T008–T009, T016, T024, T031 | Complete |
| FR-002 | T005 | T008–T009, T016, T024, T031–T032 | Complete |
| FR-003 | T005, T030 | T016, T024, T032–T034 | Complete |
| FR-004 | T011 | T016–T018 | Complete |
| FR-005 | T012–T013 | T016–T018 | Complete |
| FR-006 | T019–T023 | T024–T026 | Complete |
| FR-007 | T015, T023 | T017, T025 | Complete |
| FR-008 | T006, T027–T028 | T031, T033–T034 | Complete |
| FR-009 | T005, T029 | T009, T032, T034 | Complete |
| FR-010 | T005–T006, T027–T030 | T009, T031, T034 | Complete |
| FR-011 | T011–T015, T019–T023 | T017, T025 | Complete |
| FR-012 | T035–T036 | T037–T039 | Complete |
| DR-001 | T007, T014, T020 | T010, T017, T025, T043 | Complete |
| DR-002 | T007, T012, T019–T020 | T010, T016, T024, T043 | Complete |
| DR-003 | T015, T023, T027–T030 | T009, T031–T033, T043 | Complete |
| DR-004 | T014, T020 | T017, T025, T043 | Complete |
| DR-005 | T007, T014 | T010, T017, T043 | Complete |
| DR-006 | T005–T034 review | T009, T017, T025, T031, T043 | Complete |

## Format Validation

- All 44 tasks use checkbox, sequential task ID, optional parallel marker, story label
  where applicable, requirement references where applicable, and exact file path or
  executable command context.
- Every FR and DR appears in at least one test/evidence task and one implementation or
  documentation/review task.
