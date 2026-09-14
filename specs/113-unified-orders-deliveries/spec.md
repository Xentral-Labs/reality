# Feature Specification: Unified Orders and Deliveries

**Created**: 2026-09-07
**Language**: English
**Status**: Owner-authorized next migration increment after the explicit missing-workspaces reminder.

## Context and Intent
### Problem
The accepted sidebar includes Orders & deliveries, but operators currently have only the open customer delivery cases under Your work and supporting legacy registers.
### Scope
A dedicated unified workspace joins customer/supplier order evidence with outgoing/incoming delivery registers. Follow an exact order into its delivery commitments, inspect provenance and open existing customer delivery actions.
### Non-Goals
No new order creation, supplier receipt action, holds/allocation planner, cancellation, bulk action, order-level readiness derivation, financial totals, schema, credential changes, rollout, merge or old App/Playground retirement. Facts remains the next separate workspace. Advanced order operations remain in supporting workspaces.

## User Scenarios & Testing
### US1 — Understand promised deliveries (P1)
An operator chooses customer or supplier deliveries, searches party/item/delivery identity and switches between operationally open deliveries and all recorded history. Every row shows current promised, fulfilled and open quantities with its unit, due date, counterparty and recorded status. The remaining quantity column describes unfulfilled quantity; a cancelled commitment is not open work even if unfulfilled quantity remains.
Acceptance: revisions and corrected movements affect rows through shared services. Supplier rows identify the supplier, not the receiving company. Open means recorded open status and positive remaining quantity. All includes fulfilled/cancelled commitments. Filters apply before count/pagination; no cross-unit totals.
### US2 — Follow an order (P1)
An operator chooses customer-order or supplier-order documents, searches the existing evidence register and opens its Inspector. View deliveries filters the appropriate delivery direction by exact document identity, including multiple document lines and completed history.
Acceptance: explicit sales_order/purchase_order filters exclude invoices before pagination. A document with no deliveries has an honest empty result. Identical human numbers never merge records. Follow the shortest actual document-line relationship, falling back to the direct document link. No fulfillment field is added to a document.
### US3 — Act with context (P2)
Open a customer delivery in the existing Your work case, then reserve/ship through its established reviewed action. Incoming rows use the shared commitment Inspector for quantities, evidence and source. Supporting advanced operations remain available.
Acceptance: no new write route; opening a register, Inspector or action case has no business mutation. Foreign selected records do not disclose details. Filters and selected Inspector survive reload and are reset when switching companies.

## Requirements
- **FR-001**: Add a selected Orders & deliveries sidebar destination at `/app/orders-deliveries`, with bookmarkable deliveries/customer-order/supplier-order sections. Normalize unknown filters, reset page on filter change and clear selected records/order scope on company change. Legacy `/app/orders` stays supporting.
- **FR-002**: Reuse and extend shared delivery_work for customer/supplier type, open/all status and exact order document filtering; retain customer/open defaults. Count and page after filters, use effective quantities/dates and correction-adjusted fulfillment, and select the correct counterparty and unit. Customer delivery_case remains customer-only.
- **FR-003**: Order documents use existing evidence reads with explicit sales_order or purchase_order type. Show received amount/currency and document identity without deriving operational status or currency totals. Search copy matches the existing number/ID/source search rather than promising party-name search.
- **FR-004**: Order → deliveries uses opaque document ID and the true line/document relationship, chooses the correct direction and includes all history. Clearing order scope returns to a wider register. No browser-side association or pagination.
- **FR-005**: Every delivery/order is inspectable through the shared tenant-scoped Inspector. Customer delivery opens its existing exact case and confirmed actions; supplier delivery never opens a customer action. Existing action services and confirmation behavior remain unchanged.
- **FR-006**: Loading, empty, failure/retry, pagination, foreign scope and company reset are explicit. No mutation request arises from this workspace's register/Inspector navigation.
- **FR-007**: All new copy is translated in en/de/nl/es; three sections work in light/dark at390/1440px with keyboard focus return. Quantities retain units; the UI does not aggregate them.

## Success Criteria
Backend regression proves revised incoming deliveries, exact order filtering across lines and tenants, pagination and unchanged customer defaults. Browser proof covers order → deliveries → existing customer case, supplier Inspector, filter reload, retry/empty/company reset, no navigation writes and48 localized screenshots. Full required suites pass.

## Assumptions and Dependencies
The owner explicitly asked to continue with Orders & deliveries followed by Facts. Reuse is selective; legacy parity is not required. Existing evidence register and canonical delivery observations remain authoritative. Its document register is a separate evidence tab, not the old materialized order-readiness dashboard. No projection freshness or order-level readiness claim is introduced. Supplier execution and advanced order controls require later reviewed scope.

## Requirement Traceability
| Requirements | Stories | Planned evidence |
| --- | --- | --- |
| FR-001 FR-006 | US1–US3 | Route/filter normalization, reload/company reset, error/empty/browser |
| FR-002 | US1 | Shared service/API tests for direction, revised values, corrections, unit, paging and defaults |
| FR-003 FR-004 | US2 | Order type filtering and exact multi-line/document/tenant traversal |
| FR-005 | US3 | Customer case and supplier Inspector navigation, existing action regression |
| FR-007 | US1–US3 | Four locales, two themes, two widths and keyboard Inspector return |
