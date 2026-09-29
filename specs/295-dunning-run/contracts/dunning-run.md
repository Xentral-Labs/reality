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
`dunning_schedule_value_invalid` (negative days or fee, more than four decimals),
`finance_account_default_missing` (the existing code: a positive fee without a `dunning_fee_revenue` default), `dunning_preview_stale` (the finance revision changed).

Setting the schedule raises the finance revision, so a run prepared under the old schedule is stale.

## Read `finance_dunning_run_context`

Input: `{"run_date": "2026-10-01", "party_ids": ["pty_..."]}` (`party_ids` optional).

Output:

```json
{"revision": 7, "run_date": "2026-10-01",
 "notices": [{"party_id": "pty_...", "currency": "EUR", "level": 2, "fee_amount": "5.0000",
   "items": [{"invoice_id": "doc_...", "number": "INV-1", "open": "100.00",
              "days_overdue": 30, "previous_notice_id": "dun_...",
              "previous_level": 1, "previous_notice_date": "2026-09-10", "wait_days": 14}]}],
 "ready_for_collection": [{"invoice_id": "doc_...", "party_id": "pty_...",
                           "last_notice_id": "dun_...", "open": "80.00"}],
 "left_out": [{"invoice_id": "doc_...", "party_id": "pty_...", "code": "credit_available"}]}
```

Refusal: `dunning_schedule_missing`.

## Command `finance.dunning.run`

Input: `{"expected_revision": 7, "run_date": "2026-10-01", "party_ids": [],
"items": [{"invoice_id": "doc_...", "level": 2}]}` (at least one item, at most 500).

Execution re-derives the context for the same date and customers. Receipt:

```json
{"run_source_record_id": "src_...", "notices": [<notice_detail>...],
 "skipped": [{"invoice_id": "doc_...", "code": "paid"}]}
```

Skip codes: `paid`, `level_changed`, `in_collection`, `credit_available`.
Refusals: `dunning_schedule_missing`, `dunning_run_item_unknown` (an item that was never a
customer invoice of the tenant), `dunning_preview_stale` on a stale revision. Replay of the same confirmed
proposal returns the same receipt.

## Command `finance.dunning.collection.handover`

Input: `{"expected_revision": 7, "invoice_ids": ["doc_..."], "handover_date": "2026-11-01",
"reason": "No payment after third reminder"}`

Receipt: the handover detail plus `hold_id` (the new or the already active delivery hold).

Refusals: `collection_mixed_customers`, `collection_level_missing`,
`collection_invoice_not_open`, `collection_already_handed_over`, `collection_reason_missing`.

## Reads `finance_dunning_collection_handovers` / `finance_dunning_collection_handover`

List newest first; detail by `handover_id`:

```json
{"id": "col_...", "party_id": "pty_...", "handover_date": "2026-11-01", "reason": "...",
 "invoice_ids": ["doc_..."], "last_notice_ids": {"doc_...": "dun_..."},
 "hold_id": "phd_...", "source_record_id": "src_..."}
```
