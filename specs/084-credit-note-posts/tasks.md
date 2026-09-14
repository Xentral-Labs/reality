---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Credit Note Gives the Money Back

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

Two are particular to this feature. The settlement concept has to widen before anything can be
posted or settled, so Phase 3 comes before everything that depends on it. And replacing a
public service function is one step with its callers, as making a parameter required was in
Spec 077 — the old operation goes and the demo moves in the same change, or the suite cannot
run.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the six accepted scope decisions are recorded in `specs/084-credit-note-posts/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/084-credit-note-posts/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/084-credit-note-posts/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] Add failing `tests/test_credit_notes.py::test_a_credit_note_posts_the_reverse_of_an_invoice` asserting balanced entries mirroring the invoice posting
- [x] T006 [P] [US1] [FR-001] Add failing `tests/test_credit_notes.py::test_a_paid_invoice_can_still_be_credited` proving the ordinary consumer return is expressible and leaves the receivable negative
- [x] T007 [P] [FR-002] [DR-003] Add failing `tests/test_credit_notes.py::test_the_stated_total_is_what_posts` proving a credit note whose lines disagree with its header posts the header
- [x] T008 [P] [FR-003] Add failing `tests/test_credit_notes.py::test_posting_is_refused_where_it_would_be_wrong` covering a document that is not a credit note, a second posting and a zero total, each with a positive control alongside
- [x] T009 [P] [US2] [FR-004] [DR-004] Add failing `tests/test_credit_notes.py::test_a_credit_may_be_netted_against_an_open_invoice` asserting the invoice's open amount falls through the shared settlement derivation
- [x] T010 [P] [US2] [FR-005] Add failing `tests/test_credit_notes.py::test_a_credit_may_be_refunded` asserting cash leaves and the credit note is settled
- [x] T011 [P] [US2] [FR-006] Add failing `tests/test_credit_notes.py::test_settling_is_refused_beyond_what_is_owed` covering over-settlement, a currency mismatch and a party mismatch, with positive controls
- [x] T012 [P] [FR-007] Add failing endpoint tests in `tests/test_master_data_api.py` and failing tool assertions in `tests/test_application_catalog.py` for both postings
- [x] T013 [P] [FR-010] Add failing `test_derivation.py::test_the_posting_norm_describes_this_tenant`, with the positive control that reaching the minimum history claims a norm
- [x] T014 [P] [US3] [FR-008] Add failing `test_derivation.py::test_credit_note_unposted` covering an old unposted credit note and a recent one
- [x] T015 [P] [US4] [FR-009] Add failing `test_derivation.py::test_credit_note_unsettled` covering unsettled, partly settled and fully settled
- [x] T016 [P] [FR-011] [FR-012] [DR-006] Add failing `test_derivation.py::test_credit_note_classes_expose_full_entry_shape` asserting identity, severity, title, impact, record type/id, the figures and opaque traces for both
- [x] T017 [P] [FR-013] [DR-002] [DR-005] Add failing `test_derivation.py::test_credit_note_classes_clear_through_reality` proving posting and settling each clear their entry with nothing persisted and no status written
- [x] T018 [P] [FR-017] Add failing `test_derivation.py::test_credit_note_classes_order_longest_first` proving deterministic order across repeated reads
- [x] T019 [P] [DR-007] Add failing `test_derivation.py::test_credit_note_classes_are_tenant_scoped` proving neither the classes nor the norm leak across tenants
- [x] T020 [P] [FR-014] Add failing `test_explanation.py::test_credit_note_classes_explanation_and_not_found_parity` covering both identities, a cleared one, a malformed one and a foreign tenant
- [x] T021 [P] [FR-016] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry both
- [x] T022 [FR-015] [FR-018] Update the closed registry expectation in `test_coverage.py`, the class list in `tests/test_application_catalog.py`, and add the assertion that `returned_not_credited`'s guidance names both money classes

## Phase 3: What a Settlement May Settle

- [x] T023 [FR-004] [FR-005] Rename `_invoice_control_entry` to `_settlement_control_entry` in `packages/reality-core/src/reality/services/core.py` and teach it the four settleable documents — sales invoice, supplier invoice, credit note, customer refund — with their control account and side
- [x] T024 [FR-004] Give `open_invoice_amount` a docstring saying that "invoice" means any document settlement can settle, and confirm every existing caller still gets the same answer for the two document types it knew

## Phase 4: The Two Postings

- [x] T025 [US1] [FR-001] [FR-002] [FR-003] [DR-003] [DR-009] **Operation and callers together** — add `post_sales_credit_note` posting the stated total as the reverse of a sales invoice with no invoice required, delete `post_sales_credit`, and move `packages/reality-core/src/reality/demo/normal_month.py` to the new operations
- [x] T026 [US2] [FR-005] [FR-006] Add `post_customer_refund`, recording a `customer_refund` document and allocating it against the credit note it repays, mirroring `post_customer_payment`
- [x] T027 [FR-007] Add both endpoints in `packages/reality-core/src/reality/web/api.py`, both agent tools in `packages/reality-core/src/reality/mcp/catalog.py`, and both commands with their parameter descriptions in `packages/reality-core/config/command_catalog.yaml`
- [x] T028 [DR-007] Classify the new public operations in `packages/reality-core/config/tenant_isolation_catalog.yaml`
- [x] T029 Confirm the whole backend suite passes with both postings and the old operation gone

## Phase 5: The Two Classes

- [x] T030 [FR-010] Add the posting norm to `packages/reality-core/src/reality/services/exceptions.py` using Spec 080's learned-threshold helper with its own floor, recorded with its reasoning beside the others
- [x] T031 [US3] [FR-008] [FR-011] Add `_credit_note_unposted_exceptions` over credit notes with no posting
- [x] T032 [US4] [FR-009] [FR-011] Add `_credit_note_unsettled_exceptions` over posted credit notes with an unsettled remainder, needing no threshold because the money is owed from the moment it is posted
- [x] T033 [FR-012] [FR-015] **Atomic activation** — register both derivators, place them in both order constants beside the financial classes, and declare each in `packages/reality-core/config/operational_exception_catalog.yaml` with severity, record type, the `084/FR-008` and `084/FR-009` authorities, evidence, description, owner and clearing path
- [x] T034 [FR-016] Prove rather than assert that no adapter change is required beyond the new endpoints and tools
- [x] T035 Create `specs/084-credit-note-posts/quickstart.md` and record the result of the four independent acceptance stories

## Phase 6: Cross-References and Documentation

- [x] T036 [FR-018] Extend `returned_not_credited`'s description to say it reports whether the goods were credited on paper rather than whether money moved, and to name both money classes
- [x] T037 Write both new descriptions so `credit_note_unposted` and `credit_note_unsettled` name each other as the two stages of one credit, and so `credit_note_unsettled` says why `unmatched_financial_event` does not cover it
- [x] T038 Re-run the cross-reference review over all twenty-two classes and confirm every confusable pair is mutual
- [x] T039 [FR-015] Add the two taxonomy rows to `docs/features/operational_exceptions.md`
- [x] T040 Record in `docs/features/ledger.md` that four document types are settleable, with their control account and side, and that a credit note posts the reverse of a sales invoice
- [x] T041 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T042 [P] Add the specification row and the new evidence row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added and no stored value changed
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`, paying particular attention to the two new rows in the settlement table — a wrong side would balance and still be wrong
- [x] T904a [DR-009] Confirm nothing outside the repository could be calling `post_sales_credit`, and say so in the pull request
- [x] T904b Measure the demo month: unchanged. The demo now records, posts and nets a real credit note where it previously called an operation nobody could reach, so it exercises the whole credit path correctly and neither new class fires. The pinned queue needed no change
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005, T006 | T025 | Done |
| FR-002 | T007 | T025 | Done |
| FR-003 | T008 | T025 | Done |
| FR-004 | T009 | T023, T024 | Done |
| FR-005 | T010 | T023, T026 | Done |
| FR-006 | T011 | T026 | Done |
| FR-007 | T012 | T027 | Done |
| FR-008 | T014 | T031, T033 | Done |
| FR-009 | T015 | T032, T033 | Done |
| FR-010 | T013 | T030 | Done |
| FR-011 | T016 | T031, T032 | Done |
| FR-012 | T016 | T033 | Done |
| FR-013 | T017 | T031, T032 | Done |
| FR-014 | T020 | T033 | Done |
| FR-015 | T022 | T033, T039 | Done |
| FR-016 | T021 | T034 | Done |
| FR-017 | T018 | T031, T032 | Done |
| FR-018 | T022 | T036 | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T017 | T031, T032 | Done |
| DR-003 | T007 | T025 | Done |
| DR-004 | T009 | T023 | Done |
| DR-005 | T017 | T031, T032 | Done |
| DR-006 | T016 | T031, T032 | Done |
| DR-007 | T019 | T028, T030 | Done |
| DR-008 | T022 | T033 | Done |
| DR-009 | T904a | T025 | Done |
