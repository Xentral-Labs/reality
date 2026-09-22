# Operational Integrity Checklist: Operational Integrity

**Purpose**: Validate requirement quality before implementation
**Created**: 2026-09-22
**Feature**: [spec.md](../spec.md)

## Completeness

- [ ] CHK001 Are requirements present for every applicable return identity dimension and for absence of optional identities? [Completeness, Spec FR-001–FR-004]
- [ ] CHK002 Are both unambiguous and ambiguous reservation-reconciliation outcomes specified, including partial retention? [Completeness, Spec FR-005–FR-008]
- [ ] CHK003 Does cancellation cover unfulfilled, partially fulfilled, held, fulfilled, already-cancelled, stale, and cross-tenant commitments? [Coverage, Spec FR-009–FR-012]
- [ ] CHK004 Are all three proposal outcomes—known no effect, exact recorded effect, and genuinely unknown—defined with distinct safe next actions? [Completeness, Spec FR-013–FR-016]
- [ ] CHK005 Are historical inconsistency and repair boundaries explicit enough to prohibit silent rollout repair? [Completeness, Spec FR-019]

## Clarity and Consistency

- [ ] CHK006 Is “unambiguous retained allocation” bounded by exact location and every applicable tracking identity rather than chronology or document context? [Clarity, Spec FR-007]
- [ ] CHK007 Is automatic reservation release consistently described as an explicitly reviewed operational consequence rather than part of the received revision statement? [Consistency, Spec Assumptions]
- [ ] CHK008 Is cancellation consistently the closure of open remainder while fulfilled quantity and Movement history remain intact? [Consistency, Spec FR-010–FR-011]
- [ ] CHK009 Is a hold consistently excluded as cancellation evidence or state? [Consistency, Spec Non-Goals, FR-011]
- [ ] CHK010 Is proposal lifecycle consistently separated from business effect and current observation? [Consistency, Spec FR-014–FR-016]

## Authority and Traceability

- [ ] CHK011 Do requirements preserve Movement as physical authority and the direct return-to-resolving-Movement link? [Domain, Spec DR-001–DR-002]
- [ ] CHK012 Do requirements keep Document outside commitment, reservation, fulfilment, and cancellation authority? [Domain, Spec DR-003–DR-004]
- [ ] CHK013 Is the cancellation reason given durable business evidence outside proposal-only state without adding an unproven typed field? [Authority, Plan §Reality flow]
- [ ] CHK014 Are tenant, proposal, normalized intent, and immutable evidence all required for reconciliation? [Security, Spec FR-015]
- [ ] CHK015 Are human numbers and tracking labels explicitly excluded from identity/correlation? [Domain, Spec DR-007]

## Concurrency and Failure Coverage

- [ ] CHK016 Are stale review outcomes specified for concurrent disposition, revision, shipment, reservation, and cancellation? [Coverage, Spec Edge Cases]
- [ ] CHK017 Is rollback proof required before returning an executing proposal to a replayable state? [Safety, Spec FR-013–FR-015]
- [ ] CHK018 Does the specification avoid treating missing evidence alone as proof that no effect occurred? [Safety, Spec US4]
- [ ] CHK019 Are repeated confirmation and lost-response outcomes measurable without permitting handler reexecution? [Acceptance, Spec SC-005–SC-006]

## Interface and Acceptance Quality

- [ ] CHK020 Is parity required across Web, MCP, Chat, CLI, and API without requiring duplicate business rules? [Coverage, Spec FR-017]
- [ ] CHK021 Are review and receipt fields sufficient to detect the audited wrong-location return even when aggregate quantity balances? [Acceptance, Spec SC-001, SC-007]
- [ ] CHK022 Can every success criterion be verified from planned executable evidence without implementation-specific interpretation? [Measurability, Spec SC-001–SC-008]
- [ ] CHK023 Are generated catalogs and durable feature contracts identified as dependencies when public behavior changes? [Dependency, Spec Assumptions]

## Review

- **Specification reviewer**: Product owner approved scope in conversation on 2026-09-22
- **Domain/architecture reviewer**: Pending
- **Decision**: Draft review checklist; all items remain reviewer-owned and unchecked
