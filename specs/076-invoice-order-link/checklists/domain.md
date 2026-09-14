# Domain Checklist: Invoice Lines Know What They Bill

**Purpose**: Validate the schema addition, the derivations and the catalog authority before implementation  
**Created**: 2026-09-05  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Schema Addition

- [ ] CHK001 Is the column justified by conditions that cannot be expressed without it, rather than by convenience? [Clarity, Spec §Problem, Plan §Constitution Check]
- [ ] CHK002 Is the line-level grain argued from consolidated invoicing and partial delivery, rather than from precision for its own sake? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK003 Is the reference the shortest true link — billed line to agreed line, never through party, item or date? [Completeness, Spec §DR-006]
- [ ] CHK004 Is it explicit that the reference records what was billed and adds no status to either document? [Clarity, Spec §DR-001]
- [ ] CHK005 Is the migration limited to one nullable column with a downgrade that drops it and moves no data? [Completeness, Plan §Data and migration impact]

## Absence as a Statement

- [ ] CHK006 Is the meaning of a null reference fixed as "bills nothing from an order" rather than left as unknown? [Clarity, Spec §FR-003]
- [ ] CHK007 Is the contract that every order-billing line sets the reference stated, together with what breaks if it is not kept? [Completeness, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK008 Is the absence of production data given as the reason no tolerance is built, so a future reader knows the reasoning was conditional? [Clarity, Spec §Clarifications]

## Derivation Correctness

- [ ] CHK009 Are quantities billed required to sum across every referencing invoice line, so partial and consolidated invoicing need no special case? [Completeness, Spec §FR-007]
- [ ] CHK010 Are delivered and received quantities required to come from the existing commitment-to-movement path rather than a second count? [Consistency, Spec §FR-008, DR-003]
- [ ] CHK011 Are the two unreported cells of the four-way square named with their reasons, so their absence reads as a decision? [Clarity, Spec §Non-Goals, Clarifications]
- [ ] CHK012 Is an order line with nothing delivered defined as silent, whatever has been billed? [Coverage, Spec §US1 scenario 5]
- [ ] CHK013 Is the price class scoped to lines that carry a reference, since nothing was agreed for the others? [Clarity, Spec §US3 scenario 3]
- [ ] CHK014 Are mismatched units named as an edge case rather than silently converted? [Clarity, Spec §Edge Cases, Assumptions]

## Validation and Tenancy

- [ ] CHK015 Is a wrong reference refused at recording rather than stored and ignored later? [Completeness, Spec §FR-002]
- [ ] CHK016 Does validation cover another tenant, a non-order document, and the opposite side of the business? [Coverage, Spec §FR-002, Edge Cases]
- [ ] CHK017 Is every read, derivation, validation and explanation required to be tenant-scoped? [Completeness, Spec §DR-005]

## Catalog and Consistency

- [ ] CHK018 Do all three classes carry the description, owner and clearing path Spec 071 made mandatory? [Completeness, Spec §FR-013]
- [ ] CHK019 Are the shipped and billed classes required to name each other, and both the price class? [Consistency, Plan §Design, Tasks T030]
- [ ] CHK020 Is `document_line` as an eighth carrier checked against every consumer that reads a record type? [Coverage, Plan §Review Risks, Tasks T027]
- [ ] CHK021 Is it explicit that no cause is added? [Completeness, Spec §DR-007]

## Scope Held Open

- [ ] CHK022 Is it clear that the financial flow still works on the header amount, and that tax per position, position credits and margin by item all depend on a change this feature does not make? [Clarity, Spec §Non-Goals]
- [ ] CHK023 Is the `credit_note` type without ledger handling recorded as a separate open thread rather than absorbed here? [Clarity, Spec §Non-Goals]

## Acceptance and Traceability

- [ ] CHK024 Are the success criteria measurable without reference to implementation? [Measurability, Spec §SC-001–SC-006]
- [ ] CHK025 Does every FR and DR map to an acceptance scenario and a named proof or a stated review? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product scope for the four decisions was accepted on 2026-09-05. The domain review
  recorded here is still open, and it carries more weight than usual: this is the first
  schema change in this line of work.
