# Data Model: Dunning Run and Escalation

No column is added to existing tables. Levels, eligibility and "ready for collection" are
derived at read time (DR-002).

## dunning_schedule_level (new)

The company's stated rule for one dunning level. Replaced as a whole by a confirmed
`finance.dunning.schedule.set`; history lives in the source records.

| Column | Type | Rule |
|---|---|---|
| `tenant_id` | string | FK `tenant.id`; part of the primary key |
| `id` | string | opaque, prefix `dsl` |
| `level` | integer | `BETWEEN 1 AND 3`; unique per tenant |
| `wait_days` | integer | `>= 0`; level 1: days overdue, levels 2 and 3: days since the last notice |
| `fee_amount` | numeric(18,4) | `>= 0`; stated fixed fee |
| `source_record_id` | string | composite FK `source_record`; the confirmed request |
| `updated_at` | UTC timestamp | |

A schedule is complete only with all three levels; the command refuses anything else
(`dunning_schedule_incomplete`).

## collection_handover (new)

A confirmed decision to hand a customer's items to collection.

| Column | Type | Rule |
|---|---|---|
| `tenant_id` | string | FK `tenant.id`; part of the primary key |
| `id` | string | opaque, prefix `col` |
| `party_id` | string | composite FK `party`; the customer |
| `handover_date` | date | stated |
| `reason` | text | not empty |
| `source_record_id` | string | composite FK `source_record`; unique |
| `created_at` | UTC timestamp | |

## collection_handover_invoice (new)

| Column | Type | Rule |
|---|---|---|
| `tenant_id` | string | part of the primary key |
| `id` | string | opaque, prefix `chi` |
| `handover_id` | string | composite FK `collection_handover` |
| `invoice_id` | string | composite FK `document`; unique per tenant (an item is handed over once) |

## Reused

- `dunning_notice`, `dunning_notice_invoice`, `dunning_fee_charge` documents and fee postings
  (spec 247), unchanged.
- `party_hold` with the new reason code `collection` in `HOLD_REASONS`.
- `source_record` with `source_system = "internal_dunning"` and record types
  `dunning_schedule`, `dunning_run`, `dunning_notice`, `collection_handover`.

## Events

| Event | Subject | Payload |
|---|---|---|
| `dunning.schedule_set` | `tenant` | levels with wait days and fees |
| `dunning.run_confirmed` | `source_record` (the run) | run date, notice ids, skipped items with codes |
| `dunning.notice_recorded` | `dunning_notice` | unchanged; run notices name the run |
| `dunning.collection_handover_recorded` | `collection_handover` | invoice ids, reason, hold id |
| `party.delivery_hold_placed` | `party` | unchanged, reason `collection` |

## Migration

`0102_dunning_run`: the three tables with composite tenant FKs and FK indexes. No backfill.
