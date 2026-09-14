# Plan: Unified financial reversal
## Technical context
Existing PostgreSQL/SQLAlchemy core reversal, application tool ledger_reverse, FastAPI and React common action lifecycle. No migration or new event/tool name.
## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Original links retained; inverse explained by LedgerReversal and attributed event | PASS |
| Reality authority | Open/allocated amounts derived; no document status mutation | PASS |
| Proven schema | Existing relation, entries, allocations and proposal suffice | PASS |
| Shared tenant services | Pure review/read helper and canonical reversal service | PASS |
| Tests first | Focused stale/effect/recovery tests before implementation | PASS |
| Explainability | Before/after balances and original/inverse Inspector links | PASS |
| Simplicity | Reuse common action lifecycle and ledger.reversed event | PASS |
| Received values | Exact inverse of original entries; observations only for balances | PASS |
## Design
services/financial_reversal_actions.py provides private scoped searchable group choices, pure review of canonical preview plus active allocations/counterpart state and invoice/payment projections, overlap guard, exact attributed proof and separate current observation. Choice query is paginated by posting group with human document/party labels.
core.py reverse_ledger_posting_group adds optional action_id and immutable original/inverse snapshots to existing ledger.reversed event. tools/application.py passes attribution and skips old standalone preview normalization when common review exists. Canonical receipt remains reversal/group IDs and replayed.
services/delivery_actions.py adds dispatch/eligibility/reconciliation. services/payment_actions.py uses shared financial overlap guard for payment→reversal conflicts; the reverse direction is checked too. web/api.py allows common prepare and exposes read-only group choices.
apps/web/src/unified/FinancialReversalCard.tsx uses existing proposal recovery, reason editor, selectable groups, inverse/effect review and verified links. Finance header and payment/journal rows launch it; Actions/Chat/Decisions use the same card. api.ts and localization.tsx supply types/translations.
## Validation and rollback
Tests: both invoice/payment directions, allocations active/inactive, exact inverse and receipt, no preparation writes, stale counterpart/payment changes, cross-tenant/actor/practice, overlap, event tampering, response loss and historical proof. Preserve old direct reversal tests. Full core, web contracts/build/i18n/format, reversal/payment/invoice/finance browser journeys, shared form reads only, spec/lint/diff and final review. Freeze core during full suite. Rollback entry availability without deleting any financial history.
