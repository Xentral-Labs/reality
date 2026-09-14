# Plan: Customer-wide delivery holds
## Technical Context
Existing Python/SQLAlchemy/PostgreSQL canonical hold tools, FastAPI company review lifecycle and React/TypeScript unified UI. No schema or new dependency. Bounded customer role selection; review snapshots the party and full active hold set, without an affected-delivery count.
## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Manual decision: proposal → attributed event → PartyHold → Party; no fabricated source | PASS |
| Reality owns state | Existing PartyHold/CommitmentHold, never document fulfillment status | PASS |
| Proven schema | No migration or additional field | PASS |
| Tenant/shared services | All reads scoped; canonical tools and existing tenant mutation lock | PASS |
| Spec/test traceability | Seven FR mapped in spec/tasks; backend tests first | PASS |
| Explainable web | Customer/event Inspector and exact historic receipt | PASS |
| Received values | Original note/reason preserved; no price/quantity calculation | PASS |
| Smallest design | Customer-only reviewed wrapper; general party tools remain compatible | PASS |
## Design and layers
Core hold_party_delivery and release_party_delivery_hold gain optional validated action_id and attributed events. Existing signatures and behavior remain compatible. Events include exact hold snapshot payload and release timestamp for historical receipt proof. No mutation in new reads.
services/customer_hold_actions.py provides customer-role context (party attributes, active holds, canonical reasons), normalized review, same-customer unresolved hold/shipment/correction overlap checks, exact receipt and current observation. Shipment/correction overlap resolves party via tenant-scoped Commitment. Reservation permission remains unchanged. Review tokens bind the shown customer/hold state; lock precedes revalidation and canonical execution. No-op reviewed actions reject. General raw CLI/MCP proposal creation/approval keeps its preexisting semantics, as with opening stock.
services/delivery_actions.py dispatches prepare/review/detail/confirmation/recovery and overlap; tools/application.py translates/injects action ID. web/api.py adds read-only customer-holds/{party_id} through the service; existing common reviewed mutation endpoints unchanged.
CustomerHoldCard.tsx uses bounded customer master-data search, reason/note or exact release set, reviewed scope, persistent prepare identity, explicit uncertain-result status check, safe reconciliation and historical Inspector links. Customer delivery case and selected customer master data seed identity; global actions/Chat/Decisions use the same card. Master-data prepared proposals navigate to Decisions to avoid its reference-editor proposal route.
## Verification
Tests before implementation: validation/no-op/no effect, exact action event/replay, existing/future shipment gating and allowed reservations, individual holds remaining, stale state/reapply and stale shipment, independent concurrency, mutual unresolved shipment/correction overlap, tenant/practice/HTTP authorization, committed and uncommitted failure, historic release/rehold proof and tampered receipts. Browser five entries, unknown prepare/confirm/reconcile, reject, empty/paged search, company switch, four languages, keyboard and responsive light/dark. Adjacent holds/opening/delivery browsers; complete backend, contracts/localization/build/format/lint/spec/diff.
## Migration and rollback
No schema. New events add fields without changing existing event meaning. Prior raw events without attribution cannot be falsely claimed as new verified receipts. Restore old adapters if needed; recorded holds/events remain. No shared business writes or real provider/mail calls in tests. No deployment or retirement.
