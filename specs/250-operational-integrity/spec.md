# Feature Specification: Operational Integrity

**Feature Branch**: `250-operational-integrity`
**Created**: 2026-09-22
**Status**: Draft — awaiting product/domain review
**Language**: English
**Input**: User description: "Correct the operational-integrity defects found by the independent CanisPro B2B MCP audit before improving agent guidance or demo breadth: tracked return dispositions, reservation consistency after quantity revisions, real cancellation, and proposal lifecycle recovery."

## Context and Intent

### Problem

An external agent completed a broad B2B workflow but left states that looked plausible in aggregate while being operationally false in detail. A damaged lot-tracked return remained in quarantine while good stock was moved and written off; a reduced customer promise retained more active reservation than its revised open quantity; a compliance hold was used as a substitute for cancellation; and known failed confirmations remained indefinitely marked as executing. These states make inventory, availability, open work, and agent recovery unreliable.

### Scope

- Resolve an arrived return while preserving its physical tracking identity and explicit link to the return movement.
- Keep active reservations consistent when an open commitment quantity is revised downward.
- Make cancellation of an unfulfilled remainder available through the shared confirmed-action boundary used by Web, MCP, Chat, CLI, and API consumers.
- Distinguish a known refusal with no effect from a genuinely indeterminate execution, and reconcile an indeterminate proposal only from authoritative evidence.
- Expose results that let humans and agents verify the exact operational effect rather than inferring success from transport or aggregate totals.

### Non-Goals

- Changing exact-location reservation into automatic parent/child location aggregation.
- Treating a hold as cancellation or adding delivery lifecycle fields to Documents.
- Automatically retrying an execution whose outcome is genuinely unknown.
- Repairing historical tenant records automatically; repair remains an explicit reviewed action.
- Changing costing, contribution margin, taxation, settlement, dunning, demo profiles, or token authorization.
- Adding warehouse task orchestration, picking strategy, or automated disposition decisions.

### Existing Contracts

- [`specs/008-commitments-holds/spec.md`](../008-commitments-holds/spec.md)
- [`specs/009-inventory-execution/spec.md`](../009-inventory-execution/spec.md)
- [`specs/023-movement-corrections/spec.md`](../023-movement-corrections/spec.md)
- [`specs/059-safe-proposal-confirmation/spec.md`](../059-safe-proposal-confirmation/spec.md)
- [`specs/093-promises-can-be-revised/spec.md`](../093-promises-can-be-revised/spec.md)
- [`specs/139-unified-app-foundation/spec.md`](../139-unified-app-foundation/spec.md)
- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/commitment_holds.md`](../../docs/features/commitment_holds.md)
- [`docs/features/reservations.md`](../../docs/features/reservations.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolve the Exact Returned Stock (Priority: P1)

As a warehouse operator, I can dispose of arrived returned goods without losing or changing their lot, serial, or handling-unit identity, so the stock removed or relocated is exactly the stock that came back.

**Why this priority**: Disposing a different physical identity can destroy good stock while leaving damaged goods available or quarantined, even when the company-wide total still balances.

**Independent Test**: Receive a lot-tracked customer return directly into quarantine while the same item and lot also have stock in a normal location, then confirm scrap, restock, repair, and supplier-return dispositions and reconcile every location and tracking identity.

**Acceptance Scenarios**:

1. **Given** a lot-tracked return arrived in quarantine, **When** its full quantity is scrapped, **Then** the disposition removes that exact lot from quarantine, resolves the return once, and does not move or reduce stock in any other location.
2. **Given** a tracked return, **When** it is restocked or moved for repair, **Then** the resolving movement inherits the return's lot, serial, and handling-unit identities that apply and moves stock from the recorded arrival location to the explicitly reviewed destination.
3. **Given** one return split across multiple dispositions, **When** each part is confirmed, **Then** their sum never exceeds the arrived quantity and each part preserves the same applicable tracking identity.
4. **Given** an untracked return or a return without a particular optional identity, **When** it is resolved, **Then** no tracking identity is fabricated.
5. **Given** a disposition preview, **When** the underlying return or prior dispositions change before confirmation, **Then** stale confirmation is refused without creating a movement.

---

### User Story 2 - Revise a Promise Without Over-Reserving Stock (Priority: P1)

As an order operator, I can confirm a reduced promised quantity and see the reservation consequence before execution, so stock beyond the revised open requirement becomes available without rewriting the counterparty's statement or shipment history.

**Why this priority**: An active reservation above the quantity still promised understates free stock and makes availability and order readiness false.

**Independent Test**: Reserve a customer promise through multiple reservations, fulfil part of it, then confirm several downward and upward revisions and verify promised, fulfilled, active reserved, open, and available quantities after each step.

**Acceptance Scenarios**:

1. **Given** an open commitment with active reservation above its proposed revised open quantity, **When** the revision is reviewed, **Then** the preview identifies the exact reservation quantity that will remain and the exact excess that will be released.
2. **Given** that review is confirmed without intervening change, **When** the revision settles, **Then** the received revision remains append-only, fulfilled history is unchanged, and active reservation does not exceed the revised open quantity.
3. **Given** multiple active reservations, locations, lots, or serial identities, **When** an exact excess cannot be released without choosing which allocation to keep, **Then** review returns the eligible reservation choices and confirmation is refused until the operator submits the opaque reservation IDs and retained quantities to keep; Reality does not silently choose a physical identity or location.
4. **Given** a revision equal to or below already fulfilled quantity, **When** confirmed, **Then** the commitment settles with no open quantity and all remaining active reservations release while movements remain intact.
5. **Given** an increased quantity or a reduction that leaves active reservation within the new open quantity, **When** confirmed, **Then** no unrelated reservation is changed.

---

### User Story 3 - Cancel the Open Remainder Truthfully (Priority: P1)

As an order operator or external agent, I can prepare, review, and confirm cancellation of the unfulfilled remainder of a customer or supplier commitment for an explicit reason, without using a hold or changing the supporting document into operational authority.

**Why this priority**: Holds are temporary execution controls. Using one as cancellation leaves false backlog and misrepresents the customer's or supplier's statement.

**Independent Test**: Cancel an unfulfilled reserved commitment, a partially fulfilled commitment, and a supplier commitment through each public interface and verify one shared result.

**Acceptance Scenarios**:

1. **Given** an unfulfilled commitment with active reservations, **When** cancellation is confirmed, **Then** only its open remainder is cancelled, all active reservations release, physical stock is unchanged, and the commitment is no longer open work.
2. **Given** a partially fulfilled commitment, **When** cancellation is confirmed, **Then** past movements and fulfilled quantity remain, the unfulfilled remainder closes, and no active reservation remains for it.
3. **Given** an active commitment hold, **When** its commitment is cancelled, **Then** the hold is released while its reason and history remain; a hold is never created as a cancellation effect.
4. **Given** a fulfilled or already cancelled commitment, **When** cancellation is prepared or confirmed, **Then** it is refused without changing history.
5. **Given** a document containing multiple commitments, **When** an operator chooses cancellation, **Then** the review identifies the exact opaque commitments and open quantities; document number is display context only and document status is not used as delivery authority.
6. **Given** equivalent confirmed input through Web, MCP, Chat, CLI, or API, **When** it executes, **Then** every interface reaches the same tenant-scoped service and returns the same business outcome and explanation path.

---

### User Story 4 - Recover Proposal State Without Guessing (Priority: P1)

As an operator or agent, I can distinguish a known pre-effect refusal from an execution whose outcome is genuinely unknown, and I can reconcile the latter without blind replay.

**Why this priority**: A permanently executing proposal blocks dependent work; incorrectly retrying an uncertain mutation can duplicate physical or financial effects.

**Independent Test**: Exercise validation failure before handler entry, known transactional rollback, process interruption at the effect boundary, committed effect with lost response, and true unresolved execution, then compare proposal state, evidence, and permitted next action.

**Acceptance Scenarios**:

1. **Given** confirmation fails a validation or authorization check before any handler effect can occur, **When** the response is returned, **Then** the proposal is not left executing and the refusal explains whether fresh review, corrected input, or a different principal is required.
2. **Given** a handler transaction is known to have rolled back completely, **When** failure is returned, **Then** the proposal is not left executing and no effect is reported.
3. **Given** the request may have crossed an effect boundary, **When** no authoritative evidence proves success or rollback, **Then** it remains explicitly unresolved and is never retried automatically.
4. **Given** immutable tenant-scoped evidence proves the exact intended effect committed, **When** the proposal is reconciled, **Then** it settles as executed with a stable receipt and later reads return the same result.
5. **Given** authoritative evidence proves no effect and replay is safe, **When** the proposal is reconciled, **Then** it returns to a reviewable non-executing state without creating an effect.
6. **Given** evidence is absent but absence cannot prove rollback, **When** reconciliation runs, **Then** the proposal remains unresolved and explains why.

### Edge Cases

- The returned quantity is partially dispositioned before a second actor confirms a stale review.
- A return movement references a lot that is now present in several locations.
- A serial-tracked return quantity is not one or identities differ across attempted disposition.
- A quantity revision races a shipment, reservation release, or another revision.
- Fulfilled quantity exceeds the newly stated quantity; both received statements remain true.
- Cancellation races fulfilment, another cancellation, or a reservation mutation.
- A bulk/document cancellation contains a mixture of open, fulfilled, cancelled, or held promises.
- A proposal handler commits an effect but fails before the proposal receipt is stored.
- Matching evidence belongs to another tenant, another proposal, or a different normalized intent.
- Historical bad records already contain excess active reservation or unresolved dispositions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A resolving return movement MUST inherit every applicable tracking identity from the arrived return movement and MUST NOT require the caller to restate that identity.
- **FR-002**: Return disposition MUST use the return's recorded arrival location as its source and MUST retain the direct resolving link to that return movement.
- **FR-003**: Return disposition review MUST show item, quantity, arrival location, applicable tracking identities, destination when applicable, prior resolved quantity, and unresolved quantity.
- **FR-004**: Confirmed dispositions MUST prevent cumulative resolved quantity from exceeding the arrived return quantity under concurrent or repeated confirmation.
- **FR-005**: A downward commitment-quantity revision MUST NOT leave active reserved quantity above the revised open quantity.
- **FR-006**: Revision review MUST disclose the exact reservation consequence before confirmation.
- **FR-007**: Reality MUST release excess reservation automatically only when it can preserve the retained allocation without choosing among different locations or tracking identities; otherwise review MUST return the eligible opaque reservation IDs and quantities, and confirmation MUST require an explicit retained allocation whose total does not exceed revised open quantity.
- **FR-008**: Revision reconciliation MUST preserve the append-only received revision, original commitment, fulfilment movements, released reservation history, and tenant scope.
- **FR-009**: Operators and external agents MUST be able to prepare, review, confirm, explain, and recover cancellation of the open remainder through shared application behavior.
- **FR-010**: Cancellation MUST retain the commitment and fulfilment history, record an explicit reason, close only the unfulfilled remainder, and release its active reservations and active commitment holds.
- **FR-011**: Cancellation MUST NOT create a hold, modify physical stock, delete history, or make Document status the authority for delivery or purchase fulfilment.
- **FR-012**: Cancellation preparation and confirmation MUST reject fulfilled, already cancelled, foreign-tenant, stale, or otherwise ineligible commitments without partial effects.
- **FR-013**: A known refusal before effect or a known complete rollback MUST NOT strand a proposal in executing state.
- **FR-014**: A proposal whose effect boundary may have been crossed MUST remain unresolved until sufficient authoritative evidence proves the exact intended effect or proves replay safe.
- **FR-015**: Reconciliation MUST match tenant, proposal identity, normalized intended action, and immutable correlated evidence; unrelated or merely similar business state MUST NOT settle it.
- **FR-016**: An executed or reconciled proposal MUST return one stable receipt that distinguishes technical execution, applied business effect, current observation, and any remaining work.
- **FR-017**: Web, MCP, Chat, CLI, and API adapters MUST use the same tenant-scoped services for these mutations and reads; mutating Web and agent flows MUST retain preview and explicit confirmation.
- **FR-018**: Each result MUST expose the shortest explanation path from proposal to created or changed Reality records and, where applicable, their Evidence and SourceRecord.
- **FR-019**: Existing historical inconsistencies MUST be discoverable and explainable but MUST NOT be silently rewritten by rollout or ordinary reads.

### Domain and Traceability Requirements

- **DR-001**: Movement remains the sole physical stock authority; disposition creates a resolving Movement rather than a stored stock balance or mutable return status.
- **DR-002**: Return disposition MUST use Movement → resolving Movement as the shortest true link; tracking identity is inherited from physical evidence rather than duplicated from caller input.
- **DR-003**: Commitment and CommitmentRevision remain authorities for the original and newly stated promise; Document remains optional evidence and MUST gain no operational lifecycle field.
- **DR-004**: Reservation remains linked only to Commitment; revision and cancellation MUST NOT add Document, DocumentLine, or Source foreign keys to Reservation.
- **DR-005**: Proposal state is an execution-boundary observation, not business authority; settlement MUST follow the authoritative domain effect and immutable evidence.
- **DR-006**: Every read, preview, mutation, lock, and reconciliation query MUST enforce tenant scope.
- **DR-007**: Human document numbers, lot labels, and external references MUST be display/search values only and MUST NOT establish identity or correlation.
- **DR-008**: No new persistent field or infrastructure is permitted unless planning proves existing records cannot express a required accepted scenario.

### Key Entities

- **Movement**: Append-only physical event, including the arrived return and its exact resolving disposition movement.
- **Tracking identity**: Existing lot, serial unit, or handling unit carried by physical movements.
- **Commitment**: Directional promise whose fulfilled and open quantities are derived.
- **CommitmentRevision**: Append-only received restatement of promised quantity or date.
- **Reservation**: Exact-location and optional tracked allocation to one customer commitment.
- **CommitmentHold**: Temporary execution control that is not cancellation.
- **ChangeProposal**: Reviewed, confirmed execution boundary with recoverable lifecycle.
- **BusinessEvent and SourceRecord**: Immutable correlation and provenance where the operation produces them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In every tracked-return acceptance test, quantity by item, location, lot, serial, and handling unit reconciles exactly before and after disposition; zero unrelated stock changes.
- **SC-002**: Across all tested revision and cancellation sequences, active reserved quantity never exceeds current open quantity after a successful operation.
- **SC-003**: One hundred percent of tested cancellations retain prior movements and released reservation/hold history while leaving zero active allocation for the cancelled remainder.
- **SC-004**: The same cancellation scenario completed through every supported interface yields the same derived commitment state and explanation links.
- **SC-005**: One hundred percent of planted known pre-effect refusals and complete rollbacks finish in a non-executing state, while one hundred percent of genuinely indeterminate cases remain protected from automatic replay.
- **SC-006**: Reconciliation accepts every exact correlated effect and rejects every planted wrong-tenant, wrong-proposal, wrong-intent, and merely similar-state case.
- **SC-007**: An operator or agent can determine from one result whether the request executed, what quantity or records it affected, and what remains unresolved, without comparing aggregate totals.
- **SC-008**: Existing inventory, commitment, correction, proposal-safety, tenancy, Web, MCP, CLI, and documentation verification remain green.

## Assumptions and Dependencies

- Existing cancellation domain behavior in Spec 008 is authoritative and will be exposed rather than reimplemented as document status or a new parallel lifecycle.
- Existing append-only commitment revisions remain received statements. Automatic excess release is allowed only as an explicitly previewed and confirmed operational consequence.
- Reservations remain exact-location allocations; parent warehouse nodes do not imply pickable stock in child locations.
- Existing movement corrections remain the explicit path for repairing already recorded incorrect movements.
- Existing at-most-once proposal semantics remain authoritative: uncertainty is preserved whenever absence of evidence does not prove absence of effect.
- PostgreSQL transaction and locking behavior remains the shared concurrency boundary.
- Applicable long-lived contracts and generated tool documentation will be updated when behavior or public capabilities change.

## Requirement Traceability

| Requirement | Scenario(s) | Planned acceptance evidence |
|---|---|---|
| FR-001–FR-004, DR-001–DR-002 | US1 | Tracked/untracked, split, stale, repeated, concurrent, and cross-location disposition tests |
| FR-005–FR-008, DR-003–DR-004 | US2 | Multi-reservation, fulfilment, revision race, identity ambiguity, and exact availability tests |
| FR-009–FR-012, FR-017–FR-018 | US3 | Shared service plus Web/MCP/Chat/CLI/API contract and business-story tests |
| FR-013–FR-016, DR-005 | US4 | Pre-effect refusal, rollback, interruption, committed-effect, replay-safe, and mismatch tests |
| FR-019, DR-006–DR-008 | All | Historical-read, tenant-isolation, schema review, and relationship review |
