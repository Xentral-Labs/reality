# Architecture experiment contract

Status: planned experiment interface, no public API/tool registration in this phase.

## Inputs and lifecycle

The planned `benchmarks.large_tenant_registers.costing_runner` accepts profile
`reduced|full`, seed, business date, strategy `direct|projection`, explicit disposable
confirmation and output path. Database credentials come from the existing benchmark
configuration mechanism and must never be printed. Reject any target not satisfying
spec 033's disposable-name/initial-state protections.

Full profile is fixture J exactly, seed 234 and business date 2026-09-18. Reduced runs
use the same generator/kernel/case definitions with a published smaller manifest; they
cannot stand in for full performance acceptance. Dataset identity includes generator
version, seed, dates, policy and all expected cardinalities. Reuse requires equality.

## Observation envelope

Each read carries tenant, scope identity/filter, effective cutoff, knowledge cutoff,
policy version and requested consistency. Return exact decimal strings with currency
and unit, immutable evidence/assignment references, coverage by required cost dimension,
and formula/method identity. Missing is not zero.

Projection responses additionally carry generation, covered input watermark and freshness
(`ready`, `pending`, `stale`, `failed`, `unavailable`). A strict live read refuses with
`cost_not_ready` if it cannot supply an exact current bounded answer. An explicit stale
read may return a prior generation with its cutoffs; never mix its totals with live rows.

## Measured workloads

- Order: <=100 positions, complete scope, <=500 ms p95.
- Inventory: first 100 rows plus filtered totals, <=2 s p95.
- Monthly contribution: product/customer grouping, <=3 s p95.
- Attention: first page and counts including four cost classes, <=2 s p95.
- Tool answer: same shared observation scope, <=3 s p95 excluding model/network latency.
- One affected receipt: committed-to-published <=30 s p95 under fixture J load.
- Full per-tenant reconstruction: <=120 s for each of three runs, cold/warm disclosed.

Follow fixture J's warmup/sample/resource protocol. Record timeouts, row/query counts,
memory and work excluded from timing. First missing-cache reads return honest state
within budget; they may not rebuild. Full result conservation and tenant isolation are
mandatory regardless of latency. Do not silently skip refusal/incomplete cases.

## Result and decision

Machine-readable results identify revision/content digest, schema/generator/kernel
versions, environment, exact cardinalities, inputs/checksums, percentile samples and
separate correctness/performance outcomes. Produce a Markdown summary from those results.
An exception or incomplete run cannot create a passed result. A faster incorrect strategy
is rejected. If both fail, record the limiting query/algorithm and revise the design;
do not relax approved acceptance thresholds without review.

No product surface may advertise costing support from passing this experiment alone.


## Implemented v3 response subset

Prototype `snapshot_read` returns `state` (`current`, `stale`, `not_ready`), generation,
published/input adjustment revisions and value. Live reads suppress stale values. The
caller holds one repeatable-read snapshot; a current value means current at that snapshot,
not an assurance that nothing committed immediately afterward. New evidence during replay
remains pending beyond the frozen publication revision. Full effective/knowledge/source
version and per-scope product metadata remains the richer target above.

Mixed-load evidence reports 200 samples per surface, state counts, reader time windows,
actual committed update offsets and at least 30 updates. The producer remains active
until all readers finish; a missed one-per-second input rate fails the measured verdict.
Historical preliminary runs without these checks are explicitly superseded.
