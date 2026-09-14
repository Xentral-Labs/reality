# Unified Receipt and Reservation Release

**Language**: English
**Created**: 2026-09-07
**Status**: Scope accepted through the owner's instruction to implement the proposed next increment.

## Context and Intent
### Problem
Incoming deliveries and reservations are visible in the new App, but receiving goods and releasing reservations still require a legacy or practice interface.
### Scope
Add reviewed supplier receipt and reservation release to the unified company App, using existing operations. Make both discoverable from their records and the global action launcher, and open matching company Chat proposals in the same review card.
### Non-Goals
No partial-release capability, new order, invoice, hold, opening-stock or correction workflow. No schema, arbitrary movement editor, new sandbox capability, deployment or legacy retirement.

## User Scenarios & Testing
### US1 — Receive an incoming delivery (Priority: P1)
An operator selects an open supplier delivery in Orders & deliveries, enters a quantity and reviews its item, destination and effect. Confirmation records the receipt and refreshes current quantities.
**Independent test:** Receive 3 of 8 promised units; remaining becomes 5 and physical stock increases by 3. Preparation alone changes neither. Over-receipt and wrong-direction selection are refused by shared validation.
### US2 — Release a reservation (Priority: P1)
An operator selects an active reservation in Warehouse, reviews the exact reservation and its full remaining reserved quantity, then confirms. Physical stock and the delivery commitment remain unchanged; reserved stock decreases and availability increases.
**Independent test:** Release an active reservation of 6 units in full. A foreign, inactive or stale selection cannot cause an unintended change.
### US3 — Use one action experience (Priority: P2)
Both actions are discoverable in the launcher with searchable, bounded record selection. Matching company Chat proposals and Decisions open the same exact review. Reload restores the proposal. Editing requires a fresh review; uncertain outcomes are checked without repeating execution.
**Independent test:** Form and Chat produce equivalent effects; repeat confirmation creates one effect; recovery opens the recorded event and original record.
### Edge Cases
No eligible records; duplicate names; missing item/location; tracked items; partial quantities; concurrent receipt/release; membership revoked after review; foreign IDs; rejected proposals; lost prepare/confirm response; observed state unavailable; no model; archived practice contexts.

## Requirements
- **FR-001**: Offer supplier receipt from incoming delivery records and the launcher. Selection binds exact supplier commitment, item and destination; reference choices remain scoped and bounded.
- **FR-002**: Offer reservation release from active Warehouse reservations and the launcher. Show the exact reservation, commitment, item, location and available release quantity; release the selected active reservation in full, preserving the existing service semantics.
- **FR-003**: Preparation stores only an exact proposal. Confirmation requires current review and authorization, validates shared business constraints and rejects stale state. Editing invalidates the prior review. Preserve tenant isolation and existing sandbox admission/tool policies.
- **FR-004**: Use shared application tools for forms and company Chat; integrate matching proposals with Decisions and reload recovery. Duplicate confirmation and unknown outcomes must not duplicate movements or release events. Verified receipts remain distinct from current observations.
- **FR-005**: Refresh affected registers after settlement, preserve navigation and Inspector trace links, retain existing customer reserve/shipment flows and table behavior. Forms remain usable without AI.
- **FR-006**: Provide English, German, Dutch and Spanish, light/dark, desktop/mobile and keyboard-accessible controls. Test loading, empty, invalid and unknown-result states. Action forms separate field groups by 16px. Show record pagination only when more than one page exists; align previous/next controls and the page indicator in a distinct row below selection.

## Key Entities
Existing supplier/customer Commitment, Reservation, Movement, BusinessEvent and ChangeProposal. Receipt follows Commitment to evidence; release follows Reservation to Commitment. No duplicate authority or relationship.

## Success Criteria
- **SC-001**: Both independent stories complete inside the new App with correct observed quantities and one traceable effect per confirmation.
- **SC-002**: All planned stale, foreign, replay and recovery checks pass with no unauthorized or duplicate effect.
- **SC-003**: Both actions can be found from their registers and launcher, and completed without a provider at desktop and mobile sizes.

## Assumptions and Dependencies
The owner's “ja mach” approves receipt and reservation release only. Existing shared receipt and release semantics remain authoritative; no confirmation is inferred from opening a form. Specs 107, 109, 113 and 115 provide the review, register and table foundations. Technical names remain optional detail. Required verification includes service/API regressions, frontend contracts, browser journeys and the full affected backend suite.

## Requirement Traceability
| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | T004, T010 | T005, T011 |
| FR-002 | T006, T010 | T007, T011 |
| FR-003 | T004, T006, T008 | T005, T007, T009 |
| FR-004 | T008, T010 | T009, T011 |
| FR-005 | T010, T013 | T011, T014 |
| FR-006 | T010, T013 | T012 |
