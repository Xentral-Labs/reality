---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Invoice Lines Know What They Bill

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The rules established by earlier specifications apply: evidence exists before a class is
declared, activating a class is atomic, and a class without a description, an owner and a
clearing path is refused.

One is new to this feature. The column has to exist before anything can reference it, and
the migration has to be part of the same step as the model attribute — a model field without
its revision breaks every fresh database, and a revision without the field breaks nothing
but means nothing. Phase 3 is therefore a single indivisible task.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the four accepted scope decisions are recorded in `specs/076-invoice-order-link/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/076-invoice-order-link/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/076-invoice-order-link/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] Add failing `tests/test_documents.py::test_invoice_line_records_the_order_line_it_bills` asserting the reference persists and reads back
- [x] T006 [P] [FR-002] [DR-005] Add failing `tests/test_documents.py::test_invoice_line_reference_is_validated` covering another tenant's line, a line that is not on an order, and a sales invoice line pointing at a purchase order line
- [x] T007 [P] [US1] [FR-003] [FR-004] Add failing `tests/operational_exceptions/test_derivation.py::test_shipped_not_billed` covering nothing billed, partly billed, and nothing delivered
- [x] T008 [P] [US2] [FR-005] Add failing `test_derivation.py::test_billed_not_received` covering billed beyond receipt, billed and received in full, and received but not yet billed
- [x] T009 [P] [US3] [FR-006] Add failing `test_derivation.py::test_invoice_price_differs` covering a differing price, an identical price, and a line that bills no order line
- [x] T010 [P] [US1] [FR-007] Add failing `test_derivation.py::test_billing_sums_across_invoices` proving two invoice lines on different invoices both count towards one order line
- [x] T010a [P] [FR-005a] Add failing `test_derivation.py::test_non_deliverable_lines_are_never_reported` proving a freight or discount line on a purchase order, which carries no commitment, is never reported as unreceived
- [x] T010b [P] [FR-007a] Add failing `test_derivation.py::test_mismatched_units_are_not_compared` proving an order line in boxes and an invoice line in pieces produce no entry
- [x] T010c [P] [FR-015] Add failing `test_derivation.py::test_line_classes_order_longest_first` proving deterministic order across repeated reads
- [x] T011 [P] [FR-008] [DR-003] Add failing `test_derivation.py::test_one_delivered_quantity_path` asserting the delivered quantity is read through one shared helper
- [x] T012 [P] [FR-009] [FR-010] [DR-004] Add failing `test_derivation.py::test_line_classes_expose_full_entry_shape` asserting identity, severity, title, impact, record type/id, causal values and opaque traces for all three
- [x] T013 [P] [FR-011] [DR-001] [DR-002] Add failing `test_derivation.py::test_line_classes_clear_through_reality` proving billing, receipt and correction each clear their entry with nothing persisted
- [x] T014 [P] [DR-005] Add failing `test_derivation.py::test_line_classes_are_tenant_scoped` proving none of the three leaks across tenants
- [x] T015 [P] [FR-012] Add failing `test_explanation.py::test_line_classes_explanation_and_not_found_parity` covering all three identities, a cleared one, a malformed one and a foreign tenant
- [x] T016 [P] [FR-014] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry all three
- [x] T017 [FR-013] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: The Column

- [x] T018 [FR-001] **Model and migration together** — add `billed_document_line_id` as a nullable self-referencing foreign key on `DocumentLine` in `packages/reality-core/src/reality/db/core.py` and create revision `0037_invoice_order_link` in `packages/reality-core/migrations/versions/`, revising `0036_erp_interpretation_rules`, adding the column and dropping it on downgrade
- [x] T019 [FR-001] Accept the reference per line in `ManualDocumentLineWrite` and pass it through `create_manual_document_with_lines` in `packages/reality-core/src/reality/services/core.py`
- [x] T020 [FR-002] [DR-005] [DR-006] Validate the reference where a line is recorded and where it is corrected: same tenant, an order document, and the matching side of the business
- [x] T021 Confirm the migration chain applies to an empty database and the whole backend suite passes with the column present and unused

## Phase 4: The Three Classes

- [x] T022 [US1] [US2] [FR-007] [FR-007a] [FR-005a] [FR-008] [DR-003] Add the shared helpers for the quantity billed against an order line and the quantity delivered through its commitment to `packages/reality-core/src/reality/services/exceptions.py`, skipping lines that promised no delivery and pairs recorded in different units
- [x] T023 [US1] [FR-003] [FR-004] [FR-009] Add `_shipped_not_billed_exceptions` over sales order lines
- [x] T024 [US2] [FR-005] [FR-009] Add `_billed_not_received_exceptions` over purchase order lines
- [x] T025 [US3] [FR-006] [FR-009] Add `_invoice_price_differs_exceptions` over invoice lines that carry a reference
- [x] T026 [FR-010] [FR-013] **Atomic activation** — register all three derivators, place them in both order constants beside the commitment classes, and declare each in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, `076/FR-004`, `076/FR-005` and `076/FR-006` authorities, evidence, description, owner and clearing path
- [x] T027 [FR-012] Verify the explanation path handles record type `document_line` and leaves the `import_job` `raw_source` branch unchanged
- [x] T028 [FR-014] Prove rather than assert that no adapter change is required: `tests/test_master_data_api.py::test_inspector_explains_a_line_class_without_knowing_it` explains an entry carried by the eighth record type through the untouched shared contract
- [x] T029 Create `specs/076-invoice-order-link/quickstart.md` and record the result of the independent acceptance stories

## Phase 5: Cross-References and Documentation

- [x] T030 Write the three descriptions so the shipped and billed classes name each other as the two sides of the same comparison, and both point at the price class as the third thing that can be wrong about one pair of lines
- [x] T031 Re-run the cross-reference review over all thirteen classes: three pairs needed the mutual half added — billed-and-not-received with the overdue supplier commitment and with the overdue payable, and shipped-and-not-billed with the overdue receivable
- [x] T032 [FR-013] Add the three taxonomy rows to `docs/features/operational_exceptions.md`
- [x] T033 Record the new relationship in `docs/DATA_MODEL.md`, including that a null reference means the line bills nothing from an order
- [x] T034 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T035 [P] Add the specification row and the new evidence rows to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check` and confirm the traceability tables match the delivered tests
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 Review the migration chain and the downgrade path, which is the first schema change in this line of work
- [x] T904 Review the final diff against the Constitution and every FR and DR, including the review risks in `plan.md`
- [x] T904a Measure the demo queue. It stays quiet — and records in `quickstart.md` that this proves less than it appears, because the demo ships nothing at all and so cannot exercise the three classes in either direction
- [x] T905 Re-derive the feature number immediately before opening the pull request

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T018, T019 | Done |
| FR-002 | T006 | T020 | Done |
| FR-003 | T007 | T023 | Done |
| FR-004 | T007 | T023, T026 | Done |
| FR-005 | T008 | T024, T026 | Done |
| FR-005a | T010a | T022 | Done |
| FR-007a | T010b | T022 | Done |
| FR-015 | T010c | T026 | Done |
| FR-006 | T009 | T025, T026 | Done |
| FR-007 | T010 | T022 | Done |
| FR-008 | T011 | T022 | Done |
| FR-009 | T012 | T023, T024, T025 | Done |
| FR-010 | T012 | T026 | Done |
| FR-011 | T013 | T023, T024, T025 | Done |
| FR-012 | T015 | T027 | Done |
| FR-013 | T017 | T026, T032 | Done |
| FR-014 | T016 | T028 | Done |
| DR-001 | T013 | T023, T024, T025 | Done |
| DR-002 | T013 | T023, T024, T025 | Done |
| DR-003 | T011 | T022 | Done |
| DR-004 | T012 | T023, T024, T025 | Done |
| DR-005 | T014 | T020, T023, T024, T025 | Done |
| DR-006 | T031 | T020, T030 | Done |
| DR-007 | T017 | T026 | Done |
