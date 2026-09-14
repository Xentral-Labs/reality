# Feature Specification: Complete Operational Exception Coverage

**Feature Branch**: `[020-exception-class-coverage]`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Close 013/FR-005 with deterministic derivation and focused executable proof for every documented initial operational exception class."

## Context and Intent

### Problem

The operational exception contract documents six initial taxonomy entries, but current
focused evidence proves only commitment shortage/risk behavior. Operators cannot rely on the
queue as a complete, consistently explainable view of the documented conditions, and
future changes can silently leave a class without derivation or proof.

### Scope

- Establish one stable, reviewable inventory of all documented initial exception classes.
- Derive every visible class and documented cause from current tenant-owned Source,
  Evidence, or Reality records.
- Give every exception a stable class identifier, severity, summary, authoritative
  record identity, impact context, and explanation path.
- Prove appearance, explanation, tenant isolation, and cause-based disappearance for
  every visible class and cause with focused business stories.
- Detect documentation, derivation, and evidence drift when the class inventory changes.
- Close only the accepted `013/FR-005` coverage gap after all evidence passes.

### Non-Goals

- Persisted exception tickets, acknowledgement, assignment, manual closure, or history.
- New operational state on Documents or other Evidence records.
- Automatic remediation or new mutation commands.
- Notification, escalation, scheduling, or configurable severity policy.
- New accounting matching behavior beyond reporting an already observable unmatched
  financial condition.
- Schema changes, migrations, or typed fields added solely for exception derivation.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/013-explain-projections/spec.md`](../013-explain-projections/spec.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/TEST_STRATEGY.md`](../../docs/TEST_STRATEGY.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-08-31

- Q: Should outgoing commitment at risk and insufficient reservation appear as two
  entries or one umbrella entry? → A: Use one `outgoing_commitment_at_risk` queue entry
  with `insufficient_reservation` as its stable cause; never emit a duplicate entry.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Every Documented Exception Class (Priority: P1)

As Head of Operations, I can rely on the exception queue to surface each documented
initial condition from authoritative business records.

**Why this priority**: A documented queue that silently omits known conditions creates
false confidence and cannot serve as an operational work surface.

**Independent Test**: Build one controlled tenant story for each approved class, read
the queue, and verify the exact class, severity, authoritative record, and impact.

**Acceptance Scenarios**:

1. **Given** each documented class cause exists, **When** the queue is read, **Then**
   each cause produces the expected stable class identifier and authoritative record.
2. **Given** a populated second tenant has the same human identifiers and its own
   exception causes, **When** the first tenant reads its queue, **Then** no foreign
   exception or foreign contribution appears.
3. **Given** no exception cause exists, **When** the queue is read, **Then** it is empty
   and no placeholder or stored ticket remains.

---

### User Story 2 - Explain and Remediate a Derived Exception (Priority: P1)

As an operator, I can inspect any current exception, understand its Source/Evidence/
Reality cause, and make it disappear by correcting that cause through the owning action.

**Why this priority**: A queue item is useful only when its cause and resolution path are
reproducible without editing the derived view.

**Independent Test**: For each class, explain the current record, perform the existing
owning remediation where one is available, and verify that refresh removes only the
resolved condition.

**Acceptance Scenarios**:

1. **Given** a current exception, **When** it is explained, **Then** the result identifies
   its class, authoritative record, causal values, and the shortest available path to
   Evidence and Source.
2. **Given** the authoritative cause is corrected through an existing business action,
   **When** exceptions refresh, **Then** that exception disappears without exception
   state being edited.
3. **Given** a stale, unknown, resolved, or foreign exception identity, **When** it is
   explained, **Then** it returns the same non-disclosing not-found outcome.

---

### User Story 3 - Prevent Exception Coverage Drift (Priority: P1)

As a reviewer, I can detect when documentation, class derivation, or focused evidence
falls out of sync.

**Why this priority**: Closing the gap must remain true when new exception classes or
derivation paths are added later.

**Independent Test**: Introduce controlled missing, stale, duplicate, and unproven class
entries and verify that the coverage gate names the exact mismatch deterministically.

**Acceptance Scenarios**:

1. **Given** the approved initial taxonomy, **When** coverage is validated, **Then**
   every visible class and cause maps exactly once to derivation authority and focused evidence.
2. **Given** a documented class lacks derivation or evidence, **When** validation runs,
   **Then** it fails and names that class.
3. **Given** a stale or duplicate implementation class is present, **When** validation
   runs, **Then** it fails without hiding any other mismatch.

---

### User Story 4 - Close the Accepted Baseline Gap (Priority: P2)

As a product owner, I can verify that `013/FR-005` is no longer an accepted uncertainty
while all unrelated gaps remain visible.

**Why this priority**: The baseline must reflect evidence, not implementation intent.

**Independent Test**: Run every visible-class and cause story plus the coverage gate,
then compare the baseline and coverage matrix before and after the single gap closure.

**Acceptance Scenarios**:

1. **Given** all class derivations and focused proofs pass, **When** the baseline is
   reviewed, **Then** `013/FR-005` is `Verified as-is` with exact evidence references.
2. **Given** any class remains missing or unproven, **When** closure is attempted,
   **Then** `013/FR-005` remains a documented gap.
3. **Given** the gap closes, **When** the coverage matrix is compared, **Then** only
   `013/FR-005` and the corresponding counts change.

### Edge Cases

- One authoritative record satisfies more than one class condition.
- A cause changes between queue read and explanation.
- A commitment has no due date or no optional Evidence/Source chain.
- An import failure has no user-facing error detail.
- A movement has a Source link but no Commitment, or a reason but no Source link.
- A payment is partially allocated rather than wholly unmatched.
- Duplicate human document, source, party, or item identifiers exist across tenants.
- A class is documented with a display label but lacks a stable identifier.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain one stable initial taxonomy containing five
  visible queue classes—outgoing commitment at risk, overdue incoming supplier
  commitment, source interpretation failure, unexplained movement where a link is
  expected, and unmatched financial event when ledger matching exists—and the mandatory
  `insufficient_reservation` cause under outgoing commitment risk.
- **FR-002**: Every visible class MUST have a stable machine-readable identifier,
  operator label, default severity, derivation authority, authoritative record type,
  and focused evidence. Every documented cause MUST have a stable machine-readable
  identifier, operator label, parent class, governing authority, and focused evidence,
  and MUST inherit the parent class's default severity, derivation authority, and
  authoritative record type.
- **FR-003**: Exception derivation MUST use current authoritative tenant-owned records
  and MUST NOT depend on mutable exception ticket state.
- **FR-004**: An insufficient Reservation MUST produce exactly one visible
  `outgoing_commitment_at_risk` queue entry whose stable cause is
  `insufficient_reservation`; the cause MUST remain independently testable and MUST NOT
  produce a second queue entry for the same condition.
- **FR-005**: An overdue incoming supplier commitment MUST derive only when an open
  supplier-delivery commitment has remaining quantity and its due time is in the past;
  missing due times MUST NOT be treated as overdue.
- **FR-006**: A source interpretation failure MUST derive from a currently failed source
  processing attempt and identify both the failed processing record and immutable Source.
- **FR-007**: An unexplained movement MUST derive only for a movement type that requires
  business context when neither an expected Commitment/Source link nor a non-empty
  operator reason explains it; ordinary opening stock and fully linked execution MUST
  NOT be classified as unexplained.
- **FR-008**: An unmatched financial event MUST derive from the unmatched remainder of a
  posted customer or supplier payment on a control account; fully allocated payments
  MUST NOT appear, and partial allocation MUST report only the remaining amount.
- **FR-009**: Every emitted exception MUST identify its class, severity, authoritative
  record identity, concise impact, and the causal values needed to reproduce it.
- **FR-010**: Listing, explanation, projections, Web/API, tools, Chat, and MCP MUST share
  the same tenant-scoped exception derivation rather than implement class rules separately.
- **FR-011**: Unknown, resolved, stale, and foreign exception identities MUST be
  non-disclosing and MUST NOT return another tenant's records or cause details.
- **FR-012**: Correcting the authoritative cause through an existing owning action MUST
  remove the exception on refresh without editing or deleting exception state.
- **FR-013**: A deterministic coverage gate MUST fail for missing, stale, duplicate, or
  unproven documented classes and MUST report mismatches in stable class order.
- **FR-014**: `013/FR-005` MUST remain a documented gap until all five visible class
  derivations and the documented cause have focused proof, and all shared-boundary,
  tenant, and owner reviews pass.

### Domain and Traceability Requirements

- **DR-001**: Source, Evidence, and Reality remain authoritative; exceptions only expose
  current derived conditions and never become operational truth.
- **DR-002**: Every exception MUST use the shortest true opaque relationship to its
  authoritative record and traverse existing links to Evidence and Source when present.
- **DR-003**: Missing optional Evidence or Source MUST be explicit and MUST NOT make an
  otherwise valid Reality exception unexplained.
- **DR-004**: Every exception query and explanation MUST enforce tenant scope; human
  numbers, codes, labels, and external IDs MUST NOT establish identity.
- **DR-005**: Remediation MUST use the owning application service and MUST NOT directly
  mutate projection, exception, Document, or Source state.
- **DR-006**: This feature MUST NOT add schema, duplicate relationships, mutate immutable
  Source payloads, or introduce adapter-specific business rules.

### Key Entities *(when data is involved)*

- **Exception Class Definition**: Stable derived-condition identity with label, severity,
  authority, record type, and focused evidence.
- **Operational Exception**: Current derived observation linking one class to one
  authoritative tenant-owned record and reproducible impact values.
- **Authoritative Cause**: Existing Commitment, Reservation, Import processing record,
  Movement, Ledger posting/allocation, and related Evidence/Source records.

## Success Criteria *(mandatory)*

- **SC-001**: All five visible initial classes and the documented
  `insufficient_reservation` cause have deterministic derivation and at least one focused
  positive, negative, tenant-isolation, and explanation proof, plus either clearing proof
  through an existing owning action or explicit proof that no retroactive remediation
  exists.
- **SC-002**: A controlled story containing every approved condition produces exactly
  five visible class identities, includes `insufficient_reservation` only as the cause
  of outgoing commitment risk, and produces no duplicate or undocumented entry.
- **SC-003**: Correcting each remediable cause removes 100% of the corresponding current
  exceptions without changing exception state directly.
- **SC-004**: A populated foreign tenant contributes zero queue entries, amounts,
  quantities, record identities, or explanation details to the local tenant.
- **SC-005**: Missing, stale, duplicate, or unproven class fixtures fail the coverage
  gate and name every mismatch deterministically.
- **SC-006**: Existing application interfaces return class-consistent results from the
  shared derivation, with no interface-specific class rule.
- **SC-007**: No schema, migration, new stored operational state, or Source payload
  mutation is introduced.
- **SC-008**: Only `013/FR-005` is removed from accepted gaps and all unrelated baseline
  decisions remain unchanged.
- **SC-009**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The six-entry taxonomy in the existing Operational Exceptions contract is the complete
  initial V0 inventory; it contains five visible classes and one cause. Adding another
  visible class or cause requires a specification update.
- Current commitments, import processing records, movements, ledger entries,
  allocations, Documents, and SourceRecords contain sufficient authoritative data for
  the specified derivations.
- Clock-dependent stories use a controlled business time so overdue results are stable.
- Existing remediation actions are reused where available; a class whose cause cannot
  currently be corrected remains explainable but does not justify a new mutation here.
- Exception class definitions may be source-controlled authority but are not persisted
  business records.

## Open Questions

No open product questions remain. The owner selected one outgoing-risk umbrella entry
with an independently testable insufficient-reservation cause on 2026-08-31 and
approved the complete specification on 2026-08-31.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 scenarios 1–3; US3 scenario 1 | class inventory and derivation stories |
| FR-004 | US1 scenario 1; US2 scenarios 1–2 | approved outgoing-risk/reservation behavior |
| FR-005–FR-008 | US1 scenarios 1–3; US2 scenarios 1–2 | one focused story per supplier, source, movement, and finance class |
| FR-009–FR-012 | US2 scenarios 1–3 | explanation, non-disclosure, shared-boundary, and clearing proof |
| FR-013 | US3 scenarios 1–3 | deterministic coverage-drift tests |
| FR-014 | US4 scenarios 1–3 | baseline and policy regression gate |
| DR-001–DR-006 | US1–US4 | authority, lineage, tenancy, remediation, and no-schema review |
