---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Overdue Receivable Visibility

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

Carried over from Spec 068 and verified against `catalogs.py`:

1. **Evidence must exist before a class is declared.** `load_operational_exception_catalog`
   resolves every `path::test_name` evidence entry and raises when the function is absent.
2. **Activating a class is atomic.** The validator requires the catalog ids to equal
   `OPERATIONAL_EXCEPTION_CLASS_ORDER` exactly and the catalog derivations to equal the
   `DERIVATION_REGISTRY` keys exactly, so the derivation, its registry entry, both order
   constants and the catalog entry land in one step.

No cause is added, so the cause vocabulary and its gate are untouched and no Phase-3-style
gate change is needed. The consolidation in Phase 3 takes its place: it must land before
the class, because the class consumes the rule it produces.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm the three accepted scope decisions are recorded and no clarification marker remains in `specs/069-overdue-receivables/spec.md`
- [ ] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/069-overdue-receivables/plan.md`
- [ ] T003 Complete the reviewer-owned domain review in `specs/069-overdue-receivables/checklists/domain.md`
- [ ] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [ ] T005 [P] [US2] [FR-003] [DR-004] Add failing `tests/test_ledger.py::test_invoice_due_date_rule` covering a term of several days, a term of zero days, no term at all, an empty invoice date, and an unparseable invoice date
- [ ] T006 [P] [US2] [FR-009] [DR-004] Add failing `tests/test_ledger.py::test_one_aging_rule_serves_every_consumer` proving the register and the read model return the same due date and days overdue for one invoice at one instant, and that the read model performs no arithmetic of its own
- [ ] T007 [P] [US1] [FR-001] [DR-003] Add failing `tests/operational_exceptions/test_derivation.py::test_overdue_receivable` asserting the entry, its due date, its days overdue and its trace
- [ ] T008 [P] [US1] [FR-002] Add failing `test_derivation.py::test_overdue_receivable_boundaries` covering a fully settled invoice, an invoice whose term has not elapsed, an invoice due exactly at the instant, a reversed invoice, a supplier invoice, and an invoice with an unreadable date
- [ ] T009 [P] [US1] [FR-004] [DR-002] Add failing `test_derivation.py::test_overdue_receivable_reports_the_outstanding_amount` proving a partially settled invoice reports the remainder and not the gross amount
- [ ] T010 [P] [US1] [FR-005] Add failing `test_derivation.py::test_overdue_receivable_entry_shape` asserting identity, severity, title, impact, record type/id, causal values, currency and opaque trace
- [ ] T011 [P] [US1] [FR-006] [DR-001] Add failing `test_derivation.py::test_overdue_receivable_clears_through_settlement` proving the entry disappears once the remainder is allocated, with nothing persisted
- [ ] T012 [P] [US1] [DR-005] Add failing `test_derivation.py::test_overdue_receivable_is_tenant_scoped` proving no leak across tenants, including the payment-term lookup
- [ ] T013 [P] [US2] [FR-008] Add failing `test_derivation.py::test_overdue_receivable_orders_before_unmatched_payment` proving deterministic order across repeated reads and oldest due date first
- [ ] T014 [P] [US1] [FR-007] Add failing `test_explanation.py::test_overdue_receivable_explanation_and_not_found_parity` covering the identity, a settled identity, a malformed one and a foreign tenant
- [ ] T015 [P] [FR-011] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry this class too
- [ ] T016 [FR-010] Update the closed registry expectation in `tests/operational_exceptions/test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: One Due-Date Rule

- [ ] T017 [US2] [FR-003] [DR-004] Add `effective_payment_term`, `invoice_due_date` and `invoice_days_overdue` to `packages/reality-core/src/reality/services/core.py`, owning the term cascade, the string-date parse guard and the last-resort fallback
- [ ] T017a [US2] [FR-003] Carry the party's payment-term id on both open-item row builders and prove the cascade in `tests/test_ledger.py::test_invoice_term_cascades_from_the_document_to_the_party`
- [ ] T018 [US2] [FR-009] Give `aging_register` an optional evaluation instant in the same file and express it through the two helpers
- [ ] T019 [US2] [FR-009] [DR-004] Replace the duplicated arithmetic in `packages/reality-core/src/reality/web/read_models.py:aging_page` with calls to the helpers and give it the same optional evaluation instant, leaving pagination where it is
- [ ] T020 [US2] Confirm the whole backend suite still passes, proving the consolidation changed no behaviour before the class consumes it

## Phase 4: The Class

- [ ] T021 [US1] [FR-001] [FR-002] [FR-004] [DR-001] [DR-002] [DR-003] [DR-005] Add `_receivable_exceptions` to `packages/reality-core/src/reality/services/exceptions.py`, walking the tenant's open items, keeping unsettled sales invoices, and deriving the due date through the shared rule
- [ ] T022 [US1] [FR-005] Populate impact and causal values with the outstanding amount, currency, due date and days overdue, and build the trace from opaque invoice, control-entry and SourceRecord identities
- [ ] T023 [US1] [FR-005] [FR-008] [FR-010] **Atomic activation** — in one step, register the derivator in `DERIVATION_REGISTRY`, place `overdue_receivable` seventh in `CLASS_ORDER` (`services/exceptions.py`) and in `OPERATIONAL_EXCEPTION_CLASS_ORDER` (`catalogs.py`), and declare the class with its severity, record type, `069/FR-001` authority and evidence in `packages/reality-core/config/operational_exception_catalog.yaml`
- [ ] T024 [US1] [FR-007] Verify the explanation path handles record type `document` and leaves the `import_job` `raw_source` branch unchanged
- [ ] T025 [US1] [FR-011] Confirm no change is required in `web/read_models.py` beyond T019, nor in `web/api.py`, `tools/application.py`, `services/projections.py`, `services/core.py` or `apps/web/src/`, and record the confirmation in the pull request
- [ ] T026 [US1] Create `specs/069-overdue-receivables/quickstart.md` and record the result of the independent acceptance stories

## Phase 5: Documentation

- [ ] T027 [FR-010] Add the taxonomy row with its clearing path and the due-date rule to `docs/features/operational_exceptions.md`
- [ ] T028 [P] Regenerate `apps/docs/content/catalogs/exceptions.md` and `apps/docs/content/de/catalogs/exceptions.md` with the generator, then run `npm run format` in `apps/docs` — without the formatting pass every catalog page shows a whitespace-only diff
- [ ] T029 [P] Add the specification row and the new evidence rows to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [ ] T900 Run `make spec-check` and confirm the traceability tables match the delivered tests
- [ ] T901 Run `make lint` and the complete backend PostgreSQL suite
- [ ] T902 Confirm `apps/web` and `provider-site` are unchanged against `origin/main`
- [ ] T903 Confirm the migration chain is unchanged and no revision was added
- [ ] T904 Review the final diff against the Constitution and every FR and DR, including the review risks listed in `plan.md`
- [x] T904a Seed a realistic tenant with invoices that carry no payment term and record the observed volume, so the first-deployment receivable backlog is judged on real data rather than assumed
- [x] T905 Decide the party-level payment-term question raised in the plan's review risks: decided on 2026-09-04 against leaving it, because the measurement in T904a put a 22% false-positive rate behind it. The rule cascades to the party and the fallback is now a last resort.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T007 | T021, T023 | Pending |
| FR-002 | T008 | T021 | Pending |
| FR-003 | T005, T017a | T017, T017a | Pending |
| FR-004 | T009 | T021, T022 | Pending |
| FR-005 | T010 | T022, T023 | Pending |
| FR-006 | T011 | T021 | Pending |
| FR-007 | T014 | T024 | Pending |
| FR-008 | T013 | T023 | Pending |
| FR-009 | T006 | T018, T019 | Pending |
| FR-010 | T016 | T023, T027 | Pending |
| FR-011 | T015 | T025 | Pending |
| DR-001 | T011 | T021 | Pending |
| DR-002 | T009 | T021 | Pending |
| DR-003 | T007, T010 | T022 | Pending |
| DR-004 | T005, T006 | T017, T019 | Pending |
| DR-005 | T012 | T021 | Pending |
| DR-006 | T016 | T023 | Pending |
