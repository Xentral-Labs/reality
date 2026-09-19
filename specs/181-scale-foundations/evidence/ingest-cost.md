# Ingest Cost Measurement

- Revision: `aa10f4fc97afa137a145bee96a877a9ad526c0d0`
- PostgreSQL: `17.10`
- Python: `3.12.4` on `macOS-27.0-arm64-arm-64bit`

## One order to cash, as the company grows

| Orders before | Step | Records | Queries each | SQL ms each | Largest repeated reads |
|---:|---|---:|---:|---:|---|
| 0 | order | 1 | 158 | 54 | `source_record` ×58, `playground_run` ×20, `tenant` ×17, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 0 | invoice | 2 | 140 | 48 | `source_record` ×70, `tenant` ×42, `playground_run` ×34, `business_event` ×16, `document` ×14, `finance_state` ×12 |
| 0 | payment | 2 | 229 | 102 | `source_record` ×78, `tenant` ×73, `playground_run` ×51, `document` ×35, `business_event` ×28, `ledger_reversal` ×25 |
| 64 | order | 2 | 115 | 289 | `source_record` ×64, `tenant` ×34, `playground_run` ×32, `business_event` ×16, `import_job` ×10, `party` ×8 |
| 64 | invoice | 2 | 208 | 183 | `source_record` ×78, `tenant` ×68, `playground_run` ×49, `document` ×28, `business_event` ×26, `finance_state` ×21 |
| 64 | payment | 2 | 230 | 222 | `source_record` ×78, `tenant` ×73, `playground_run` ×51, `document` ×35, `business_event` ×28, `ledger_reversal` ×26 |
| 183 | order | 1 | 158 | 179 | `source_record` ×58, `playground_run` ×20, `tenant` ×17, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 183 | invoice | 2 | 140 | 100 | `source_record` ×70, `tenant` ×42, `playground_run` ×34, `business_event` ×16, `document` ×14, `finance_state` ×12 |
| 183 | payment | 2 | 230 | 208 | `source_record` ×78, `tenant` ×73, `playground_run` ×51, `document` ×35, `business_event` ×28, `ledger_reversal` ×26 |
| 401 | order | 1 | 158 | 217 | `source_record` ×58, `playground_run` ×20, `tenant` ×17, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 401 | invoice | 2 | 414 | 603 | `tenant` ×146, `source_record` ×101, `playground_run` ×94, `document` ×69, `business_event` ×56, `ledger_reversal` ×52 |
| 401 | payment | 2 | 178 | 205 | `source_record` ×68, `tenant` ×52, `playground_run` ×38, `document` ×26, `ledger_reversal` ×26, `business_event` ×20 |

Queries per order to cash grow **1.42×** from the smallest measured company to the largest. SC-001 allows 1.20.

## Limitations

- Query counts mean the same on any host; the milliseconds do not.
- One intake process, no competing worker: this is the cost of the path, not the throughput of a deployment.
- SC-001 is a statement about a curve. A single checkpoint cannot answer it, and the ratio is only as good as the largest size measured.
