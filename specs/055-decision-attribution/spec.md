# Feature Specification: Decision Attribution

**Feature Branch**: `[055-decision-attribution]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "You cannot see in history who rejected or accepted. Does that information exist?"

## Context and Intent

### Problem

An approval boundary exists to record who crossed it. This one did not.

The audit record keeps who *requested* a change, as `human` or `agent`, and whether it ended executed or rejected. It keeps nothing about who decided it. The decision history register can therefore show that a batch of 31 locations was rejected, but not by whom, and not when.

The information is not merely unshown, it is discarded. The approval route already resolves the signed-in principal and hands it to the service as `confirming_principal`, but the service uses it only for membership mutations and drops it for every other tool. The rejection path never received a principal at all. No security audit event and no business event fills the gap either: the business event links back to the change proposal but carries no user.

### Scope

- Record when a change proposal was settled and by which person.
- Attribute both outcomes, approval and rejection, through the same path.
- Show the person in the decision history register beside who requested the change.
- Keep the record honest where no person can be named.

### Non-Goals

- Reconstructing attribution for decisions settled before this feature; that information never existed.
- Attributing the *request* to an individual; the record keeps the actor kind, and changing that is separate work.
- Changing who may approve, the execution boundary, or the two-step review.
- Turning the register into a user directory, or exposing identities beyond the company whose history is read.

### Existing Contracts

- [Web UI Specification](../../docs/WEB_SPEC.md)
- [Decision History Register](../054-decision-history-table/spec.md)
- [Tenant Access](../003-tenant-access/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See who decided (Priority: P1)

As an owner, I can see for any settled decision which person approved or rejected it, so the approval boundary is auditable rather than merely enforced.

**Why this priority**: An approval nobody can be held to is a formality, not a control.

**Independent Test**: Approve one change and reject another as a signed-in person, then read the decision history register.

**Acceptance Scenarios**:

1. **Given** a person approved a change, **When** its history row renders, **Then** it names that person and states when the decision was taken.
2. **Given** a person rejected a change, **When** its history row renders, **Then** it attributes the rejection the same way an approval is attributed.
3. **Given** a row names a decision maker, **When** it is read beside the requester, **Then** an agent-requested and person-approved change is distinguishable from one a person requested.

### User Story 2 - Read an honest blank (Priority: P1)

As an owner, I can tell the difference between a decision whose maker is unknown and one nobody made, so an empty cell never reads as an attribution.

**Why this priority**: A fabricated or guessed attribution in an audit trail is worse than an absent one.

**Independent Test**: Read history containing a decision settled before this feature, and one taken without a signed-in principal.

**Acceptance Scenarios**:

1. **Given** a decision was settled before attribution existed, **When** its row renders, **Then** both the person and the moment read as unknown rather than as a value.
2. **Given** a decision was taken without a signed-in principal, such as through the CLI, **When** its row renders, **Then** the moment is stated and the person reads as unknown.
3. **Given** a person decided only in another company, **When** this company's history is read, **Then** that person is never named in it.

### Edge Cases

- A decision maker has no display name and must be identified some other way.
- A decision maker's account is later removed or deactivated.
- The same person settles decisions in two companies.
- A page of history mixes attributed and unattributed decisions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Settling a change proposal MUST record the moment it was settled, for both approval and rejection.
- **FR-002**: Settling a change proposal MUST record the deciding person when a signed-in principal made the decision.
- **FR-003**: The rejection path MUST receive and record the principal exactly as the approval path does.
- **FR-004**: A decision taken without a signed-in principal MUST still record the moment and MUST leave the person unrecorded rather than substituting one.
- **FR-005**: Attribution MUST be nullable, so decisions settled before this feature keep an honest blank instead of a fabricated value.
- **FR-006**: The decision history register MUST show the deciding person beside who requested the change, and MUST show the moment of the decision.
- **FR-007**: An unattributed decision MUST render as unknown in the register, distinctly from a named one.
- **FR-008**: A decision maker MUST be identified by display name, falling back to the account address when no display name is set.
- **FR-009**: Every English string added by this feature MUST carry a German, Dutch, and Spanish translation.

### Domain and Traceability Requirements

- **DR-001**: Only a person who actually settled a decision of the company being read MAY be resolved to a name, so the register cannot be used to enumerate accounts.
- **DR-002**: Attribution MUST NOT change who may approve, the execution boundary, the two-step review, or any existing audit value.
- **DR-003**: The reader that resolves names MUST be tenant-scoped and discoverable by the tenant isolation catalog.
- **DR-004**: The schema change MUST be additive and reversible, and MUST NOT require a backfill.

### Key Entities *(when data is involved)*

- **Decision attribution**: The moment a change proposal was settled and, when known, the person who settled it, both nullable on the existing audit record.

## Success Criteria *(mandatory)*

- **SC-001**: For any decision taken by a signed-in person after this feature, the register names that person and the moment.
- **SC-002**: No decision is ever shown with an attribution that was not recorded.
- **SC-003**: Reading one company's history never names a person who decided only in another.
- **SC-004**: The migration applies and reverses without data loss and without a backfill step.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The signed-in principal is already resolved by the web boundary and reaches the approval service; only rejection needed the same wiring.
- Decisions reached through the CLI or an unauthenticated path legitimately have no person, and the record says so.
- Attribution of the *request* to an individual, beyond the actor kind already stored, remains future work.
- The decision history register from 054 provides the surface this attribution is read in.

## Open Questions

None. The absence of historical attribution is a fact about the existing data, recorded above rather than left open.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-004 | US1 scenarios 1-2, US2 scenario 2 | Service tests for approval, rejection and the unattended path |
| FR-005, FR-007 | US2 scenarios 1-2 | History payload test for an unattributed decision |
| FR-006, FR-008 | US1 scenarios 1-3 | Register column contract and named-decider payload test |
| FR-009 | US1 | Localization audit across English, German, Dutch, and Spanish |
| DR-001, DR-003 | US2 scenario 3 | Cross-tenant naming test and tenant isolation catalog coverage |
| DR-002 | US1-US2 | Diff review for unchanged permissions and review flow |
| DR-004 | US2 scenario 1 | Migration upgrade and downgrade test |
| SC-001-SC-005 | All scenarios | Full required quality gates |
