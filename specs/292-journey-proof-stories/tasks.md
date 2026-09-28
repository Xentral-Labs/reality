# Tasks: Journey Proof Stories

**Input**: Design documents from `/specs/292-journey-proof-stories/`

**Tests**: The stories are the deliverable. Each story is written to the journey's business outcome before any catalog change. Paths are relative to the repository root.

## Phase 1: Specification and Design Gates

- [x] T001 Record the approved twelve-journey scope in `specs/292-journey-proof-stories/spec.md`
- [x] T002 Record per-journey services and expected outcomes in `specs/292-journey-proof-stories/research.md`
- [x] T003 Complete the Constitution Check and outcome rule in `specs/292-journey-proof-stories/plan.md`
- [x] T004 Rebase onto `origin/main` after PR #243 merges and confirm the catalog carries FR-002a limitations

## Phase 2: User Story 1 — Order changes (P1)

**Goal**: A04, A06, A07 and A19 are proven end to end or carry their finding.

**Independent Test**: `pytest tests/scenarios/test_catalog_orders_and_shipments.py`

- [x] T005 [P] [US1] [FR-001] [FR-002] A04 story: 10 ordered, 4 shipped, raised to 12, 8 open, 4 delivered, in `packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py`
- [x] T006 [P] [US1] [FR-001] [FR-002] A06 story: reserved three-line order, one reviewed cancellation, only that line closed and unreserved, in `packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py`
- [x] T007 [P] [US1] [FR-001] [FR-002] A07 story: every line of a reserved order cancelled, no active reservation, stock unchanged, in `packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py`
- [x] T008 [P] [US1] [FR-001] [FR-002] [DR-001] A19 story: zero-price line beside a priced line, both shipped, invoice with the free line at zero, no revenue and no `shipped_not_billed` for the free line, in `packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py`

## Phase 3: User Story 2 — Returns and refunds (P1)

**Goal**: F01, F05 and F07 are proven end to end or carry their finding.

**Independent Test**: `pytest tests/scenarios/test_catalog_stock_and_returns.py`

- [x] T009 [P] [US2] [FR-001] [FR-002] F01 story: paid delivery, full return, credit citing the order line, refund paid, invoice and credit open 0, no return or billing signal, in `packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py`
- [x] T010 [P] [US2] [FR-001] [FR-002] F05 story: partly damaged return, `scrap_loss` disposition, full-quantity credit with a damage charge line, disposition and credit each correct, in `packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py`
- [x] T011 [P] [US2] [FR-001] [FR-002] F07 story: invoiced original, return, zero-price replacement shipped, no credit, refund or payment, no open-work signal for the exchange (failed on a missing capability; pinned as `test_an_exchange_moves_no_money_but_reads_as_uncredited_and_unbilled`), in `packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py`

## Phase 4: User Story 3 — Payments and balances (P2)

**Goal**: C04, M08 and N06 are proven end to end or carry their finding.

**Independent Test**: `pytest tests/scenarios/test_catalog_finance.py -k "C04 or M08 or N06"`

- [x] T012 [P] [US3] [FR-001] [FR-002] C04 story: two prepayment orders, one payment allocated to both invoices, both `fulfillment_readiness` ship-ready, in `packages/reality-core/tests/scenarios/test_catalog_finance.py`
- [x] T013 [P] [US3] [FR-001] [FR-002] M08 story: customer short payment through `finance.settlement.apply` with an `agreed_deduction` reduction, invoice open 0, reason on the review and the adjustment source record, in `packages/reality-core/tests/scenarios/test_catalog_finance.py`
- [x] T014 [P] [US3] [FR-001] [FR-002] N06 story: open invoice, credit note, deposit, unpaid prepayment invoice and unallocated prepayment, party balance row equals their signed sum, in `packages/reality-core/tests/scenarios/test_catalog_finance.py`

## Phase 5: User Story 4 — Stated tax cases (P2)

**Goal**: N01 and N02 keep stated tax as given.

**Independent Test**: `pytest tests/scenarios/test_catalog_finance.py -k "N01 or N02"`

- [x] T015 [P] [US4] [FR-001] [DR-002] N01 story: customer with VAT ID, sales invoice with stated net, tax 0, gross and an internal EU case reference, all read back as stated, in `packages/reality-core/tests/scenarios/test_catalog_finance.py`
- [x] T016 [P] [US4] [FR-001] [DR-002] N02 story: supplier invoice under reverse charge with stated net, tax 0 and gross read back as stated, in `packages/reality-core/tests/scenarios/test_catalog_finance.py`

## Phase 6: User Story 5 — The Guide follows the evidence (P1)

**Goal**: Catalog statuses match story outcomes.

**Independent Test**: `pytest tests/test_business_journey_catalog.py tests/test_business_journey_questions.py`

- [x] T017 [US5] [FR-005] For each failed story, decide defect (fix with a regression test naming the requirement) or missing capability (rename the story to pin today's behavior as a limitation); record the decision in `specs/292-journey-proof-stories/research.md`
- [x] T018 [US5] [FR-003] [FR-004] Promote passing journeys and update limitations and `internal_evidence` in `packages/reality-core/config/business_journey_catalog.yaml`
- [x] T019 [US5] [FR-003] Add the pinned scope test (supported cites a catalog story; partial carries a finding) in `packages/reality-core/tests/test_business_journey_catalog.py`
- [x] T020 [US5] [FR-006] Record statuses and findings in `docs/scenarios/coverage.md` (`docs/scenarios/catalog.md` carries no status column and needs no change)
- [x] T021 [US5] [FR-007] Regenerate `apps/docs/.vitepress/data/business-journeys.json` and `apps/docs/public/generated/business-journeys.json` with `make docs-generate`
- [x] T022 [US5] [SC-004] Ask the Guide about each promoted journey and confirm `supported` with the journey cited, per `specs/292-journey-proof-stories/quickstart.md`

## Final Phase: Verification and Review

- [x] T023 Update the three catalog module rows in `docs/SPEC_COVERAGE_MATRIX.md` with the new IDs and spec 292
- [x] T024 Run Ruff on the changed test modules from `packages/reality-core` with `--no-cache`, `make spec-check` and `make docs-catalog-check`
- [ ] T025 Run the complete required PostgreSQL backend suite with `make test`
- [ ] T026 Review the diff against FR-001–FR-008, DR-001–DR-003 and the Constitution; confirm no schema, tool, service or UI change unless T017 recorded a defect fix

## Dependencies

- T004 precedes T018–T021, which edit the limitations PR #243 introduces. T005–T016 do not depend on it.
- T005–T016 are independent of each other (different stories; same module files, so write them sequentially per module).
- T017 follows the stories; T018–T022 follow T017; T023–T026 close.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001, FR-002 | T005–T016 | — | Done |
| FR-003, FR-004 | T019 | T018 | Done |
| FR-005 | T017 | T017 | Done |
| FR-006 | — | T020 | Done |
| FR-007 | T022 | T021 | Done |
| FR-008 | T026 | — | Pending |
| DR-001 | T008–T011 | — | Done |
| DR-002 | T015–T016 | — | Done |
| DR-003 | T005–T016 | — | Done |

## MVP

US1 and US2 (T005–T011) plus T017–T022 for those seven journeys.
