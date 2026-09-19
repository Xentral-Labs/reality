# Research: Scale Foundations — measurements of 2026-09-12

**Language**: English

All figures from one host process against the local Docker stack (PostgreSQL 17, api on
`main` + features 179/180), host-to-container round trip roughly one millisecond per query.
Absolute times are environment-bound; query counts and growth are not.

## Target

| Quantity | Value |
| --- | --- |
| Companies | 10,000 |
| Orders per company per day | 100 – 1,000 |
| Orders per day, total | 1 – 10 million |
| Orders per second, average | 12 – 115 |
| Rows per day at ~20 rows per order | 20 – 200 million |
| Source payloads per year at ~5 KB per order | 2 – 18 TB |

## 1. Ingest cost per order (owner's dedicated point)

Fresh Sandbox company, Demo Data connected, orders through `enqueue_source` and the demo
interpreters, invoices and payments after the order-to-cash plan (feature 168). Profile of 20
orders on a 200-order company:

| Step | Queries | SQL time | Largest repeated reads |
| --- | --- | --- | --- |
| Order | 70 | 150 ms | `tenant` ×17, `playground_run` ×12, `source_record` ×4, `business_event` count ×4 |
| Invoice | 93 | 177 ms | `tenant` ×21, `playground_run` ×13, `document` ×6, `source_record` ×6 |
| Payment | 138 | 333 ms | `tenant` ×26, `playground_run` ×15, `ledger_reversal` ×15, `document` ×12.6, `ledger_entry` ×11 |
| Order-to-cash total | ~300 | ~660 ms | |

Roughly a third of every step is the authority check (`_require_business_mutation` →
`require_core_operation` → `get_tenant` / `require_playground_run`) issued per service call.
The payment step walks reversals, entries and documents per candidate while matching.

Throughput of the single intake process on the 100,000-order fixture (`ten_95dfab078f`):

| Orders recorded | Orders / s | Queries / order |
| --- | --- | --- |
| 200 | 3.5 | 301 |
| 400 | 3.0 | 302 |
| 600 | 1.9 | 302 |

| 800 | 1.4 | 302 |

The query count per order is flat; the time per order rises. Cause, read from the code:
`payment_intake.payment_candidates` iterates **every** sales invoice of the paying customer in
that currency, open or long paid (`select(Document)` without a status predicate), and calls
`core.open_invoice_amount` for each, which in turn reads the control entry, the reversal, the
account balance and `active_settlement_allocations` — the latter loads every allocation of
the company. One payment therefore costs O(invoices of the customer × allocations of the
company); with a skewed customer pool a few buyers carry most orders and the cost climbs with
every order recorded. Sampling `pg_stat_activity` during the run shows `ledger_entry` row
reads as the most frequent active statement. The worker's minute-level projection refresh of
the same company competes on the database and adds to the slope. Later checkpoints (1k, 3k,
10k, 30k, 100k) are appended below as the run completes.

### Measured again, 2026-09-19, by a tool that stays

The numbers above came from scripts in a scratch directory. They are gone, which is
why nobody could say whether the ingest path had improved. FR-006 asks for the
measurement as a maintained tool; it is now `packages/reality-core/benchmarks/ingest_cost`
and its record is [evidence/ingest-cost.json](evidence/ingest-cost.json).

| Orders already recorded | Queries per order to cash | SQL ms |
| --- | --- | --- |
| 0 | 527 | 205 |
| 64 | 553 | 694 |
| 183 | 528 | 487 |
| 401 | 750 | 1,024 |

**Queries per order to cash grow 1.42× from the smallest measured company to the
largest. SC-001 allows 1.20.** That criterion is therefore missed today, and — for
the first time — missed measurably.

Three things this does not say. It is **not** a comparison with the September figures:
this measures a whole scheduler occurrence, including the throttle check and the
settlement scan, where the earlier profile measured the service calls inside one. It
is a new baseline on a stated method, not evidence of a regression. The SQL
milliseconds moved between 205 and 1,024 on a host that was not idle and should be
read as a shape, not a value. And the largest company measured is 401 orders, two
orders of magnitude below the target in SC-001, so the ratio is only as good as that
range — a longer run is the obvious next measurement, and the tool takes
`--checkpoints` for it.

What the per-table column still shows, unchanged since September: `tenant`,
`playground_run` and `source_record` dominate every step — 73, 51 and 78 reads in one
payment. That is the authority check issued per service call rather than per
transaction, which FR-001 names and which nothing has yet addressed.

### FR-001, first step: the authority check, 2026-09-19

The per-table column named its own fix. `require_core_operation` established the
profile's authority on every service call — `require_playground_run`, a four-table
join that deliberately re-reads, and a `Tenant` select beside it. FR-001 asks for
that once per transaction, reused by every call within it.

It is now established once and remembered, keyed by session, transaction, tenant,
run and user. The answer is forgotten the moment that transaction writes a `Tenant`
or a `PlaygroundRun` — the two records it rests on — and a refusal is never
remembered, only a permission. Both are held by tests in
`tests/test_operational_read_performance.py`.

Measured with the tool above, same method, same host:

| Step | Queries before | Queries after | `tenant` | `playground_run` |
| --- | --- | --- | --- | --- |
| Order | 158 | 140 | 17 → 8 | 20 → 11 |
| Invoice | 140 | 118 | 42 → 21 | 34 → 13 |
| Payment | 229 | 168 | 73 → 33 | 51 → 15 |
| **Order to cash** | **527** | **426** | | |

Nineteen per cent fewer queries at an empty company, thirty-one per cent at sixty
orders (553 → 383). The reads that fell are exactly the ones the measurement
pointed at, which is the useful part: this was not a guess that happened to help.

What remains: `source_record` is now the largest repeated read of every step, and
`tenant` is still read from paths that do not go through the profile branch.
Neither is addressed here.

#### At three thousand orders, on a quiet host

The short run above spans 60 orders, which is not a curve. This one runs to 3,001
with the same code and nothing else on the machine; it is the record now in
[evidence/ingest-cost.json](evidence/ingest-cost.json).

| Orders already recorded | Queries per order to cash | SQL ms |
| --- | --- | --- |
| 0 | 505 | 361 |
| 500 | 304 | 122 |
| 1,500 | 326 | 197 |
| 3,001 | 507 | 516 |

**Queries per order to cash do not grow: 1.0× from the smallest company to the
largest, where SC-001 allows 1.20.** The earlier reading of 1.42× came from a
401-order span before this change and does not survive either correction.

Three honest qualifications. The middle checkpoints are lower because those sweeps
produced two records each, and a sweep's fixed cost — claiming, the throttle check,
the settlement scan — is halved when it is divided by two. The number is therefore
per record produced in a sweep, not per record in isolation, and it moves with how
many the demo profile happens to deliver. **SQL time does still grow**, 361 to 516
ms, so something is becoming dearer even where the statement count does not. And
the absolute target is far off: SC-001 asks for at most 60 reads and 100 ms for one
order to cash, and this measures 507 and 516.

So FR-001's curve criterion is met over this range and its absolute one is not.
The per-table column says where the rest sits: `source_record` ×58 to ×62 in every
step, against `tenant` ×8 to ×14 and `playground_run` ×11 now that the authority is
established once.

## 2. Whole-company derivation

Demo company `ten_de87f2e90b` (6,641 documents, 8,808 ledger entries, 2,230 open items):

| Read | Before #227 | After #227 |
| --- | --- | --- |
| `aging_register` (open items) | 26.6 s | 0.4 s |
| all 35 exception classes | 229 s | ~2 s, 68 queries |
| stored attention register (spec 180) | — | 42–81 ms |

Per builder on the same company (after #227):

| Builder | Seconds | Queries | Rows |
| --- | --- | --- | --- |
| payments | 228.3 | 18,347 | 2,293 |
| commitment_register | 14.4 | 42,214 | 2,345 |
| document_register | 9.9 | 20,927 | 6,975 |
| fulfillment_queue | 8.9 | 25,808 | 2,343 |
| fulfillment_blockers | 8.5 | 25,808 | 2,343 |
| item_supply_demand | 8.1 | 25,830 | 4 |
| timeline | 3.5 | 2,362 | 18,656 |
| exceptions | 1.0 | 69 | 2,386 |
| open_financial_items | 0.3 | 11 | 2,337 |
| journal | 0.1 | 3 | 9,278 |
| inventory, tenant_usage | 0.0 | 26 each | — |
| **all twelve** | **283.1** | | |

## 3. Refresh granularity

Feature 179 runs all twelve projections of a company in one `projections.refresh` child with a
30 s wall clock and a 20 s statement timeout. On the demo company the run ends in
`handler_timeout` and stays in `retry`; the `exceptions` projection is never published there
without the explicit maintenance refresh. Time-sensitive projections (`exceptions`,
`commitment_register`, `tenant_usage`) become eligible every 60 s for every company.

## 4. Storage shape

Not measured yet. Recorded for the storage feature: table list, current sizes of the demo
company, and the payload share of `source_record`.

## Scale fixture checkpoints (appended as they complete)

The run is stopped at 10,000 orders by owner decision (2026-09-12); the intake degradation is
established, and the payment matching is being batched before any longer run.

### 1,000 orders (`ten_95dfab078f`, 16:27 UTC; 3,004 documents, 4,008 ledger entries, 13,033 events, 990 allocations)

Intake: 1.38 orders/s at this point (3.5 at 200).

| Builder | Seconds | Queries | Rows |
| --- | --- | --- | --- |
| payments | 82.1 | 8,036 | 1,004 |
| fulfillment_blockers | 15.2 | 11,036 | 1,000 |
| item_supply_demand | 9.7 | 11,036 | 4 |
| commitment_register | 9.5 | 18,005 | 1,000 |
| fulfillment_queue | 9.1 | 11,036 | 1,000 |
| exceptions | 5.4 | 226 | 1,060 |
| document_register | 5.3 | 9,015 | 3,004 |
| timeline | 1.7 | 1,007 | 8,039 |
| journal, open_financial_items, inventory, tenant_usage | ≤ 0.2 each | | |

Exception classes together: 5.1 s, 226 queries; `overdue_receivable` 4.1 s / 167 queries for 43
rows is the only class above 0.3 s (a per-row read remains there).

### Payment matching batched (PR, branch `perf-payment-matching-reads`)

| Read | Before | After |
| --- | --- | --- |
| `payments` builder, fixture at 2,000 orders | 234.6 s, 11,227 queries | 0.6 s, 10 queries |
| `payments` builder, demo company | 228 s | 0.5 s |
| candidate search, 2 vs 12 settled invoices | grows with history | identical query count |

### Builders batched (branch `perf-projection-builder-reads`)

| Builder | 1,000 orders, before | 3,000 orders, after |
| --- | --- | --- |
| fulfillment_blockers | 15.2 s, 11,036 queries | 0.5 s, 40 |
| fulfillment_queue | 9.1 s, 11,036 | 0.7 s, 40 |
| item_supply_demand | 9.7 s, 11,036 | 0.6 s, 40 |
| commitment_register | 9.5 s, 18,005 | 0.3 s, 16 |
| document_register | 5.3 s, 9,015 | 0.7 s, 5 |
| timeline | 1.7 s, 1,007 | 0.5 s, 7 |

With #227, the payment matching branch and this one, every one of the twelve builders reads a
bounded number of times; the remaining cost is loading the company's rows once and Python, so
it still grows linearly with the company. That is the point where batching stops helping and
FR-002 (derive by change) begins.

### 3,000 orders (17:09 UTC; 9,007 documents, 12,014 ledger entries, 39,026 events, 2,971 allocations) — unbatched code

| Builder | 1,000 orders | 3,000 orders | growth for 3× data |
| --- | --- | --- | --- |
| payments | 82.1 s, 8,036 q | 548.7 s, 24,060 q | 6.7× time (superlinear: per payment × allocations) |
| commitment_register | 9.5 s, 18,005 q | 43.2 s, 54,005 q | 4.5× |
| exceptions (all classes) | 5.4 s, 226 q | 35.7 s, 589 q | 6.6× — `overdue_receivable` alone 23.5 s / 530 q (per-row settlement instants over all allocations) |
| fulfillment_blockers | 15.2 s, 11,036 q | 30.2 s, 33,036 q | 2× |
| document_register | 5.3 s, 9,015 q | 25.4 s, 27,024 q | 4.8× |
| fulfillment_queue | 9.1 s, 11,036 q | 25.2 s, 33,036 q | 2.8× |
| item_supply_demand | 9.7 s, 11,036 q | 24.8 s, 33,036 q | 2.6× |
| timeline | 1.7 s, 1,007 q | 1.3 s, 3,007 q | — |
| journal, open_financial_items, inventory, tenant_usage | ≤ 0.4 s | ≤ 0.4 s | flat (already bulk) |

The whole twelve-builder refresh at 3,000 orders: about 13 minutes on the unbatched code, against a
30 s job budget. The branches `perf-payment-matching-reads` and `perf-projection-builder-reads`
remove every per-record read named here (the `overdue_receivable` one included).

Single-process intake throughput over the run (orders per second): 200 → 3.5, 1,000 → 1.4,
2,000 → 1.5, 3,000 → 0.9, 5,000 → 1.6, 7,000 → 1.2, 9,000 → 0.8. The dips coincide with the
checkpoint measurements and the worker's projection refreshes competing on the same database; the
trend is down, consistent with the payment matcher's cost per payment growing with the customer's
invoice count.

### 10,000 orders (19:21 UTC; 30,043 documents, 40,086 ledger entries, 130,107 events, 9,908 allocations)

Same company, measured twice: with the code the run ingested on (`main` before #236) and with
`main` + #236 + the #235 branch. Row counts are identical in both columns.

| Builder | Unbatched | Batched | Rows |
| --- | --- | --- | --- |
| payments | **timeout at 900 s** | 1.3 s, 11 q | 10,043 |
| exceptions (all classes) | 259.5 s, 1,916 q | 5.6 s, 1,544 q | 10,689 |
| document_register | 112.7 s, 90,132 q | 1.7 s, 6 q | 30,043 |
| commitment_register | 95.1 s, 180,005 q | 0.9 s, 17 q | 10,000 |
| fulfillment_queue | 92.6 s, 110,036 q | 1.5 s, 41 q | 10,000 |
| item_supply_demand | 59.9 s, 110,036 q | 1.1 s, 41 q | 4 |
| fulfillment_blockers | 55.6 s, 110,036 q | 1.4 s, 41 q | 10,000 |
| timeline | 6.6 s, 10,007 q | 1.0 s, 8 q | 80,156 |
| open_financial_items | 1.0 s, 12 q | 1.2 s, 12 q | 10,000 |
| journal | 1.2 s, 4 q | 0.6 s, 4 q | 40,086 |
| inventory, tenant_usage | ≤ 0.2 s | ≤ 0.2 s | |
| **all twelve** | **> 27 min** | **≈ 17 s** | |

Within the exception classes `overdue_receivable` fell from 204 s / 1,857 queries to 1.7 s /
1,485 queries: the per-row settlement instants are now bounded to one control entry but still one
read per overdue row (508 rows) — the last per-row read in the derivation, small enough to leave
for the incremental design.

Ingest over the whole unbatched run: 10,000 orders with invoices and payments in 2 h 54 min from one
process, falling from 3.5 to 0.6–0.8 orders/s.

### Comparison run with the batched code (`ten_1bf93aeb26`, started 19:22 UTC)

Fresh company, same generator, 10,000 orders, checkpoints at 1,000 / 3,000 / 10,000.

| Orders recorded | Unbatched, orders/s | Batched, orders/s |
| --- | --- | --- |
| 200 | 3.5 | 6.0 |
| 1,000 | 1.4 | 6.1 |
| 3,000 | 0.9 | 3.5 |
| 5,000 | 1.6 | 2.7 |
| 7,000 | 1.2 | 2.2 |
| 9,000 | 0.8 | 1.5 |

Queries per order stayed at ~297 in both runs. Batching the matcher roughly doubled the
throughput at every size, but the slope is still there: the batched run took 4 h 30 min in total,
of which the stretch from 9,000 to 10,000 took 3 h 20 min while the database was blocked (the
PostgreSQL log shows `canceling statement due to lock timeout … while locking tuple in relation
"tenant"` and the checkpoint measured one class at 582 s for a single query; re-measured afterwards
the same class took 0.5 s). That stretch is an artifact of the shared local database, not of the
code, and is excluded from the curve above.

Checkpoints with the batched code (all twelve builders, seconds): 1,000 → 2.2 s; 3,000 → 4.7 s;
10,000 → 17 s (re-measured after the blocked stretch: `exceptions` 7.4 s, `payments` 1.6 s).

**What still grows per payment at 10,000 orders** (profile of the payment step, SQL time
per payment 362 ms, 135 queries):

| Statement | Per payment | Cause |
| --- | --- | --- |
| `SELECT ledger_entry.* …` ×9 | 197 ms | filtered by tenant, document and `account`; `account` and `document_id` carry no index, so each read walks the tenant's 40,000 entries (`account_balance`, `_settlement_control_entry`) |
| `SELECT ledger_reversal.original_posting_group_id … IN (…)` ×1 | 115 ms | `settlement_positions` still measures **all** invoices of the paying customer to find the open ones; the IN list is the customer's whole invoice history |
| `SELECT document …` ×12.5, `playground_run` ×15, `tenant` ×26 | 20 ms | authority and reference reads per service call |

The order step costs 27 ms and the invoice step 43 ms at this size; the payment step is the
whole remaining slope. Two fixes follow directly for the ingest feature: an index on
`ledger_entry (tenant_id, document_id)` (and `account`), and a candidate search that selects open
invoices in SQL rather than measuring the customer's history.

## Removing a company: the same missing indexes

Deleting the two 10,000-order fixture companies through the table loop
`permanently_delete_tenant` uses (every tenant-scoped table, then the tenant) took about 32
minutes each, almost all of it in foreign-key checks on columns without an index:

| Step | Rows | Time | Cause |
| --- | --- | --- | --- |
| `DELETE FROM business_event` | 130,107 | cancelled after 36 min | `business_event.causation_id` references `business_event.id` with no index: one sequential scan of the whole table per deleted row |
| same, after `CREATE INDEX ON business_event (causation_id)` | 129,903 | 3.7 s | |
| `DELETE FROM document` | 30,043 | 198 s → 52–81 s with `ix_ledger_entry_document_id` | `ledger_entry.document_id` unindexed |
| `DELETE FROM source_record` | 30,070 | 1,785 s and 1,877 s | every table that carries `source_record_id` (documents, import jobs, ledger entries, facts, parties, items…) checks referrers without an index |
| `DELETE FROM document_line` | 20,000 | 70 s | referrers of `document_line.id` unindexed |

The two indexes were created by hand in the local database first; the branch
`perf-foreign-key-indexes` turns the finding into a rule (`reality.db.core.index_foreign_keys`,
80 indexes, migration `0059_foreign_key_indexes`). The rule covers: `business_event (causation_id)`, `ledger_entry (document_id)` and an index on
every `source_record_id` and `document_line_id` foreign key. They cut the payment step's
`ledger_entry` reads and make company removal a matter of seconds.
