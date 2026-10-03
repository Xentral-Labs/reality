# Tasks: Marketplace and Payment-Provider Payouts

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Clarify the spec (decisions delegated to the recommended options, 2026-10-02)
- [x] T002 Plan
- [x] T003 Tasks

## Phase 2: Payout settlement (FR-001, FR-003)

- [ ] T004 Tests in `tests/finance/test_payouts.py`:
  - charges allocate and record;
  - refunds settle credit notes;
  - chargebacks return payments;
  - fees and the deposit;
  - the total refusal;
  - an unmatched line, then settled again;
  - replay and a changed statement;
  - account refusals;
  - tracking-number references;
  - isolation.
- [ ] T005 Core private hooks: `_line_account_ids`, `_cash_account_id`, `_source_record`, the `tracking_number` reference
- [ ] T006 `services/payouts.py`: preview, settlement, reads
- [ ] T007 Command, review, MCP, CLI and catalogs; the `payout_line_unmatched` class

## Phase 3: Authorizations (FR-002)

- [ ] T008 Tests in `tests/finance/test_payment_authorizations.py`:
  - record and capture;
  - refusals;
  - the read;
  - the expired finding and how it clears;
  - isolation.
- [ ] T009 Migration 0126 and models
- [ ] T010 `services/payment_authorizations.py`, commands, reads and the `payment_authorization_expired` class

## Phase 4: Stories and Guide (FR-005)

- [ ] T011 Stories L03, R04 (bounded queries), C09, C10, C13
- [ ] T012 Promote the journeys: Guide catalog, coverage, roadmap, matrix, docs

## Phase 5: Verification

- [ ] T013 Backend suites, spec policy and web checks
- [ ] T014 Review of the diff; fix findings
