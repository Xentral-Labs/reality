# Tasks: Chargebacks, Returned Direct Debits and Payment Fees

**Input**: Design documents from `/specs/297-payment-returns-fees/`

**Tests**: Written before their implementation task and observed failing where practical. Every "no finding" assertion has a positive control; every refusal asserts its code. Paths are relative to the repository root; `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the approved scope and the four clarifications in `specs/297-payment-returns-fees/spec.md`
- [x] T002 Record design decisions R1–R7 in `specs/297-payment-returns-fees/research.md`
- [x] T003 Define the record, role and documents in `specs/297-payment-returns-fees/data-model.md` and the contract in `specs/297-payment-returns-fees/contracts/payment-returns.md`
- [x] T004 Complete the Constitution Check in `specs/297-payment-returns-fees/plan.md`

## Phase 2: Foundational

- [x] T005 [FR-001] [DR-001] Failing migration and model tests for `payment_return` (kind and bearer checks, one return per payment, FK indexes) and the `payment_fee_expense` role in `core/tests/finance/test_payment_returns.py`
- [x] T006 [DR-001] Model, migration `core/migrations/versions/0103_payment_returns.py`, the role in `core/src/reality/domain/finance.py`, the `CreateAccount` literal, `SETTLEMENT_CONTROL` and the transaction matrix; data model catalog, reporting-graph deferral, schema-index later tables, isolation catalog

## Phase 3: User Story 1 — Record a returned payment (C15)

- [x] T007 [P] [FR-001] [FR-002] Failing service tests: a returned direct debit reverses the payment and reopens its invoice; a chargeback keeps kind, reason and reference; a fee charged on is the customer's own charge and the company's cost is recovered; a fee as expense books payment-fee expense; zero fee posts nothing; a payment paying two invoices reopens both; each refusal code; replay; tenant isolation, in `core/tests/finance/test_payment_returns.py`
- [x] T008 [FR-001] [FR-002] Implement `core/src/reality/services/payment_returns.py` and the `finance.payment.return` command and reads in `core/src/reality/tools/finance.py` and `core/src/reality/tools/application.py`
- [x] T009 [P] [FR-003] Failing tests: `payment_returned` reports the reopened invoice (positive control) and clears when it is paid again or credited; the invoice inspector names the return, in `core/tests/finance/test_payment_returns.py`
- [x] T010 [FR-003] Implement the class in `core/src/reality/services/exceptions.py` with every pinned list, and the invoice inspector section in `core/src/reality/web/api.py`

## Phase 4: Payment fees and charges (E08)

- [x] T011 [P] [FR-006] Failing tests: a payment of 97 with a stated payment fee of 3 settles an invoice of 100 and books 3 as payment-fee expense; returning such a payment is refused with `payment_return_fee_adjusted`, in `core/tests/finance/test_payment_returns.py`
- [x] T012 [FR-006] Add the `payment_fee` category to `StatedReduction` and `accept_adjustment`

## Phase 5: Surfaces

- [x] T013 [P] [FR-004] Failing adapter tests (MCP propose and reads, CLI, HTTP, tenant isolation) in `core/tests/finance/test_payment_return_adapters.py`
- [x] T014 [FR-004] MCP tools, CLI commands, HTTP reads; catalogs (command, tool topics, discovery and its Web fixture, resource labels, refusals with de/nl/es, ratchet, business events, reference catalog), pinned counts, docs regeneration
- [x] T015 [FR-004] Web: "Payment returned" on recorded customer payments with its dialog, the "Payment fee" reduction label, labels in four languages; i18n audit and build

## Phase 6: Journeys and Verification

- [ ] T016 [FR-005] [SC-001] Business stories C15 (returned direct debit with a fee charged on, paid again) and E08 (freight and surcharge lines on a sales invoice; a payment with a deducted provider fee) in `core/tests/scenarios/test_catalog_finance.py`
- [ ] T017 [FR-005] [SC-002] Promote C15 and E08 with evidence and specific keywords; check neighbour questions; coverage and roadmap
- [ ] T018 Full backend suite from a clean worktree and the Web checks
- [ ] T019 Manual check per `quickstart.md` on an isolated stack
- [ ] T020 Review of the diff; fix findings
