# Scoped live availability: capped full run

Exploratory v3 fixture, final scoped-reader source digest recorded in live-projection.json.

| Surface | Mixed p95 | Samples | Budget |
|---|---:|---:|---:|
| order | 57.23 ms | 200 | 500 ms |
| tool | 1107.49 ms | 200 | 3000 ms |
| inventory | 89.64 ms | 200 | 2000 ms |
| monthly | 192.97 ms | 200 | 3000 ms |
| attention | 265.70 ms | 200 | 2000 ms |

Live tool readiness: **200/200 current**, with 174 projection reads and 26 direct calculations.
Half the requested tool scopes target the last order in the actively changed hot pool.
Freshness is not evidence completeness; incomplete DB values remain null.

36 one-per-second changes sustained; publication p95 1.098 seconds, maximum 1.125 seconds.
All 609,000 observation rows and 10,000 inventory pools reconcile with full reconstruction.
Reconstruction plus publication: 32.641s, 30.852s, 42.494s.

Aggregate display freshness remains conservative; the live order path does not publish
or combine aggregate generations. Exact reference-host and actual product worker/adapter
qualification remain open. The tested local timing/rate budgets pass.
