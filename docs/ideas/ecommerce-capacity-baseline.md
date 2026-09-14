# Idea: Production-shaped ecommerce capacity baseline

**Status:** Brainstorming — not approved, not an implementation specification

## Problem

Reality needs an honest measurement of what the system can process today, where its
first bottlenecks appear, how it behaves under backlog and partial supply, and roughly
which Docker or AWS resources one real company would require.

A synthetic test that sends one endpoint at a constant requests-per-second rate would
not answer this. A real ecommerce day creates interacting work:

- orders with several lines arrive unevenly;
- popular items create reservation and inventory contention;
- payments arrive before, with, or after orders and may be retried;
- some items are immediately available while others arrive later;
- warehouse shifts release, pick, pack, and ship accumulated demand;
- fulfillment and payment events update Business Events and projections;
- exceptions are opened, explained, and later disappear when supply arrives;
- operators and agents read queues while writes continue;
- imports, jobs, projections, and retries can build backlogs.

The initial target is one tenant processing **100,000 customer orders per day** with
production-shaped peaks and complete operational consequences, not merely accepting
100,000 HTTP requests.

## Established groundwork from Spec 033

Spec 033 establishes a narrower **10,000 same-day orders read-cardinality baseline**.
Its deterministic PostgreSQL dataset uses a 1–3 line distribution and related
SourceRecords, Documents/Lines, Commitments, Reservations, Movements, financial records,
materialized projections, and a separate sentinel tenant. It exercises Orders,
Commitments, Inventory, Reservations, Movements, Open items, Payments, Journal, and
Documents twice through the Product Web read models and retains a Pydantic-validated
result with SQL-boundary evidence.

The later capacity specification should reuse or extend, rather than recreate:

- `benchmarks/large_tenant_registers/dataset.py` for deterministic profiles and
  cardinality validation;
- `benchmarks/large_tenant_registers/cases.py` for bounded operator-read cases;
- tenant sentinels and Source → Evidence → Reality sample checks;
- the versioned JSON/Markdown result model and environment/content identification.

Spec 033 does **not** prove production-shaped ingestion throughput, concurrent writes
and reads, worker or projection freshness under load, backlog recovery, resource
saturation, soak stability, failure recovery, Docker sizing, or AWS capacity/cost. Its
first complete projection build is intentionally excluded from register-read timings
and remains an important workload for this future idea to measure and improve.

## Questions the baseline must answer

1. How many complete orders per second can the current system sustain at acceptable
   latency and projection freshness?
2. Which resource saturates first: application CPU, Python workers, PostgreSQL CPU,
   locks, connections, I/O, transaction log, job backlog, or projection rebuild work?
3. How much event and database amplification does one order create through Source,
   Evidence, Reality, Business Events, jobs, and projections?
4. Can the system absorb realistic peaks without losing data or violating domain
   invariants?
5. How quickly does it recover after a peak or downstream pause?
6. What happens when many orders compete for the same inventory or wait for later
   supply?
7. Can warehouse, finance, Web, and agent reads remain usable while ingestion and
   fulfillment are busy?
8. Which measured application, worker, and PostgreSQL resources are needed for one
   tenant at the target load with agreed safety headroom?

## Success definition

The baseline is successful when it produces a reproducible report, not when it merely
reaches one attractive throughput number. The report must contain:

- tested git revision, schema revision, configuration, dataset, and scenario seed;
- offered versus completed business throughput;
- latency percentiles for each important command and query;
- queue depth, oldest-job age, projection lag, and recovery time;
- application, worker, and database resource curves;
- lock waits, slow queries, database growth, and write amplification;
- business invariant and reconciliation results;
- the first proven bottleneck and evidence supporting that conclusion;
- a measured Docker resource envelope;
- a time-stamped AWS sizing range derived from those measurements;
- assumptions, uncertainty, safety margin, and explicit non-findings.

Passing a test must never be defined only as “no HTTP errors.” An accepted order whose
ImportJob or projections remain hours behind has not completed the business flow.

## Workload model

### Daily volume and peak shape

`100,000 orders/day` averages only about `1.16 orders/second`, so the average is not the
interesting load. The test needs a configurable ecommerce arrival curve rather than a
claimed universal profile.

Start with a provisional model and calibrate it later from a real merchant:

| Window | Provisional offered order rate | Purpose |
|---|---:|---|
| Overnight floor | 0.2-0.5x daily average | Background traffic and maintenance overlap |
| Morning ramp | 1-3x daily average | Gradual queue and cache warming |
| Normal daytime | 2-5x daily average | Sustained trading load |
| Campaign peak | 10-20x daily average for 15-30 minutes | Ecommerce promotion spike |
| Flash burst | 30-50x daily average for 1-5 minutes | Shock absorption, not necessarily steady-state capacity |
| Post-peak drain | Reduced new traffic | Measure backlog recovery |

For the target volume, `20x` average is roughly `23 orders/second`; `50x` is roughly
`58 orders/second`. These are test hypotheses, not claims about a typical merchant.
The final Spec must select a target peak multiplier, duration, and permissible backlog
from business evidence.

Use two time modes:

- **compressed business day** to reproduce the full order/payment/warehouse lifecycle
  quickly while preserving relative timing;
- **wall-clock soak** for several hours or days to reveal leaks, database growth,
  checkpoint drift, and recovery behavior that time compression can hide.

### Order and catalog shape

The dataset must be large and skewed enough to avoid toy behavior:

- configurable catalog size, active assortment, Party count, and warehouse count;
- order-line distribution with single-line, typical multi-line, and large baskets;
- quantities and currencies represented with production Decimal behavior;
- a Zipf-like or measured popularity distribution so a small set of hot SKUs receives
  a large share of demand;
- ordinary items, scarce items, out-of-stock items, lot/serial-tracked items where
  supported, and items receiving later supply;
- new and returning Parties plus guest-like source identities where supported;
- stable external IDs and controlled changed versions for idempotency tests.

Report both orders/second and lines/second. Capacity cannot be compared meaningfully
without the line distribution.

### Business-flow mix

Each simulated order should follow one of several deterministic paths:

| Flow | Example behavior |
|---|---|
| Paid and available | Order, payment, reservation, pick/ship, financial and inventory projections |
| Payment delayed | Order waits, payment arrives later, processing continues |
| Partial stock | Available lines progress; missing line waits for replenishment |
| Entirely unavailable | Commitment and exception remain open until later receipt |
| Split fulfillment | Several shipments complete one order over time |
| Payment retry | Duplicate or retried provider delivery remains idempotent |
| Order update/cancel | New immutable source version causes explicit correction behavior |
| Refund/dispute | Financial follow-up appears after fulfillment or payment |
| Invalid/unmapped source | Evidence is retained safely without creating false Reality |

The mix and timing are configuration, recorded in every result. The first benchmark
must not invent unimplemented business behavior merely to look comprehensive.

### Two- or three-shift operation

Warehouse activity is not uniform with order arrival. Model configurable shifts:

- orders accumulate before a shift or during reduced staffing;
- workers read fulfillment queues and blockers;
- reservations and releases occur concurrently;
- pick/pack/ship commands arrive at bounded worker rates;
- receipts replenish missing items during a later shift;
- waiting orders become actionable and create a catch-up wave;
- shift changes can temporarily reduce processing while new orders continue;
- finance/payment processing and projections continue independently.

The benchmark should measure whether later stock receipt wakes the correct waiting
work without repeatedly scanning or rebuilding unrelated tenant data.

## Production-equivalent load path

Use the planned deterministic integration simulator as the external workload source,
but keep capacity driving separate from simulator correctness:

```text
scenario/capacity driver
          |
          v
external-system simulator
  +-- webhook
  +-- pull/reconciliation API
  +-- file/import where relevant
          |
          v
normal SourceRecord + ImportJob + interpreter path
          |
          v
Evidence / Reality / Business Events / projections
          |
          v
public operational and trace reads
```

The load test must use public or production-equivalent adapter boundaries. It must not
insert orders, payments, movements, jobs, or events through direct ORM/database writes.
Setup may create a pre-sized catalog and initial inventory through supported bulk/test
fixtures only when the setup method and its exclusion from measured traffic are
explicit.

All generated activity should carry deterministic external identities and an
OperationContext so one sample order can be traced end to end even during peak load.
High-cardinality operation IDs belong in sampled logs/traces, not metric labels.

## Traffic classes to run concurrently

Measure a mixed workload rather than a write-only benchmark:

- source ingestion: orders, payments, fulfillments, refunds, products, and receipts;
- import workers and retry processing;
- inventory reservation, release, movement, and fulfillment commands;
- incremental projection consumers/builders;
- operational reads: fulfillment queue, blockers, stock, commitments, payments;
- trace/explain reads for sampled orders and exceptions;
- Web/API navigation calls representative of warehouse and finance operators;
- MCP/agent read tools at a bounded, separately reported rate;
- proposal creation and a small realistic number of confirmed mutations;
- periodic reconciliation/pull traffic and duplicate webhook delivery.

Report each traffic class separately. A fast ingestion endpoint must not hide unusable
operator reads or starved projection consumers.

## Measurements and service-level indicators

### Business throughput

- offered, accepted, interpreted, reservable, shipped, and financially processed
  orders per second;
- lines, SourceRecords, Facts, Commitments, Movements, LedgerEntries, Business Events,
  and ProjectionRows created or updated per order;
- duplicate, stale, conflicting, unmapped, failed, and retried deliveries;
- complete end-to-end time from external delivery to query-visible business outcome.

### Latency and freshness

- p50, p95, p99, and maximum latency per command/query class;
- ImportJob queue depth and oldest pending age;
- Business Event consumer/checkpoint lag by sequence and wall time;
- projection freshness and rebuild duration;
- time from stock receipt to a waiting order becoming actionable;
- time from payment receipt to financial/fulfillment visibility;
- backlog drain time after each peak or pause.

### Application and worker resources

- CPU, resident memory, garbage collection where observable, open files, and network;
- request/task concurrency, active sessions, timeouts, and error categories;
- database pool checked-out/waiting connections and acquisition time;
- worker throughput, utilization, retries, and time spent per interpreter/projection;
- container restarts, throttling, and out-of-memory events.

### PostgreSQL resources

- CPU, memory/cache behavior, connections, transactions, commits, and rollbacks;
- data, index, WAL, and temporary-file growth;
- read/write IOPS, throughput, latency, checkpoints, and vacuum behavior;
- query time and call counts from `pg_stat_statements` or equivalent;
- row/index scans, sort spills, dead tuples, and autovacuum lag;
- lock waits, deadlocks, serialization/conflict retries, and hot rows/index pages;
- tenant-scoped query-plan behavior at production-like cardinality.

### Correctness

- no cross-tenant access or association;
- SourceRecords remain immutable and duplicates remain idempotent;
- inventory, reservations, movements, commitments, and ledgers satisfy their existing
  invariants;
- projections reconcile with authoritative Reality after backlog drains;
- sampled results retain Source → Evidence → Reality and OperationContext traces;
- failure injection produces known retry/quarantine behavior without silent loss.

## Test suite, not one run

Run a sequence that identifies different limits:

1. **Correctness warm-up:** small complete day; verify every business invariant.
2. **Baseline:** target daily curve on intentionally modest resources.
3. **Step load:** increase offered rate in stable steps until an SLI fails or a resource
   saturates.
4. **Campaign spike:** target peak with realistic duration and post-peak recovery.
5. **Hot-SKU contention:** concentrate orders on scarce/high-volume items.
6. **Warehouse catch-up:** release later receipts and process waiting orders during a
   shift wave.
7. **Projection stress:** maintain writes while operational projections consume events;
   include a controlled rebuild outside and, if required, during traffic.
8. **Dependency pause:** stop one worker/projection consumer, build backlog, restore it,
   and measure drain without data loss.
9. **Resource constraint:** lower CPU, memory, connections, or IOPS one dimension at a
   time to verify the suspected bottleneck.
10. **Soak:** sustained production-shaped mixed traffic long enough to observe growth,
    vacuum, connection, and memory behavior.
11. **Noisy-neighbor check:** after the single-tenant goal, add another tenant to prove
    tenant isolation and identify shared-resource interference.

Do not begin with an uncontrolled maximum-load run. Establish correctness and stable
instrumentation before searching for the breaking point.

## Bottleneck analysis method

For each step, correlate the first violated SLI with resource saturation and trace/query
evidence. Examples:

- rising request latency plus connection-pool wait, without database CPU saturation,
  suggests pool or long-transaction pressure;
- database CPU saturation plus a small set of high-total-time queries suggests query or
  index work before adding application replicas;
- lock waits concentrated on inventory/reservation records suggest contention and
  transaction design, not insufficient web CPU;
- low ingestion latency but growing ImportJob age means workers, interpreters, or their
  database writes are the capacity boundary;
- low job lag but increasing projection checkpoint lag isolates projection throughput;
- adequate CPU with high storage latency/WAL/checkpoint pressure suggests the database
  storage envelope is limiting;
- operator-read p99 degradation during writes reveals missing workload isolation or
  query/index issues.

Every claimed bottleneck should be challenged by changing only the suspected resource
or code path and rerunning the same scenario. Correlation alone is not enough.

## Docker resource envelope

Run the same scenario across a small, explicit matrix rather than one developer laptop:

| Component | Variables to sweep |
|---|---|
| Web/API | replicas, vCPU quota, memory limit, process/worker count, DB pool size |
| Import workers | replicas, vCPU, memory, concurrency, retry schedule |
| Projection workers | replicas or partitions, vCPU, memory, checkpoint batch size |
| MCP runtime | replicas, vCPU, memory, session concurrency, DB pool size |
| PostgreSQL | vCPU, memory, storage IOPS/throughput, max connections, relevant settings |

Record actual container limits and measured utilization. “Runs on Docker” is not a
capacity result unless CPU throttling, memory, storage, and database topology are
controlled.

## From measurements to an AWS estimate

Do not select an AWS instance family in the Idea. AWS offerings and prices change, and
local vCPU is not automatically equivalent to a cloud vCPU. At benchmark execution
time, use current official AWS specifications and pricing for the chosen region.

Derive an estimate in this order:

1. Measure steady and peak CPU, memory, connections, network, IOPS, throughput, data
   growth, WAL, and backup needs per component at the target workload.
2. Measure maximum sustainable throughput before each SLI fails.
3. Add explicit business headroom for forecast growth and explicit operational
   headroom for failover, deploys, maintenance, and skew.
4. Select at least two candidate application/worker and managed PostgreSQL shapes whose
   documented limits exceed the measured envelope.
5. Rerun the production-shaped benchmark on those candidates; do not rely only on
   arithmetic translation from local Docker.
6. Report a range: minimum observed, recommended starting size, and scale-up/scale-out
   trigger.
7. Include database storage/IOPS, replicas or failover topology, load balancer, logs,
   backups, and data transfer where relevant—not only compute instance prices.
8. State region, purchase model, availability expectation, and pricing timestamp.

The output may say, for example, “two application replicas plus dedicated worker pools
and one PostgreSQL class in this measured range,” but only after cloud verification.
The result must separate capacity sizing from high-availability sizing: surviving an
instance loss may require more resources than nominal throughput alone.

## Provisional acceptance targets

The final Spec must set numeric targets with the owner. Candidate targets to discuss:

- all 100,000 daily orders are durably accepted and eventually interpreted exactly
  once according to source-version semantics;
- the selected campaign peak is absorbed with zero silent loss and bounded error rate;
- p95/p99 command and operational-read latency stay within agreed thresholds;
- projection lag and oldest ImportJob age remain below agreed limits in normal load;
- peak backlog drains within an agreed time after offered traffic falls;
- stock receipt makes eligible waiting orders visible within an agreed freshness bound;
- correctness reconciliation is exact after all queues drain;
- steady target operation leaves agreed CPU, memory, connection, and I/O headroom;
- the system survives one selected worker/application failure without losing accepted
  work, with recovery time reported separately.

Until those thresholds are chosen, the test is exploratory and must not claim that
100,000 orders/day is “supported.”

## Smallest useful slice

1. Use one tenant with production-shaped catalog, Parties, inventory, and hot SKUs.
2. Generate a deterministic paid-order flow through production-equivalent ingestion.
3. Scale to 100,000 orders in a compressed day with a configurable `20x` campaign peak.
4. Include multi-line orders, delayed payment, partial stock, later receipt, and split
   fulfillment at modest but non-zero rates.
5. Run import workers, Business Events, all current operational projections, warehouse
   reads, finance reads, and sampled trace/MCP reads concurrently.
6. Capture application, worker, PostgreSQL, queue, projection, and business metrics.
7. Run baseline, step, spike, hot-SKU, recovery, and one multi-hour soak test.
8. Reconcile all authoritative business state and projections after drain.
9. Produce the first bottleneck report and a Docker resource matrix.
10. Validate at least one candidate AWS application/worker/database shape before
    publishing a recommended range.

Out of scope for the first slice: claiming universal ecommerce behavior, testing every
connector, global multi-region operation, browser rendering load, arbitrary AI model
latency, purchasing infrastructure, or optimizing code before the baseline identifies
a measured constraint.

## Questions to resolve before specification

1. What peak multiplier and duration represent the target merchant: normal day,
   campaign day, or Black-Friday-like event?
2. What are the actual order-line, hot-SKU, payment, partial-stock, cancellation,
   refund, and split-shipment distributions?
3. Which commands constitute “order fully processed” for the first capacity claim?
4. What p95/p99 latency, ImportJob age, projection lag, and backlog recovery limits are
   acceptable?
5. How many warehouse users, finance users, MCP clients, and concurrent shifts must be
   represented?
6. Which current projections must remain fresh, and may any be intentionally delayed
   during a flash peak?
7. What database/data-retention horizon must exist before the run so query plans see
   mature cardinality rather than an empty database?
8. Which AWS region, availability target, and pricing model should the eventual cost
   estimate use?
9. Is the first claim single-tenant only, or must one large tenant coexist with many
   smaller tenants?
10. Which failure is required in the first slice: worker loss, application loss,
    database failover, dependency timeout, or storage throttling?

## Promotion trigger

Move this idea into a numbered Spec Kit feature after agreeing on the peak curve,
business-flow distributions, completion definition, latency/freshness/recovery limits,
production-sized dataset, and AWS region/availability assumptions. The specification
should define measurable business outcomes and correctness constraints. The plan
should choose tooling, observability, environments, and execution stages without
introducing test-only business write paths.
