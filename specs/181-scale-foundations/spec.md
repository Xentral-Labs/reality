# Feature Specification: Scale Foundations

**Feature Branch**: `181-scale-foundations`
**Created**: 2026-09-12
**Status**: Draft, measurements in progress (see research.md); owner review pending
**Language**: English
**Input**: Owner target (German, 2026-09-12): "10.000 Kunden, die jeweils ca. 100–1000 Orders am Tag haben"; the owner asked for the ingest cost per order to be its own point in this specification.

## Context and Intent

### Problem

Reality is built for one company at a time being explained completely: every read and every
stored projection re-derives the whole company, every service call re-checks its authority,
and every synthetic order walks the full order-to-cash path in one process. That was right for
proving the domain model. It does not carry the owner's target: 10,000 companies with 100 to
1,000 orders a day each, which is 1 to 10 million orders a day, 12 to 115 orders a second on
average with peaks several times higher, and tens of terabytes of retained source payloads a
year.

Measurements on 2026-09-12 (research.md) put numbers on the four places where the current
design spends work in proportion to the whole company rather than to the change:

1. **Ingest cost per order.** One order with its invoice and payment costs about 300
   database round trips and 660 ms of SQL through the real intake path, of which roughly a
   third are repeated authority reads (`tenant`, `playground_run`) issued once per service call
   instead of once per transaction, and the payment part walks `ledger_reversal`,
   `ledger_entry` and `document` per candidate. Throughput of one intake process fell from
   3.5 to 1.4 orders a second within the first 800 orders of a fresh company, because the
   payment matcher measures every invoice the customer ever had against every allocation the
   company holds; the cost grows with history.
2. **Whole-company derivation.** Every exception class and every projection builder reads the
   whole company. After PR #227 the exception derivation on a 6,600-document company takes
   about two seconds; the twelve builders together take 283 s, `payments` alone 228 s.
3. **Refresh granularity.** Feature 179 refreshes all twelve projections in one job with a
   30 s budget, and time-sensitive projections become eligible every minute for every
   company. On the same company the job never completes; multiplied by 10,000 companies the
   timer alone would demand more than a hundred cores.
4. **Storage shape.** Operational rows and lossless source payloads share the same tables in
   one PostgreSQL cluster; nothing is partitioned or tiered, and the event outbox grows without
   retention.

### Scope

This specification fixes the target, names the measured baseline, and states the properties
the system must have to reach it. It is the umbrella for the implementing features; each of
the four areas becomes its own feature specification with its own plan. It also makes the
measurement itself a first-class, repeatable capability, because every later decision depends
on it.

### Non-Goals

- No change to the Constitution: source payloads stay lossless, derivations are never stored
  as authority, human numbers are never identity, every table stays tenant-scoped.
- No new business rule, no change to what an exception class or a projection means.
- No decision here on a specific sharding product or cloud service; that belongs to the
  storage feature and its plan.
- No premature parallelism: the per-order cost must fall first, or more workers only multiply
  the waste.

### Existing Contracts

- [Background projections](../179-background-projections/spec.md) — the refresh job, its
  budget, freshness metadata.
- [Attention from the stored projection](../180-attention-from-stored-exceptions/spec.md) —
  the reading side is already independent of company size (42–81 ms).
- PR #227 — the batching pattern that took the exception derivation from 229 s to ~2 s.
- [Company setup and Demo Data](../../docs/features/company-setup-demo.md) — the synthetic
  intake path the scale fixture reuses.
- [Scheduled jobs](../../docs/features/scheduled-jobs.md) — the shared scheduler and worker.

## User Scenarios & Testing

### User Story 1 - Ingest at target cost (Priority: P1)

An integration delivers a day's orders for a large company; each order, invoice and payment is
recorded and interpreted with a bounded, predictable number of reads that does not grow with the
company's history.

**Why this priority**: Nothing downstream matters if the orders cannot get in. This is the
owner's explicit point.

**Independent Test**: Run the scale fixture to 10,000 and 100,000 orders and compare the
per-order query count and SQL time of the first and last thousand.

**Acceptance Scenarios**:

1. **Given** a company with 100,000 recorded orders, **When** the next order with invoice and
   payment is interpreted, **Then** the total reads stay within the budget SC-001 sets and are
   within 20 % of the cost at 1,000 orders.
2. **Given** one intake transaction, **When** it calls several core services, **Then** the
   tenant and authority checks are read once per transaction, not once per call, and the
   authority they establish is identical to today's.
3. **Given** a payment to match, **When** the matcher looks for candidates, **Then** it reads
   the open items it needs in bounded queries rather than per candidate document.

---

### User Story 2 - Derive by change, not by company (Priority: P1)

A business event changes one commitment; only the exception classes and projection rows that
depend on that record are re-evaluated, and a promise becoming overdue at midnight is found
through its date, not by scanning every promise.

**Independent Test**: With the scale fixture at 100,000 orders, emit one event and measure the
work the refresh does; compare with a full rebuild.

**Acceptance Scenarios**:

1. **Given** a company with 100,000 orders and a ready generation, **When** one commitment
   changes, **Then** the refresh touches the rows of that commitment and the classes that read
   it, and finishes within the per-event budget SC-002 sets.
2. **Given** promises whose dates pass without any event, **When** the time-based refresh runs,
   **Then** it selects them by date through an index and evaluates only those.
3. **Given** closed history (paid invoices, shipped and billed orders), **When** any derivation
   runs, **Then** it reads none of it unless a class is explicitly about history.

---

### User Story 3 - Bounded, independent refresh jobs (Priority: P2)

A slow builder for one projection never blocks the others, never loses the progress of the
others, and never keeps a company's freshness at "pending" forever.

**Acceptance Scenarios**:

1. **Given** twelve projections due for one company, **When** they are refreshed, **Then**
   each projection is its own unit of work with its own budget and its own published
   checkpoint.
2. **Given** a builder that exceeds its budget, **When** the run ends, **Then** the other
   projections are ready, the slow one reports `failed` with its reason, and the failure is
   visible in the freshness metadata.
3. **Given** 10,000 companies, **When** nothing changed for a company, **Then** no refresh is
   scheduled for it by a timer alone; time-sensitive work is selected by date across companies.

---

### User Story 4 - Storage that grows sideways (Priority: P2)

Operational data stays fast at hundreds of millions of rows, source payloads are retained
losslessly without sitting in the hot tables, and companies can be placed on different
database clusters without changing a service.

**Acceptance Scenarios**:

1. **Given** a year of the target volume, **When** operational tables are queried by a tenant
   and a date range, **Then** partition pruning keeps the read bounded by that range.
2. **Given** a source record, **When** its payload is read for an explanation, **Then** it is
   returned losslessly from a tiered store through the same reference the record carries today.
3. **Given** two database clusters, **When** a company is placed on the second, **Then** every
   read and write for it reaches the right cluster through the tenant scope alone.

---

### User Story 5 - Measure before deciding (Priority: P1)

An engineer can create a synthetic company of any size through the real intake path, run the
builder and class measurements at checkpoints, and compare two commits on the same numbers.

**Acceptance Scenarios**:

1. **Given** a target order count and checkpoints, **When** the fixture runs, **Then** it
   records orders per second, queries per order, every builder's and class's seconds, queries
   and rows, and table sizes, in a machine-readable file.
2. **Given** two runs, **When** their files are compared, **Then** every change in cost is
   attributable to a builder, a class or an intake step.

### Edge Cases

- A company that suddenly grows tenfold in a day must not starve its neighbours' refreshes.
- A builder that times out must never leave a half-published generation.
- Sharding must never let a tenant id resolve to two clusters.
- The fixture must be refused on business (non-sandbox) companies.

## Requirements

### Functional Requirements

- **FR-001**: Ingest cost. Interpreting one order, one invoice or one payment MUST cost a
  bounded number of database reads that does not grow with the company's history. Authority
  and tenant checks MUST be established once per transaction and reused by every core service
  call within it, with the same refusals as today. The payment matcher MUST read its candidate
  open items in bounded queries. The measured cost per step is recorded in research.md and
  the target in SC-001.
- **FR-002**: Incremental derivation. Exception classes and projection builders MUST accept
  a change set (record ids by type) and re-evaluate only the rows that depend on it; full
  company evaluation remains available for maintenance rebuilds. Time-based transitions MUST be
  selected by indexed dates.
- **FR-003**: Working set. Derivations MUST read only open or active records unless the class
  is explicitly about history; closed records MUST be excluded by predicate, not filtered in
  memory.

  Measured 2026-09-19 by adding sixty cancelled promises to a company and comparing what
  each derivation reads. The fulfilment queue, the blockers and supply and demand each read
  **124 rows more** — not because their promise query lacked a predicate, which it had, but
  because they were handed the terms of every promise in the company and the whole document
  table to look up four orders in. Bounded to the open promises and their orders, the three
  are flat: sixty more cancelled promises now cost them nothing.
  `test_working_set.py` keeps it that way and fails without the fix.

  **Exceptions is exempt, and it is the interesting case.** Its evaluation loads every
  commitment, document, line and revision of the company. That cannot be reduced to an open
  working set, because half of its thirty-five classes judge what happened *after* a promise
  was fulfilled — billed and not received, received and not billed, shipped and not billed.
  An open-work set would not be a cheaper version of that answer, it would be a different
  one. The reduction available here is narrowing by change set (spec 241), not by status.
  What was fixed is that six classes each re-read the same order-line promises; they now
  share one read per side of the trade within an evaluation.
- **FR-004**: Refresh units. Each projection of each company MUST be its own scheduled unit
  with its own budget, checkpoint and failure state. Timer-driven eligibility MUST be replaced
  by date-indexed selection across companies; a company with no change and no due date MUST
  cause no work.
- **FR-005**: Storage. Operational tables MUST be partitionable by tenant and time; source
  payloads MUST be movable to a tiered store behind the existing reference; every repository
  query MUST resolve its cluster from the tenant scope.
- **FR-006**: Measurement. The repository MUST carry the scale fixture and measurement as a
  maintained tool, refused on business companies, producing the machine-readable record User
  Story 5 describes.
- **FR-007**: Sequencing. The implementing features MUST land in the order ingest cost,
  incremental derivation, refresh units, storage; parallel workers are added only after
  FR-001 is met.

### Key Entities

- **Change set**: the record ids by type one business event touched; input to incremental
  derivation.
- **Refresh unit**: one projection of one company with its budget, checkpoint and state.
- **Scale record**: one measurement file of a fixture run.

## Success Criteria

### Measurable Outcomes

- **SC-001**: One order with invoice and payment costs at most 60 database reads and 100 ms
  of SQL on a company with 100,000 orders, within 20 % of the same cost at 1,000 orders.

  The baseline this cited — "2026-09-12: ~300 reads, ~660 ms, and rising with history" —
  came from scripts that no longer exist and cannot be reproduced. It is superseded by the
  measurement the repository now carries (`benchmarks/ingest_cost`, FR-006). That
  measurement reports two numbers, and this criterion is about the first: **interpreting**
  one record, which is what every intake pays, against the **sweep** around it, which for
  a synthetic company also carries the demo generator's selection and throttle that no
  customer's company runs.

  Measured 2026-09-19 to 1,500 orders, after the authority check moved to once per
  transaction: **223 statements per order to cash**, flat across the range at 1.01× where
  this criterion allows 1.20. A first reading of 507 counted both spans; it was right
  about the growth and wrong about the size by more than double. The absolute part of
  this criterion remains unmet by about four times.
- **SC-002**: After one business event on a company with 100,000 orders, the affected
  projections are ready within 5 s of worker time; a full rebuild of that company stays a
  maintenance operation.
- **SC-003**: With 10,000 synthetic companies of which 1 % change per minute, the refresh
  fleet's work is proportional to the changes and the due dates, not to the company count.
- **SC-004**: Reads of the Exceptions page, the registers and Home stay under 300 ms server
  time at 100,000 orders per company (already met for the Exceptions page, spec 180).
- **SC-005**: Two fixture runs on the same commit differ by less than 10 % on every recorded
  cost.

## Assumptions and Dependencies

- PostgreSQL stays the only supported database; partitioning and multiple clusters are
  PostgreSQL features and deployments, not a new engine.
- The measured baseline comes from one host process against the local stack; absolute times
  will differ in production, ratios and growth curves will not.
- Features 179 and 180 are merged; #227 is the reference pattern for batching.

## Requirement Traceability

| Requirement | Evidence (planned) |
| --- | --- |
| FR-001, SC-001 | research.md ingest profile; implementing feature "ingest cost"; fixture runs at 1k and 100k |
| FR-002, FR-003, SC-002 | implementing feature "incremental derivation"; fixture event test |
| FR-004, SC-003 | implementing feature "refresh units"; multi-company fixture |
| FR-005 | implementing feature "storage shape"; partition pruning and cluster resolution tests |
| FR-006, SC-005 | `scripts/scale_run.py` (from the 2026-09-12 scratch tool) and its record format |
| FR-007 | order of the implementing specifications |
