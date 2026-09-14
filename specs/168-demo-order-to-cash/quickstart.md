# Quickstart and verification: Demo Data pays its orders

**Feature**: [spec.md](spec.md) · [plan.md](plan.md) · [tasks.md](tasks.md) · [review.md](review.md)
**Checkout**: `.claude/worktrees/invoice-lines-research`, branch `168-demo-order-to-cash`
**Language**: English

## Try it

1. Create a Sandbox company with empty content or the international demo, open Integrations
   and connect Demo Data. The preview lists the payment term `DEMO-14-2` among the prerequisites.
2. Start the source. The status shows the order schedule and, under "Order to cash", the
   settlement schedule's next run.
3. After a few minutes invoices appear for the orders; minutes later payments follow. Open
   Items shows settled invoices and, for roughly one order in twenty, a partial invoice or an
   unmatched payment. Payments shows customer credit for overpayments.
4. On an unallocated payment, choose "Use available credit": the dialog lists suggested invoices
   with the reason each one fits. Confirm one to allocate it.
5. On a short-paid invoice, choose "Accept settlement reduction" to close a withheld remainder
   with an evidenced reduction; the cash entry stays as received.

Late and overdue behaviour appears only on a demo running longer than the fourteen-day term.

## Independent stories (T028, T032)

| Story | Proof | Result |
|---|---|---|
| US1 exact invoice and payment | `tests/test_demo_data_intake.py::test_settlement_occurrence_emits_due_records_in_bounded_batches`, `tests/scenarios/test_demo_order_to_cash.py` | pass |
| US2 short and over | `tests/test_payment_intake.py`, `tests/scenarios/test_demo_order_to_cash.py`, `tests/operational_exceptions/test_payment_differences_from_demo.py` | pass |
| US3 unmatched → candidates → confirmation | `tests/test_payment_intake.py`, `tests/finance/test_settlement_flows.py::test_payment_credit_context_carries_candidate_reasons`, story test | pass |
| US4 controls and status | `tests/test_demo_data.py`, `tests/test_demo_data_intake.py::test_settlement_uses_each_order_schedule_seed_and_pause_never_bursts`, `tests/test_demo_data_security.py` | pass |
| US5 late and never | `tests/operational_exceptions/test_payment_differences_from_demo.py`, story test | pass |

T031: no change to `services/exceptions.py` was needed; the existing classes surface the
differences unchanged.

## Checks run on 2026-09-10

- `make spec-check`: pass.
- `make lint`: pass.
- `git diff --check`: pass.
- Focused backend runs during implementation: planner 13, core 23, Demo Data/intake/security/API 35,
  scheduler/migration/setup/catalog/isolation and story/exception suites, all green.
- Web: `node --test scripts/*.test.mjs` 121 passed; `npm run i18n:audit` four languages pass;
  `tsc -b` clean; `prettier --check` clean.
- Docs site: format check, 45 tests, VitePress build pass.
- Full backend PostgreSQL suite (`../../.venv/bin/pytest -q --tb=short` from `packages/reality-core`):
  2,230 passed, 1 failed, 9 skipped in 5:34. The one failure was
  `tests/finance/test_adjustments.py::test_additive_reduction_migration_preserves_populated_accounts`,
  which asserted the old head revision name after a refused downgrade; it now expects
  `0055_demo_settlement_schedule` and passes (module rerun: all green). No other test changed.

## Rollout notes

Apply migration `0055_demo_settlement_schedule` once; deploy API, scheduler and worker from one
revision. Existing connections keep producing orders and gain the settlement stream on their
next explicit start. Rollback: stop the connection, downgrade the migration; recorded invoices,
payments and allocations are valid business history.

## Live browser run on the local stack — 2026-09-10 (T038, first part)

The stack on port 8080 was rebuilt from this branch (seven images), migration
`0055_demo_settlement_schedule` was applied (`0054_target_mappings` → `0055`), and the six
application services were recreated; API and web healthy. Then
`apps/web/scripts/demo-data-payments-browser.mjs` ran against `http://127.0.0.1:8080`:

```sh
PLAYWRIGHT_MODULE=<other checkout>/node_modules/playwright/index.mjs \
DEMO_O2C_EMAIL=<local owner> DEMO_O2C_PASSWORD=<local owner password> \
node apps/web/scripts/demo-data-payments-browser.mjs
```

| Step | Result |
|---|---|
| Sign in, create Sandbox company `Order to cash 2026-09-10T20:44` (`ten_de87f2e90b`), connect, start at 300/h | pass; the preview listed the payment term `DEMO-14-2`, start created the settlement schedule |
| Panel shows the order-to-cash block with the three finance links | pass (`01-panel-started.png`) |
| First invoice booked, first payment allocated, first invoice settled | pass after 9 minutes (`02-panel-settling.png`) |
| Open items shows a synthetic invoice as settled | pass (`03-open-items-paid.png`) |
| Short payment residual and unmatched payment, candidate confirmation | not reached before the run was stopped after 43 minutes for the night; see below |

Live figures at 21:27 UTC, 43 minutes after start: 219 orders, all imported; 211 invoices;
128 payments received, 128 allocated, 128 invoices settled; 0 failures; 0 differences yet.
A database check confirmed 128 payments, 128 allocations and 128 distinct settled invoices.
Payment paths so far: 120 provider, 8 bank transfers, all exact.

Two observations:

- **The ten-record batch bound saturates at 300 orders per hour.** Five orders per minute
  produce five invoices plus five first payments, exactly the bound, so the stream lagged
  (161 invoices for 213 orders after 34 minutes). Lowering the rate to 60 through the normal
  `set_rate` control let the backlog drain and left the settlement schedule untouched, as
  specified. Recommendation for a follow-up: raise the bound to about 25 per occurrence or
  shorten the interval; either is a spec FR-018 change.
- **Differences arrive slowly by design.** Bank transfers are due 10–90 minutes after the
  invoice, so within the first 40 minutes only about one bank payment in ten is due at all;
  eight exact ones in a row is unremarkable. The unmatched case (one order in a hundred)
  needs roughly an hour of bank payments at 60 orders per hour.

The test company kept running at 60 orders per hour; the second part followed the next morning.

Screenshots of the first part are kept outside the repository in
`/private/tmp/reality-demo-o2c-browser/`.

## Live browser run, second part — 2026-09-11 (T038 complete)

Overnight the laptop slept twice. Both schedules of the test company ended with one
`stale_claim` failure each (worker lease expired while the process was frozen) and the shared
scheduler disabled them, so the panel showed "Execution needs attention" and no next
settlement. This is the pre-existing spec 147 behaviour, not part of feature 168; the
documented recovery, stop then start, created fresh order and settlement schedules and the
stream resumed at once. Differences had accumulated before the freeze: 5 open residuals,
5 unmatched payments, 125.00 customer credit.

The full script then ran against the same company (`DEMO_O2C_TENANT=ten_de87f2e90b`) and
passed end to end in about one minute (exit 0):

| Step | Result |
|---|---|
| Sign in, reuse the running connection; settlement schedule present and due | pass |
| Panel block and links | pass (`01-panel-started.png`, `02-panel-settling.png`) |
| Open items shows a settled synthetic invoice | pass (`03-open-items-paid.png`) |
| Open items shows a short-paid invoice as partial | pass (`04-open-items-partial.png`) |
| "Use available credit" on an unmatched payment opens the guided dialog with "Suggested invoices" and the reason "Amount equals the open amount" | pass (`05-candidates.png`) |
| Review, then confirm: receipt "Settlement recorded", allocated 25.00, remaining claim 0.00, remaining credit 0.00 | pass (`06-review.png`, `07-confirmed.png`) |
| Status afterwards: payments allocated +1, unmatched payments −1, credit −25.00, no failures | pass |

Two script corrections came out of the live run: the row actions of the Open items register
live in the inline preview opened by the `entry` query parameter, and the customer-balance
flow must be read with `item_status=outstanding` across pages, because settled payments are
listed as used credits too. Screenshots: `/private/tmp/reality-demo-o2c-browser-final/`.

Observation for the scheduler contract, outside this feature: a sleeping developer machine
turns lease expiry into a disabled schedule that needs a manual stop and start.

## Batch bound raised — 2026-09-11

After the live run, FR-018 and SC-005 were amended from ten to 25 settlement records per
occurrence and `services/demo_data.py::SETTLEMENT_BATCH` set to 25. At 300 orders per hour
the stream needs about ten records a minute (five invoices plus five first payments, plus
occasional second payments); 25 keeps the backlog from growing at every supported rate.
The intake tests keep exercising the bound with a patched batch of ten so a dozen orders
still need two occurrences.

## Rebased onto main — 2026-09-11

After `git rebase --onto origin/main` (main at `12bfc4b`) and the renumbering to 168, the
complete backend suite passed: 2,232 passed, 9 skipped in 5:49. Web contract tests (121),
TypeScript build, four-language audit, Prettier, docs-site tests (45) and build, `make lint`,
`make spec-check` and `git diff --check` all pass on the rebased branch.
