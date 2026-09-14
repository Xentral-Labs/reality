---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Customer Promise and Stock Coverage Exceptions

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

Two properties of the catalog gate dictate the phase order below. Both were verified
against `validate_operational_exception_catalog` and `load_operational_exception_catalog`
in `packages/reality-core/src/reality/catalogs.py`.

1. **Evidence must exist before a class is declared.** The loader resolves every
   `path::test_name` evidence entry and raises when the function is absent. Phase 2 is
   therefore a hard precondition, not only test-first discipline.
2. **Activating a class is atomic.** The validator requires the catalog ids to equal
   `OPERATIONAL_EXCEPTION_CLASS_ORDER` exactly and the catalog derivations to equal the
   `DERIVATION_REGISTRY` keys exactly. A YAML entry without its constants, or constants
   without their YAML entry, makes every catalog load raise, so the whole suite fails
   rather than the new tests. T024 and T029 each bundle derivation registration, both
   order constants and the catalog entry into one step that must land together. Two
   classes may be activated one after the other, because each intermediate state is
   internally consistent.

The gate relaxation in Phase 3 is the exception to that rule: scoping duplicate causes per
class and naming the existing vocabulary in a constant are no-ops for the catalog as it
stands, so they land safely on their own and must precede the first class that reuses a
cause.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm the four accepted scope decisions are recorded and no clarification marker remains in `specs/068-promise-coverage-exceptions/spec.md`
- [ ] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/068-promise-coverage-exceptions/plan.md`
- [ ] T003 Complete the reviewer-owned domain review in `specs/068-promise-coverage-exceptions/checklists/domain.md`
- [ ] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

All paths below are under `packages/reality-core/tests/operational_exceptions/`.

- [ ] T005 [P] [US1] [FR-001] [DR-002] Add failing `test_derivation.py::test_overdue_outgoing_customer_commitment` asserting the entry, its remaining quantity, its due/evaluation instants, and its commitment trace
- [ ] T006 [P] [US1] [FR-002] Add failing `test_derivation.py::test_overdue_outgoing_boundaries` covering absent due date, future due date, due date equal to the evaluation instant, non-open status, and a fully shipped commitment
- [ ] T007 [P] [US1] [FR-003] [FR-003a] Add failing `test_derivation.py::test_overdue_outgoing_supersedes_at_risk` asserting exactly one entry for the commitment, `insufficient_reservation` present as its cause, and an impact summary that names the overdue remainder plus one clause for the attached cause
- [ ] T008 [P] [US1] [FR-004] Add failing `test_derivation.py::test_at_risk_unchanged_before_due_date` proving the existing class is untouched for a not-yet-due commitment
- [ ] T009 [P] [US2] [FR-005] Add failing `test_derivation.py::test_reservation_exceeds_stock` covering a reservation that loses its backing through an adjustment, exact equality, sufficient stock, an item reserved without any recorded movement, and reservations held in a different location than the stock — the last case must produce no entry, because coverage is judged per item across the tenant
- [ ] T010 [P] [US2] [FR-005a] Add failing `test_derivation.py::test_reservation_exceeds_stock_impact` asserting the shortfall and the number of competing commitments
- [ ] T011 [P] [US2] [DR-003] [DR-007] Add failing `test_derivation.py::test_reservation_exceeds_stock_references_are_opaque` asserting opaque reservation and commitment references and the absence of any failing-promise attribution
- [ ] T012 [P] [US2] [DR-004] Add failing `test_derivation.py::test_queue_and_inventory_agree_on_availability` comparing the entry against the Inventory availability for the same item, and proving the commitment itself reports no at-risk entry while its reservation is unbacked
- [ ] T013 [P] [FR-006] Add failing `test_derivation.py::test_new_classes_expose_full_entry_shape` asserting identity, severity, title, impact, record type/id, causal values and trace for both classes
- [ ] T014 [P] [FR-007] [DR-001] Add failing `test_derivation.py::test_new_classes_clear_through_reality` proving each entry disappears after shipment, receipt, or reservation release, with nothing persisted
- [ ] T015 [P] [DR-005] Add failing `test_derivation.py::test_new_classes_are_tenant_scoped` proving neither class leaks across tenants, including the candidate-item selection
- [ ] T016 [P] [US3] [FR-009] Add failing `test_derivation.py::test_queue_order_places_overdue_before_at_risk` proving deterministic order across repeated reads, including the item class ordered by its earliest contributing reservation
- [ ] T017 [P] [US3] [FR-008] Add failing `test_explanation.py::test_new_class_explanation_and_not_found_parity` covering both new identities and the identity change when a commitment crosses its due date
- [ ] T018 [P] [FR-011] Add failing `test_explanation.py::test_shared_consumer_parity_includes_new_classes` proving every shared consumer sees both classes
- [ ] T019 [US3] [FR-010] [DR-006] Update `test_coverage.py` with the seven-class closed registry, `test_catalog_rejects_cause_vocabulary_drift`, `test_class_order_constants_agree`, `test_shared_cause_is_declared_on_both_classes`, and `test_catalog_rejects_duplicate_cause_within_one_class`
- [ ] T019a [FR-010] Update the class list in `packages/reality-core/tests/test_application_catalog.py`, the second place that pins the closed vocabulary

## Phase 3: Catalog Gate

- [ ] T020 [FR-010] [DR-006] Scope cause-duplicate detection to a single class and add `OPERATIONAL_EXCEPTION_CAUSE_VOCABULARY` to `packages/reality-core/src/reality/catalogs.py`, replacing the hardcoded single-cause assertion while keeping the vocabulary closed
- [ ] T021 Confirm the unchanged production catalog still loads and every existing operational exception test passes, proving the gate change is a no-op before any class is added

## Phase 4: User Story 1 — Late Customer Promises (P1)

- [ ] T022 [US1] [FR-001] [FR-002] [FR-007] [DR-001] [DR-002] [DR-005] Add the overdue branch for open `customer_delivery` commitments to `_commitment_exceptions` in `packages/reality-core/src/reality/services/exceptions.py`, sorting on `due_at` and building the entry from the existing commitment trace
- [ ] T023 [US1] [FR-003] [FR-003a] [FR-004] Implement exclusivity and the clause-per-cause impact rule in the same pass: emit the overdue entry with `insufficient_reservation` as its cause when reservations do not cover the remainder, and skip the at-risk branch for that commitment
- [ ] T024 [US1] [FR-006] [FR-009] [FR-010] [DR-006] **Atomic activation** — in one step, register the derivator in `DERIVATION_REGISTRY`, place `overdue_outgoing_customer_commitment` first in `CLASS_ORDER` (`services/exceptions.py`) and in `OPERATIONAL_EXCEPTION_CLASS_ORDER` (`catalogs.py`), and declare the class with its severity, record type, `068/FR-001` authority, reused cause and evidence in `packages/reality-core/config/operational_exception_catalog.yaml`
- [ ] T025 [US1] Create `specs/068-promise-coverage-exceptions/quickstart.md` and record the result of the independent acceptance story for this class

## Phase 5: User Story 2 — Stock Promised More Than Once (P2)

- [ ] T026 [US2] [FR-005] [FR-007] [DR-001] [DR-004] [DR-005] Add `_stock_coverage_exceptions` to `packages/reality-core/src/reality/services/exceptions.py`, selecting items with at least one active tenant-scoped reservation and comparing `active_reserved` against `stock_at`
- [ ] T027 [US2] [FR-005a] [FR-009] Populate impact and causal values with observed stock, reserved quantity, shortfall and the number of competing commitments, and set the entry's sort instant to the earliest `reserved_at` among the contributing active reservations
- [ ] T028 [US2] [DR-003] [DR-007] Build the trace from opaque item, reservation and commitment identities without restating business fields or naming a failing promise
- [ ] T029 [US2] [FR-006] [FR-009] [FR-010] **Atomic activation** — in one step, register the derivator, place `reservation_exceeds_stock` fourth in both order constants, and declare the class with record type `item`, `068/FR-005` authority and evidence in `packages/reality-core/config/operational_exception_catalog.yaml`
- [ ] T030 [US2] Run the independent acceptance story and record the result in `specs/068-promise-coverage-exceptions/quickstart.md`

## Phase 6: User Story 3 — Keep the Queue Readable (P3)

- [ ] T031 [US3] [FR-008] Verify the explanation path in `packages/reality-core/src/reality/services/exceptions.py` handles record type `item` and leaves the `import_job` `raw_source` branch unchanged
- [ ] T032 [US3] [FR-011] Replace the class predicate in the Inspector route of `packages/reality-core/src/reality/web/api.py` with a cause check, so the reservation shortfall keeps its metric on the overdue entry, and prove it in `packages/reality-core/tests/test_master_data_api.py`
- [ ] T032a [US3] [FR-011] Confirm no change is required in `packages/reality-core/src/reality/web/read_models.py`, `tools/application.py`, `services/projections.py`, `services/core.py`, or `apps/web/src/`, and record the confirmation in the pull request
- [ ] T033 [US3] Run the independent acceptance story for ordering and single-entry behavior and record the result in `specs/068-promise-coverage-exceptions/quickstart.md`

## Phase 7: Documentation

- [ ] T034 [FR-010] Add both taxonomy rows with their clearing paths to `docs/features/operational_exceptions.md`, including the note that an overdue outgoing promise supersedes its at-risk entry
- [ ] T035 [P] Regenerate `apps/docs/content/catalogs/exceptions.md` and `apps/docs/content/de/catalogs/exceptions.md` with `PYTHONPATH=packages/reality-core/src .venv/bin/python apps/docs/scripts/generate-catalog-reference.py`, then run `npm run format` in `apps/docs` — the generator emits unaligned Markdown and without the formatting pass every catalog page shows a whitespace-only diff
- [ ] T036 [P] Add the specification row and the new evidence rows to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [ ] T900 Run `make spec-check` and confirm the traceability tables in `spec.md` and `plan.md` match the delivered tests
- [ ] T901 Run `make lint` and the complete backend PostgreSQL suite
- [ ] T902 Confirm `apps/web` and `provider-site` are unchanged against `origin/main`; a frontend build proves nothing for this feature because the queue row contract it reads is untouched
- [ ] T903 Confirm the migration chain is unchanged and no revision was added
- [ ] T904 Review the final diff against the Constitution and every FR and DR, including the review risks listed in `plan.md`
- [x] T904a Open the decision queue of a realistic demo tenant and record the observed overdue volume, so the first-deployment backlog is judged on real data before merge rather than assumed
- [ ] T905 Update status checklists only after all required checks are green, and only where this feature actually changes verified release status

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T022, T024 | Pending |
| FR-002 | T006 | T022 | Pending |
| FR-003 | T007 | T023, T024 | Pending |
| FR-003a | T007 | T023 | Pending |
| FR-004 | T008 | T023 | Pending |
| FR-005 | T009 | T026, T029 | Pending |
| FR-005a | T010 | T027 | Pending |
| FR-006 | T013 | T024, T029 | Pending |
| FR-007 | T014 | T022, T026 | Pending |
| FR-008 | T017 | T031 | Pending |
| FR-009 | T016 | T024, T027, T029 | Pending |
| FR-010 | T019 | T020, T024, T029, T034 | Pending |
| FR-011 | T018 | T032, T032a | Pending |
| DR-001 | T014 | T022, T026 | Pending |
| DR-002 | T005 | T022 | Pending |
| DR-003 | T011 | T028 | Pending |
| DR-004 | T012 | T026 | Pending |
| DR-005 | T015 | T022, T026 | Pending |
| DR-006 | T019 | T020, T024 | Pending |
| DR-007 | T011 | T028 | Pending |
