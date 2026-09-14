---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Lot Can Expire

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

**The clearing path is checked before the class is designed.** Spec 091 found five shipped classes
whose fix nothing reached; writing off stock and returning it to a supplier both have to be
reachable, or the class reports something nobody can end.

**Nothing computed enters the diff.** The one rule this specification is about is that no date and
no horizon is derived, so the review step that greps the diff for a threshold is a task rather
than an afterthought.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/109-a-lot-can-expire/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and that the Complexity Tracking entry justifies the column in `specs/109-a-lot-can-expire/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/109-a-lot-can-expire/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm from the schema that nothing can hold a best-before date today, and from the command catalog that writing stock off and returning it to a supplier are reachable, so the class has a clearing path
- [x] T006 [DR-003] Confirm from the source how many classes already reach the Spec 080 learned helper, and record the figure in `plan.md`

## Phase 2: The Date

- [x] T007 [P] [FR-001] [FR-005] [DR-006] Add failing `test_inventory_tracking_reservations.py::test_a_lot_carries_the_stated_best_before`, including that an undated lot asserts nothing
- [x] T008 [P] [FR-002] Add failing `test_inventory_tracking_reservations.py::test_a_best_before_can_be_stated_afterwards`
- [x] T009 [P] [FR-003] [FR-004] Add failing `test_inventory_tracking_reservations.py::test_a_different_best_before_is_refused`, covering an unreadable date and an accepted re-statement of the same date, each with a positive control
- [x] T010 [P] [DR-005] Add failing `test_inventory_tracking_reservations.py::test_lot_expiry_is_tenant_scoped`
- [x] T011 [P] [FR-010] Add failing `test_inventory_tracking_reservations.py::test_expiry_blocks_nothing`
- [x] T012 [DR-001] Add the nullable `expires_at` date to `Lot` in `db/core.py` with a migration and no backfill
- [x] T013 [FR-001] [FR-002] [FR-003] [FR-004] Accept the date in `create_lot` and add `state_lot_expiry` to `services/core.py`

## Phase 3: The Class And Its Cause

- [x] T014 [P] [FR-006] [FR-007] Add failing `test_derivation.py::test_stock_expired`, covering a lot still ahead of its date, one with nothing held, and the entry clearing on a write-off
- [x] T015 [P] [FR-008] Add failing `test_derivation.py::test_expired_stock_reserved_for_a_customer`, including the cause going when the reservation is released
- [x] T016 [P] [FR-009] Add failing `test_derivation.py::test_expired_lots_are_ordered_by_the_day_they_expired`
- [x] T017 [P] [DR-004] Add failing `test_derivation.py::test_the_quantity_held_is_the_one_stock_rule`
- [x] T018 [DR-002] Add `stock_expired` and the `reserved_for_delivery` cause to the catalog, the class order, the cause vocabulary and the derivation registry
- [x] T019 [FR-006] [FR-008] Add the derivation to `services/exceptions.py`, reading the quantity held from the shared tracked-identity stock rule
- [x] T020 [FR-011] Run the complete backend suite and confirm nothing moved for a company whose lots state no date
- [x] T021 Create `specs/109-a-lot-can-expire/quickstart.md` and record the three independent acceptance stories

## Phase 4: Surfaces and Documentation

- [x] T022 Declare the command in `config/command_catalog.yaml`, add the operations to `config/tenant_isolation_catalog.yaml`, and add `lot.expiry_stated` to `config/business_event_catalog.yaml`
- [x] T023 Add the date to the agent tool, the MCP schema and the endpoints, and describe it in the shared input glossary
- [x] T024 Run the drift gates and confirm every catalog agrees
- [x] T025 Record the date and the class in `docs/features/inventory.md`, including that nothing is blocked or chosen
- [x] T026 [P] Record the class and the absent horizon in `docs/features/operational_exceptions.md`
- [x] T027 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T028 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording the report that was deliberately not built and what would unblock it

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm exactly one migration was added and that it has a working downgrade
- [x] T904 [DR-003] Review the final diff and confirm no threshold, horizon or learned statistic entered it
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T007 | T012, T013 | Done |
| FR-002 | T008 | T013 | Done |
| FR-003 | T009 | T013 | Done |
| FR-004 | T009 | T013 | Done |
| FR-005 | T007 | T019 | Done |
| FR-006 | T014 | T018, T019 | Done |
| FR-007 | T014 | T019 | Done |
| FR-008 | T015 | T018, T019 | Done |
| FR-009 | T016 | T019 | Done |
| FR-010 | T011 | — | Done |
| FR-011 | T020, T901 | — | Done |
| DR-001 | T903 | T012 | Done |
| DR-002 | T024 | T018 | Done |
| DR-003 | T006, T904 | — | Done |
| DR-004 | T017 | T019 | Done |
| DR-005 | T010 | T013, T019 | Done |
| DR-006 | T007, T009 | T013 | Done |
