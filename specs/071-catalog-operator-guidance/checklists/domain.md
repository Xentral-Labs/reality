# Domain Checklist: Operator Guidance in the Exception Catalog

**Purpose**: Validate catalog-authority and documentation requirements before implementation  
**Created**: 2026-09-04  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Authority and Drift

- [ ] CHK001 Is it required that guidance is validated as strictly as evidence, so a class cannot reach the queue without it? [Completeness, Spec §FR-002, DR-002]
- [ ] CHK002 Is it explicit that guidance is metadata about a class and is never read to make an operational decision? [Clarity, Spec §DR-001]
- [ ] CHK003 Is the cause contract explicitly left unchanged, so the shared reservation-shortfall reason is not forced to carry text twice? [Coverage, Spec §DR-003]
- [ ] CHK004 Is the recurrence this feature prevents named, rather than the defect being treated as a one-off omission? [Clarity, Spec §Problem]

## Content Quality of the Guidance

- [ ] CHK005 Is a description required to state the business condition rather than restate the derivation name or record type? [Clarity, Spec §FR-003]
- [ ] CHK006 Is a clearing path required to say so explicitly where no remediation exists? [Completeness, Spec §FR-004]
- [ ] CHK007 Is the owner defined as an operational function rather than a team or a person, so it survives reorganisation? [Clarity, Spec §Assumptions]
- [ ] CHK008 Is it acknowledged that three requirements are verified by reading rather than by test, with the reason? [Measurability, Plan §Test Strategy]

## Documentation Consolidation

- [ ] CHK009 Is it required that no per-class guidance is maintained by hand anywhere else? [Completeness, Spec §FR-006]
- [ ] CHK010 Does the handbook keep the narrative that is genuinely not per-class, rather than being gutted? [Clarity, Spec §FR-007, Plan §Design]
- [ ] CHK011 Is the feature contract's remaining role — the specification-level class, cause and authority mapping — stated positively rather than as a leftover? [Clarity, Spec §FR-008]
- [ ] CHK012 Is the risk that removing the handbook table is a regression for its current readers addressed? [Coverage, Plan §Review Risks]

## Boundaries

- [ ] CHK013 Is it explicit that no exception's derivation, severity, order, identity or values change? [Completeness, Spec §FR-009]
- [ ] CHK014 Is the English-on-the-German-page decision recorded with its reason, so it does not read as an oversight? [Clarity, Spec §Clarifications, Assumptions]
- [ ] CHK015 Are remediation procedures excluded, so the catalog states what clears an entry and not how to run the business? [Clarity, Spec §Non-Goals]
- [ ] CHK016 Does every FR and DR map to an acceptance scenario and a named proof or a stated review? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product scope for the three decisions in the spec's Clarifications section was accepted
  on 2026-09-04. The domain review recorded here is still open.
