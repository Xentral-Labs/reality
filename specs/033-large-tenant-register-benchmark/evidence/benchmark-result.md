# Large-Tenant Register Benchmark Result

- Outcome: **PASSED**
- Revision: `dc3973310e6be23c86e32c3b420f9fd830952b4d`
- Schema revision: `0029_ledger_reversals`
- Profile: `full`
- Business date: `2026-09-01`
- Orders: `10000`
- PostgreSQL: `17.10`
- Tested-content SHA-256: `3408c653c6db15469ed797fd6953f161735db6686f1380b841e736b6c00df7b4`

## Dataset cardinalities

| Record family | Count |
|---|---:|
| Source Records | 10000 |
| Documents | 10240 |
| Document Lines | 19999 |
| Commitments | 19999 |
| Items | 150 |
| Reservations | 140 |
| Movements | 150 |
| Ledger Entries | 480 |
| Projection Rows | 111867 |
| Orders | 10000 |

## Cases

| Family | Outcome | Duration (ms) | Rows / total |
|---|---|---:|---:|
| Orders | passed | 577.595 | 50 / 10000 |
| Commitments | passed | 128.512 | 50 / 19999 |
| Inventory | passed | 48.684 | 50 / 150 |
| Reservations | passed | 26.377 | 50 / 140 |
| Movements | passed | 22.854 | 50 / 150 |
| Open items | passed | 28.976 | 50 / 120 |
| Payments | passed | 41.576 | 50 / 120 |
| Journal | passed | 17.414 | 50 / 480 |
| Documents | passed | 97.056 | 50 / 10240 |

## Limitations

- Durations are observations for the recorded environment, not universal latency guarantees.
- This result proves bounded reads at recorded cardinality, not ingestion throughput or concurrent production capacity.
- Initial projection construction is excluded from register timings and remains future capacity-work evidence, not a proven production throughput path.

## Accepted evidence review

- All nine required register families passed with a default page of 50 and a hard
  maximum of 100 rows.
- Repeated runs over the completed dataset produced identical semantic results,
  including stable adjacent pages and complete filtered totals.
- Zero-match, invalid/minimum/maximum page-size, categorical, date and Decimal filter
  cases passed. Every captured materialization query was tenant-scoped and bounded.
- The distinguishable control tenant has records in every covered family and no
  control-tenant sentinel or row appeared in primary-tenant results.
- Source payload hashes and version identities, shortest Document/Line/Commitment
  links, and balanced ledger posting groups passed dataset validation.

## Validation gates

- Focused benchmark/read-model/API tests: `10 passed`.
- Complete PostgreSQL backend suite: `263 passed, 7 skipped` after rebasing onto the
  current `main` and running the exact CI command without a custom PYTHONPATH.
- Ruff on all changed Python paths: passed.
- Canonical Pydantic v2 result validation and exact exported-schema comparison: passed.
- Specification policy: passed.
