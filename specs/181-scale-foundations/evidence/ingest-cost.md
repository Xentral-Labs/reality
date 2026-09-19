# Ingest Cost Measurement

- Revision: `2315b92a8874201f3078163d28915caca79a9bde`
- PostgreSQL: `17.10`
- Python: `3.12.4` on `macOS-27.0-arm64-arm-64bit`

## One order to cash, as the company grows

| Orders before | Step | Records | Queries each | SQL ms each | Largest repeated reads |
|---:|---|---:|---:|---:|---|
| 0 | order | 1 | 140 | 95 | `source_record` ×58, `playground_run` ×11, `tenant` ×8, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 0 | invoice | 1 | 164 | 130 | `source_record` ×62, `playground_run` ×11, `tenant` ×11, `business_event` ×8, `scheduled_job_run` ×7, `document` ×7 |
| 0 | payment | 1 | 201 | 136 | `source_record` ×62, `tenant` ×14, `document` ×14, `ledger_reversal` ×12, `playground_run` ×11, `business_event` ×10 |
| 500 | order | 4 | 74 | 24 | `source_record` ×76, `business_event` ×32, `tenant` ×29, `import_job` ×20, `playground_run` ×17, `party` ×14 |
| 500 | invoice | 4 | 96 | 34 | `source_record` ×86, `tenant` ×41, `business_event` ×32, `document` ×28, `finance_state` ×24, `import_job` ×20 |
| 500 | payment | 4 | 134 | 63 | `source_record` ×85, `document` ×55, `tenant` ×53, `ledger_reversal` ×52, `business_event` ×40, `ledger_entry` ×40 |
| 1500 | order | 3 | 81 | 40 | `source_record` ×70, `business_event` ×24, `tenant` ×22, `playground_run` ×15, `import_job` ×15, `party` ×11 |
| 1500 | invoice | 3 | 103 | 60 | `source_record` ×78, `tenant` ×31, `business_event` ×24, `document` ×21, `finance_state` ×18, `playground_run` ×15 |
| 1500 | payment | 3 | 142 | 97 | `source_record` ×78, `document` ×42, `tenant` ×40, `ledger_reversal` ×39, `business_event` ×30, `ledger_entry` ×30 |
| 3001 | order | 1 | 140 | 98 | `source_record` ×58, `playground_run` ×11, `tenant` ×8, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 3001 | invoice | 1 | 164 | 187 | `source_record` ×62, `playground_run` ×11, `tenant` ×11, `business_event` ×8, `scheduled_job_run` ×7, `document` ×7 |
| 3001 | payment | 1 | 203 | 232 | `source_record` ×62, `tenant` ×14, `document` ×14, `ledger_reversal` ×13, `playground_run` ×11, `business_event` ×10 |

Queries per order to cash grow **1.0×** from the smallest measured company to the largest. SC-001 allows 1.20.

## Limitations

- Query counts mean the same on any host; the milliseconds do not.
- One intake process, no competing worker: this is the cost of the path, not the throughput of a deployment.
- SC-001 is a statement about a curve. A single checkpoint cannot answer it, and the ratio is only as good as the largest size measured.
