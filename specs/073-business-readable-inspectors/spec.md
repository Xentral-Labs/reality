# Feature Specification: Business-readable Inspectors

**Feature Branch**: `073-business-readable-inspectors`
**Created**: 2026-09-04
**Status**: Approved
**Language**: English
**Input**: "Make important Fact, Exception, and operational drill-downs immediately understandable to ERP consultants instead of leading with technical records and identifiers."

## Context and Intent

### Problem

The shared Reality Inspector exposes correct fields, provenance, events, and source
payloads, but its first viewport still reads like a technical record viewer. A Fact such
as gift-wrap intent leads with a predicate, an opaque Commitment ID, and a generic
Source → Fact → Subject chain. Operational Exceptions with identical titles do not show
the affected order or business record prominently enough to distinguish legitimate
separate cases from duplicates. ERP consultants must decode identifiers and open raw
sections before they can answer what is true, which business object is affected, why
Reality believes it, and what should happen next.

### Scope

- Establish one business-first hierarchy for the shared inspector used by Facts,
  Exceptions, Commitments, Documents, Inventory-related records, Payments, Journal,
  Reservations, and Movements.
- Lead with a concise business meaning, current state, best available business reference,
  and next useful action or review guidance.
- Present the Source → Evidence → Reality chain as an explanation of why Reality knows
  the result, using human references where authoritative context exists.
- Keep exact IDs, predicates, event types, raw values, and source payload available in a
  secondary technical disclosure.
- Make repeated Exception titles distinguishable through the affected business reference
  without treating human references as identity.
- Preserve a compact, responsive drawer suitable for desktop and mobile review.

### Non-Goals

- New facts, exception classes, workflow actions, mutations, notifications, or automatic
  remediation.
- New persistence, schema, migrations, copied display fields, or human-number identity.
- Inventing a business reference, explanation, or next step when authoritative context is
  unavailable.
- Replacing the technical Explorer or removing raw traceability.
- Separate inspector implementations for each register.

### Existing Contracts

- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/WEB_UX_MATRIX.md`](../../docs/WEB_UX_MATRIX.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/013-explain-projections/spec.md`](../013-explain-projections/spec.md)
- [`specs/058-runtime-traceability/spec.md`](../058-runtime-traceability/spec.md)
- [`specs/070-activity-business-language/spec.md`](../070-activity-business-language/spec.md)
- [Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand a Fact immediately (Priority: P1)

An ERP consultant opens a Fact and can state what Reality observed, its value, the
affected business object, and the originating business reference without decoding an
opaque identifier.

**Why this priority**: Facts are explicit source-supported observations and should be the
clearest demonstration of why Reality can be trusted.

**Independent Test**: Open a source-backed gift-wrap Fact for an order Commitment and
verify that the first viewport identifies the observation, value, order reference,
subject meaning, and source before technical details are expanded.

**Acceptance Scenarios**:

1. **Given** a source-backed Fact whose subject and source have authoritative business
   context, **When** it is inspected, **Then** the first viewport states the business
   observation and value and names the best available order, document, party, or item
   reference.
2. **Given** a Fact without an external source or resolvable business context, **When** it
   is inspected, **Then** the view says that the observation is manual or internal and
   does not invent a reference.
3. **Given** support detail is needed, **When** Technical details is expanded, **Then** the
   exact Fact ID, subject ID, predicate, source-record ID, timestamps, and activity remain
   available.

### User Story 2 - Distinguish and act on an Exception (Priority: P1)

An operator opens one of several similarly titled Exceptions and immediately sees which
business record it concerns, why it needs attention, and the next appropriate review
step.

**Why this priority**: A decision queue is unsafe when legitimate separate cases look
like duplicate warnings.

**Independent Test**: Create two at-risk Commitments with the same exception title but
different source orders, inspect both, and verify each first viewport names its own
business reference and cause while retaining distinct opaque identities underneath.

**Acceptance Scenarios**:

1. **Given** two Exceptions with the same class and title but different affected records,
   **When** either is inspected, **Then** its business reference and affected record
   context make the cases distinguishable without exposing the opaque ID as the headline.
2. **Given** an Exception with supported operator guidance, **When** it is inspected,
   **Then** the current problem, business impact, reason, and next review step appear
   before trace and raw data.
3. **Given** an Exception has disappeared because Reality changed, **When** its former
   link is opened, **Then** the existing safe not-found behavior remains unchanged.

### User Story 3 - Use one predictable drill-down (Priority: P2)

An ERP consultant can move among linked operational records without relearning the
detail layout or losing access to technical evidence.

**Why this priority**: Consistency reduces investigation time across the daily ERP
surface and prevents one-off drawer designs.

**Independent Test**: Inspect a Fact, Commitment, Document, Reservation, Movement,
Payment, Party, Item, and Exception and verify the same hierarchy and responsive behavior
while record-specific content remains correct.

**Acceptance Scenarios**:

1. **Given** any supported operational record, **When** it opens in the shared inspector,
   **Then** it uses the sequence Summary → Current position → Why Reality knows this →
   Related business context → Technical details.
2. **Given** a linked row in the inspector, **When** the user follows it, **Then** the
   linked record replaces the drawer content in the same hierarchy and tenant context.
3. **Given** a narrow viewport, **When** the inspector opens, **Then** business summary,
   references, actions, and disclosures remain readable without horizontal scrolling.

### Edge Cases

- A Fact value is false, zero, null-like, a decimal, or a long string.
- The Fact subject is a Commitment or DocumentLine and only the shortest true links may
  be followed to source context.
- A manual record has no SourceRecord or Document.
- Several records share the same human reference while retaining different opaque IDs.
- A linked party, item, document, or source is absent or no longer available.
- An Exception carries several causes or a long impact explanation.
- An inspector has no events, no related rows, or no source payload.
- A loading or error state replaces stale content from the previously inspected record.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every supported operational drill-down MUST use one shared business-first
  inspector hierarchy rather than a record-specific card composition.
- **FR-002**: The first viewport MUST identify what the record means, its current state,
  the best available authoritative business reference, and what the user should review
  next when guidance exists.
- **FR-003**: A source-backed Fact MUST present predicate meaning, explicit value,
  affected business subject, observation time, and best available source or document
  reference before opaque identifiers.
- **FR-004**: An operational Exception MUST present problem, impact, affected business
  reference, causes, and available operator guidance before technical trace fields.
- **FR-005**: The explanation chain MUST label why Reality knows the result and use human
  business references when available, while preserving Source → Evidence → Reality order.
- **FR-006**: Exact opaque IDs, predicates, event types, timestamps, raw values, and source
  payload MUST remain available under an explicit secondary technical disclosure.
- **FR-007**: Missing optional context MUST be described honestly or omitted; the product
  MUST NOT invent business references, causes, or actions.
- **FR-008**: Loading, error, empty-related-data, desktop, and mobile states MUST preserve
  the shared hierarchy without showing stale content or requiring horizontal scrolling.
- **FR-009**: Following a linked record MUST keep the user in the same inspector and active
  tenant while replacing the displayed record context.

### Domain and Traceability Requirements

- **DR-001**: Business presentation context MUST be derived through existing tenant-scoped
  shortest true links; no copied business field or new persistence is permitted.
- **DR-002**: SourceRecord, Evidence, Facts, and operational Reality records remain the
  authorities; presentation MUST NOT reinterpret or change their business meaning.
- **DR-003**: Business summaries, references, and guidance MUST come from shared
  tenant-scoped server reads; the browser MUST NOT reconstruct business rules.
- **DR-004**: Human references are display context only and MUST NOT replace opaque record
  identity or relationship traversal.
- **DR-005**: This feature MUST add no schema or migration.

### Key Entities *(when data is involved)*

- **Inspector explanation**: A read-only tenant-scoped presentation of one authoritative
  record, its business meaning, current position, trace, related context, and technical
  evidence.
- **Business reference**: The best available human-facing order, document, party, item, or
  source reference reached through an existing shortest true link; never identity.

## Success Criteria *(mandatory)*

- **SC-001**: In acceptance review, an ERP consultant can identify what a Fact means, its
  value, affected business object, and source reference in under 15 seconds without
  expanding Technical details.
- **SC-002**: Two same-titled Exceptions for different records can be distinguished from
  their first viewport without reading opaque IDs.
- **SC-003**: All supported inspector kinds retain exact Source, Evidence, Reality, event,
  and raw-payload traceability on demand.
- **SC-004**: Desktop and 390-pixel mobile acceptance checks show no horizontal scrolling
  in the business summary and explanation sections.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof or an
  explicitly recorded visual-review result.

## Assumptions and Dependencies

- The shared inspector route remains the single drill-down entry used by the important
  operational registers.
- Existing links provide enough context for the first Fact and Exception improvements;
  unavailable context is represented honestly rather than added to the data model.
- Existing operator guidance in the operational exception catalog remains authoritative.
- The user approved the business-first shared-inspector scope on 2026-09-04.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-008, FR-009 | US3.1-US3.3 | Shared frontend inspector contract and responsive visual review |
| FR-002, FR-003, FR-005-FR-007 | US1.1-US1.3 | Fact inspector API story and frontend hierarchy contract |
| FR-002, FR-004-FR-007 | US2.1-US2.3 | Exception explanation API story and frontend hierarchy contract |
| DR-001-DR-005 | All | Tenant isolation, no-schema review, and shortest-link service tests |
| SC-001-SC-005 | All | Business story, contracts, build, localization audit, and visual review |
