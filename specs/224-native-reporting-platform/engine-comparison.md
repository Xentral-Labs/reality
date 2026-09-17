# Deferred Engine Measurement

Status: deferred, not cancelled and not executed. Date: 2026-09-17.
No cloud account, deployment, billable resource, second engine or tenant-data transfer is
authorised by this document. No performance or replication result has been measured.

## Why this is no longer a gate

The previous revision made engine selection a precondition for all production work,
because a user-authored SQL dialect would have become part of every stored artifact.
That is no longer true. The stored query form is a typed traversal against a declared
model; it contains no SQL and no dialect. A different execution backend is therefore a
compiler change, not a migration of saved reports.

Deferral is safe because of that property, not because the question became uninteresting.
The reference questions and the hard gates below are preserved verbatim in substance, so
the measurement can be run later without redesigning it.

## Trigger

Revisit when **all** of the following hold, measured on real tenant data on a quiet
machine, baseline and change compared back to back:

1. A first-slice reference question exceeds an agreed p95 latency target at the observed
   concurrency, and
2. the PostgreSQL escalation ladder has been climbed and recorded — appropriate indexes,
   then measured query shape changes, then a materialised projection, then columnar
   storage — and the target is still missed, and
3. the cost is dominated by scanning rather than by traversal depth or by a defect in the
   generated statement.

If depth is the cost, the answer is a depth bound or a different declaration, not another
engine. Prior experience in this repository is that the first large slowdown was a
query-shape defect: live exception derivation went from 229 s to about 2 s, and spec 180
reached 42 to 81 ms, all on PostgreSQL. Measure the shape before buying hardware.

Also re-check at each review whether SQL/PGQ has reached PostgreSQL core, since it would
serve this design without a second system.

## Reference questions, if it is ever run

| ID | Question | Required semantics |
|---|---|---|
| E01 | Customer stated order value this period versus prior year | Independently aggregated periods; customers present in only one; currency and NULL separation; explicit timezone and half-open periods |
| E02 | Top three products per month and currency | Received line amounts; grouped intermediate results and window ranking; deterministic tie policy; no price-times-quantity reconstruction |
| E03 | Customer order value versus invoiced amounts and allocated settlements | Three separately aggregated branches at customer and currency grain, joined on the grouping keys; separate date bases; credit and reversal handling; no guessed order-payment attribution |

Each needs independently stated expected amounts and evidence identifiers. Comparing two
candidates against each other proves nothing: the same semantic mistake in both is still
a mistake. Spec 222's saved Q01 report is the compatibility baseline.

## Hard gates for any candidate

1. Expected-result equality for every supported question, including corrections and
   reversals.
2. No foreign canary, unauthorised side effect or privileged fallback.
3. Exact decimal values, declared coverage and evidence routes preserved. A candidate
   without an exact decimal type fails here, which is where the graph databases were
   rejected in `research.md`.
4. Tested joined-data consistency and freshness behaviour. A derived copy must disclose
   or refuse an inconsistent combined observation rather than presenting it as current.
5. Save-contract compatibility and an artifact-preserving migration and rollback design.

A candidate passing all five is then compared on cold and warm latency at realistic
concurrency, resource use, impact on the operational write workload, replication lag and
recovery where applicable, operator effort and itemised cost. A faster wrong result
cannot win. Incomplete evidence records "undecided" and changes nothing.

## What a derived copy would still owe

Recorded here so the work is not underestimated if the trigger ever fires: preserved
NULLs and exact decimals, correct resolution of row versions and delete markers at query
time, initial snapshot plus concurrent change, replay, update, deletion, late source
correction, ledger reversal, allocation change, disconnect, restart and resnapshot
without double counting, and a demonstrated consistent publication boundary across
invoice, posting and allocation. A healthy connector on one table proves nothing about a
joined observation. A hand-loaded target proves query behaviour only.

For an ERP this is a correctness obligation, not a latency preference: a balance list
combining a new invoice with an old allocation is wrong, not slightly stale.
