# Feature Specification: Auditable Manual Document-Line Corrections

**Feature Branch**: `[022-auditable-document-line-corrections]`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Close 006/FR-008 with a supported, auditable correction path for existing manual DocumentLines."

## Context and Intent

### Problem

Operators can correct eligible fields on a manually entered Document header, but they
cannot correct an existing manual DocumentLine through a supported application path.
They must currently leave incorrect normalized Evidence in place or work around the
system, weakening trust, traceability, and tenant-safe interface equivalence.

### Scope

- Correct the lines of an existing manually entered Document through the shared
  application boundary.
- Validate the corrected evidence with the same business rules and tenant boundaries as
  initial manual entry.
- Preserve an audit trail that identifies the correction, the affected evidence, and
  the fields or lines that changed.
- Expose the correction consistently to authorized interfaces and explanation paths.
- Provide executable proof for the previously documented `006/FR-008` gap.

### Non-Goals

- Correcting externally sourced evidence, which continues to require a new immutable
  SourceRecord version and re-interpretation.
- Reversing or rewriting Commitments, Reservations, Movements, or LedgerEntries.
- Adding operational status fields to Document or DocumentLine.
- Introducing approval workflows, bulk corrections, or arbitrary schema expansion.
- Changing the meaning of human document numbers, line numbers, or source references
  into identity.

### Existing Contracts

- `specs/006-documents-evidence/spec.md` (`FR-008` and correction baseline)
- `.specify/memory/constitution.md` (Source → Evidence → Reality and correction rules)
- `docs/WEB_SPEC.md` (Documents and shared-service correction behavior)
- `docs/features/operational_fields.md` (stored Evidence versus derived Reality)
- `docs/SPEC_COVERAGE_MATRIX.md` (documented gap inventory)

## Clarifications

### Session 2026-08-31

- Q: What happens when economically meaningful line Evidence already has linked Reality? → A: Reject the correction and direct the operator to the owning Reality correction workflow.
- Q: What is the authoritative correction request shape? → A: An atomic full replacement snapshot containing all intended lines.
- Approval: Product owner approved the specification on 2026-08-31.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct Manual Line Evidence (Priority: P1)

An authorized operator corrects inaccurate line evidence on a manually entered
Document and can verify exactly what changed without losing the prior audit context.

**Why this priority**: This is the missing capability identified by `006/FR-008` and
is the smallest slice that restores trustworthy manual Evidence.

**Independent Test**: Create a manual Document with lines, submit a valid correction,
and verify the resulting line evidence, unchanged unrelated values, and correction
audit using only public application behavior.

**Acceptance Scenarios**:

1. **Given** a tenant-owned manual Document with valid lines and no protected
   downstream consequences, **When** an authorized operator submits a valid line
   correction, **Then** the intended corrected Evidence is available atomically and an
   audit record identifies the document and the exact line-level changes.
2. **Given** a correction containing an item, unit, quantity, amount, or reference that
   violates manual-entry rules, **When** it is submitted, **Then** the entire correction
   is rejected and the existing Evidence and Reality remain unchanged.
3. **Given** an externally sourced Document, **When** a manual line correction is
   attempted, **Then** it is rejected with guidance to use source version correction.

---

### User Story 2 - Preserve Reality Boundaries (Priority: P2)

An operator receives a safe, explicit outcome when corrected Evidence could conflict
with Reality that has already been derived from the Document or its lines.

**Why this priority**: Evidence correction must never silently rewrite operational or
financial truth.

**Independent Test**: Derive a Commitment or LedgerEntry from manual Evidence, attempt
an economically meaningful line correction, and verify the approved boundary behavior
and the unchanged downstream records.

**Acceptance Scenarios**:

1. **Given** a manual Document or line with linked Reality, **When** an operator requests
   an economically meaningful line correction, **Then** the system rejects the request,
   leaves Evidence and Reality unchanged, and directs the operator to the owning Reality
   correction workflow.
2. **Given** a rejected correction, **When** the operator inspects the result, **Then**
   the reason and the appropriate owning correction workflow are clear.

---

### User Story 3 - Use One Tenant-Safe Capability (Priority: P3)

An authorized caller uses the same correction semantics from every supported interface,
while another tenant cannot observe or alter the evidence.

**Why this priority**: Interface-specific rules or missing tenant filters would make the
correction unsafe even if the core behavior worked.

**Independent Test**: Exercise the shared service through its supported adapters and
attempt the same operation with another tenant's identifiers.

**Acceptance Scenarios**:

1. **Given** equivalent valid requests from supported interfaces, **When** each request
   reaches the application boundary, **Then** validation, correction, audit, and outcome
   semantics are equivalent.
2. **Given** a Document, line, item, or related identifier owned by another tenant,
   **When** a correction is attempted, **Then** no cross-tenant evidence is disclosed or
   changed and no audit record leaks protected details.
3. **Given** a mutating chat or agent request, **When** confirmation has not been
   provided, **Then** no correction is committed.

### Edge Cases

- A correction adds or removes lines rather than only changing values.
- Submitted line references are duplicated, omitted, reordered, or unknown.
- The correction contains zero lines, zero or negative quantities, invalid units,
  inconsistent currency values, or an item from another tenant.
- The Document has changed since the operator loaded the correction form.
- Audit recording or validation fails partway through the request.
- A retry submits the same intended correction after the first request succeeded.
- A manual Document has no SourceRecord and must remain explainable.
- Reality links exist at Document level, line level, or both.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an authorized, tenant-scoped application operation
  for correcting existing DocumentLines belonging to a manually entered Document.
- **FR-002**: The correction MUST validate all submitted line Evidence using the same
  domain rules as manual Document creation, including tenant ownership of referenced
  entities.
- **FR-003**: The correction and its audit record MUST succeed atomically; any validation,
  concurrency, or persistence failure MUST leave existing Evidence and Reality unchanged.
- **FR-004**: The audit record MUST identify the corrected Document, actor context when
  available, time, and an unambiguous before/after description of every added, removed,
  or changed line value without using human references as identity.
- **FR-005**: The system MUST reject manual line correction for Evidence linked to an
  external SourceRecord and direct callers to the immutable source-version workflow.
- **FR-006**: The system MUST NOT implicitly create, update, cancel, reverse, or delete
  Commitments, Reservations, Movements, or LedgerEntries as a side effect of an Evidence
  correction.
- **FR-007**: When Reality already references the Document or any of its lines, the
  system MUST reject economically meaningful line corrections, leave Evidence and
  Reality unchanged, and direct the operator to the owning Reality correction workflow.
- **FR-008**: The correction request MUST provide one atomic full replacement snapshot
  containing every intended line; omission removes an existing line, a line without an
  existing opaque identity adds a line with a system-assigned identity, and inclusion
  of an existing opaque line identity retains or changes that line.
- **FR-009**: The correction MUST detect stale concurrent edits and reject them rather
  than silently overwriting a newer accepted Evidence state.
- **FR-010**: Retrying an already accepted identical request MUST NOT create a second
  effective correction or ambiguous audit history.
- **FR-011**: Supported API, Web, CLI, MCP, chat, and agent paths MUST delegate to the
  same correction operation rather than reproduce validation or business rules.
- **FR-012**: Mutating chat and agent correction requests MUST require explicit
  confirmation before commit; read-only preview and explanation MUST NOT require it.
- **FR-013**: Document detail and inspection MUST explain the current manual line
  Evidence and its correction history without presenting Evidence as operational truth.

### Domain and Traceability Requirements

- **DR-001**: Manual Document and DocumentLine remain Evidence; Source is not invented
  for manual entry, and linked Reality remains independently authoritative.
- **DR-002**: DocumentLine MUST retain its shortest true Document relationship, while
  downstream Reality MUST retain only its already proven Evidence links.
- **DR-003**: Tenant identity MUST be enforced on every lookup and relationship used by
  correction, audit, preview, and explanation paths.
- **DR-004**: Human document numbers, line numbers, SKUs, and references MUST remain
  display or matching values and MUST NOT become correction identity.
- **DR-005**: Operational state shown after a correction MUST continue to be derived
  from Reality and MUST NOT be stored on Document or DocumentLine.

### Key Entities *(when data is involved)*

- **Document**: Tenant-scoped normalized manual Evidence header that owns the lines being
  corrected and may already be referenced by Reality.
- **DocumentLine**: Tenant-scoped normalized line Evidence identified by an opaque ID and
  related to its Document through the shortest true link.
- **BusinessEvent**: Tenant-scoped audit evidence describing an accepted correction and
  its before/after line changes.
- **Reality records**: Commitments, Reservations, Movements, and LedgerEntries whose
  operational or financial meaning is never silently rewritten by this feature.

## Success Criteria *(mandatory)*

- **SC-001**: All valid supported kinds of manual line change complete atomically and
  produce an exact before/after audit description in executable business-story tests.
- **SC-002**: Invalid, stale, external-source, and cross-tenant attempts leave Evidence
  and Reality unchanged in 100% of covered cases.
- **SC-003**: Corrections involving existing Reality cause zero implicit downstream
  record mutations in all executable correction-boundary tests.
- **SC-004**: Equivalent requests through every supported interface produce the same
  observable correction and rejection semantics.
- **SC-005**: Document inspection can explain the accepted correction history and current
  Evidence through opaque relationships without adding operational status fields.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Existing authorization, tenant context, manual-entry validation, BusinessEvent audit,
  and Document inspection capabilities will be reused.
- Header correction remains governed by the existing shared operation; this feature may
  coordinate header and line changes only when required for one atomic Evidence result.
- External correction remains governed by immutable SourceRecord versioning.
- Owning Reality correction workflows are separate features and are not implemented here.
- The implementation plan must prove that any required persistence change has a repeated
  core-logic use case before expanding the schema.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-004 | US1.1–US1.2 | Manual line correction business-story and atomicity tests |
| FR-005 | US1.3 | External Evidence rejection test |
| FR-006–FR-008 | US1.1, US2.1–US2.2 | Full-snapshot and Reality-boundary tests |
| FR-009–FR-010 | Edge cases: concurrency and retry | Stale request and idempotent retry tests |
| FR-011–FR-012 | US3.1, US3.3 | Adapter-equivalence and confirmation tests |
| FR-013 | US2.2 | Document inspection and correction-history test |
| DR-001–DR-002 | US1.1, US2.1 | Evidence/Reality relationship tests |
| DR-003–DR-004 | US3.2 | Tenant-isolation and opaque-identity tests |
| DR-005 | US2.1 | Operational-field regression test |
