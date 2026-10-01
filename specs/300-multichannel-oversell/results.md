# Results: Peak Intake (spec 300 FR-003, journey L07)

Measured on 2026-10-01 at commit `ced61bc1`, with `benchmarks/peak_intake` on a disposable local PostgreSQL 17.10 database. Machine: macOS arm64, 8 cores; Python 3.12.4. Each run used a fresh database migrated to head, 10,000 Shopify order payloads (1–2 lines, 200 items, seed 300), and stock planned at 80 % of demand.

| Run | Store 10,000 payloads | Work import jobs | Orders/s | Failed | Reserve 15,008 promises (4 connections) |
|---|---|---|---|---|---|
| 1 process | 196 s | **404 s** | 24.7 | 0 | 224 s (60 ms each per connection) |
| 4 processes | 100 s | **226 s** | 44.3 | 0 | 201 s (54 ms each per connection) |

**Target**: 10,000 orders within two hours (7,200 s). One process interprets them in under seven minutes, about 18 times faster than needed. L07's throughput holds.

Invariants held in both runs:
- 10,000 sales orders, each interpreted exactly once;
- every import job completed;
- no item reserved beyond its stock;
- 3,080 and 3,082 promises got less than they asked for once stock ran out;
- `item_oversold` reported all 200 items with exactly the demand that stock could not cover.

## Findings

- **Parallel workers repeat each other's work.** `process_pending_import_jobs` selects pending jobs without `SKIP LOCKED`, so four processes take the same batches. Each waits on the job row lock and then returns the completed result. They reported 34,101 completions for 10,000 jobs. Throughput still rose 1.8× and every order was interpreted once, so this is waste, not a defect; a follow-up can claim jobs with `SKIP LOCKED` as the scheduled-job queue already does.
- **Storing the payloads takes about as long as interpreting them** with one process (196 s against 404 s), because each webhook call commits on its own. It is well inside the target.
- **Reservations take about 55–60 ms each per connection.** All connections serialize on the tenant delivery lock, so four connections are barely faster than one would be. 15,008 promises take under four minutes.
- **The spec 181 figure (1.4–3.5 orders/s) measured the Demo Data order-to-cash path** with its invoice and payment. Shop intake alone, measured here, is an order of magnitude faster.
