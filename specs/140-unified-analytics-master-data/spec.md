# Feature Specification: Unified Analytics and Master Data

**Feature Branch**: `139-unified-app-foundation` (additive follow-on in the existing isolated checkout)
**Language**: English
**Created**: 2026-09-07
**Status**: Implemented and technically verified in the isolated opt-in preview; owner product review and deployment remain separate.
**Input**: Continue the approved new-design App; add Analytics and Master data before later workspace migration and retirement.

## Context and Intent

### Problem
Home and the delivery case work, but operators need a separate view of recorded activity and a clear place to maintain the references that those cases use.

### Scope
Add Analytics, its compact Home entry and a Master data destination for customers, suppliers, items and locations in the same shell. Reuse existing business operations and explanation paths. Implement basic creation and name maintenance, with SKU maintenance for items. Preserve all unedited commercial, tracking, hierarchy and provenance values.

### Non-Goals
No forecasting, inferred blocked revenue, automation scores, reconstructed historical backlog or historical reservation snapshots. No new business tables. No full pricing/payment-term editor, bulk import, deletion, practice admission change, legacy retirement, deployment or merge. Advanced existing reference maintenance stays reachable through supporting workspace links.

## User Scenarios & Testing

### User Story 1 — Understand recorded position and activity (Priority: P1)
The operations lead opens Analytics from Home, chooses 7, 30 or 90 UTC calendar days, and opens the records behind a figure or daily point.

**Independent test**: With two open promises, one fully reserved and one uncovered/overdue, totals and contributors agree before and after a partial shipment. Different units are never added as quantities.

**Acceptance scenarios**:
1. Current cards show open customer-delivery commitments, the share fully reserved, those needing reservation and overdue ones. Coverage is unavailable when the denominator is zero.
2. The chart counts new customer-delivery commitments by creation date and effective positive shipments by occurrence date. These are different record families, not an order conversion rate. Corrected originals and compensation records do not count as effective shipments.
3. Current-position cards stay current when the chart period changes. Chart contributors obey the selected UTC day/period; current contributors obey the card definition. Counts are complete tenant totals independent of contributor pagination.
4. Empty recorded days mean no matching recorded activity, not proof that upstream history is complete. Definitions, observation time and the recorded-history limitation are visible.
5. Home and Analytics use the same position definitions; no prototype history is presented as company truth.

### User Story 2 — Find and explain references (Priority: P1)
An operator opens Master data, searches the selected family and opens a record without losing their place.

**Independent test**: Similar customer names and an identically named supplier remain separate opaque selections; paging and company changes preserve isolation.

**Acceptance scenarios**:
1. Customers and suppliers follow existing Party roles, items and locations use their existing records. Search, active/all filter and paging run over the full scoped register.
2. Details show current fields, active state and provenance and open the existing Inspector/source links.
3. Delivery party/item/location references can lead to the appropriate master-data selection. Advanced reference maintenance is reachable in its existing workspace.

### User Story 3 — Maintain a reference safely (Priority: P1)
An operator creates a basic reference or edits its permitted fields, reviews the exact intent and confirms it.

**Independent test**: Rename an item with tracking, default location and source metadata; those unedited values remain unchanged. A concurrent edit causes refusal and a fresh review is needed.

**Acceptance scenarios**:
1. Customers/suppliers require a name; items require name, SKU and unit; locations require name and use the existing warehouse defaults. Edits change names and optionally item SKU; roles, units, hierarchy and advanced fields are preserved.
2. Opening/cancelling a form creates nothing. Preparation creates only a durable proposal. Same request identity and intent recover that proposal; a changed intent cannot reuse it.
3. Confirmation uses the canonical application tool. Repeated confirmation has one effect, stale edits fail, rejection does not mutate a reference, and uncertain execution never automatically resubmits.
4. Refresh restores pending review/result by proposal identity. Successful results link to the actual record. Unsupported legacy commands continue through their existing review paths.

### User Story 4 — Stay in one understandable App (Priority: P2)
All new pages use the foundation shell, four languages, both themes and accessible layouts at 390 and 1440 px.

**Independent test**: Navigate Home → Analytics → contributor → delivery → Master data, reload, change company and use keyboard-only review/close.

### Edge Cases
Unknown due dates; no open commitments; identical display names; missing provenance; corrected/replaced shipments; UTC midnight; mixed units/currencies; period outside recorded history; inactive references; concurrent reference edits; foreign IDs; changed authorization; response loss; unavailable reads; no AI provider.

## Requirements

- **FR-001**: Add Analytics and Master data routes within the same opt-in shell; preserve authorized company, selected record, bounded filter and period state across URL navigation/reload.
- **FR-002**: Compose current delivery position and daily activity using authoritative shared semantics; document question, unit, time basis, scope, correction treatment and completeness for every metric.
- **FR-003**: Provide bounded contributors for every metric and selected chart day, with exact record/Inspector links; totals must not derive from a loaded page.
- **FR-004**: Add a compact Home Analytics entry using those same definitions and explicit empty/unavailable states.
- **FR-005**: Provide searchable, paginated, tenant-scoped customer/supplier/item/location registers with active/all filtering, record detail and provenance links.
- **FR-006**: Provide basic create/edit forms, preserving every field outside the explicitly editable set and rejecting stale edits from an earlier record snapshot.
- **FR-007**: Use durable canonical tool proposals, explicit review/confirmation, request replay and outcome lookup; never retry an uncertain mutation automatically.
- **FR-008**: Enforce tenant and ordinary-company authorization for reads, preparation, confirmation and linked references. Preserve practice and legacy policies.
- **FR-009**: Connect delivery reference links and master proposals in Decisions/Chat to their new destination while preserving existing delivery action behavior.
- **FR-010**: Deliver en/de/nl/es, light/dark, 390/1440 px, keyboard focus and safe rendering; no mock metric or later-module placeholder may appear as working live data.

## Assumptions and Dependencies

The owner's continuation accepts the previously announced Analytics/Master data phase and the established design-first migration direction. The basic four reference families are the smallest useful maintenance scope. Existing commercial tools remain supporting paths. UTC is explicit for aggregate buckets; locale formatting does not change bucket membership. Recorded activity is a view of retained records, not evidence of complete external-system history. Spec 139's services, shell, action safety and preserved legacy paths are prerequisites. No constitutional exception or schema expansion is needed.

## Success Criteria

- **SC-001**: Card totals equal full contributor counts across more than one page; Home agrees with Analytics for the same company.
- **SC-002**: Correction, UTC-boundary, unknown-date and mixed-unit fixtures give the defined results without inferred money or source totals.
- **SC-003**: Each of four reference families can be created and renamed through review; stale/foreign edits and repeated confirmations cannot overwrite unrelated fields or duplicate effects.
- **SC-004**: All new routes and review states remain usable in four languages, both themes and both target widths, with no page-wide overflow.
- **SC-005**: The existing delivery, proposal, tenant and practice regressions remain green; no old interface is retired in this increment.

## Requirement Traceability

All repository artifacts are written in English; translated UI copy is intentional product localization.

| Requirement | Acceptance scenario | Executable evidence |
| --- | --- | --- |
| FR-001, FR-009 | US4 navigation, US2-3 | unified-app-contract.test.mjs, unified-workspaces-browser.mjs |
| FR-002, FR-003 | US1 metrics and contributors | test_company_insights.py, unified-workspaces-browser.mjs |
| FR-004 | US1 Home entry | unified-workspaces-browser.mjs |
| FR-005 | US2-1, US2-2 | test_reference_workspace.py, test_unified_workspace_api.py |
| FR-006 | US3-1 | test_reference_workspace.py |
| FR-007, FR-008 | US3-2 to US3-4 | test_reference_workspace.py, test_unified_workspace_api.py, unified-workspaces-browser.mjs |
| FR-010 | US4 localized responsive review | unified-workspaces-browser.mjs, i18n:audit |
