# V3 capped mixed-load measurements

Supplemental exploration, not exact reference-host or product qualification.

| Surface | Ready read-only p95 | Mixed p95 | Current mixed responses | Budget |
|---|---:|---:|---:|---:|
| order | 2.81 ms | 29.33 ms | 129/200 | 500 ms |
| tool | 2.54 ms | 22.18 ms | 128/200 | 3000 ms |
| inventory | 5.04 ms | 34.51 ms | 129/200 | 2000 ms |
| monthly | 92.82 ms | 89.66 ms | 129/200 | 3000 ms |
| attention | 583.21 ms | 126.89 ms | 129/200 | 2000 ms |

Mixed tool timings include 72 explicit not-ready refusals; they are not 200 ready answers.
Display responses retain a stale marker while the tenant-wide generation is pending.

31 late changes sustained one commit per second; publication p95 515.52 ms, maximum 712.14 ms.
All 609,000 contribution observations and 10,000 inventory pools matched complete reconstruction.
Reconstruction including publication: 19.715, 20.602, 19.599 seconds.

Each of two tenants retains 1,000,000 movements: 291,000 receipts, 9,000 receipt-family returns,
600,000 issues and 100,000 transfers. Fixed component/attribution/matching counts remain unchanged.

The preliminary input-rate failure was corrected; final measured budgets pass.
Exact reference-host, complete cold-cache, product worker/adapter and live-availability gates remain open.
