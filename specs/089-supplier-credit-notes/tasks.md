---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: The Credit That Comes the Other Way

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply: evidence exists before a class is declared, activating a class is
atomic, a class without a description, an owner and a clearing path is refused, and every
negative test carries a positive control in the same test.

One constraint is particular to this feature. It is a mirror, so the money moves before anything
watches it: the postings and the settlement are proven first, and the two classes are written
only once a supplier credit can actually be netted and refunded.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/089-supplier-credit-notes/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/089-supplier-credit-notes/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/089-supplier-credit-notes/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Re-check the recorded "no `supplier_credit_note` type exists" note against the model rather than believing it, and record what is genuinely missing

## Phase 2: Failing Proof for the Money

- [x] T006 [P] [US1] [FR-001] [FR-003] [DR-007] Add failing `test_credit_notes.py::test_a_supplier_credit_note_posts_the_reverse` asserting the exact reverse of the supplier invoice posting, every figure equal to the document's own gross amount, and a settlement control entry that can be found
- [x] T007 [P] [FR-002] Add failing `test_credit_notes.py::test_a_supplier_credit_note_posts_once_and_for_something` covering a second posting and an amount of zero, each with a positive control
- [x] T008 [P] [FR-004] Add failing `test_credit_notes.py::test_a_supplier_credit_settles_only_its_own_supplier` covering another supplier's invoice and a document of the wrong type, each with a positive control
- [x] T009 [P] [FR-005] [FR-008] Add failing `test_credit_notes.py::test_netting_leaves_the_remainder_open` proving a partial netting leaves both remainders and a full one settles the invoice
- [x] T010 [P] [US2] [FR-006] [FR-007] Add failing `test_credit_notes.py::test_a_supplier_refund_settles_the_credit`, including a refund beyond what the credit still claims
- [x] T011 [P] [FR-008] Add failing `test_credit_notes.py::test_a_credit_takes_a_payable_off_the_overdue_queue` proving the aging register and `overdue_payable` need no telling that a credit was involved
- [x] T012 [P] [DR-003] Add failing `test_credit_notes.py::test_one_allocation_service_settles_both_sides` asserting both directions reach the same allocation service
- [x] T013 [P] [DR-005] Add failing `test_credit_notes.py::test_supplier_credit_operations_are_tenant_scoped`

## Phase 3: The Money

- [x] T014 [FR-001] [FR-002] [DR-007] Add `post_supplier_credit_note` to `packages/reality-core/src/reality/services/core.py`, posting the exact reverse of the supplier invoice and refusing a second posting
- [x] T015 [FR-003] Add the two `SETTLEMENT_CONTROL` rows, and say in a comment why `open_invoice_amount` needs no change
- [x] T016 [FR-006] [FR-007] Add `record_supplier_refund` and `post_supplier_refund`, the mirror of the customer pair
- [x] T017 [FR-004] [FR-005] [DR-003] Add `allocate_supplier_credit_note`, refusing another party and another type, and going through the one existing allocation service
- [x] T018 [FR-018] Run the complete existing backend suite and record that nothing else moved

## Phase 4: Failing Proof for the Classes

- [x] T019 [P] [US3] [FR-009] Add failing `test_derivation.py::test_supplier_credit_unposted`, with the positive control that booking it clears the entry
- [x] T020 [P] [FR-010] Add failing `test_derivation.py::test_supplier_credit_unclaimed`, with the positive control that netting it in full clears the entry
- [x] T021 [P] [FR-011] Add failing `test_derivation.py::test_the_two_credit_sides_stay_apart`, proving each pair of classes reports only its own document type
- [x] T021a [P] [FR-009a] Add failing `test_derivation.py::test_each_side_learns_its_own_rhythm`, proving a history of prompt sales credits does not judge slow supplier credits, with the positive control that a history of supplier credits does
- [x] T022 [P] [FR-012] [DR-004] Add failing `test_derivation.py::test_the_supplier_credit_entries_expose_full_shape` asserting identity, severity, title, impact, record type/id, causal values and opaque traces
- [x] T023 [P] [FR-013] [DR-002] Add failing `test_derivation.py::test_the_supplier_credit_entries_clear_through_reality` with nothing persisted
- [x] T024 [P] [FR-017] Add failing `test_derivation.py::test_the_supplier_credit_entries_order_deterministically`
- [x] T025 [P] [DR-005] Add failing `test_derivation.py::test_the_supplier_credit_classes_are_tenant_scoped`
- [x] T026 [P] [FR-014] Add failing `test_explanation.py::test_supplier_credit_explanation_and_not_found_parity` covering the identity, a cleared one, a malformed one and a foreign tenant
- [x] T027 [P] [FR-015] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry both
- [x] T028 [FR-015] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 5: The Classes

- [x] T029 [US3] [FR-009] [FR-009a] [FR-011] Add `_supplier_credit_unposted_exceptions`, reading only supplier credit notes, after generalising `_credit_notes`, `_credit_is_posted` and `_credit_posting_threshold` to take the document type and control account they are asking about, so the rule is shared and the history is not
- [x] T030 [FR-010] [FR-011] [FR-012] [FR-013] [FR-017] Add `_supplier_credit_unclaimed_exceptions` with no threshold
- [x] T031 [FR-015] **Atomic activation** — register both derivators, place them in both order constants beside their selling-side mirrors, and declare both in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `089/FR-009` and `089/FR-010` authorities, evidence, description, owner and clearing path
- [x] T032 [FR-015] Write the guidance so each new class and its selling-side mirror name each other, and say plainly that a credit for returned goods carries no evidence of the goods
- [x] T033 Create `specs/089-supplier-credit-notes/quickstart.md` and record the result of the three independent acceptance stories

## Phase 6: Surfaces and Catalogs

- [x] T034 [FR-016] Declare the four operations in `packages/reality-core/config/command_catalog.yaml` with parameter descriptions, agent coverage and capability guidance
- [x] T035 [FR-016] Declare the operations and their tools in `packages/reality-core/config/tenant_isolation_catalog.yaml`, in the family their selling-side mirrors sit in
- [x] T036 [FR-016] Add the agent tools in `packages/reality-core/src/reality/tools/application.py`, the schemas in `mcp/catalog.py` and the endpoints in `web/api.py`, mirroring the selling side
- [x] T037 [FR-016] Run the drift gates and confirm every catalog agrees

## Phase 7: Cross-References and Documentation

- [x] T038 Re-run the cross-reference review over all twenty-seven classes and confirm every confusable pair is mutual
- [x] T039 [FR-015] Add the taxonomy rows to `docs/features/operational_exceptions.md`
- [x] T040 [P] Record the supplier credit and refund postings in `docs/features/ledger.md` and the chain in `docs/features/procure_to_pay.md`, including what is still missing
- [x] T041 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T042 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording the goods half as the remaining gap

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Measure the demo month's queue and confirm it is unchanged, recording that the demo records no supplier credit so this proves nothing about volume
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T006 | T014 | Done |
| FR-002 | T007 | T014 | Done |
| FR-003 | T006 | T015 | Done |
| FR-004 | T008 | T017 | Done |
| FR-005 | T009 | T017 | Done |
| FR-006 | T010 | T016 | Done |
| FR-007 | T010 | T016 | Done |
| FR-008 | T009, T011 | T015, T017 | Done |
| FR-009 | T019 | T029 | Done |
| FR-009a | T021a | T029 | Done |
| FR-010 | T020 | T030 | Done |
| FR-011 | T021 | T029, T030 | Done |
| FR-012 | T022 | T030 | Done |
| FR-013 | T023 | T029, T030 | Done |
| FR-014 | T026 | T031 | Done |
| FR-015 | T027, T028 | T031, T032, T039 | Done |
| FR-016 | T037 | T034, T035, T036 | Done |
| FR-017 | T024 | T030 | Done |
| FR-018 | T018 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T023 | T029, T030 | Done |
| DR-003 | T012 | T017 | Done |
| DR-004 | T022 | T030 | Done |
| DR-005 | T013, T025 | T014, T029 | Done |
| DR-006 | T028 | T031 | Done |
| DR-007 | T006 | T014 | Done |
