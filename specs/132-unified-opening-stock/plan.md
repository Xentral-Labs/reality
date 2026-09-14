# Plan: Opening stock
## Technical Context
Existing Python/SQLAlchemy/PostgreSQL movement service and proposal lifecycle; React shared action modal. No schema, new tool name, event family or dependency.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Provenance | Existing manual proposal → attributed event → immutable movement; no invented source/document | PASS |
| Reality / values | Stock derived from movements; Decimal quantity validated without rounding | PASS |
| Tenant/services | Existing record_movement, tenant lock and authorization; adapters only | PASS |
| Schema / simplicity | Existing movement, event and proposal metadata | PASS |
| Tests | Failing service/API/concurrency cases first, then browser and complete suite | PASS |
| Explainability | Additive before/after and reserved balance; exact historical receipt separate from current observation | PASS |
## Design
Add services/opening_stock_actions.py for strict untracked intent validation via core._append_movement(validate_only=True), Decimal precision check, canonical optional UTC time, item/location attributes and physical/reserved snapshots. Add early dispatch in delivery_actions review/detail/reconcile and opening-stock eligibility. Existing application._opening_movement_evidence supplies source-free receipt proof; strengthen event snapshot verification locally. Reconciliation reconstructs canonical records receipt, never invokes movement_create again.
Use existing movement_correction_actions.action_keys to block unresolved opening-related same-pool overlaps in both directions, keeping unrelated pools independent. All reviewed mutations already serialize via tenant lock. Preserve existing raw CLI/MCP opening proposal approval behavior with a narrowly documented compatibility exclusion from the newly broadened review-eligibility guard; new UI proposals always contain and enforce their review token. Practice flow remains untouched. Existing raw proposals can acquire the new review via review_existing; historical source-free receipts remain inspectable without fabricating historical balances.
Frontend OpeningStockCard.tsx uses existing bounded suggestions and deliveryActions.prepare/review/detail/confirm/reconcile. Persist only request identity/intent for lost preparation; confirmation uncertainty blocks writes and requires status checking. Typed opening_stock launcher alias dispatches existing movement_create. ActionCard selects by detail movement_type for raw/previous proposals. Warehouse entry, global launcher and Chat/Decisions share it; verified movement opens Inspector and existing correction remains in Warehouse.
## Verification
New tests: additive stock, precision/field/identity guards, stale stock/reference, request replay, legacy raw compatibility, exact receipt/mismatch/reconciliation and later corrections, unresolved mutual overlap, independent concurrent proposals, tenant/practice/HTTP. Browser all entries, bounded choices, lost prepare/confirm, reject/reload/company switch, four-language layouts. Full backend, web contracts/i18n/build/format/browser, lint/spec/diff required. Restart local API after checks; no shared business mutations.
## Rollback
No migration. Restore previous adapters while preserving recorded movements/events/proposals. New strict precision/untracked scope applies to reviewed opening entry only; general movement core contracts remain unchanged.
