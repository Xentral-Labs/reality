# Research: Multichannel Oversell, Deadlines and Peak Intake

Read on 2026-10-01 against `origin/main` at 03524fb6. Paths are under `packages/reality-core/src/reality/`.

## R1. Today

- **Stock**: `services/core.py` `stock_at(item, location=None)` sums movements into and out of locations; without a location it is the item-wide total. `active_reserved` sums active reservations the same way.
- **Demand and supply**: `open_quantity(commitment)` is the promise in force less what was shipped (customer) or received (supplier). `services/delivery_reads.py` `fulfillment_expressions` computes it in SQL with revisions applied. There is no per-item aggregate of either.
- **Findings**:
  - `reservation_exceeds_stock` compares reserved with stock per item.
  - `outgoing_commitment_at_risk` reports an undated-or-not-yet-due promise whose reservation is short.
  - `overdue_outgoing_customer_commitment` reports a promise past its date. Both come from `_commitment_exceptions` (`services/exceptions.py`), an if/elif that never lists one promise twice.
  - Nothing reports demand above stock plus supply, and nothing reports a fully reserved promise close to its date.
- **Channel**: `document.sales_channel` is set by every intake. Shopify writes `shopify`, Demo Data `demo_data`, the file import its source system, and manual entry the stated text. No reader groups by it.
- **Intake**: a Shopify order is stored as a source record and an import job; `process_import_job` interprets it into an order with open promises. Intake reserves nothing; `reserve` checks stock at the promise's location under the tenant delivery lock. `process_pending_import_jobs` works pending jobs one by one (Web `POST /import-jobs/work`, CLI); it selects without `SKIP LOCKED` and locks each job row.
- **Measurement**: `benchmarks/ingest_cost` measures queries and milliseconds per order, invoice and payment of Demo Data intake at company-size checkpoints. Spec 181 measured 3.5 falling to 1.4 orders/s in one process within the first 800 orders. 10,000 orders in two hours need 1.39 orders/s sustained.

## R2. Item oversold (FR-001)

- **Decision**: a class `item_oversold`, one finding per item.
  - Demand is the open quantity of open customer-delivery promises for the item.
  - Supply is the item-wide stock on hand plus the open quantity of open supplier-delivery promises.
  - The finding is reported while demand exceeds supply. Its values are demand, on hand, incoming, shortfall and, per sales channel, the quantity and the orders.
  - Only promises in the item's own unit are summed; a promise in another unit is named in the finding as not comparable and left out of the sums.
  - Its trace names every promise and document involved. Severity high.
- **Neighbours**: `outgoing_commitment_at_risk` is per promise and about reservation; `reservation_exceeds_stock` is about reservations against stock. A company can be oversold with no reservation at all, which is the B14 gap.
- **Bound**: demand and supply are read in two grouped queries for all items, not per item; a statement-count test pins it.
- **Rejected**: per location (B14 asks about the company's stock across channels; per-location coverage is spec 303); counting supply only when due before the demand (needs a dated allocation, out of scope).

## R3. Deadline at risk (FR-002)

- **Decision**: a class `outgoing_commitment_due_soon` in `_commitment_exceptions`.
  - It is reported when the promise is open, quantity remains, and its date in force is after the read instant and less than one day ahead (`DUE_SOON_MARGIN = timedelta(days=1)`).
  - It takes precedence over `outgoing_commitment_at_risk` for the same promise and carries `insufficient_reservation` as a cause when the reservation is short, as the overdue class does. One promise is still never listed twice.
  - Once the date passes, overdue wins.
  - A revised date carries `promise_was_revised` like the overdue class.
- **Clock**: the class reads the clock. `next_clock_moment` gains the instant one day before each open promise's date, so the stored generation refreshes when the window opens; `CLOCK_READING` gains the class.
- **Rejected**: learned margin and a per-company setting (owner decision).

## R4. Peak intake (FR-003)

- **Decision**: a benchmark `benchmarks/peak_intake`:
  - **Setup**: a disposable company with items, stock and a Shopify connection.
  - **Intake**: 10,000 Shopify order payloads stored as import jobs, then worked by `process_pending_import_jobs` from N parallel processes (N = 1 and 4), the path the Web and CLI use. Wall-clock time, orders per second and failures are recorded.
  - **Reservations**: the reservation pass reserves every promise from four parallel connections through `reserve`.
  - **Invariant checks**: no item has more reserved than in stock; every order was interpreted once; the `item_oversold` shortfall equals demand less stock.
  - **Output**: a JSON report and a Markdown summary; the measured run is recorded in `results.md`.
  - **Tests**: a small run (50 orders, 2 processes) is a regular test of the benchmark's own correctness.
- **Promotion rule**: L07 is supported only if the 10,000 orders are processed within two hours.
- **Rejected**: optimising intake in this spec (owner decision); measuring through the demo scheduler (it is not the shop path).

## R5. Stories (FR-005)

- **B14**:
  - Orders from Shopify and from a second channel exceed stock, and the finding names both channels.
  - Positive control: within stock, nothing is reported.
  - A purchase order covering the shortfall clears it.
- **L02**:
  - A marketplace order (second channel, promised tomorrow, fully reserved) is reported as due soon.
  - Control: a promise three days ahead is not reported.
  - Shipping clears it; a date that has passed is reported as overdue only.
- **L07**: follows the measurement.
- The second channel is a manual order with a stated sales channel, or a file import whose source system names the channel; T009 confirms which path states it through a reviewed tool.

## R6. Gates

- **Two classes**:
  - `CLASS_ORDER`, `DERIVATION_REGISTRY`, `CLASS_DEPENDENCIES`
  - `catalogs.py`, `operational_exception_catalog.yaml`
  - the class lists in three tests, `CLOCK_READING`
  - `reference_catalog.yaml` consumers and their counts
  - `resource_catalog.yaml` membership and German labels
  - de/nl/es for label and resolution, checked with `npm run test:i18n`
- **No schema**: no migration, no new table or column.
- **No new mutation**: the findings are reads; the existing exception tools, Web pages and CLI carry them. The benchmark is a developer tool, not an application command.
