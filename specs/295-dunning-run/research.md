# Research: Dunning Run and Escalation

Code reading on 2026-09-29 against `origin/main` (`c1e1b853`). Paths are relative to
`packages/reality-core/`.

## R1. What already exists (spec 247)

- `services/dunning.py`: `preview_notice`, `record_notice`, `notice_detail`, `notices`,
  `reverse_notice`. One notice has one level (1 to 3), one customer, one currency, a stated fee
  and one or more invoices (`dunning_notice_invoice`). A positive fee creates a
  `dunning_fee_charge` document and posts receivable against `dunning_fee_revenue`.
- A reversal is the event `dunning.notice_reversed` on the notice; there is no column.
- `finance.dunning.record` and `finance.dunning.reverse` run through
  `tools/finance.py` `EDGE_COMMANDS` and the finance change proposal; the Web posts them to
  `/finance/commercial/proposals` (`apps/web/src/finance/DunningNotice.tsx`).
- `services/finance/worklists.py` `overdue_document_ids` reads `aging_register` once for a date.
- `lock_finance` serializes finance writers. Its revision rises with every finance posting,
  payments included (`core._require_business_mutation`), so the run cannot use it as its
  staleness check: a payment since the review would refuse the whole run instead of skipping
  the paid item. The run pins the schedule's source record instead (R4).
- The existing refusals in `dunning.py` are uncoded; new refusals are coded (spec 286 ratchet).

## R2. Where the schedule lives

**Decision**: A new table `dunning_schedule_level` with one row per company and level (1 to 3):
waiting days and fixed fee. It is replaced as a whole by the reviewed command
`finance.dunning.schedule.set`, whose confirmed request is a source record.

**Rationale**: Constitution III: every run reads it to decide each item's level and each
notice's fee (FR-003, FR-007). A JSON setting on the tenant would be read the same way but
cannot carry the level check and non-negative constraints. Rows per level keep the sequence
explicit and the constraint simple (`level BETWEEN 1 AND 3`, unique per tenant).

**Alternatives rejected**: per payment term or per party group (owner: one per company);
storing the schedule on each notice (the notice already records its level and fee as stated at
confirmation, which is all history needs).

## R3. How an item's level is derived

**Decision**: At read time, per invoice: the latest non-reversed notice linking it
(`dunning_notice_invoice` → `dunning_notice`, excluding notices with a
`dunning.notice_reversed` event). No stored level (DR-002).

| Last notice | Proposed | Allowed when |
|---|---|---|
| none | level 1 | `days_overdue ≥ level 1 wait days` on the run date |
| level 1 or 2 | next level | `run date − last notice date ≥ wait days of the next level` |
| level 3 | nothing; listed as ready for collection | open and overdue |
| any, and handed to collection | nothing | never again |

The derivation reads aging once, the notice links once and the reversal events once for the
tenant (optionally limited to the selected customers); there is no per-invoice query
(spec 181, spec 241).

## R4. The run as one reviewed command

**Decision**: A read `finance_dunning_run_context` returns the preview and the finance revision.
The command `finance.dunning.run` takes `run_date`, optional `party_ids`, the prepared
`items` (`invoice_id` plus proposed `level`) and the reviewed `schedule_source_record_id`. On execution it takes
`lock_finance`, re-derives the preview for the same date and customers, and records one spec 247
notice per customer, currency and level for items still eligible at their proposed level. Every
other prepared item is skipped with a code: `paid` (no longer open or overdue), `level_changed`
(a notice was recorded or reversed since), `in_collection`, `credit_available`.

- Items not in `items` are not dunned; that is how the clerk deselects (FR-008).
- Each notice has its own source record, `external_id = "{action_id}:{n}"`, so
  `notice_detail`'s lookup of the fee document by source record stays unique and replay is
  idempotent per notice. A run source record (`dunning_run`, `external_id = action_id`) holds
  the confirmed request and the receipt, and each notice's payload names it.
- `record_notice` is split into a private `_record_notice(..., source_key)` that both the
  single notice and the run call. Its behaviour for `finance.dunning.record` is unchanged
  (DR-003).
- The fee of a notice is the schedule's fee for its level at confirmation (FR-002). It is the
  company's stated amount, not a calculation (Constitution VIII).
- If nothing remains eligible, the run records nothing and returns the skipped list; it is not
  an error.

**Alternatives rejected**: one proposal per notice (a run over 40 customers would need 40
approvals); a run that re-derives without the prepared items (the clerk would approve something
other than what was reviewed).

## R5. Credit available

**Decision**: `services/finance/credits.py` `available_credit_rows` for customers, read once;
a customer with an open credit in the currency is left out and named `credit_available` in the
preview. The clerk applies the credit first (existing settlement).

## R6. Collection handover

**Decision**: New tables `collection_handover` (customer, date, reason, source record) and
`collection_handover_invoice` (link, unique per invoice), recorded by the reviewed command
`finance.dunning.collection.handover` with `invoice_ids` of one customer, `handover_date`,
`reason` and `expected_revision`. Each invoice must be open and its last non-reversed notice at
level 3 (codes `collection_level_missing`, `collection_invoice_not_open`,
`collection_already_handed_over`, `collection_mixed_customers`). In the same transaction the
customer gets a delivery hold with the new hold reason `collection` unless a hold is active.

**Rationale**: Constitution III: the run filters on it every time (FR-004), and the handover
read and the invoice explanation join on it. A level-4 notice would create a dunning document
and a notice the customer never receives. Hard rule 2 forbids a document field.

`core.hold_party_delivery` commits; the handover needs it inside its transaction, so it gets
the codebase's `_commit` flag (as `create_document` has) and the handover passes `_commit=False`.

**Not in scope**: taking an item back from collection (spec non-goal).

## R7. Surfaces and gates

- MCP/Chat: `finance_dunning_schedule`, `finance_dunning_run_context`,
  `finance_dunning_collection_handovers`, `finance_dunning_collection_handover` (reads);
  `finance_dunning_schedule_set_propose`, `finance_dunning_run_propose`,
  `finance_dunning_collection_propose` (proposals).
- CLI: `finance dunning-schedule`, `finance dunning-schedule-set`, `finance dunning-run`,
  `finance dunning-collection`, all through the same change proposal.
- Web: on the Finance dunning area, a schedule form, a "Prepare dunning run" review with
  deselectable items and skipped reasons, and a "Hand over to collection" action on items ready
  for collection. The existing `/finance/commercial/proposals` endpoint carries the commands;
  new read endpoints for schedule, run preview and handovers.
- Gates: tenant isolation catalog and count, `command_catalog.yaml` (commands, coverage,
  guidance, parameters), `tool_catalog.json` topic, `action_discovery.json` and its Web fixture,
  `resource_catalog.yaml` with German labels, `service_refusals.json` plus de/nl/es,
  `refusal_ratchet.json`, `business_event_catalog.yaml` (`dunning.schedule_set`,
  `dunning.run_confirmed`, `dunning.collection_handover_recorded`), `data_model.yaml`,
  reporting-graph deferral, FK indexes, hold reason label in four languages, `make docs-generate`.
