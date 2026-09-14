---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Best-Before Can Be Corrected

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply. Two are particular to this feature.

**The kind of change is settled before the shape.** A revision and a correction have different
records in this product, and picking the wrong one would be a table nobody needed.

**The source-record question is measured before it is answered**, because the sibling operation
answers it the other way and consistency by imitation would have been wrong here.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/110-a-best-before-can-be-corrected/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and that no Complexity Tracking exception is claimed in `specs/110-a-best-before-can-be-corrected/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/110-a-best-before-can-be-corrected/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm from Spec 093's own source that its record is described as not a correction, and from `correct_manual_document_lines` that a corrected value's audit is carried by its event
- [x] T006 Confirm from the source that no import path creates lots, so the lot's source record cannot be read as the date's provenance

## Phase 2: The Correction

- [x] T007 [P] [FR-001] [FR-006] [DR-002] [DR-004] [DR-006] Add failing `test_inventory_tracking_reservations.py::test_a_misread_best_before_can_be_corrected` and `::test_a_correction_records_what_it_replaced`
- [x] T008 [P] [FR-002] [FR-003] [FR-004] [FR-005] Add failing `test_inventory_tracking_reservations.py::test_a_correction_refuses`, covering an empty reason, a mismatched confirmation, a correction that changes nothing and an unreadable date in either position, each with a positive control
- [x] T009 [P] [FR-001] Add failing `test_inventory_tracking_reservations.py::test_a_best_before_can_be_corrected_to_nothing`, including correcting a date back in and naming the absence
- [x] T010 [P] [DR-005] Add failing `test_inventory_tracking_reservations.py::test_correcting_expiry_is_tenant_scoped`
- [x] T011 [P] [FR-007] Add failing `test_inventory_tracking_reservations.py::test_stating_a_different_date_names_the_correction`
- [x] T012 [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] Add `correct_lot_expiry` to `services/core.py`, reusing the one stated-date rule
- [x] T013 [FR-007] Correct the refusal message in `state_lot_expiry` so it names the correction

## Phase 3: The Queue Follows

- [x] T014 [P] [FR-008] Add failing `test_derivation.py::test_the_queue_follows_a_corrected_best_before`, covering an entry going and an entry appearing
- [x] T015 [FR-010] Run the complete backend suite and confirm nothing moved for a lot nobody corrects
- [x] T016 Create `specs/110-a-best-before-can-be-corrected/quickstart.md` and record the three independent acceptance stories

## Phase 4: Surfaces and Documentation

- [x] T017 Declare the command in `config/command_catalog.yaml`, add the operation to `config/tenant_isolation_catalog.yaml`, and add `lot.expiry_corrected` to `config/business_event_catalog.yaml`
- [x] T018 Add the agent tool, the MCP schema and the endpoint, and describe the confirmation in the shared input glossary
- [x] T019 Run the drift gates and confirm every catalog agrees
- [x] T020 Record the correction in `docs/features/inventory.md`, including what correcting to nothing loses
- [x] T021 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T022 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration, no new model and no new command beyond the correction were added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T007, T009 | T012 | Done |
| FR-002 | T008 | T012 | Done |
| FR-003 | T008 | T012 | Done |
| FR-004 | T008 | T012 | Done |
| FR-005 | T008 | T012 | Done |
| FR-006 | T007 | T012, T017 | Done |
| FR-007 | T011 | T013 | Done |
| FR-008 | T014 | — | Done |
| FR-009 | T903 | T012 | Done |
| FR-010 | T015, T901 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T007 | T012 | Done |
| DR-003 | T901 | — | Done |
| DR-004 | T007 | T012 | Done |
| DR-005 | T010 | T012 | Done |
| DR-006 | T007 | T012 | Done |
