# Reality Reference Week

Owner clarification: the broader goal is now one reactive
[Reality Company Simulator](company-simulator.md) with general-company and
Shopify-company profiles and configurable duration. This week remains its existing
fixed-action kernel regression; it is not a completed agent-management game.

Established scenario name: **Reality Referenzwoche** (English: **Reality Reference
Week**). Its first 24 hours are the **Reality Referenztag** (English: **Reality
Reference Day**). References to either name mean this protocol, including its exact
events and checkpoint oracle. The reference day is the first-day subset of the
reference week, not a separate scenario.

Status: authored protocol v1 with an executable local manual-source core replay.
Implementation and verification: [spec 372](../../specs/372-reference-week-harness/spec.md)
and [start guide](../../packages/reality-core/scenarios/reference_week/README.md).
The protocol itself changes no business rule. Unknown adapter support must be
reported before execution, not implemented implicitly to make the rehearsal pass.

## Purpose and authority

Prove that accepted sources, delivery commitments, reservations and physical
movements reconcile without missing or duplicated quantities. The one-day run is
the first 24 hours of the seven-day run. Each starts in a new empty Sandbox company,
not the canonical demo profile. Do not enable random Demo Data or other intake.

References: [decision-gated intake](../features/decision-gated-intake.md),
[company setup](../features/company-setup-demo.md),
[scenario coverage](coverage.md), and [the domain guide](../ERP_MONTH.md).
In particular, `services/core.py` derives stock from movements, open quantity from
effective promise minus fulfillment, and deliberately does not subtract customer
returns from delivery fulfillment.

Writing this script authorizes no live mutations. On a later explicit start, record
the selected company, run scope and authorized review arrangements. Use normal
tenant-scoped tools/services. An agent reviewer needs the existing explicit finite
owner mandate; spawning an agent or holding a token does not grant one. If unavailable,
use the existing human confirmation flow and report the run as supervised.

## Reproducibility and clock

- Scenario ID: `reality-reference-week`; version: `reality-reference-week-v1`.
  Former draft identifier: `zero-company-v1`. No random inputs. Start with a unique run ID.
- T0: Monday 2026-10-05 08:00 UTC in scenario time. D1–D7 are successive
  24-hour periods; `D2 00:00` means T0 + 24 hours, not calendar midnight.
- Times below are offsets from each day's start. Run either in real time or
  compressed, in the stated order. Record scenario time and actual processing time
  separately. Do not claim that application time is virtual unless supported.
- Every event has a stable identity within its run. Preserve source payloads and
  map authored labels to returned opaque IDs; labels/SKUs are never foreign keys.
- Checkpoints are barriers: emit no next event until prior effects have committed
  and the observed projection has incorporated their event cutoff. Default timeout:
  120 real seconds per barrier, recorded in the run manifest. A timeout is a failure
  or blocked run, not permission to change expected numbers or skip the barrier.
- Within one timestamp, execute rows top to bottom. Take snapshots before continuing.
  Do not backdate commands or mutate the database to simulate time.

## Company and exact inputs

Create `Reality Rehearsal <run-id>` as Empty / Sandbox. At checkpoint Z0 there
are zero scenario items, customers, suppliers, orders, commitments, reservations,
movements and ledger entries. Company identity, membership and infrastructure
records are excluded from these business counts.

Load one supplier, `North Supply Test`, three customers, `Workshop Test` (K1),
`Retail Test` (K2), `Studio Test` (K3), and locations W1 / W2. All are fictional.
Customer addresses and correspondence are fixture data; use `.invalid` email
addresses and a local transport sink. No external email delivery is needed.

| SKU | Item | Unit | Stated net sales price | Opening stock W1 |
| --- | --- | --- | --- | --- |
| A | Workshop lamp | pcs | EUR 10.00 | 20 |
| B | Mounting bracket | pcs | EUR 5.00 | 12 |
| C | Power adapter | pcs | EUR 8.00 | 0 |

W2 starts empty. No kits, lots, serials, holds, taxes, price rules or unit conversion.
Opening stock consists of two explicit movements, not edited balance fields.
All purchases use North Supply Test and W1. Purchasing prices are explicitly
EUR 6.00 / 3.00 / 4.00 for A/B/C; do not infer ledger postings from a purchase.

Orders are actual recorded test orders through the normal application boundary,
not imaginary counts in an agent conversation. The source states the line prices
above, currency EUR, quantities and exact totals below. No invoicing or payment is
requested in this inventory run: ledger-entry count must remain zero. Financial
posting and settlement correctness require a separate follow-up scenario.

| Order | Customer | Arrival | Lines | Stated net total | Promised dispatch |
| --- | --- | --- | --- | --- | --- |
| S1 | K1 | D1 01:00 | A6, B2 | 70.00 | D1 02:00 |
| S2 | K2 | D1 03:00 | A8 | 80.00 | D1 04:00 |
| S3 | K3 | D1 05:00 | A10, B4 | 120.00 | D1 06:00 available part; D2 01:00 rest |
| S4 | K1 | D1 07:00 | B3 | 15.00 | D1 10:00; cancelled before dispatch |
| S5 | K2 | D2 02:00 | A5, C3 | 74.00 | D2 03:00 |
| S6 | K3 | D3 02:00 | A7, B2, C4 | 112.00 | D3 03:00 |
| S7 | K1 | D4 01:00 | A6, B5, C4 | 117.00 | D4 02:00 available part; D5 01:00 rest |
| S8 | K2 | D5 02:00 | A4, B2, C2 | 66.00 | D5 03:00 |
| S9 | K3 | D6 04:00 | A3, B3, C1 | 53.00 | D6 05:00 |
| S10 | K1 | D7 02:00 | A2, B1, C2 | 41.00 | D7 03:00 from W1 |

Partial deliveries are explicitly permitted for S3/S7. Use the supported split/date
representation if available; do not invent two commitments for one line solely to
represent the authored dispatch plan. Checkpoint counts assume one per order line.
Store the plan in the fixture if the current interface cannot express both dates.

## Day 1: detailed event script

Before every acceptance, preserve the raw input and reviewed exact proposed effects.
At the raw/prepared barrier there must be no new accepted order, commitment,
reservation, movement or posting. After acceptance, verify exact party, item,
quantity, source lineage and one customer commitment per accepted order line.
If the chosen supported order path is a direct authenticated human operation,
record that distinction; do not claim it tested external-intake preparation.

| Event | Time | Input / expected approved action | Required observation |
| --- | --- | --- | --- |
| E00 | 00:00 | Create empty company | Z0: all scenario business counts zero |
| E01 | 00:05 | Submit and accept the three items, parties and two locations | Z1: 3 items, 3 customers, 1 supplier, 2 locations; stock all zero |
| E02 | 00:15 | Accept opening stock A20/B12 at W1 | Z2: physical (20,12,0); 2 opening movements; no promises |
| E03 | 01:00 | K1 submits S1; review and accept | 1 order, 2 customer commitments; open (6,2,0); stock unchanged |
| E04 | 01:15 | Approve reservations S1 A6/B2 | Physical (20,12,0), reserved (6,2,0), free (14,10,0) |
| E05 | 02:00 | Warehouse confirms S1 dispatch A6/B2 | Physical (14,10,0); S1 fulfilled; reservations consumed |
| E06 | 03:00 | K2 submits S2; accept and reserve A8 | Physical (14,10,0), reserved (8,0,0), free (6,10,0) |
| E07 | 04:00 | Confirm S2 dispatch A8 | Physical (6,10,0); no open customer quantity |
| E08 | 05:00 | K3 submits S3; accept and reserve A6/B4 only | M1: physical (6,10,0), reserved (6,4,0), free (0,6,0); open customer (10,4,0), uncovered (4,0,0) |
| E09 | 05:15 | Reviewer approves PO1: A20/C10; due D2 00:00 | Supplier open (20,0,10); physical and reservations unchanged |
| E10 | 06:00 | Confirm S3 partial dispatch A6/B4 | M2: physical (0,6,0); S3 A4 remains open; no active reservation |
| E11 | 07:00 | K1 submits S4; accept and reserve B3 | Physical (0,6,0), reserved (0,3,0), free (0,3,0) |
| E12 | 08:00 | K1 cancels S4; approve commitment cancellation | M3: physical (0,6,0), reserved zero; S4 commitment cancelled, reservation released; S3 A4 alone open |
| E13 | 09:00 | Resubmit byte-identical S3 source through its original supported intake identity; replay its executed acceptance proposal | No second order/commitment/effect; retain returned replay evidence |
| E14 | 23:59 | Freeze day-end snapshot | M4 below; no supplier receipt has occurred |

The purchase decisions are authored procurement instructions for an exact core
rehearsal: PO1 A20/C10 at E09 and PO2 A16/B12/C10 on D3. In agent mode, ask the
operator to propose those exact purchases within 15 scenario minutes of the stated
trigger. Do not claim these are an existing automatic reorder policy. PO1 includes
an explicitly planned C launch buffer; A shortage alone cannot imply C demand.

## Days 2–7: exact continuation

| Event | Time | Input / expected approved action | Required observation |
| --- | --- | --- | --- |
| E15 | D2 00:00 | Supplier actually delivers PO1 A12/C10; accept receipt | Physical (12,6,10); PO1 A8 still open; C fulfilled |
| E16 | D2 00:15 | Reserve S3 remaining A4 | M5: physical (12,6,10), reserved (4,0,0), free (8,6,10) |
| E17 | D2 01:00 | Ship S3 remaining A4 | S3 fully fulfilled; physical (8,6,10) |
| E18 | D2 02:00–03:00 | Accept S5, reserve A5/C3, then ship at 03:00 | M6: physical (3,6,7), customer open zero; PO1 A8 still open |
| E19 | D3 00:00 | Receive remaining PO1 A8 | Physical (11,6,7); PO1 fully fulfilled |
| E20 | D3 02:00–03:00 | Accept S6, reserve all lines, ship at 03:00 | Physical (4,4,3); customer open zero |
| E21 | D3 03:15 | Approve PO2 A16/B12/C10, due D5 00:00 | M7: supplier open (16,12,10); stock (4,4,3) unchanged |
| E22 | D4 01:00 | Accept S7; reserve A4/B4/C3 only | M8: physical (4,4,3), reserved (4,4,3), free zero; customer open (6,5,4), uncovered (2,1,1) |
| E23 | D4 02:00 | Ship reserved part of S7 | M9: physical zero; customer open (2,1,1); reserved zero |
| E24 | D5 00:00 | Receive PO2 A16/B6/C10; B6 remains outstanding | Physical (16,6,10); supplier open (0,6,0) |
| E25 | D5 00:15–01:00 | Reserve and ship S7 remainder A2/B1/C1 | Physical (14,5,9); S7 fulfilled |
| E26 | D5 02:00–03:00 | Accept S8, reserve all, ship at 03:00 | M10: physical (10,3,7); customer open zero; supplier B6 still open |
| E27 | D6 00:00 | Receive final PO2 B6 | Physical (10,9,7); all supplier commitments fulfilled |
| E28 | D6 01:00 | K2 announces return of S5 A2 by fixture email | Stock unchanged; no delivery commitment reopened |
| E29 | D6 02:00 | Warehouse confirms returned A2, resalable at W1 | Physical (12,9,7); S5 remains fulfilled; original shipment remains recorded |
| E30 | D6 03:00 | Count B8, book adjustment out B1 with count evidence/reason | Physical (12,8,7); no order/purchase commitment changed |
| E31 | D6 04:00–05:00 | Accept S9, reserve all, ship at 05:00 | M11: physical (9,5,6); all open quantities/reservations zero |
| E32 | D7 01:00 | Transfer A3 W1 → W2 | M12: global (9,5,6); W1 (6,5,6); W2 (3,0,0); no fulfillment effect |
| E33 | D7 02:00–03:00 | Accept S10, reserve/ship from W1 | W1 (4,4,4), W2 (3,0,0); global (7,4,4) |
| E34 | D7 23:59 | Freeze week-end snapshot | M13 below |

At each compressed accept/reserve/ship row, capture three separate snapshots.
Reservation never changes physical stock. Dispatch, not a plan or outgoing email,
fulfills a customer promise. Only actual receipt fulfills a supplier promise.

## Milestone oracle

Vectors are exact quantities in A/B/C order. Counts are accepted sales orders ever
recorded, including S4, and orders with at least one live non-cancelled open customer
commitment. They are not counts of historical commitment or reservation rows.
`Customer open` excludes cancelled commitments even if a low-level remaining-quantity
helper still returns the original unfulfilled quantity for a cancelled record.

| Checkpoint | After | Sales orders | Open sales orders | Physical | Active reserved | Customer open | Supplier open |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Z0 | E00 | 0 | 0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| Z1 | E01 | 0 | 0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| Z2 | E02 | 0 | 0 | 20/12/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| M1 | E08 | 3 | 1 | 6/10/0 | 6/4/0 | 10/4/0 | 0/0/0 |
| M2 | E10 | 3 | 1 | 0/6/0 | 0/0/0 | 4/0/0 | 20/0/10 |
| M3 | E12 | 4 | 1 | 0/6/0 | 0/0/0 | 4/0/0 | 20/0/10 |
| M4 | E14 | 4 | 1 | 0/6/0 | 0/0/0 | 4/0/0 | 20/0/10 |
| M5 | E16 | 4 | 1 | 12/6/10 | 4/0/0 | 4/0/0 | 8/0/0 |
| M6 | E18 | 5 | 0 | 3/6/7 | 0/0/0 | 0/0/0 | 8/0/0 |
| M7 | E21 | 6 | 0 | 4/4/3 | 0/0/0 | 0/0/0 | 16/12/10 |
| M8 | E22 | 7 | 1 | 4/4/3 | 4/4/3 | 6/5/4 | 16/12/10 |
| M9 | E23 | 7 | 1 | 0/0/0 | 0/0/0 | 2/1/1 | 16/12/10 |
| M10 | E26 | 8 | 0 | 10/3/7 | 0/0/0 | 0/0/0 | 0/6/0 |
| M11 | E31 | 9 | 0 | 9/5/6 | 0/0/0 | 0/0/0 | 0/0/0 |
| M12 | E32 | 9 | 0 | 9/5/6 | 0/0/0 | 0/0/0 | 0/0/0 |
| M13 | E34 | 10 | 0 | 7/4/4 | 0/0/0 | 0/0/0 | 0/0/0 |

Every checkpoint from Z1 onward has exactly 3 items, 3 customer-role parties,
1 supplier-role party and 2 locations. One party may hold multiple roles in Reality;
do not count the company's own party as another customer or supplier.

Day end: 6 customer commitments: 4 fulfilled, 1 open, 1 cancelled; 2 supplier commitments
open; one purchase order. Use that exact split, not an order header status.
Week end: 23 customer commitments: 22 fulfilled, 1 cancelled; 5 supplier
commitments fulfilled; 2 purchase orders. Sales totals sum to EUR 848.00 as stated
commercial evidence, including the cancelled EUR 15.00. This is not revenue.

Week-end stock reconciliation, independent of Reality's displayed balance:

| SKU | Opening | Supplier receipts | Customer returns | Customer shipments | Count loss | Closing |
| --- | --- | --- | --- | --- | --- | --- |
| A | 20 | 36 | 2 | 51 | 0 | 7 |
| B | 12 | 12 | 0 | 19 | 1 | 4 |
| C | 0 | 20 | 0 | 16 | 0 | 4 |

Transfer A3 has net global effect zero. Fulfilled shipment quantities remain
51/19/16 despite the return. No active reservations remain. Historical consumed
and released reservations must remain explainable; their row count is not fixed
because supported splitting can create extra rows.

## Two execution modes and agent roles

**Core replay first:** exact actions are executed through the existing authorized
boundary in the authored order. Compare after every event as well as milestones.
This proves booking behavior independently of how well an operator chooses actions.

**Agent rehearsal second:** a fresh company and identical script; the operator
receives only current inputs and purchasing instructions, never future customer
events or oracle snapshots. Measure proposals, approval, effects and timing
separately. If it misses a dispatch or proposes the wrong purchase, retain the fixed
milestone mismatch. Also reconcile stock against the effects that actually committed:
correct stock after late dispatch is an operator miss, while unexplained stock is a
core defect. Do not silently perform the missed action to make the result green.

On an explicit later start, use an orchestrator and two separately scoped agents:

1. **Simulator:** creates the authored customers/items and submits the exact order,
   cancellation, supplier and warehouse evidence. It does not approve the operator's
   choices or repair stock. It owns fixture email text and a local sink, not a real
   mailbox. For S4: “Please cancel order S4, all 3 brackets, before dispatch.” For
   S5: “We are returning 2 lamps from S5; no replacement requested.” Link both to
   resolved same-company opaque party/order references.
2. **Observer:** read-only access; takes fresh complete, paginated snapshots, verifies
   per-line identities and quantities against this oracle, and reports differences.
   It must not execute proposals, create corrective entries or infer success from
   another agent's narration. Prefer deterministic arithmetic/comparison for all
   numbers; use agent reasoning only to explain a recorded mismatch.

The orchestrator enforces barriers and controls operator access. The Reality operator
under test proposes acceptance, reservations, purchases and fulfillment actions;
simulator warehouse evidence remains the independent statement of physical events.
Real supplier transport, customer transport and warehouse integrations are not
implied by fixture generation. Unsupported email/intake adapters are declared
blocked or replaced by a documented supported manual-source path before starting.

## Checks, failure evidence and output

At every accepted order line prove Source → Evidence → Commitment. At every
reservation prove Commitment linkage and exact remaining allocation. At every
shipment/receipt prove the linked promise, item, quantity and location. Compare
authoritative read services and refreshed projections; a sampled cockpit list is
not sufficient proof of complete counts.

Always check: tenant isolation, nonnegative physical/free stock in this fixture,
active reservations no greater than physical stock or remaining live promise,
cancelled S4 has no active allocation, receipts do not exceed the authored purchase,
and no unexpected ledger entries. Customer return does not reopen S5.

E13 exercises supported source identity and proposal-receipt replay, not a general
guarantee that every mutation accepts a caller idempotency key. Do not retry an
ambiguous dispatch. Record it as unknown and reconcile first. Extra failure probes
(over-reserving, wrong-tenant reads/writes, stale review, changed replay payload)
belong in an isolated branch company so they cannot contaminate the fixed oracle.

For each run retain these artifacts outside business tables:

- Manifest: script version/hash, run/company IDs, code revision, adapter choices,
  authority basis, actual/scenario time mapping, timeouts and projection freshness.
- Event log: E-ID, original payload hash, source/proposal/decision/receipt and affected
  opaque IDs, scenario time, submitted/committed/observed real times, outcome.
- Checkpoint records: expected/actual quantities, per-order line states, counts,
  event cutoff, projection checkpoint and complete evidence links.
- Report: day/week result, first failing event and checkpoint, expected/actual/delta,
  missing/duplicate records, timing failures, unknown effects and suspected layer
  (source, acceptance, core booking, projection freshness or operator).

Pass requires every applicable exact checkpoint and invariant, complete lineage,
zero unexplained quantity delta and no unresolved outcome. Blocked capability or
approval is not a pass. Never change this version's oracle during a run; improvements
create a new version and a new empty company. Preserve a failed company for diagnosis.

## Implementation boundary

The executable fixture is
[`scenario.yaml`](../../packages/reality-core/scenarios/reference_week/scenario.yaml).
The shared harness lives in `packages/reality-core/scenarios/harness/`; the scenario
adapter in `scenarios/reference_week/`. The local command supports day and week
scope, creates a fresh practice Sandbox and uses the normal confirmed application
tools. The independent observer compares after every event and retains reports.

This first adapter exercises manual-source proposals. E13 replays an executed order
proposal receipt; raw external-source admission is separate future coverage. E28
records the return announcement text without mailbox transport. Scenario time is
compressed and logged separately from actual booking time. Reads are authoritative
and synchronous; materialized projection freshness is not yet verified. No AI
operator, mandate, background schedule or Shopify connection is created.

Automated proofs use disposable PostgreSQL databases and rolled-back test companies.
A retained command-line run requires your existing eligible local account and a
migrated local test database. See the start guide for the exact command and outputs.
