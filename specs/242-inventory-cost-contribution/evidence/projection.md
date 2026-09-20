# Exploratory projection measurements

Generated from projection.json; not an architecture qualification.

| Workload | Samples | p95 | Budget |
|---|---:|---:|---:|
| order | 200 | 2.47 ms | 500 ms |
| tool | 200 | 3.38 ms | 3000 ms |
| inventory | 200 | 7.49 ms | 2000 ms |
| monthly | 200 | 89.95 ms | 3000 ms |
| attention | 200 | 387.99 ms | 2000 ms |

Reconstruction seconds: 16.967, 20.396, 19.453.
Late receipt refresh: 30 samples, p95 217.57 ms; 3,000 affected issue rows.

Two tenants, each 100,000 orders, 10,000 items, 1,000,000 movements, 1,000,000 cost components, 1,000,000 attribution parts and 600,000 matching parts.

Qualification remains false for the limitations recorded in the JSON.
