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
  **The matcher reads the invoices that can still owe (2026-09-20).** The candidate
  search loaded every invoice the customer ever had and worked out the open amount of
  each: eleven statements at fifty invoices and eleven at four hundred, but 11 ms
  against 55 — flat in statements, growing in rows. It now selects in one read the
  invoices whose control postings are not already covered by allocations that are still
  active: **16 ms at four hundred, and the curve is flat.** A test measures rows read
  rather than statements, because that is the measure the growth was hiding in.

  Two things about that change are worth keeping. The filter is deliberately generous —
  it counts every control posting whatever its direction, and keeps any invoice a
  reversal touches — because taking one invoice too many costs a row while dropping an
  open one would hide it from the matcher. And the first shape of the query was **7.5
  times slower than no filter at all** (413 ms against 55): correlated `IN` subqueries
  and `NOT IN` over the reversals. The anti-join that replaced it is the one measured.

  **What the repeated reads are, now that the measurement can say.** The ingest record
  counted reads per table across both spans, so `source_record ×58` looked like the
  intake when most of it was the demo generator's own selection; interpreting one record
  reads it 5 to 7 times. Per span, the largest repetitions left are `tenant` 8 to 14 per
  step, `tenant_event_progress` 8 to 10, and in the payment step `document` ×14,
  `ledger_reversal` ×13 and `ledger_entry` ×10. The tenant purpose is immutable by a
  database trigger and is read five times in one payment's call tree — the next thing
  worth establishing once per transaction.

- **FR-002**: Incremental derivation. Exception classes and projection builders MUST accept
  a change set (record ids by type) and re-evaluate only the rows that depend on it; full
  company evaluation remains available for maintenance rebuilds. Time-based transitions MUST be
  selected by indexed dates.

  Implemented as spec 241. The mechanism is complete and merged: the change set, the partial
  merge, the refusals, the fallback report, and the equivalence property that stands between
  an optimisation and a silently wrong projection.

  **Ten of twelve builders narrow** — `journal`, `document_register`, `inventory`,
  `item_supply_demand`, `fulfillment_queue`, `fulfillment_blockers`, `commitment_register`,
  `timeline`, `open_financial_items`, `payments`. The remaining two evaluate the company,
  which is always correct and always allowed (a builder may decline). What is left:

  * `tenant_usage` — **measured, and it does not narrow.** Its single row is the company:
    the change set names records and the row names totals, so there is nothing to narrow
    by. The measurement said the assumption behind "the widest" was wrong as well. A
    refresh cost 37 statements and 10.6 ms at 200 orders, 11.5 ms at 800 and 12.6 ms at
    2,400 — a twelvefold company for 19 % more — so the round trips were the cost and the
    scans were not. The twenty-four grouped aggregates became one statement: 14 statements
    and 7–8 ms, flat across the same range. If the scans ever do show, the next step is
    maintained counters with reconciliation, not a change set.
  * `exceptions` (37) is the largest and needs its own design, because its evaluation loads
    the whole company by construction (see FR-003). The **first obstacle is removed**: its
    stored rows carried `position`, each row's place in the whole company's order, and a
    refresh that derives three rows cannot know a rank. The cause was one line —
    `OperationalException.to_dict()` dropped `sort_at` — so the order had to be kept as a
    number. The row now carries the key the derivation orders by and the readers order by
    it, which also ends a quieter disagreement: within a class the derivation puts the
    oldest first, while a reader without `sort_at` fell back on the record id. The
    narrowing itself, the input scope and the clock are the remaining steps
    (`docs/ideas/exceptions-derive-by-change.md`), and their order was corrected by
    counting: 43 of this module's reads go straight to the session and 11 through the
    shared scope, so bounding that scope narrows a few classes and leaves the company
    read. Narrowing here is all-or-nothing — a class may be skipped only when it is
    provably unaffected — and whether a class is record-local has no universal probe, as
    a first attempt showed by calling two company-wide classes record-local. The clock
    does have one, and its list is now measured rather than recalled: three classes read
    it (`tests/operational_exceptions/test_class_clock.py`).

  **The rule that makes narrowing safe, learned twice and stated once:** an event's subject is
  what was *acted on*, not everything the action created. `ledger.reversed` names the original
  posting group while the counter-entries live in a new one no event names; `movement.corrected`
  names the corrected movement while the replacement it appends may carry a *different article*.
  Both were found by asking what the producing service creates that its event does not name, and
  both are pinned by tests that fail when the stored relation is not followed. Ask that question
  first of every remaining builder.

  `item_supply_demand` added a second question of the same family, about reach rather than
  creation: `party.delivery_hold_placed` names the party and nothing else, while what it stops
  is every article that party is still waiting for. The subject is resolved through the open
  promises, as the register resolves a party to its documents. The two paths now share the
  blocking rules and the row shape, so the only thing a narrowed run decides for itself is
  which promises to read.

  The queue and its blockers added the third question, about **disappearance**: what a
  narrowed refresh speaks for cannot be the rows it produced, because an order that just
  finished and a blocker that just cleared produce nothing. Each names what it resolved —
  the orders, and every reason of every promise on them — so the row that should go has a
  key that says so. They also sharpened the trap: a movement correction may book its
  replacement against a *different* promise, and the service then settles the status of
  both, so two orders change and the one event names neither.

  The register of promises showed what a projection gives up when it is a register rather
  than a queue. It keeps the promise that was cancelled, so it has no open-work bound to
  hide behind: renaming an article reaches every promise ever made for it, and past
  `MAX_NARROWED_ROWS` it declines. That is the honest shape — the cheap changes narrow, the
  wide ones are a rebuild wearing another name.

  The timeline was the builder that read the company's whole history on every refresh: five
  tables end to end. It is also the first that can answer **"nothing of mine changed"**. A
  timeline row is one of five records and prints that record's own fields plus its article's
  name, so a document, a party, a location or an observation — all real changes the catalog
  rightly says invalidate it — reach no row. Such a window produces no rows and speaks for
  none, which writes and removes nothing rather than re-reading the history.

  The open items then corrected this specification's own judgement. They were written off
  above because `payments.run` names the tenant; a payment run is indeed declined, but a
  posting, an allocation, a party and a payment term all resolve to documents, which is
  every other window.

  They also produced the clearest lesson about how far a subject reaches — and it was the
  existing test suite, not the sabotage pass, that produced it. Reversing a **payment's**
  posting group un-settles its allocation, and the row that changes is the **invoice's**: a
  document the event does not name and the reversed group's own entries do not carry. An
  allocation ties two documents together, so touching either side moves both, and the
  counterpart must be read from the allocation table rather than from the active
  allocations — because the reversal is exactly what made one inactive. The same hop,
  taken twice, is what `payments` needs to see an invoice reversal.

  The `LedgerReversal` relation itself is *not* followed by either: a sabotage of that
  lookup changed no outcome, because the event names the original posting group and the
  word `reversed` comes from the stored relation. Two lookups of the same shape, one
  necessary and one not — which is why each is decided by watching a test fail rather than
  by symmetry.

  `tenant_usage` closed the list by being measured rather than narrowed, and it is the
  clearest case in this feature of measuring before deciding: the builder called the widest
  was nearly flat, and the work it actually wanted was fewer round trips.

  `payments` completed that correction: the pair this specification wrote off both narrow.
  Its own lesson is about a subject that points one record short of the row. A settlement
  allocation names the *control* entry of a payment's posting group, while the row is the
  cash entry beside it, so the resolution takes a second hop through the group. Stopping at
  the named entry leaves the payment's allocated amount stale, which is the figure the
  projection exists to show. And the allocation hop runs in both directions here too:
  reversing an **invoice's** posting group gives the payment back what it had allocated,
  and that group holds no cash entry at all.

  **`exceptions` narrows by class, and that is the shape its own measurement asked for
  (2026-09-20).** Eleven builders narrow by record; this one cannot, because half its
  classes judge what happened after a promise was fulfilled and several compare records
  against each other — a credit limit against a party's whole ledger, an invoice number
  against every other. What it does have is classes a warehouse event cannot possibly
  have moved.

  Measuring told the rest. On a company of 200 orders the whole catalog costs 69 ms, and
  46 of them are the open-items read that five money classes share. So the inputs became
  lazy — read when a class first asks rather than before any class runs — and a refresh
  evaluates only the classes the change set can have moved. A movement skips those five
  and with them that read: **51 statements and 210 ms become 39 and 70 at 200 orders, and
  337 ms become 221 at 600.**

  A class absent from `CLASS_DEPENDENCIES` is evaluated whatever changed, so the list is a
  set of claims to be tested rather than a promise to be complete: a missing entry costs a
  saving, never a wrong answer. `payments.run` names the company, so nothing is skipped
  for it.

  **The cadence is a date now (2026-09-20).** `exceptions` was rebuilt for every company
  every sixty seconds in case something had aged. The checkpoint records
  `clock_due_at` — the earliest moment a verdict could change with no event at all — and the
  selection compares that instead. Three things in this catalog are judged against a date
  the records carry (a promise's date in force, an open item's due date, a lot's
  best-before), so their next future value is when the projection next has something to
  say. Everything else ages against a span measured from a record's own timestamp, and
  rather than enumerate those records — a list to forget something from — the answer is
  capped at twenty-four hours.

  The trade is stated rather than hidden: an age-based verdict on a company where *nothing
  happens* can now be up to a day late where it was up to a minute. It matters only for
  idle companies, because any business event re-derives this projection through its change
  set. Measured cost of one evaluation: 75 statements, 65 ms at 200 orders and 179 ms at
  800. An idle company paid 1,440 of those a day and now pays one — at ten thousand
  companies, the difference between hundreds of CPU-hours a day and a fraction of one, to
  discover that nothing changed.

  **Time-based transitions**: delivered in the part that mattered, and not in the part the
  requirement literally names. Measurement showed that two of the three projections refreshed
  every sixty seconds do not read the clock at all, and they were taken off the cadence.
  `exceptions` remains, and cannot be selected by indexed date as written: about half its
  thirty-five classes compare against a *threshold learned from finished promises*, which moves
  for every standing record at once and has no per-record date to select by. That is a feature
  of its own, not a task.
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

  Delivered 2026-09-19 for the selection half. The scheduler took every company in the
  instance and asked twelve questions about each, so ten thousand quiet companies cost a
  hundred and twenty thousand reads a sweep. It now asks all companies at once in one
  indexed read and never visits a quiet one; asking a selected company what is behind is
  one round trip rather than twelve, with the eligibility rules unchanged.

  Two things had to be learned to get there, and both are recorded because they constrain
  what can be done next. A company's progress may **not** live on the `tenant` row: every
  table that references a company takes `FOR KEY SHARE` on it, so writing it on every
  business event makes concurrent REPEATABLE READ transactions fail to serialise. And a
  projection's own `last_event_sequence` may **not** be compared against the company's,
  because it counts only the events that projection depends on and sits below the company's
  on purpose — a journal no posting has touched stays at zero however busy the company is.
  The checkpoint therefore carries a second number, how far the *company* had got when that
  projection last looked, and that is what the fleet-wide selection compares.

  **Delivered 2026-09-20 for the run half as well.** Each projection that is behind gets
  its own run, so a builder that exceeds its budget fails a run about one projection: that
  one reports `failed` with its reason and waits for someone, and its neighbours are
  untouched. The coalescing the shared run gave is kept per projection — a projection with
  a run already waiting is not enqueued again — and a quiet company still produces nothing.

  The guard that made this one run per company was a partial unique index on
  `(tenant_id, job_type)`; migration `0069_projection_run_per_projection` takes the
  projection into it, read out of the run's own configuration so the queue stays the only
  place that says what is already promised.

  **What it costs, measured rather than assumed.** A full cycle of one company — enqueue,
  then work the queue empty — went from 175 statements to 394 when all twelve projections
  are behind, and from 156 to 295 after one business event leaves eight behind. That is
  roughly twice the *bookkeeping*: a lock, an insert, an authorisation, a claim and a
  completion per run. The builders' own work is unchanged and grows with the company, so
  the share this overhead takes falls as companies grow. One operational consequence is
  worth knowing: a worker sweep takes at most ten runs, so a company behind on twelve is
  worked in two sweeps rather than one.
- **FR-005**: Storage. Operational tables MUST be partitionable by tenant and time; source
  payloads MUST be movable to a tiered store behind the existing reference; every repository
  query MUST resolve its cluster from the tenant scope.

  Untouched as of 2026-09-19. `PARTITION BY` appears nowhere in the repository, no payload is
  tiered, and no query resolves a cluster. It is the largest remaining piece of this spec and
  nothing currently depends on it, which is why FR-007 puts it last.
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

  **Never measured at that size.** The largest company these changes were verified against is
  the repository fixture and a 10,000-order benchmark tenant. Nothing here may be reported as
  meeting this criterion until it has been run.
- **SC-003**: With 10,000 synthetic companies of which 1 % change per minute, the refresh
  fleet's work is proportional to the changes and the due dates, not to the company count.

  The structural obstacle is removed: discovery is one indexed read across all companies and a
  quiet company is not visited (FR-004). **The proportionality itself is unmeasured** — there
  has never been a ten-thousand-company fixture. Until there is, the claim is that the shape is
  right, not that the number is.
- **SC-004**: Reads of the Exceptions page, the registers and Home stay under 300 ms server
  time at 100,000 orders per company (already met for the Exceptions page, spec 180).

  Met for the Exceptions page only. The registers and Home have **not** been measured at
  100,000 orders per company.
- **SC-005**: Two fixture runs on the same commit differ by less than 10 % on every recorded
  cost.

  **Compared for the first time on 2026-09-20, and it needed a change after all.** It was
  written here as the cheapest criterion — a run, not a change. The first pair of runs on the
  same commit disagreed by 400 queries against 168 for one invoice, and reported 0.99× and
  0.58× as the same commit's SC-001 ratio. Three defects in the measurement, each found by
  the comparison and each fixed:

  1. **The divisor counted one kind of record.** A settlement sweep invoices and pays in the
     same pass. A sweep that invoiced one order and paid five others produced exactly one
     `sales_invoice`, passed the "one record" filter, and was recorded as the cost of one
     invoice — five times too high. The measured sweep must now deliver exactly one record of
     *any* kind.
  2. **The sweep was handed the whole backlog.** The fixture placed a settlement run's moment
     four hours ahead, so everything due came at once. It now places it on the first due
     moment, which leaves one item due. Two items falling due in the same instant are
     ordinary — a generator batch stamps several orders alike — and the sweep that carries
     both is rejected, which is also what clears the tie for the next attempt.
  3. **A missing step was reported as an improvement.** When a checkpoint found no
     single-record payment sweep, the summary still divided largest by smallest and printed
     0.53× — a halving that was one absent measurement. The ratio is now refused when the
     samples do not hold the same steps.

  After those, two runs at 0/250/500 orders agree on **52 of 54 recorded costs**: `order` at
  52 interpreting queries and `invoice` at 73 in all six samples of both runs. The two that
  differ are the payment step, by 4 of 208 (2 %) — and it varies *within* a run as well
  (109, 111, 113), so it is which payment the fixture met, not the host. That is inside the
  10 % this criterion allows.

  **The timings are not, and on this hardware cannot be.** Twenty-four of the fifty-four
  costs are milliseconds beyond 10 %: up to 75 % at the first checkpoint, where the caches
  are cold, and 10–27 % afterwards. The record already says the milliseconds do not mean the
  same on any host; this criterion as written ("every recorded cost") therefore cannot be met
  by a wall clock on a shared machine. **Decision needed from the owner:** read SC-005 as the
  counts, with the timings reported beside their spread, or keep it as written and accept that
  it stays unmet. The comparison tool implements the first reading — counts exact, timings to
  the tolerance — and says which is which in every finding.

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
