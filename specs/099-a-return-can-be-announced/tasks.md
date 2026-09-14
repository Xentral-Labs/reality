---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: The Parcel That Has Not Left Yet

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

**The returnable rule is extracted alone**, before any announcement exists, with the whole suite
proving the returning-movement path still refuses and accepts exactly what it did.

**The measurement behind not using a Commitment is taken before the table is written**, because
if it turns out to be four branches rather than seventeen the design should change.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/099-a-return-can-be-announced/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and both Complexity Tracking entries justify the schema in `specs/099-a-return-can-be-announced/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/099-a-return-can-be-announced/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 [DR-002] Count the `customer_delivery` references and the two-way branches whose `else` means supplier delivery, and record the figures in `plan.md`

## Phase 2: The Returnable Rule, Alone

- [x] T006 [FR-002] [DR-003] Extract `returnable_quantity` in `services/core.py` and make the returning-movement branch of `record_movement` its caller
- [x] T007 [FR-010] Run the complete existing backend suite and record that the return path refuses and accepts exactly what it did

## Phase 3: The Announcement

- [x] T008 [P] [FR-001] [DR-007] Add failing `test_return_announcements.py::test_what_the_customer_said_is_recorded`
- [x] T009 [P] [FR-002] [DR-003] Add failing `test_return_announcements.py::test_one_rule_answers_what_can_come_back`
- [x] T010 [P] [FR-003] Add failing `test_return_announcements.py::test_two_announcements_cannot_claim_the_same_goods`
- [x] T011 [P] [FR-004] Add failing `test_return_announcements.py::test_an_announcement_refuses`, covering zero, a negative, a supplier delivery, a delivery nothing shipped and a cancelled promise, each with a positive control
- [x] T012 [P] [FR-009] Add failing `test_return_announcements.py::test_an_announcement_can_be_withdrawn`
- [x] T013 [P] [DR-005] Add failing `test_return_announcements.py::test_announcements_are_tenant_scoped`
- [x] T014 [DR-001] Add the `ReturnAnnouncement` model and the nullable `return_announcement_id` on `Movement` in `db/core.py`, with `migrations/versions/0043_return_announcements.py` and no backfill
- [x] T015 [FR-001] [FR-003] [FR-004] [FR-009] Add `announce_customer_return`, `withdraw_return_announcement` and the announcement register to `services/core.py`

## Phase 4: The Parcel

- [x] T016 [P] [FR-005] Add failing `test_return_announcements.py::test_the_parcel_names_its_announcement`
- [x] T017 [P] [FR-006] Add failing `test_return_announcements.py::test_a_movement_refuses_a_foreign_announcement`
- [x] T018 [P] [FR-007] Add failing `test_return_announcements.py::test_an_announcement_is_finished_when_the_goods_arrive`
- [x] T019 [P] [FR-008] Add failing `test_return_announcements.py::test_more_may_arrive_than_was_announced`
- [x] T020 [FR-005] [FR-006] [FR-007] [FR-008] Accept and validate the reference in `record_movement`, settling the announcement at the moment what arrived reaches what was announced
- [x] T021 [FR-010] Run the complete suite and confirm a movement naming no announcement behaves exactly as today

## Phase 5: Nothing Arrived

- [x] T022 [P] [FR-011] [FR-013] Add failing `test_derivation.py::test_announced_return_not_arrived`, covering both rules and the entry clearing when the goods arrive
- [x] T023 [P] [FR-012] Add failing `test_derivation.py::test_an_announcement_without_a_date_or_a_history_is_not_judged`
- [x] T024 [P] [DR-004] Add failing `test_derivation.py::test_the_announcement_threshold_is_the_learned_rule`
- [x] T025 [FR-011] [FR-012] [DR-006] Add `announced_return_not_arrived` to the catalog, the class order and the derivation registry, and its derivation in `services/exceptions.py`
- [x] T026 Create `specs/099-a-return-can-be-announced/quickstart.md` and record the three independent acceptance stories

## Phase 6: Surfaces and Documentation

- [x] T027 [DR-008] Declare the commands in `config/command_catalog.yaml`, add the operations to `config/tenant_isolation_catalog.yaml`, and add the two events to `config/business_event_catalog.yaml`
- [x] T028 [DR-008] Add the agent tools, the MCP schemas and the endpoints
- [x] T029 [DR-008] Run the drift gates and confirm every catalog agrees
- [x] T030 Record the announcement in `docs/features/movements.md`, including that it is not supply and that no reference is generated
- [x] T031 [P] Record the new class in `docs/features/operational_exceptions.md`, including why it is one class judged two ways
- [x] T032 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T033 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording the measurement behind not using a Commitment

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm exactly one migration was added and that it has a working downgrade
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Phase 7: The Reference Reaches the Adapters (amendment 2026-09-11)

- [x] T031 [FR-005] Add failing `tests/test_return_announcement_adapters.py`: the MCP schema names both references; a proposal through `movement_create` fulfils an announcement; the web write carries `return_announcement_id` and `resolves_movement_id` and echoes both on write and list; a foreign announcement is still refused over the web; the CLI carries both flags
- [x] T032 [FR-005] Add `return_announcement_id` to `movement_create_propose` in `mcp/catalog.py` and one row in the docs MCP catalog
- [x] T033 [FR-005] Pass `resolves_movement_id` and `return_announcement_id` through `post_movement` in `web/api.py`, and return both on `MovementRead`
- [x] T034 [FR-005] Add `--resolves-movement-id` and `--return-announcement-id` to `movement record` in `cli/app.py`

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T008 | T014, T015 | Done |
| FR-002 | T009 | T006 | Done |
| FR-003 | T010 | T015 | Done |
| FR-004 | T011 | T015 | Done |
| FR-005 | T016, T031 | T020, T032, T033, T034 | Done |
| FR-006 | T017 | T020 | Done |
| FR-007 | T018 | T020 | Done |
| FR-008 | T019 | T020 | Done |
| FR-009 | T012 | T015 | Done |
| FR-010 | T007, T021 | — | Done |
| FR-011 | T022 | T025 | Done |
| FR-012 | T023 | T025 | Done |
| FR-013 | T022 | T025 | Done |
| FR-014 | T901 | — | Done |
| DR-001 | T903 | T014 | Done |
| DR-002 | T005 | T005 | Done |
| DR-003 | T009 | T006 | Done |
| DR-004 | T024 | T025 | Done |
| DR-005 | T013 | T015, T020, T025 | Done |
| DR-006 | T029 | T025 | Done |
| DR-007 | T008 | T015 | Done |
| DR-008 | T029 | T027, T028 | Done |
