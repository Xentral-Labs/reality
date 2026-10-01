# Tasks: Multichannel Oversell, Deadlines and Peak Intake

**Input**: Design documents from `/specs/300-multichannel-oversell/`

**Tests**: Tests precede each phase. Every "not reported" assertion has a positive control. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the owner's four decisions in `specs/300-multichannel-oversell/spec.md`
- [x] T002 Record today's behaviour and the design in `research.md`, `data-model.md` and `contracts/findings-and-benchmark.md`
- [x] T003 Complete the Constitution Check and design in `plan.md`

## Phase 2: Item oversold (FR-001)

- [x] T004 [US1] Failing tests in `core/tests/test_item_oversold.py`:
  - shop and second-channel orders exceeding stock are reported with demand, on hand, incoming, shortfall and both channels;
  - control: within stock nothing is reported;
  - an open purchase order covering the shortfall clears it;
  - shipped and cancelled quantity no longer counts;
  - a revised promise counts its quantity in force;
  - a promise in a unit the item states no relation to is named, not summed, and supply in the purchase unit counts by the item's factor;
  - the shortfall agrees with the supply and demand view;
  - another company's stock and orders never count;
  - the statement count is the same for 2 and 40 items.
- [x] T005 [US1] `_item_oversold_exceptions` and every class gate (order, registry, dependencies, catalogs, reference catalog and counts, resource labels, de/nl/es label and resolution).

## Phase 3: Deadline at risk (FR-002)

- [x] T006 [US1] Failing tests in `core/tests/test_deadline_due_soon.py`:
  - a fully reserved promise due in 12 hours is reported;
  - control: one due in three days is not;
  - an unreserved one due soon is one row carrying `insufficient_reservation`, not also at risk;
  - past its date it is overdue only;
  - shipping, cancelling or a later agreed date clears it;
  - a revised date carries `promise_was_revised`;
  - `next_clock_moment` names the instant the window opens;
  - the class clock probe's fixture has no promise within a day of either instant, so the class is named there as without a scenario and its clock is proven here.
- [x] T007 [US1] The branch in `_commitment_exceptions`, `DUE_SOON_MARGIN`, `next_clock_moment`, `CLOCK_READING` and every class gate.

## Phase 4: Peak intake (FR-003)

- [x] T008 [US1] Failing test in `core/tests/test_peak_intake_benchmark.py`:
  - 50 Shopify orders and 2 processes produce a report;
  - every order is interpreted exactly once and no item is over-reserved;
  - the shortfall check matches;
  - the runner refuses without `--confirm-disposable`.
- [x] T009 [US1] `benchmarks/peak_intake` (company, runner, report); run 10,000 orders with 1 and 4 processes on a quiet machine and record the figures in `results.md`.

## Phase 5: Stories and Guide (FR-005)

- [x] T010 Business stories B14 and L02, and L07 if T009 met the target, in `core/tests/scenarios/test_catalog_orders_and_shipments.py`.
  - The second channel is the reviewed file import (`source_ingest`), whose source system `amazon_marketplace` becomes the order's sales channel.
- [x] T011 Promote the proven journeys with story-first evidence and English and German keywords, and check that neighbouring questions keep their journeys. If L07 missed the target, its limitation states the measured figure. Then update coverage, the roadmap and the coverage matrix, and run `make docs-generate`.

## Phase 6: Verification

- [ ] T012 Full backend suite and the web checks (run alone, not beside a stack build)
- [ ] T013 Manual check per `quickstart.md` on an isolated stack
- [ ] T014 Review of the diff; fix findings
