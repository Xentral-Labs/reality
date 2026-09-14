# Plan: Partial invoicing and rebilling
## Technical context
Existing Python/SQLAlchemy/PostgreSQL invoice tools, invoice/reversal review modules and React InvoiceCard. No migration, new command/event or dependency.
## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Linked invoice evidence plus original group/reversal IDs explain availability | PASS |
| Reality authority | Availability is derived, never stored on documents | PASS |
| Proven schema | Existing line, group and reversal relations suffice | PASS |
| Shared services/tenant | One private core derivation and shared tenant mutation lock | PASS |
| Tests first | Partial/rebilling/stale/concurrency proofs precede changes | PASS |
| Explainable UI | Ordered, billed, available quantities and invoice Inspector links | PASS |
| Simplicity | Replace two guards; reuse shared review/card and existing Inspector response | PASS |
| Received values | Sum quantities only as an observation; never derive invoice amounts | PASS |
## Design
core.py private _order_line_billing derives matching invoice-line quantities and all attached original group/reversal identities, counting unposted evidence and excluding only fully reversed invoice groups. Optional projected reversal uses the same calculation without writes. Clamp availability at zero but retain actual billed quantity. Replace both canonical single/multi invoice guards; enforce exact existing numeric precision. Add invoice/manual-evidence/posting writers to the existing shared tenant lock before row locks; preserve generic evidence admission without rejecting received overbilling.
invoice_actions.py adds billing snapshots outside immutable creation for all selected lines. financial_reversal_actions.py adds projected billing availability for invoice-linked order positions outside historical proof. Existing invoice/reversal receipt shape stays intact. web/api.py document_inspector evidence_lines adds optional billing observation on order lines; api.ts types it.
InvoiceCard.tsx shows available quantity in selection/rows/review, disables exhausted positions and links prior invoice evidence. FinancialReversalCard.tsx shows released availability and updates obsolete no-rebilling text. localization.tsx supplies all four languages.
## Validation and rollback
Both directions partial→remainder→full reversal→rebilling; unposted/multi-group/credit/payment distinction, source overbilling, fractional precision, stale review despite remaining capacity, concurrent direct/shared invoices, old proof/recovery and Inspector HTTP. Full core, contracts/build/i18n/format, invoice/reversal/payment/finance browser and shared read-only form checks. No core/test edits during full suite. Rollback entry/validation together without deleting any historical invoice or reversal.
