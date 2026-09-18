# Large-Tenant Register Benchmark Result

- Outcome: **PASSED**
- Revision: `d621b6f3cf289508ac239eccc0624a169763dbaf`
- Schema revision: `0064_analysis_document_indexes`
- Profile: `full`
- Business date: `2026-09-01`
- Orders: `20000`
- PostgreSQL: `17.10`
- Tested-content SHA-256: `45b76bd16d8e129bc5245cd97a8d570da568d76f17e0510b625b9b4e36a48fa6`

## Dataset cardinalities

| Record family | Count |
|---|---:|
| Source Records | 20000 |
| Documents | 56000 |
| Document Lines | 39999 |
| Commitments | 39999 |
| Items | 150 |
| Reservations | 140 |
| Movements | 150 |
| Ledger Entries | 72000 |
| Projection Rows | 472447 |
| Orders | 20000 |

## Cases

| Family | Outcome | Duration (ms) | Rows / total |
|---|---|---:|---:|
| Orders | passed | 1963.994 | 50 / 20000 |
| Commitments | passed | 1296.118 | 50 / 39999 |
| Inventory | passed | 163.543 | 50 / 150 |
| Reservations | passed | 69.317 | 50 / 140 |
| Movements | passed | 142.793 | 50 / 150 |
| Open items | passed | 1248.653 | 50 / 20000 |
| Payments | passed | 1353.869 | 50 / 16000 |
| Journal | passed | 1464.935 | 50 / 72000 |
| Documents | passed | 684.542 | 50 / 56000 |

## Canonical derivations

What analysis pays at request time. A register case above reads a
projection; these are the derivations a projection is built from, and
they run per question.

| Derivation | Duration (ms) | Statements | Rows | Per input (µs) |
|---|---:|---:|---:|---:|
| `financial_open_items` | 2725.7 | 8 | 20000 | 136 |
| `aging_register` | 3032.9 | 9 | 20000 | 152 |
| `party_balance_rows.customer` | 4141.3 | 13 | 1 | 207 |
| `party_balance_rows.supplier` | 3006.0 | 13 | 0 | 150 |
| `inventory_rows` | 30.6 | 4 | 150 | — |
| `inventory_detail_rows` | 18.7 | 7 | 150 | — |

## Limitations

- Durations are observations for the recorded environment, not universal latency guarantees.
- This result proves bounded reads at recorded cardinality, not ingestion throughput or concurrent production capacity.
- Initial projection construction is excluded from register timings and remains future capacity-work evidence, not a proven production throughput path.
