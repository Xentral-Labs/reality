---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: An Invoice Somebody Can Actually Book

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply, and one is particular to this feature: **the proof that the money
classes were unreachable comes first**. A test that records and books an invoice through the API
alone and then reads the queue is written before anything is wired, so the failure that
motivates the whole specification is on the record rather than asserted in prose.

Nothing below the surface may move. A diff under `services/` means the scope was misjudged.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/091-invoices-can-be-booked/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/091-invoices-can-be-booked/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/091-invoices-can-be-booked/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Re-measure the declaration gap and record the two numbers in the specification rather than describing it

## Phase 2: Failing Proof

- [x] T006 [US1] [FR-009] Add failing `test_master_data_api.py::test_booking_makes_the_money_classes_reachable`, recording and booking through the API alone and then reading `overdue_receivable` and `purchase_discount_available` from the queue
- [x] T007 [P] [US1] [FR-001] [FR-003] [FR-008] [FR-010] [DR-002] [DR-003] Add failing `test_master_data_api.py::test_a_sales_invoice_can_be_booked_over_the_api`, covering a second posting, a wrong type, an unknown document and another tenant, and asserting a recorded-but-unbooked invoice owes nothing yet
- [x] T008 [P] [US2] [FR-002] [FR-003] Add failing `test_master_data_api.py::test_a_supplier_invoice_can_be_booked_over_the_api` on the same terms
- [x] T009 [P] [FR-004] [FR-005] Add failing tool presence and shape tests in `tests/test_application_tools.py` and `tests/test_ai_mcp.py`
- [x] T010 [P] [US3] [FR-005] Add failing `test_application_tools.py::test_a_document_can_be_recorded_by_an_agent`, proving a line naming an order line is judged exactly as one recorded over HTTP
- [x] T011 [FR-011] Run the complete existing backend suite and record that nothing moved

## Phase 3: The Wiring

- [x] T012 [FR-001] [FR-002] Add the two posting endpoints to `packages/reality-core/src/reality/web/api.py`, shaped exactly like the credit-note posting endpoint
- [x] T013 [FR-004] [FR-005] Add `sales_invoice_post`, `supplier_invoice_post` and `document_create` to `packages/reality-core/src/reality/tools/application.py`
- [x] T014 [FR-004] [FR-005] Add the three proposal schemas to `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T015 [FR-006] Declare the three commands in `packages/reality-core/config/command_catalog.yaml` with mode, adapters, reads, writes, effect, parameter descriptions and agent coverage
- [x] T016 [FR-007] Declare the three tools in `packages/reality-core/config/tenant_isolation_catalog.yaml`, in the family their credit-note counterparts sit in
- [x] T017 [DR-001] Confirm the diff contains no change under `services/` and none under `migrations/versions/`
- [x] T018 Create `specs/091-invoices-can-be-booked/quickstart.md` and record the result of the three independent acceptance stories

## Phase 4: Documentation

- [x] T019 [FR-006] Record the booking operations in `docs/features/ledger.md`, and in `docs/features/order_to_cash.md` and `docs/features/procure_to_pay.md` say that recording and booking are two acts
- [x] T020 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T021 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording what was unreachable and why nobody noticed

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a [DR-005] Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T007 | T012 | Done |
| FR-002 | T008 | T012 | Done |
| FR-003 | T007, T008 | T012 | Done |
| FR-004 | T009 | T013, T014 | Done |
| FR-005 | T009, T010 | T013, T014, T015 | Done |
| FR-006 | T009 | T015, T019 | Done |
| FR-007 | T011 | T016 | Done |
| FR-008 | T007 | T012 | Done |
| FR-009 | T006 | T012 | Done |
| FR-010 | T007 | T012 | Done |
| FR-011 | T011 | — | Done |
| DR-001 | T017, T903 | — | Done |
| DR-002 | T007 | T012 | Done |
| DR-003 | T007, T008 | T012 | Done |
| DR-004 | T011 | — | Done |
| DR-005 | T904a | — | Done |
