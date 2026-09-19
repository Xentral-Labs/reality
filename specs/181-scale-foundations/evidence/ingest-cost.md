# Ingest Cost Measurement

- Revision: `e17606a3b35f2f125a11a833d1f400f36f05ac50`
- PostgreSQL: `17.10`
- Python: `3.12.4` on `macOS-27.0-arm64-arm-64bit`

## One order to cash, as the company grows

Two numbers per step. **Interpreting** is what a real intake pays for one
record: `enqueue_source` and `process_import_job_bound`, the path SC-001 is
about. **Sweep** is the whole scheduler occurrence, which for a synthetic
company also carries the demo generator's selection, throttle and idempotency
work — cost no customer's company runs.

| Orders before | Step | Records | Interpreting | Sweep | ms (interp./sweep) | Largest repeated reads |
|---:|---|---:|---:|---:|---:|---|
| 0 | order | 1 | 48 | 140 | 1083 / 2609 | `source_record` ×58, `playground_run` ×11, `tenant` ×8, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 0 | invoice | 1 | 69 | 164 | 3107 / 3811 | `source_record` ×62, `playground_run` ×11, `tenant` ×11, `business_event` ×8, `scheduled_job_run` ×7, `document` ×7 |
| 0 | payment | 1 | 106 | 201 | 665 / 1018 | `source_record` ×62, `tenant` ×14, `document` ×14, `ledger_reversal` ×12, `playground_run` ×11, `business_event` ×10 |
| 502 | order | 1 | 48 | 140 | 74 / 189 | `source_record` ×58, `playground_run` ×11, `tenant` ×8, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 502 | invoice | 1 | 69 | 164 | 105 / 259 | `source_record` ×62, `playground_run` ×11, `tenant` ×11, `business_event` ×8, `scheduled_job_run` ×7, `document` ×7 |
| 502 | payment | 1 | 108 | 203 | 182 / 428 | `source_record` ×62, `tenant` ×14, `document` ×14, `ledger_reversal` ×13, `playground_run` ×11, `business_event` ×10 |
| 1500 | order | 1 | 48 | 140 | 18 / 81 | `source_record` ×58, `playground_run` ×11, `tenant` ×8, `business_event` ×8, `scheduled_job_run` ×7, `demo_data_connection` ×5 |
| 1500 | invoice | 1 | 69 | 164 | 22 / 136 | `source_record` ×62, `playground_run` ×11, `tenant` ×11, `business_event` ×8, `scheduled_job_run` ×7, `document` ×7 |
| 1500 | payment | 1 | 108 | 203 | 121 / 227 | `source_record` ×62, `tenant` ×14, `document` ×14, `ledger_reversal` ×13, `playground_run` ×11, `business_event` ×10 |

Queries per order to cash grow **1.01×** from the smallest measured company to the largest. SC-001 allows 1.20.

## Where the interpreting time went

Only the product's own span. A step whose statement count stays flat while its time grows has one query reading more rows, and this names it.

| Orders before | Step | ms | Runs | Span | Statement |
|---:|---|---:|---:|---|---|
| 0 | order | 1055 | 57 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 0 | order | 162 | 1 | interpreting | `UPDATE source_stream SET current_source_record_id=%(current_source_record_id)s::VARCHAR WHERE source_stream.id = %(source_stream_id)s::VARCHAR` |
| 0 | invoice | 449 | 5 | interpreting | `SELECT tenant.id FROM tenant WHERE tenant.id = %(id_1)s::VARCHAR FOR UPDATE` |
| 0 | invoice | 430 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 0 | payment | 230 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 0 | payment | 81 | 13 | interpreting | `SELECT document.id, document.tenant_id, document.source_record_id, document.type, document.number, document.party_id, document.currency, document.gros` |
| 502 | order | 63 | 57 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 502 | order | 10 | 11 | both | `SELECT playground_run.id, playground_run.tenant_id, playground_run.owner_user_id, playground_run.preset_key, playground_run.sandbox_kind, playground_r` |
| 502 | invoice | 59 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 502 | invoice | 15 | 2 | interpreting | `SELECT finance_state.id, finance_state.tenant_id, finance_state.revision FROM finance_state WHERE finance_state.tenant_id = %(tenant_id_1)s::VARCHAR F` |
| 502 | payment | 95 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 502 | payment | 24 | 9 | interpreting | `SELECT ledger_entry.id, ledger_entry.tenant_id, ledger_entry.posting_group_id, ledger_entry.account_id, ledger_entry.party_id, ledger_entry.amount, le` |
| 1500 | order | 15 | 57 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 1500 | order | 3 | 11 | both | `SELECT playground_run.id, playground_run.tenant_id, playground_run.owner_user_id, playground_run.preset_key, playground_run.sandbox_kind, playground_r` |
| 1500 | invoice | 15 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 1500 | invoice | 4 | 11 | both | `SELECT playground_run.id, playground_run.tenant_id, playground_run.owner_user_id, playground_run.preset_key, playground_run.sandbox_kind, playground_r` |
| 1500 | payment | 53 | 1 | interpreting | `SELECT ledger_reversal.original_posting_group_id FROM ledger_reversal WHERE ledger_reversal.tenant_id = %(tenant_id_1)s::VARCHAR AND ledger_reversal.o` |
| 1500 | payment | 20 | 9 | interpreting | `SELECT ledger_entry.id, ledger_entry.tenant_id, ledger_entry.posting_group_id, ledger_entry.account_id, ledger_entry.party_id, ledger_entry.amount, le` |

## Where the sweep time went

Selection, throttle and idempotency around the interpreting. For a synthetic company this is the demo generator, which no customer's company runs — listing it beside the product's own work is how a demo throttle once looked like an intake problem.

| Orders before | Step | ms | Runs | Span | Statement |
|---:|---|---:|---:|---|---|
| 0 | order | 1055 | 57 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 0 | order | 132 | 11 | both | `SELECT playground_run.id, playground_run.tenant_id, playground_run.owner_user_id, playground_run.preset_key, playground_run.sandbox_kind, playground_r` |
| 0 | invoice | 430 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 0 | invoice | 153 | 3 | sweep | `SELECT CASE WHEN (import_job.status = %(status_1)s::VARCHAR AND (EXISTS (SELECT interpretation_outcome.id FROM interpretation_outcome WHERE interpreta` |
| 0 | payment | 230 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 0 | payment | 45 | 11 | both | `SELECT playground_run.id, playground_run.tenant_id, playground_run.owner_user_id, playground_run.preset_key, playground_run.sandbox_kind, playground_r` |
| 502 | order | 63 | 57 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 502 | order | 23 | 2 | sweep | `SELECT CASE WHEN (import_job.status = %(status_1)s::VARCHAR AND (EXISTS (SELECT interpretation_outcome.id FROM interpretation_outcome WHERE interpreta` |
| 502 | invoice | 59 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 502 | invoice | 37 | 3 | sweep | `SELECT CASE WHEN (import_job.status = %(status_1)s::VARCHAR AND (EXISTS (SELECT interpretation_outcome.id FROM interpretation_outcome WHERE interpreta` |
| 502 | payment | 95 | 59 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 502 | payment | 52 | 3 | sweep | `SELECT CASE WHEN (import_job.status = %(status_1)s::VARCHAR AND (EXISTS (SELECT interpretation_outcome.id FROM interpretation_outcome WHERE interpreta` |
| 1500 | order | 39 | 2 | sweep | `SELECT CASE WHEN (import_job.status = %(status_1)s::VARCHAR AND (EXISTS (SELECT interpretation_outcome.id FROM interpretation_outcome WHERE interpreta` |
| 1500 | order | 15 | 57 | both | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 1500 | invoice | 55 | 3 | sweep | `SELECT CASE WHEN (import_job.status = %(status_1)s::VARCHAR AND (EXISTS (SELECT interpretation_outcome.id FROM interpretation_outcome WHERE interpreta` |
| 1500 | invoice | 21 | 1 | sweep | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |
| 1500 | payment | 53 | 3 | sweep | `SELECT CASE WHEN (import_job.status = %(status_1)s::VARCHAR AND (EXISTS (SELECT interpretation_outcome.id FROM interpretation_outcome WHERE interpreta` |
| 1500 | payment | 19 | 1 | sweep | `SELECT source_record.id, source_record.tenant_id, source_record.source_system, source_record.source_type, source_record.external_id, source_record.pay` |

## Limitations

- Query counts mean the same on any host; the milliseconds do not.
- One intake process, no competing worker: this is the cost of the path, not the throughput of a deployment.
- SC-001 is a statement about a curve. A single checkpoint cannot answer it, and the ratio is only as good as the largest size measured.
