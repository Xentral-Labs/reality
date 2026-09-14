---
description: "Requirement-traceable tasks for complete operational exception coverage"
---

# Tasks: Complete Operational Exception Coverage

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Approved specification and plan, Constitution Check PASS, and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, catalog content, tests, and repository
artifacts MUST be written in English. Tests precede the implementation they prove.
PostgreSQL is the only business test database.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [X] T001 Record the 2026-08-31 owner approvals and confirm zero clarification markers in `specs/020-exception-class-coverage/spec.md` and `plan.md`
- [X] T002 Confirm every Constitution Check row and post-design re-evaluation remain PASS in `specs/020-exception-class-coverage/plan.md`
- [X] T003 Validate taxonomy, identity, trace, and clearing semantics across `specs/020-exception-class-coverage/data-model.md` and `contracts/operational-exception-contract.md`
- [X] T004 Run `$speckit-analyze` across `specs/020-exception-class-coverage/spec.md`, `plan.md`, and `tasks.md`; resolve every CRITICAL finding before implementation

## Phase 2: Foundational Failing Proof and Taxonomy Harness

**Purpose**: Establish the closed five-class/one-cause authority, deterministic drift
failures, and reusable multi-class/two-tenant story before any coverage claim.

- [X] T005 [FR-001] [FR-002] [FR-013] Add failing missing, stale, duplicate, unordered, invalid-metadata, and empty-evidence taxonomy cases in `packages/reality-core/tests/operational_exceptions/test_coverage.py`
- [X] T006 [P] [FR-009] [FR-011] [DR-002] [DR-004] Add failing stable-identity, legacy-field, causal-value, trace, malformed-ID, and foreign-ID contract cases in `packages/reality-core/tests/operational_exceptions/test_explanation.py`
- [X] T007 [DR-001] [DR-003] [DR-004] Add a failing controlled-UTC, overlapping-human-ID, asymmetric two-tenant multi-class fixture contract in `packages/reality-core/tests/operational_exceptions/conftest.py` and `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T008 [FR-001] [FR-002] Add the contract-shaped five-class/one-cause authority with named requirements and evidence in `packages/reality-core/config/operational_exception_catalog.yaml`
- [X] T009 [FR-001] [FR-002] [FR-013] Implement taxonomy loading, schema validation, stable ordering, and registry-shape drift helpers in `packages/reality-core/src/reality/catalogs.py` and `packages/reality-core/tests/operational_exceptions/test_coverage.py`; defer production evidence-symbol resolution until T035/T039
- [X] T010 [FR-003] [FR-009] [DR-001] Add immutable exception class/cause/value types, the explicit derivation registry, and JSON conversion skeleton in `packages/reality-core/src/reality/services/exceptions.py`

**Checkpoint**: Invalid taxonomy fixtures fail precisely; the production taxonomy and
empty derivation skeleton load without claiming unimplemented class evidence.

---

## Phase 3: User Story 1 - See Every Documented Exception Class (Priority: P1)

**Goal**: Derive exactly five visible tenant-scoped queue classes and one nested cause
from current authoritative records.

**Independent Test**: Create every approved condition at controlled UTC for two populated
tenants; the local queue contains exactly the expected five identities, one umbrella
cause, exact quantities/amounts, and no foreign or undocumented entry.

### Tests

- [X] T011 [US1] [FR-003] [FR-004] Add outgoing-risk positive, partial, fully reserved/fulfilled/cancelled, no-duplicate, and exact `insufficient_reservation` cause cases in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T012 [US1] [FR-003] [FR-005] Add overdue supplier past/equal/future/missing-date, partial-receipt, full-receipt, and cancellation cases at controlled UTC in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T013 [US1] [FR-003] [FR-006] [DR-001] Add any-error failed ImportJob, empty-error fallback, immutable Source trace, successful retry, pending, and completed cases in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T014 [US1] [FR-003] [FR-007] [DR-005] Add unlinked shipment/receipt/return and excluded linked execution, opening, transfer, and audited-adjustment cases in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T015 [US1] [FR-003] [FR-008] Add unmatched, partially allocated, fully allocated, non-payment, customer, and supplier control-entry cases with exact Decimal remainder in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T016 [US1] [FR-009] [FR-011] [DR-004] Add exact five-class ordering, empty queue, overlapping-human-ID, and asymmetric foreign-tenant exclusion assertions in `packages/reality-core/tests/operational_exceptions/test_derivation.py`

### Implementation and Evidence

- [X] T017 [US1] [FR-003] [FR-004] [FR-005] Implement customer-risk and overdue-supplier derivators with controlled UTC and existing Commitment/Reservation/Movement authority in `packages/reality-core/src/reality/services/exceptions.py`
- [X] T018 [US1] [FR-003] [FR-006] [FR-007] Implement failed-import and conservative unexplained-movement derivators with explicit Source absence and no retroactive mutation in `packages/reality-core/src/reality/services/exceptions.py`
- [X] T019 [US1] [FR-003] [FR-008] Implement unmatched-payment derivation from payment control LedgerEntry and tenant-scoped SettlementAllocation remainder in `packages/reality-core/src/reality/services/exceptions.py`
- [X] T020 [US1] [FR-001] [FR-002] Complete taxonomy metadata/evidence and update exact five-class/one-cause semantics in `packages/reality-core/config/operational_exception_catalog.yaml` and `docs/features/operational_exceptions.md`
- [X] T021 [US1] [FR-003] [FR-009] [FR-011] Assemble deterministic tenant-scoped canonical ordering and compatibility dictionaries in `packages/reality-core/src/reality/services/exceptions.py`
- [X] T022 [US1] Run the complete User Story 1 slice and record class/cause counts, exact outcomes, and any proven defect in `specs/020-exception-class-coverage/quickstart.md`

**Checkpoint**: The direct shared service independently proves all five classes and the
nested cause without any adapter or projection authority.

---

## Phase 4: User Story 2 - Explain and Remediate a Derived Exception (Priority: P1)

**Goal**: Explain every current identity through shortest tenant-scoped links and clear
each remediable class only by correcting authoritative Reality/Source processing.

**Independent Test**: Explain all five local classes, reject stale/unknown/foreign IDs,
run existing owning actions for four remediable classes, and observe re-derived removal
without editing exception or projection state.

### Tests

- [X] T023 [P] [US2] [FR-009] [FR-011] [DR-001] [DR-002] Add class-specific Commitment, ImportJob/Source, Movement, Ledger/Document, explicit-absence, raw-payload, stale, malformed, and foreign explanation cases in `packages/reality-core/tests/operational_exceptions/test_explanation.py`
- [X] T024 [US2] [FR-012] [DR-005] Add reserve/ship/cancel, receive/cancel, successful retry, and payment-allocation clearing stories plus explicit no-retroactive-Movement behavior in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T025 [P] [US2] [FR-010] [FR-011] Add list/explain/current/stale/foreign application-tool parity cases in `packages/reality-core/tests/test_application_tools.py`
- [X] T026 [US2] [FR-010] [FR-011] Add Web exception list/count/Home/Inspector parity and non-disclosure cases for all record types in `packages/reality-core/tests/test_master_data_api.py`
- [X] T027 [P] [US2] [FR-010] [FR-011] Add MCP list/explain parity, stable class/cause fields, and foreign/stale non-disclosure cases in `packages/reality-core/tests/test_ai_mcp.py`

### Implementation and Evidence

- [X] T028 [US2] [FR-009] [FR-011] [DR-001] [DR-002] Implement current-queue identity lookup and class-specific hydrated Source/Evidence/Reality explanation in `packages/reality-core/src/reality/services/exceptions.py`
- [X] T029 [US2] [FR-010] Replace projection-row-only tool explanation with the shared list/explain service while preserving proposal boundaries in `packages/reality-core/src/reality/tools/application.py`
- [X] T030 [US2] [FR-010] Remove Web exception predicates and paginate/count the shared canonical result in `packages/reality-core/src/reality/web/read_models.py`
- [X] T031 [US2] [FR-010] Replace commitment/import ID inference with the shared generic exception Inspector contract in `packages/reality-core/src/reality/web/api.py`
- [X] T032 [US2] [FR-010] Preserve MCP as a thin application-tool adapter and change `packages/reality-core/src/reality/mcp/server.py` only if T027 proves a contract propagation defect, or record that no change was required in `specs/020-exception-class-coverage/quickstart.md`
- [X] T033 [US2] [FR-010] Replace the Core fallback Chat tuple rendering and compatibility path with the shared exception contract in `packages/reality-core/src/reality/services/core.py`
- [X] T034 [US2] [FR-012] [DR-005] Run every clearing/non-clearing story and record owning actions, unchanged Source/Movement history, and outcomes in `specs/020-exception-class-coverage/quickstart.md`

**Checkpoint**: Every current class is explainable through the same service and all
existing remediations clear only their authoritative cause.

---

## Phase 5: User Story 3 - Prevent Exception Coverage Drift (Priority: P1)

**Goal**: Make taxonomy, derivation, evidence, projections, and adapters fail visibly
when a class or cause changes incompletely.

**Independent Test**: Production authority validates; controlled missing, stale,
duplicate, unordered, unproven, and registry-divergent fixtures fail with stable details,
and every shared consumer matches the canonical service.

### Tests

- [X] T035 [US3] [FR-013] Complete derivation-registry, nested-cause, evidence-symbol, stable-order, and deterministic multi-error drift cases in `packages/reality-core/tests/operational_exceptions/test_coverage.py`
- [X] T036 [P] [US3] [FR-010] [FR-013] Add exception projection rebuild/parity, stable-row removal, and no-alternative-calculation cases in `packages/reality-core/tests/test_materialized_projections.py`
- [X] T037 [US3] [FR-010] [FR-013] Add production taxonomy validation to the normal application catalog regression path in `packages/reality-core/tests/test_application_catalog.py`

### Implementation and Evidence

- [X] T038 [US3] [FR-010] Replace tuple materialization with canonical exception dictionaries and stable IDs in `packages/reality-core/src/reality/services/projections.py`
- [X] T039 [US3] [FR-013] Complete production taxonomy/registry/evidence validation and deterministic error reporting in `packages/reality-core/src/reality/catalogs.py`
- [X] T040 [US3] Run taxonomy, registry, projection, tool, API, and MCP drift/parity scenarios and record final counts in `specs/020-exception-class-coverage/quickstart.md`

**Checkpoint**: A future class, cause, derivator, or interface divergence cannot pass the
normal backend quality suite.

---

## Phase 6: User Story 4 - Close the Accepted Baseline Gap (Priority: P2)

**Goal**: Change only `013/FR-005` after all complete exception evidence is green.

**Independent Test**: The baseline and coverage matrix cite the complete taxonomy and
passing class evidence while every unrelated documented gap remains unchanged.

- [X] T041 [US4] [FR-014] Verify T005–T040, all five classes/cause, explanation, applicable clearing or explicit no-retroactive-remediation proof, adapter parity, drift validation, and zero unresolved defects before baseline edits; record the gate in `specs/020-exception-class-coverage/quickstart.md`
- [X] T042 [P] [US4] [FR-014] Add a policy regression recognizing verified `013/FR-005` evidence and preserving every unrelated gap in `packages/reality-core/tests/test_spec_policy.py`
- [X] T043 [P] [US4] [FR-014] Change only `013/FR-005` from `Documented gap` to `Verified as-is` with Spec 020 evidence in `specs/013-explain-projections/spec.md`
- [X] T044 [P] [US4] [FR-014] Remove only `013/FR-005`, update the `013` verified/gap counts and accepted-gap total from 9 to 8, and record taxonomy evidence in `docs/SPEC_COVERAGE_MATRIX.md`
- [X] T045 [US4] [FR-014] Run the independent baseline-closure diff review and append the owner-acceptance note to `specs/020-exception-class-coverage/checklists/requirements.md` without changing the approved quality markers

---

## Final Phase: Cross-Cutting Review

- [X] T046 Run `$speckit-analyze` again and resolve all CRITICAL findings across `specs/020-exception-class-coverage/`
- [X] T047 Run `python3 scripts/check_spec_policy.py` and focused `packages/reality-core/tests/test_spec_policy.py` policy tests
- [X] T048 Run Ruff from the repository root for every changed Python file and the complete backend PostgreSQL suite from `packages/reality-core/`
- [X] T049 Run the frontend build and translation audit to verify the backward-compatible list/Inspector payload requires no frontend change
- [X] T050 Confirm no model or Alembic file changed and review projection rollback/disposability against `specs/020-exception-class-coverage/plan.md`
- [X] T051 Review the final diff against FR-001–FR-014, DR-001–DR-006, Source → Evidence → Reality, non-disclosure, Decimal/UTC semantics, shared-service boundaries, and no-schema scope in `specs/020-exception-class-coverage/checklists/requirements.md`
- [X] T052 Update final task checkboxes, requirement coverage, counts, commands, defects, and owner evidence in `specs/020-exception-class-coverage/tasks.md` and `quickstart.md` only after every required gate is green

## Dependencies

```text
Spec/plan approval
  └─ Taxonomy failures + typed value + multi-class fixture
      └─ US1 complete five-class/cause derivation
          └─ US2 shared explanation + authoritative clearing
              └─ US3 durable drift + projection/adapter parity
                  └─ US4 baseline closure
                      └─ Final cross-cutting review
```

- T005–T010 block every story claim.
- US1 is the canonical service slice and blocks explanation or adapter evidence.
- US2 removes current Web/Core duplication before US3 asserts durable parity.
- US3 blocks baseline closure even when individual class stories pass.
- US4 is strictly blocked by every automated requirement and unresolved defect.

## Parallel Opportunities

- T005 and T006 own different test modules; T007 starts only after their contract shape is stable.
- T023, T025, and T027 own distinct explanation/tool/MCP test files after US1 passes.
- T036 can proceed beside T035 because it owns the projection test file; T037 follows catalog API stability.
- T042 establishes the failing policy regression after T041 passes; T043 and T044 can
  then proceed in parallel because they touch separate baseline documents.
- Tasks editing `test_derivation.py`, `services/exceptions.py`, `web/api.py`, or `catalogs.py` remain sequential.

## Implementation Strategy

### MVP: Complete Direct Service Queue

Complete T001–T022. This independently proves the five-class/one-cause canonical queue
with tenant isolation but does not yet permit adapter claims or baseline closure.

### Incremental Delivery

1. Establish taxonomy drift failures, typed values, and the deterministic fixture.
2. Implement and prove every class/cause in the shared service.
3. Add shared explanation and remove Core/Web rule duplication.
4. Prove projection and adapter parity plus durable drift detection.
5. Close `013/FR-005` only after full review and owner acceptance.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T005, T035 | T008–T010, T020, T039 | Verified |
| FR-002 | T005, T035 | T008–T010, T020, T039 | Verified |
| FR-003 | T011–T016 | T017–T021 | Verified |
| FR-004 | T011, T016 | T017, T020–T021 | Verified |
| FR-005 | T012 | T017, T021 | Verified |
| FR-006 | T013 | T018, T021 | Verified |
| FR-007 | T014 | T018, T021 | Verified |
| FR-008 | T015 | T019, T021 | Verified |
| FR-009 | T006, T016, T023 | T010, T021, T028 | Verified |
| FR-010 | T025–T027, T036–T037 | T029–T033, T038 | Verified |
| FR-011 | T006, T016, T023, T025–T027 | T021, T028–T031 | Verified |
| FR-012 | T024 | T028, T034 | Verified |
| FR-013 | T005, T035–T037 | T009, T039–T040 | Verified |
| FR-014 | T041–T042 | T043–T045 | Verified |
| DR-001 | T007, T013, T023 | T010, T018, T028, T051 | Verified |
| DR-002 | T006, T023 | T028, T051 | Verified |
| DR-003 | T007, T023 | T018, T028, T051 | Verified |
| DR-004 | T006–T007, T016, T023 | T021, T028–T031, T051 | Verified |
| DR-005 | T014, T024 | T018, T034, T051 | Verified |
| DR-006 | T005–T040 review | T009–T010, T017–T021, T028–T033, T038–T039, T050–T051 | Verified |

## Format Validation

- All 52 tasks use a checkbox, sequential task ID, optional parallel marker, story label
  where applicable, requirement references where applicable, and an exact file path or
  executable command context.
- Every FR and DR maps to test evidence and implementation/documentation/review work.
- Tests precede the behavior they prove and tasks touching the same file are sequential.
