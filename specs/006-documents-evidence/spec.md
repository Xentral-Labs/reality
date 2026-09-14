# Feature Specification: Documents and Evidence Baseline

**Baseline ID**: `006-documents-evidence`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline the existing normalized Document and DocumentLine evidence behavior, traceability, and correction rules."

## Context and Intent

### Problem

Operators need normalized business evidence they can read and trace without turning
documents into the operational authority. This baseline defines what Documents and
DocumentLines record, how manual and external evidence differ, how corrections remain
auditable, and how derived Reality is explained.

### Scope

- Tenant-scoped normalized Document headers and DocumentLines.
- Atomic manual evidence entry with opaque master-data relationships.
- Optional immutable SourceRecord provenance for externally interpreted evidence.
- Typed commercial and timing fields already required by business behavior.
- Manual header correction, externally sourced correction through a new source version,
  and economic-field locking after Reality exists.
- Document register/detail and Inspector trace from Source through Evidence to Reality.

### Non-Goals

- Delivery, reservation, purchase-fulfilment, inventory, payment, or posting status on
  Document or DocumentLine.
- Treating document numbers or upstream line IDs as internal identity.
- Inferring Commitments, Movements, or Ledger Entries from manual evidence entry.
- A generic document workflow, approval state machine, attachment manager, or OCR.
- Duplicating source or document links onto Reality when a shorter true link exists.

### Existing Contracts

- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/features/shopify_ingestion.md`](../../docs/features/shopify_ingestion.md)
- [`docs/features/operational_fields.md`](../../docs/features/operational_fields.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

A Document and its lines are normalized Evidence of a business communication or
transaction. Evidence may be entered manually or interpreted from one immutable
SourceRecord. Manual entry records the header and lines atomically but deliberately
does not create operational Reality. Known interpreters may create both Evidence and
explicit downstream Reality through their owning services.

Manual document headers can be corrected through the shared service and emit an audit
event. Once a Commitment or LedgerEntry depends on the evidence, economic identity
fields become read-only. Externally sourced evidence is never overwritten; its
correction begins with a new immutable version in the same SourceStream. A general
correction operation for existing manual DocumentLines is not currently proven.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record Manual Evidence (Priority: P1)

As an operator, I can record a normalized document header and one or more lines without
silently creating fulfilment, stock, or accounting state.

**Why this priority**: Evidence must be useful independently while Reality remains
explicit and derived from its own authoritative records.

**Independent Test**: Submit a manual document with tenant-owned party, item, currency,
unit, and line values; verify atomic Evidence and the absence of inferred Reality.

**Acceptance Scenarios**:

1. **Given** valid tenant-owned references and at least one line, **When** manual
   evidence is recorded, **Then** its Document and all DocumentLines are created
   atomically with opaque relationships.
2. **Given** line quantity and unit price, **When** the document is created, **Then** its
   normalized monetary total is reproducible from its lines.
3. **Given** successful manual entry, **When** Reality registers are inspected, **Then**
   no Commitment, Reservation, Movement, or LedgerEntry was implicitly created.
4. **Given** a foreign-tenant reference, **When** entry is attempted, **Then** it fails
   without disclosing or linking the foreign record.

### User Story 2 - Interpret External Evidence (Priority: P1)

As an operator, I can see normalized evidence produced from a known external source and
still inspect exactly what the source supplied.

**Why this priority**: Normalization is useful only if it does not replace immutable
source truth.

**Independent Test**: Interpret a Shopify order and navigate from Document and lines to
the complete SourceRecord and to the minimal Reality created from the evidence.

**Acceptance Scenarios**:

1. **Given** a known valid source, **When** interpretation succeeds, **Then** one
   normalized Document and its supported lines link to that SourceRecord.
2. **Given** upstream fields not typed on the Evidence model, **When** the document is
   viewed, **Then** those fields remain available in raw source payload.
3. **Given** an upstream document or line number, **When** Evidence is stored, **Then**
   the human number remains a reference and opaque IDs remain identity.

### User Story 3 - Correct Evidence Without Rewriting History (Priority: P1)

As an operator, I can correct eligible evidence while preserving its audit and source
history and protecting Reality already derived from it.

**Why this priority**: Corrections must not make historical explanations false.

**Independent Test**: Correct a manual header before and after linked Reality exists,
then request a correction to externally sourced evidence and inspect events and source
versions.

**Acceptance Scenarios**:

1. **Given** manual evidence with no derived Reality, **When** an eligible header field
   is corrected, **Then** the value changes through the shared service and an event
   lists the changed fields.
2. **Given** linked Commitments or LedgerEntries, **When** type, party, currency, or
   gross amount is changed, **Then** the correction is rejected.
3. **Given** externally sourced evidence, **When** a correction is submitted, **Then** a
   new immutable source version and ImportJob are appended and the prior payload stays
   unchanged.
4. **Given** an existing manual line requires correction, **When** an operator attempts
   it, **Then** the current product lacks a proven supported line-correction command and
   the limitation remains visible.

### User Story 4 - Explain Evidence and Derived Reality (Priority: P2)

As an operator, I can inspect a document and distinguish its normalized Evidence from
the original Source and any Reality derived from it.

**Why this priority**: The product promise is simple operational use with full
explainability underneath.

**Independent Test**: Open sourced and manual document detail/Inspector views and
verify headers, lines, source stage, raw payload availability, and linked Reality.

**Acceptance Scenarios**:

1. **Given** sourced evidence, **When** its Inspector opens, **Then** Source, Evidence,
   and Reality appear as distinct linked stages and raw source is available.
2. **Given** manual evidence, **When** its detail opens, **Then** all typed fields and
   lines are visible without pretending an external source exists.
3. **Given** derived Commitments or LedgerEntries, **When** document detail opens,
   **Then** operational state is shown from those records rather than a document status.

### Edge Cases

- A document number repeats within or across tenants.
- A manual document has zero lines, negative values, mixed currencies, or invalid units.
- A DocumentLine references an item belonging to another tenant.
- A correction changes only presentation/reference fields after Reality exists.
- A source correction arrives stale or conflicts with the current upstream timestamp.
- Interpretation retries after Evidence was already created.
- A manual document has no SourceRecord and must still be explainable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Document and DocumentLine MUST be tenant-scoped normalized Evidence and
  MUST use opaque IDs for identity and relationships.
- **FR-002**: Manual entry MUST create one Document and all submitted DocumentLines
  atomically through the shared application boundary.
- **FR-003**: Manual evidence entry MUST NOT implicitly create Commitments,
  Reservations, Movements, LedgerEntries, or their operational states.
- **FR-004**: Externally interpreted Evidence MUST link to its immutable SourceRecord;
  unknown upstream fields MUST remain available in the lossless payload.
- **FR-005**: Document and DocumentLine MUST NOT store delivery, reservation, purchase
  fulfilment, inventory, payment, or ledger-posting status.
- **FR-006**: Typed Evidence fields MUST be limited to values repeatedly required for
  calculation, filtering, joining, constraint, prediction, or action.
- **FR-007**: Eligible manual header corrections MUST use the shared service and emit a
  tenant-scoped event identifying changed fields.
- **FR-008**: Operators MUST have an auditable supported correction path for existing
  manual DocumentLines.
- **FR-009**: Document type, party, currency, and gross amount MUST become read-only
  after Commitments or LedgerEntries are derived from the Document.
- **FR-010**: Externally sourced Evidence MUST NOT be overwritten; correction MUST append
  a SourceRecord version to the same stream for retryable interpretation.
- **FR-011**: Document detail MUST expose all typed header and line fields plus source
  identity and raw payload when a SourceRecord exists.
- **FR-012**: Document explanation MUST derive operational state from linked Reality
  records and MUST distinguish Source, Evidence, and Reality visually and semantically.
- **FR-013**: All document entry, correction, lookup, and explanation paths MUST enforce
  tenant scope and use the same application services across interfaces.

### Domain and Traceability Requirements

- **DR-001**: The canonical externally sourced chain is SourceRecord → Document or
  DocumentLine → the applicable Reality record.
- **DR-002**: A Commitment MAY reference Document and DocumentLine; Reservation MUST
  link only to Commitment and MUST NOT duplicate Evidence or Source links.
- **DR-003**: Movement MUST NOT gain a Document or DocumentLine link without a proven
  scenario; Ledger defaults to Document-level provenance.
- **DR-004**: Document numbers, source IDs, SKUs, and line numbers are human/external
  references and MUST NOT replace opaque identity.
- **DR-005**: Operational projections and actions MUST use Reality services, never
  alternative rules inferred from Document fields in Web or agent layers.

### Key Entities

- **Document**: Tenant-scoped normalized evidence header, optionally linked to the
  immutable SourceRecord from which it was interpreted.
- **DocumentLine**: Tenant-scoped normalized evidence line belonging to one Document,
  with optional item relationship and stable source-line reference.
- **SourceRecord**: Immutable external payload and version history for sourced Evidence.
- **BusinessEvent**: Tenant-scoped audit of accepted evidence corrections and other
  domain changes.

## Reality Applicability

- **Source**: Optional for manual Evidence and mandatory for externally interpreted
  Evidence; immutable payload remains the source authority.
- **Evidence**: Document and DocumentLine record normalized claims, not operational state.
- **Reality**: Commitments, Reservations, Movements, and LedgerEntries own operational
  and financial consequences.
- **Shortest links**: DocumentLine → Document; Document → SourceRecord when sourced;
  Commitment → closest Document/Line evidence; Reservation → Commitment.
- **Stored/derived**: Evidence values and provenance are stored. Fulfilment, stock,
  availability, payment, posting, and exception state are derived from Reality.
- **Shared boundary**: Manual entry, correction, interpretation, API, Web, CLI, and
  agent behavior share tenant-scoped application services.
- **Web explanation**: Document detail and Inspector show normalized fields and lines,
  original source where applicable, and linked Reality without operational status fields.

## Success Criteria *(mandatory)*

- **SC-001**: A valid manual header with lines is recorded atomically in one attempt and
  creates zero implicit operational Reality records.
- **SC-002**: Every externally sourced Document can reach its complete immutable payload
  through one direct Evidence-to-Source link.
- **SC-003**: Every displayed operational state for a Document is reproducible from
  linked Reality records with zero document-owned fulfilment or payment status fields.
- **SC-004**: Rejected protected-field corrections leave Evidence and linked Reality
  unchanged in 100% of covered cases.
- **SC-005**: External correction retains every prior payload version and never mutates
  a SourceRecord.
- **SC-006**: Document Inspector tests demonstrate the full Source → Evidence → Reality
  trail for sourced evidence and a bounded Evidence → Reality trail for manual evidence.
- **SC-007**: Every public document operation has tenant-isolation proof or a recorded
  coverage gap.

## Assumptions and Dependencies

- A manual Document legitimately has no SourceRecord; the human command is its bounded
  entry provenance.
- Line totals and document gross amount use Decimal semantics and one document currency.
- Downstream baseline specs own the exact creation and state rules of each Reality type.
- Evidence correction is not a substitute for reversing or correcting derived Reality.

## Open Questions

The product owner approved this baseline on 2026-08-31. Spec 022 subsequently defined
and verified the general manual-line correction path required by FR-008.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-004 | Verified as-is | `docs/DATA_MODEL.md`; `docs/WEB_SPEC.md` | document creation and source interpreters | `tests/test_master_data_api.py`; `tests/test_shopify_and_explain.py` | — |
| FR-005–FR-006 | Verified as-is | Constitution; Data Model; operational-fields contract | Document/DocumentLine models | `tests/test_operational_fields.py`; migration tests | — |
| FR-007 | Verified as-is | `docs/WEB_SPEC.md:Documents` | `services/core.py:correct_manual_document` | `tests/test_document_corrections.py` | — |
| FR-008 | Verified as-is | `docs/WEB_SPEC.md:Documents`; `specs/022-auditable-document-line-corrections/` | `services/core.py:correct_manual_document_lines` | `tests/test_document_corrections.py`; `tests/test_master_data_api.py` | Full snapshot, audit, concurrency, tenant, and Reality-boundary proof |
| FR-009–FR-010 | Verified as-is | `docs/WEB_SPEC.md:Documents`; Shopify contract | manual lock and source-version correction services | `tests/test_document_corrections.py` | — |
| FR-011–FR-012 | Verified as-is | `docs/WEB_SPEC.md:Documents`; Inspect pattern | document detail and Inspector read models | `tests/test_master_data_api.py` document tests | — |
| FR-013 | Verified as-is | Constitution; Web contract | tenant-scoped services and API boundary | document API, correction, and Inspector tests | — |
| DR-001–DR-005 | Verified as-is | Constitution; Data Model; Web contract | evidence and Reality relationships/services | Shopify, Inspector, commitments, and ledger tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Manual document API and service tests |
| FR-004–FR-006 | US2 | Shopify, operational-field, and schema tests |
| FR-007–FR-010 | US3 | Document correction and source-version tests; FR-008 gap |
| FR-011–FR-013 | US4 | Evidence endpoint, document Inspector, and isolation tests |
| DR-001–DR-005 | All stories | Constitution and downstream Reality relationship tests |
