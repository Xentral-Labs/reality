# Updates and Scale

Companion to [data-model.md](data-model.md). Two questions that decide whether the model
stays honest over time: what happens when the world corrects itself, and where this stops
being fast.

Measured figures come from [spec 181's research](../181-scale-foundations/research.md),
taken 2026-09-12 on the local Docker stack. Figures labelled **estimate** are reasoned
from the schema and the target volumes and have not been measured. They are stated so
they can be falsified, not believed.

## Part 1: Replace or version?

### The instinct is right, and it is already implemented

Records are replaced, and history runs in parallel. That is not a decision to be taken —
it is what the schema already does. But it does it in **four different ways**, and the
difference changes what an aggregate means, which is why the model has to know about it.

| Layer | Mechanism | Evidence in the schema |
|---|---|---|
| Raw source | Versioned append-only chain | `source_record.version`, `supersedes_source_record_id`, `payload_hash`, `received_at`, `source_version_at` |
| Interpreted records | Replaced in place, identity stable | `document`, `document_line`, `party` are found by `(tenant_id, source_record_id, type)` on re-import and reused |
| Promises | Append-only revisions | `commitment_revision` records `due_at`, `quantity`, `stated_at` per change |
| Accounting and physical facts | Append-only compensation | `ledger_reversal`, `movement_correction` (compensating plus optional replacement), `shipment_event_supersession` |
| Interpretation | Bitemporal, never updated | `fact.observed_at` (when it was true) and `fact.recorded_at` (when Reality wrote it down) |

So the history is carried twice over, in parallel, exactly as expected: losslessly and
versioned at `source_record`, and bitemporally at `fact`. Replacing the interpreted row
loses nothing that was not retained elsewhere.

### Recommendation: keep replacing. Do not version the operational tables.

Versioning `document` would cost a write amplification on every re-import and, worse, a
validity filter on every single read forever — the slowly-changing-dimension tax, paid by
every query, operational ones included. It would buy point-in-time reporting, which this
feature explicitly does not promise and whose coverage `temporal-coverage.md` records as
unproven. Paying a permanent tax for a declared non-goal is the wrong trade.

The honest consequence, which belongs in the catalog rather than in a footnote: a report
answers *what is retained now*, dated by business time. It cannot answer *what this report
would have said in March* without replaying `source_record` versions, and that replay is a
separate feature with its own coverage proof.

### The finding this raised: a second kind of double counting

Fan-out is not the only way to count something twice. **Correction mechanisms are the
other way**, and the rules are opposite depending on the node:

- **Compensating tables** (`movement`, `ledger_entry`): the correction is itself a row, so
  summing *all* rows nets out correctly. Filtering corrections away is the mistake here.
  But `count(*)` over the same rows is inflated — three rows for one corrected event.
  Sums and counts therefore need different handling on the same node.
- **Revision tables** (`commitment`): only the latest revision is true. Summing all
  revisions multiplies the promise by the number of times it changed.
- **Replaced tables** (`document`): the row is the truth, nothing to net or select.

No SQL author and no Cypher author is reminded of this by the query. So it belongs in the
declaration.

### Required change to the model

`data-model.md` gains a fourth mandatory node property, `corrections`, with the values
`replace`, `revise` and `compensate`. The compiler applies it: it selects the latest
revision for `revise`, and for `compensate` it permits measure sums over all rows while
refusing a naive `count` and offering a distinct count of corrected events instead. A node
without this property is rejected at load, like a measure without a unit.

This is a real gap that this question exposed, and it is added to the specification rather
than noted here.

## Part 2: Where this gets slow

### The short answer

Per tenant, a reporting query is index bound and the slice is small — comfortable to
roughly a million rows per node, needing attention around five million, needing
architecture beyond roughly ten million. **Estimate.**

Across the cluster, the total row count does not affect a single well-indexed tenant query
much, until the indexes stop fitting in memory. At the target in spec 181 — 10,000
companies, 20 to 200 million rows a day — that point arrives in weeks, not years.

And the honest framing: **at that target, reporting is not the first thing that breaks.**
Intake costs about 300 round trips per order today, which at 12 to 115 orders a second is
3,600 to 34,500 queries a second before anyone opens a report. The projection refresh job
already fails to complete on the demo company. Both are measured, both are spec 181's
subject. Reporting reads are bounded, cancellable and the easiest part to protect.

### The concrete finding: the indexes are not there yet

None of the node tables carries a composite index for the shape a report actually uses:

| Table | Indexes today |
|---|---|
| `document` | `tenant_id` single column; unique `(tenant_id, id)`; unique `(tenant_id, source_record_id, type)` |
| `document_line` | `tenant_id` single column; unique `(tenant_id, id)`; unique `(tenant_id, document_id, source_line_id)` |
| `movement`, `ledger_entry`, `settlement_allocation`, `party` | `tenant_id` single column only |

A question like "revenue by month for this year" filters `tenant_id` and a date range and
reads three columns. Today that is an index scan on `tenant_id` followed by a heap fetch
per row. At 250,000 orders in a year that is seconds, and the fix is not architectural:

    (tenant_id, ordered_at) INCLUDE (gross_amount, currency, party_id)   on document
    (tenant_id, document_id) INCLUDE (item_id, gross_amount, quantity)   on document_line
    (tenant_id, party_id, ordered_at)                                    on document

A covering index turns that multi-second scan into tens of milliseconds. **Estimate**, but
a well-understood one, and it is the highest-leverage single change available. It belongs
in the first slice as measured work, not as speculation.

### Per-tenant thresholds

At the target's upper end — 1,000 orders a day — one company accumulates roughly 250,000
orders, 600,000 order lines and a million ledger entries **per year** (estimate, from
about 20 rows per order in spec 181).

| Rows per node, per tenant | Behaviour | What it needs |
|---|---|---|
| under 100,000 | Everything is fast, indexes barely matter | Nothing. Most tenants, for years. |
| 100,000 – 1 million | Selective questions stay fast; full-period aggregates become visible | The covering indexes above |
| 1 – 10 million | Full-year unselective aggregates reach seconds | Measured query shape, then a materialised monthly rollup for dashboard questions |
| over 10 million | A single tenant's slice is a large table | Time partitioning within the tenant, or a derived projection. This is where the escalation ladder in `engine-comparison.md` starts. |

A tenant reaches the third band after roughly four years at the top of the target range,
or immediately on import of an existing company's history — which is the more likely way
it happens, and worth testing with the scale fixture tooling before a customer does it.

### Cluster thresholds

The total matters through memory and maintenance, not through the query plan.

| Total rows in a node table | What changes |
|---|---|
| under 100 million | An unpartitioned table with the right indexes is unremarkable |
| 100 million – 1 billion | Indexes stop fitting in cache; B-tree depth grows; autovacuum and index bloat become operational work |
| over 1 billion | A single unpartitioned table is painful to maintain — index rebuilds, vacuum windows, backup time |

At 20 to 200 million rows a day across all tenants, `document_line` crosses a billion rows
somewhere between one and two months of full-target operation. Partitioning is therefore a
question of months at target load, not years, and it is spec 181's to answer.

One genuinely good property falls out of this design: **the compiler emits `tenant_id` on
every node of every statement, always.** Hash partitioning by tenant therefore prunes
perfectly for every reporting query, with no query rewriting and no exceptions to audit.
A design where users write their own SQL could not promise that.

### What this design itself costs

| Mechanism | Cost | Note |
|---|---|---|
| Folding a measure to its grain across a fan-out | Roughly 1.5 to 3× the naive aggregate (**estimate**) | It is the cost of being right; the naive version returns a wrong number |
| Independent branches (order against invoice against settlement) | Linear in the number of branches | Three scans, not a multiplicative join — that is the point |
| Recursive traversal | Depth times branching factor | Trivial for `location`; the case to watch is a future bill of materials, where a closure table is the known answer |
| Declaration lookup and validation | Negligible, in process | Loaded once, not per query |

### The lesson from this repository's own numbers

Every large slowdown measured here so far was query *shape*, not data volume:

| Case | Before | After |
|---|---|---|
| All 35 exception classes | 229 s, whole-tenant reads | about 2 s, 68 queries |
| `payments` builder, 2,000-order fixture | 234.6 s, 11,227 queries | 0.6 s, 10 queries |
| Aging register | 26.6 s | 0.4 s |
| Attention register, spec 180 | — | 42 – 81 ms |

An eleven-thousand-query builder is what a naive per-row implementation produces, and it
is the failure mode this compiler could most easily reproduce. So the fixtures assert it
directly: **a traversal emits exactly one statement**, and the test records the query
count alongside the result. Correctness tests that do not count queries would have passed
on every one of the rows above.

Measure on a quiet machine, and compare baseline and change back to back — a background
test run once made a 2.8 second seed look like 25 seconds here.
