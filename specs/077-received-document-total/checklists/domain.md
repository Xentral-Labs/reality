# Domain Checklist: A Document's Total Is Received, Not Computed

**Purpose**: Validate the authority boundary this feature moves, before implementation  
**Created**: 2026-09-05  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Boundary

- [ ] CHK001 Is it clear that the objection is to authorship of the figure, not to arithmetic as such? [Clarity, Spec §Problem]
- [ ] CHK002 Is the harm named concretely — our rounding against the source's, on the number the ledger posts? [Clarity, Spec §Problem]
- [ ] CHK003 Is it explicit that no other derivation is affected, so the change is not read as a ban on deriving? [Completeness, Spec §DR-002, Non-Goals]
- [ ] CHK004 Is the rule applied to documents with no external counterpart, with the reason that the code cannot tell them apart? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]

## Keeping the Difference Visible

- [ ] CHK005 Is a total that disagrees with the lines required to be accepted rather than refused? [Completeness, Spec §FR-004]
- [ ] CHK006 Is the reason recorded, so the next reader does not add the validation back as an improvement? [Clarity, Spec §Non-Goals, Plan §Review Risks]
- [ ] CHK007 Is zero defined as a statement rather than an omission? [Coverage, Spec §FR-005]

## Where the Sum Went

- [ ] CHK008 Is the interface prefill defined as a suggestion a person confirms, rather than a value the client asserts? [Clarity, Spec §FR-006, Clarifications]
- [ ] CHK009 Is it acknowledged that the interface sum could drift from what the core would have produced, and that this is visible rather than silent? [Coverage, Plan §Review Risks]
- [ ] CHK010 Is the agent tool required to supply the total, with the reason that it is reading a source? [Completeness, Spec §FR-007, Clarifications]

## Scope and Consequences

- [ ] CHK011 Is it explicit that no schema changes and no stored value is rewritten? [Completeness, Plan §Data and migration impact]
- [ ] CHK012 Is the breaking effect on callers stated, together with the fact that all of them live in this repository today? [Clarity, Plan §Review Risks]
- [ ] CHK013 Does the ledger keep posting the document total, with only its origin changed? [Consistency, Spec §DR-003]

## Acceptance and Traceability

- [ ] CHK014 Are the success criteria measurable without reference to implementation? [Measurability, Spec §SC-001–SC-004]
- [ ] CHK015 Does every FR and DR map to an acceptance scenario and a named proof or a stated review? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy]
- [ ] CHK016 Is the one requirement verified by reading rather than by test identified as such, with the reason? [Measurability, Plan §Test Strategy]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product scope was accepted on 2026-09-05. This is the first feature planned under
  Constitution 1.2.0, and its Constitution Check carries the row the amendment added.
