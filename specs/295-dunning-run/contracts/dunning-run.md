# Contract: Dunning Run and Escalation

All tools are tenant-scoped and shared by Web, MCP/Chat and CLI. Commands run through the
finance change proposal and need confirmation by an authenticated active owner; reads do not.
Amounts are decimal strings; dates are ISO.

## Read `finance_dunning_schedule`

Input: `{}`. Output:

```json
{"revision": 7, "levels": [{"level": 1, "wait_days": 7, "fee_amount": "0.0000"}, ...],
 "source_record_id": "src_..."}
```

`levels` is empty when no schedule is set.

## Command `finance.dunning.schedule.set`

Input: `{"expected_revision": 7, "levels": [{"level": 1, "wait_days": 7, "fee_amount": "0"},
{"level": 2, "wait_days": 14, "fee_amount": "5"}, {"level": 3, "wait_days": 14, "fee_amount": "10"}]}`

Refusals: `dunning_schedule_incomplete` (not exactly levels 1, 2, 3),
`dunning_schedule_value_invalid` (waiting days not a whole number from 0 to 3650, or a fee below 0,
above 1,000,000 or with more than four decimals; booleans and floats are not coerced),
`finance_account_default_missing` (the existing code: a positive fee without a `dunning_fee_revenue` default), `dunning_preview_stale` (the finance revision changed).

Setting the schedule raises the finance revision, so a run prepared under the old schedule is stale.

## Read `finance_dunning_run_context`

Input: `{"run_date": "2026-10-01", "party_ids": ["pty_..."]}` (`party_ids` optional).

Output:

```json
{"revision": 7, "run_date": "2026-10-01", "party_ids": [],
 "schedule_source_record_id": "src_...",
 "notices": [{"party_id": "pty_...", "currency": "EUR", "level": 2, "fee_amount": "5.0000",
   "items": [{"invoice_id": "doc_...", "number": "INV-1", "open": "100.00",
              "days_overdue": 30, "previous_notice_id": "dun_...",
              "previous_level": 1, "previous_notice_date": "2026-09-10", "wait_days": 14}]}],
 "ready_for_collection": [{"invoice_id": "doc_...", "party_id": "pty_...",
                           "last_notice_id": "dun_...", "open": "80.00"}],
 "left_out": [{"invoice_id": "doc_...", "party_id": "pty_...", "code": "credit_available"},
              {"invoice_id": "doc_...", "code": "waiting", "level": 2, "wait_days": 14,
               "eligible_on": "2026-10-05"}]}
```

`left_out` codes: `in_collection`, `credit_available`, and `waiting` (the level's waiting
period has not passed; `eligible_on` names the first day it has).

Refusals: `dunning_schedule_missing`, `dunning_run_date_invalid`, `dunning_run_parties_invalid`
(`party_ids` is not a list).

Items in `ready_for_collection` carry `last_notice_id`.

## Command `finance.dunning.run`

Input: `{"schedule_source_record_id": "src_...", "run_date": "2026-10-01", "party_ids": [],
"items": [{"invoice_id": "doc_...", "level": 2}]}` (at least one item, at most 500).

The run carries no finance revision: every payment raises it, and a payment since the review
must skip its item rather than refuse the run. The review pins the schedule instead, because a
changed schedule changes the fees the person approved.

Execution re-derives the context for the same date and customers. Receipt:

```json
{"run_source_record_id": "src_...", "notices": [<notice_detail>...],
 "skipped": [{"invoice_id": "doc_...", "code": "paid"}]}
```

Skip codes: `paid` (nothing open), `not_due` (open but no longer overdue, or outside the run's
customers), `level_changed` (due at another level or waiting since another notice),
`in_collection`, `credit_available`.

The proposal's review applies the same rule as the confirmation: it lists the notices the chosen
items would form and, under `will_skip`, every chosen item that would be skipped with its code.
A proposal whose `schedule_source_record_id` is no longer the schedule is refused with
`dunning_preview_stale`.
Refusals: `dunning_schedule_missing`, `dunning_run_items_invalid`, `dunning_run_item_unknown`
(not a customer invoice of the tenant), `dunning_preview_stale` (the schedule changed since the
review). Replay of the same confirmed
proposal returns the same receipt.

## Command `finance.dunning.collection.handover`

Input: `{"expected_revision": 7, "invoice_ids": ["doc_..."], "handover_date": "2026-11-01",
"reason": "No payment after third reminder"}`

Receipt: the handover detail plus `hold_id` (the new or the already active delivery hold).

Refusals: `collection_invoices_missing`, `collection_mixed_customers`, `collection_level_missing`,
`collection_invoice_not_open`, `collection_already_handed_over`, `collection_reason_missing`,
`dunning_run_date_invalid` (the handover date), `dunning_preview_stale` (the finance revision
changed since the review).

## Reads `finance_dunning_collection_handovers` / `finance_dunning_collection_handover`

List newest first; detail by `handover_id`:

```json
{"id": "col_...", "party_id": "pty_...", "handover_date": "2026-11-01", "reason": "...",
 "invoice_ids": ["doc_..."], "last_notice_ids": {"doc_...": "dun_..."},
 "hold_id": "phd_...", "hold_placed": true, "source_record_id": "src_...",
 "created_at": "..."}
```
