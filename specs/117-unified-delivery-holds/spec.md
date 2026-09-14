# Unified Delivery Holds

**Language**: English
**Created**: 2026-09-08
**Status**: Scope accepted by the owner's continuation of the proposed delivery hold increment.

## Context and Intent
### Problem
The unified delivery case shows bare blocker codes and sends operators elsewhere to control holds. A delivery-specific hold and a customer-wide hold are visually indistinguishable.
### Scope
Explain active holds and their scope in the existing customer delivery case. Set or release delivery-specific holds through the shared reviewed action card, global launcher and matching company Chat/Decisions proposals. Preserve existing service semantics.
### Non-Goals
No party-wide or document-wide hold editing, supplier case redesign, new release-reason field, schema, correction workflow, deployment or legacy retirement. No inferred shipment readiness after release. Existing supplier tool semantics remain supported without expanding the customer worklist.

## User Scenarios & Testing
### US1 — Understand why delivery is blocked (Priority: P1)
An operator opens a customer delivery case and sees each active hold's reason, optional original note and scope. Own delivery holds offer release; customer-wide holds identify their broader scope and do not expose a misleading single-delivery release.
**Independent test:** With own and customer-wide holds, releasing the former leaves the latter visible. Quantities and reservations do not change.
### US2 — Control a delivery hold (Priority: P1)
An operator selects Place delivery hold, chooses a supported reason and optionally adds a note. Review identifies the exact commitment, reason, note and scope. Confirmation records the hold and blocks the existing fulfillment services. Release reviews all active holds on this commitment and then releases only that set.
**Independent test:** Prepare has no business effect; confirm creates one hold/event; release clears own holds with unchanged stock, reservations and open quantity. Reject or edit never executes the original intent.
### US3 — Continue through Chat and reload (Priority: P2)
Global launcher, case controls and company Chat use the same review/confirmation. Reload restores a proposal; duplicate confirmation is safe. Lost execution responses are checked through recorded evidence without replay.
**Independent test:** The canonical tool proposal requires the same review token; a release/reapply between review and confirmation fails stale even when the reason is identical. Recovery reconstructs the exact recorded receipt.
### Edge Cases
No selected/open delivery; no active own hold; existing own hold; unsupported reason; blank note; foreign IDs; revoked access; escaped original notes; customer-wide hold remains; multiple historical active own holds; concurrent fulfillment or hold change; unknown execution; observation failure; no provider; practice authorization.

## Requirements
- **FR-001**: The case distinguishes delivery and customer-wide holds, showing supported reason labels and original notes. Own hold release cannot remove broader customer-wide holds.
- **FR-002**: Case and global actions prepare a delivery hold with a canonical reason and optional note, or release the exact complete active own-hold set. Reject invalid/no-op intents before execution; preserve existing open-commitment rules.
- **FR-003**: Reuse shared application tools and exact state-bound review/confirmation. Snapshot hold identities and contents, recheck current authorization and state, invalidate edited reviews, and preserve tenant/practice boundaries.
- **FR-004**: Attribute hold events to proposal identity and verify exact records, receipt and event. Duplicate execution has one effect; reconciliation never invokes the mutation again. Creation evidence remains valid after later legitimate release; observations remain separate.
- **FR-005**: Matching Chat and Decisions proposals open the same card; URL recovery and register/case refresh remain intact. Placing/releasing a hold does not alter goods, reservations, money or document fulfillment fields.
- **FR-006**: Reuse the corrected shared form layout and four-language light/dark desktop/mobile controls, with loading, empty, error, review and keyboard states. Canonical reason codes remain inspectable; notes remain original escaped content.

## Key Entities
Existing CommitmentHold → Commitment → evidence/source, PartyDeliveryHold → Party, ChangeProposal and BusinessEvent. No additional authority, FK or schema.

## Success Criteria
- **SC-001**: All three entry points complete hold/release with one traceable effect and no stock/financial effect.
- **SC-002**: Every planned stale, foreign, scope, replay and recovery scenario passes without unauthorized release.
- **SC-003**: Reason, note, scope and confirmation are usable in all four languages at desktop and mobile widths without needing an AI provider.

## Assumptions and Dependencies
The owner approved the announced delivery-specific hold/release increment. Existing services define allowed reasons and release all active holds of one commitment; there is no separate release reason. Specs 107/109/116 provide the case, lock and review lifecycle. Backend, frontend, browser and policy checks must pass before completion.

## Requirement Traceability
| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | T004 T008 | T005 T009 |
| FR-002 FR-003 | T004 T008 | T005 T006 T009 |
| FR-004 | T004 | T005 T006 |
| FR-005 | T004 T008 | T006 T009 |
| FR-006 | T008 T010 | T009 |
