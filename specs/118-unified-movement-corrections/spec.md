# Unified Movement Corrections

**Language**: English
**Created**: 2026-09-08
**Status**: Scope approved by the owner's continuation of the proposed correction increment.

## Context and Intent
Operators can now receive, ship, reserve and hold in the unified app, but correcting a mistaken warehouse movement still requires the old presentation. Preserve the original movement and explain the full inverse and optional replacement before confirmation.

### Scope
Correct an existing movement from Warehouse, the global action launcher or a matching Chat proposal. The small form supports reversing a mistake or replacing its quantity while preserving its item, direction, locations and supported references. Existing canonical proposals with other supported replacement fields remain reviewable without silently changing those fields. Show current and projected stock separately from fulfillment and reservations.

### Non-Goals
No opening-stock creation, inventory-count reconciliation, financial corrections, new schema, return-resolution or return-announcement editor, deployment, legacy retirement or business mutations in the owner's shared local data for verification. Do not invent reservation restoration. Broader source/order/finance work remains separate.

## User Scenarios & Testing
### US1 — Correct a mistaken movement (P1)
Open a warehouse movement, choose correction, enter a reason and either reverse it or state a replacement quantity. Review names the selected movement, inverse, replacement and affected stock before confirmation.
**Acceptance:** A receipt of 10 corrected to 7 leaves the original 10, a linked inverse 10 and replacement 7; physical stock is 7. Preparation and rejection have no effect.
### US2 — Trust the correction history (P1)
An operator can inspect the original, inverse, replacement and event. Correcting a replacement identifies that selected replacement. An already corrected original or compensation cannot be corrected again.
**Acceptance:** Replay and recovery return the exact recorded correction without another movement; later legitimate correction does not invalidate historical proof. Reservations remain as recorded, even if this leaves an allocation shortage.
### US3 — Use the same action everywhere (P1)
Warehouse, global Actions, Chat and Decisions open the same saved review. Reload, edit, rejection and uncertain outcome handling retain the common action experience.
**Acceptance:** A reload opens the same proposal; editing requires fresh review; a stale or unauthorized confirmation records no effect.
### Edge cases
Empty selection/reason; malformed or foreign references; unsupported replacement fields; exhausted aggregate/tracked stock; serial occupancy after inverse; changed fulfillment/holds/reservations; replacement chains; changed item/location in canonical proposals; unknown outcome; missing observations; tenant switching; practice boundary; translated mobile/desktop light/dark layout.

## Requirements
- **FR-001**: Offer a searchable, paginated movement selector and contextual correction entry. Reason is required; inverse-only or replacement quantity is explicit. Preserve supported references; do not silently drop unsupported return relationships.
- **FR-002**: Use shared correction semantics for read-only preview and atomic execution. Validate replacement against the state after the inverse without writing temporary Reality records. Show selected original, inverse, optional replacement and signed effects for each affected item/location.
- **FR-003**: Bind confirmation to exact intent and relevant live state; recheck current tenant access and state under the existing mutation lock. Reject stale, invalid or foreign intents and preserve practice policy. Unknown overlapping delivery/correction executions block conflicting reviewed actions in both directions.
- **FR-004**: Link action identity to correction evidence. Verify exact correction relation, movement values and event; replay/reconciliation must never reapply the mutation. Separate historical receipt from current observation failure.
- **FR-005**: Reuse common reviewed-proposal entry points across forms, Chat and Decisions, including URL reload, edit/reject and refresh. Existing delivery actions remain working.
- **FR-006**: Keep original records and existing reservation semantics. No business logic in UI, no document fulfillment state and no new identity/schema duplication. Correction does not restore consumed reservations.
- **FR-007**: Provide readable reason/reference/effect presentation in all four languages, responsive desktop/mobile and light/dark themes; retain useful pagination and shared form spacing. Original content is escaped and technical IDs remain inspectable.

## Key Entities
Movement; MovementCorrection linking original/inverse/optional replacement; ChangeProposal; attributable BusinessEvent. A review is a snapshot, not a new business authority.

## Success Criteria
- SC-001: Receipt and shipment corrections produce exactly the reviewed stock/fulfillment effect through the same service, with original history preserved.
- SC-002: All four entry points retain exact review and require confirmation; invalid/stale/foreign/replayed/unknown executions never duplicate an effect.
- SC-003: Every FR has passing executable evidence; layouts are visually reviewed and the existing full required suite remains green.

## Assumptions and Dependencies
The owner approved existing-movement correction as the next increment. Existing correction semantics define full inversion, optional replacement and unchanged reservations. The form begins with quantity correction; supported richer canonical intents retain their exact fields in review/edit. The existing shared database on port 8080 is used by the new local preview, so business-effect verification uses isolated PostgreSQL tests and HTTP fixtures.

## Requirement Traceability
| Requirement | Implementation | Proof |
| --- | --- | --- |
| FR-001/005/007 | Correction form, launcher, Warehouse, Chat/Decisions | unified-corrections-browser.mjs |
| FR-002/006 | Shared core projected validation | test_unified_movement_corrections.py; existing correction tests |
| FR-003/004 | Correction review/evidence adapter and shared proposal lifecycle | test_unified_movement_corrections.py |
| FR-005 | Shared API/proposal entry | HTTP and browser round trips; existing delivery browsers |
