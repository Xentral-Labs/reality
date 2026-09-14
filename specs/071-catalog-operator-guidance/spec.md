# Feature Specification: Operator Guidance in the Exception Catalog

**Feature Branch**: `071-catalog-operator-guidance`
**Created**: 2026-09-04
**Status**: Draft
**Language**: English
**Input**: "The technical catalog page must say what each exception means and who owns it. If that is missing it belongs in the base data, not in a hand-written page."

## Context and Intent

### Problem

An operator reading the technical catalog cannot tell what an exception means. The
generated page for operational exceptions lists a severity, a derivation name, a record
type, an authority reference and a test path. All of it is true and none of it answers the
only question an ERP operator has: what is this telling me, and what do I do about it.

The answers exist, but not where the class is defined. The handbook chapter on exceptions
carries a hand-written table with the exact condition and the responsible role, and the
feature contract carries a hand-written column for how each entry clears. Both were
written once and are maintained by remembering to maintain them. Neither was updated when
Specs 068 and 069 added three classes, so the handbook still describes five of the eight
conditions and names an owner for none of the new ones. The generated page is complete but
says nothing; the readable pages say something but are incomplete.

That split is the defect. A class already cannot exist without a derivation, an authority
and executable evidence, because the catalog gate refuses it. Meaning and ownership are
just as much part of a class as its severity, and holding them anywhere else guarantees
they drift.

### Scope

- Make the business meaning, the operational owner and the clearing path required fields
  of every operational exception class in the closed catalog.
- Refuse a class that lacks them, exactly as the catalog already refuses one that lacks
  evidence.
- Render them on the generated catalog reference so the page answers an operator's
  question without being edited by hand.
- Replace the hand-written per-class tables in the handbook chapter and the feature
  contract with the generated reference, so the same fact is stated in one place.

### Non-Goals

- Translating the guidance. English text is sufficient on both language editions of the
  generated page; only the surrounding headings stay localised.
- Guidance per cause. Causes keep their label and authority; a reason is read through the
  class that carries it.
- Any change to derivation, severity, ordering, identity or the queue itself. No exception
  appears, disappears or changes shape because of this feature.
- Remediation instructions beyond naming the path that clears the condition. The catalog
  states what makes an entry leave, not a procedure.
- New classes, new causes, or a change to the closed vocabularies.
- Schema changes or migrations. The catalog is source-controlled metadata, not tenant data.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/007-core-catalogs/spec.md`](../007-core-catalogs/spec.md)
- [`specs/020-exception-class-coverage/spec.md`](../020-exception-class-coverage/spec.md)
- [`specs/068-promise-coverage-exceptions/spec.md`](../068-promise-coverage-exceptions/spec.md)
- [`specs/069-overdue-receivables/spec.md`](../069-overdue-receivables/spec.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-04

- Q: Where should the operator-facing description live? → A: In the base data. If the
  technical catalog is missing a description, the description belongs in the catalog, not
  in a hand-written page beside it.
- Q: Does the guidance need translating? → A: No. English is sufficient on both editions
  of the generated page.
- Q: What happens to the existing hand-written tables? → A: They are replaced by the
  generated reference. The handbook keeps its narrative about how the queues differ and
  links to the catalog for the per-class facts; the feature contract keeps the
  specification-level mapping of class, cause and authority and stops restating the
  clearing path.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand an Exception Without Asking Anyone (Priority: P1)

An operator opens the technical catalog, finds an exception class, and learns what
condition it reports, which function owns it and what makes it go away — without opening
another page and without asking the team that built it.

**Why this priority**: It is the whole point of the feature.

**Independent Test**: Read the generated catalog page and confirm every class states a
meaning, an owner and a clearing path in plain language, with no class left blank.

**Acceptance Scenarios**:

1. **Given** the generated catalog reference, **When** a class is read, **Then** it states
   in plain language what condition it reports, which operational function owns it, and
   what makes the entry leave the queue.
2. **Given** the German edition of the same page, **When** the same class is read,
   **Then** the guidance is present in English under the localised headings.
3. **Given** the handbook chapter and the feature contract, **When** per-class facts are
   sought, **Then** each points at the generated reference rather than restating them.

### User Story 2 - A Class Cannot Ship Without Its Meaning (Priority: P2)

Whoever adds the next exception class is refused until they have said what it means, who
owns it and how it clears, the same way they are already refused without evidence.

**Why this priority**: It is what stops this defect from recurring, but it is only
observable when someone adds a class.

**Independent Test**: Remove or blank each new field on a candidate catalog and verify the
validation refuses it and names the offending class.

**Acceptance Scenarios**:

1. **Given** a candidate catalog whose class has no description, no owner or no clearing
   path, **When** it is validated, **Then** validation fails and names the class and the
   missing field.
2. **Given** the production catalog, **When** it is loaded, **Then** every class carries
   all three, so the closed catalog is complete by proof rather than by inspection.

### Edge Cases

- A field is present but empty or whitespace only.
- A class has a cause; the cause carries no guidance of its own and must not be required
  to.
- The generated page is regenerated without the formatting pass.
- Guidance text contains characters that need escaping in a Markdown table or heading.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every operational exception class in the closed catalog MUST carry a business
  description, an operational owner and a clearing path.
- **FR-002**: Catalog validation MUST refuse a class whose description, owner or clearing
  path is absent, empty or whitespace only, and MUST name the class and the field.
- **FR-003**: The description MUST state the condition in business terms rather than
  restating the derivation name or the record type.
- **FR-004**: The clearing path MUST state what makes the entry leave the queue, and MUST
  say so explicitly where no remediation exists.
- **FR-005**: The generated catalog reference MUST render all three for every class, on
  both language editions, in English.
- **FR-006**: The generated reference MUST remain generated. No per-class guidance may be
  maintained by hand anywhere else in the documentation.
- **FR-007**: The handbook chapter MUST keep its narrative about how the queues differ and
  MUST reference the generated catalog instead of listing per-class conditions and owners.
- **FR-008**: The feature contract MUST keep the specification-level mapping of class,
  cause and authority and MUST NOT restate the clearing path.
- **FR-009**: No exception's derivation, severity, order, identity, causal values or trace
  may change as a result of this feature.

### Domain and Traceability Requirements

- **DR-001**: The catalog remains the single closed product authority for the exception
  vocabulary. Guidance is metadata about a class, not business state, and is never read to
  make an operational decision.
- **DR-002**: Guidance MUST be validated with the same strictness as the existing required
  metadata, so a class cannot reach the queue without it.
- **DR-003**: Causes keep their existing contract. Requiring guidance on a class MUST NOT
  require it on a cause.
- **DR-004**: The generated pages stay derived artifacts. Their content is proven by the
  catalog they come from, not by review of the page.

### Key Entities *(when data is involved)*

- **Exception class metadata**: The catalog entry, which gains a description, an owner and
  a clearing path beside its existing label, severity, record type, authority and evidence.
- **Generated catalog reference**: The English and German pages derived from that catalog.

## Success Criteria *(mandatory)*

- **SC-001**: An operator can name the meaning, the owner and the clearing path of any of
  the eight classes from the technical catalog alone.
- **SC-002**: No page outside the generated reference lists per-class conditions, owners or
  clearing paths.
- **SC-003**: A class missing any of the three cannot be loaded, and the failure names it.
- **SC-004**: The queue behaves identically before and after: same classes, same order,
  same identities, same values.
- **SC-005**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The eight existing classes get guidance written from what is already known about them:
  the conditions and owners recorded in the handbook chapter for the original five, and
  the specifications for the three added by Specs 068 and 069.
- The owner names an operational function, not a person or a team name, so it stays true
  across organisations.
- English guidance on the German page is acceptable because the audience for the technical
  catalog reads English metadata already — derivation names, record types and test paths
  are English on both editions today.
- The generator continues to require the formatting pass afterwards; that is unchanged by
  this feature and already recorded.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US2 scenario 2 | production catalog completeness test |
| FR-002 | US2 scenario 1 | per-field validation refusal test |
| FR-003 | US1 scenario 1 | production catalog guidance review |
| FR-004 | US1 scenario 1 | production catalog guidance review |
| FR-005 | US1 scenarios 1, 2 | generated page content test |
| FR-006 | US1 scenario 3 | documentation review |
| FR-007 | US1 scenario 3 | documentation review |
| FR-008 | US1 scenario 3 | documentation review |
| FR-009 | US1 scenario 1 | unchanged derivation and ordering suite |
| DR-001 | US2 scenario 2 | catalog authority test |
| DR-002 | US2 scenario 1 | per-field validation refusal test |
| DR-003 | US2 scenario 1 | cause contract regression test |
| DR-004 | US1 scenario 2 | generated page content test |
