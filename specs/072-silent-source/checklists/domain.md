# Domain Checklist: Silent Source Detection

**Purpose**: Validate derivation, expectation and catalog-authority requirements before implementation  
**Created**: 2026-09-04  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Expectation

- [ ] CHK001 Is it required that the expectation comes from observed history alone, with no value a tenant can set? [Completeness, Spec §FR-003, DR-002]
- [ ] CHK002 Are the four constants stated with their reasoning, so a reviewer can disagree with a number rather than with a behaviour? [Clarity, Spec §Assumptions, Plan §Design]
- [ ] CHK003 Is the choice of the longest observed pause over an average justified by the case it protects — a source with nights and weekends? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK004 Is the absolute floor required, so a source with a rhythm of minutes is not reported for a brief interruption? [Completeness, Spec §FR-004]
- [ ] CHK005 Is a history of identical timestamps, where the longest pause is zero, given a defined behaviour? [Coverage, Spec §Edge Cases, Plan §Design]
- [ ] CHK006 Is a genuinely changing rhythm addressed rather than smoothed away? [Clarity, Spec §Assumptions, Plan §Review Risks]

## What Is Watched

- [ ] CHK007 Is the declared, active capability established as the carrier, with the reason a stream is not? [Clarity, Spec §Clarifications]
- [ ] CHK008 Is a capability that has never delivered explicitly excluded, with the reason that it would light up every fresh tenant? [Completeness, Spec §Non-Goals, US2]
- [ ] CHK009 Is it stated that ingestion validates neither direction, so capabilities without records and records without capabilities both exist? [Clarity, Spec §Assumptions]
- [ ] CHK010 Is it explicit that silence is measured at Reality's door rather than in the source system, and what that does and does not cover? [Clarity, Plan §Review Risks]

## Reality, Authority and Tenancy

- [ ] CHK011 Is the class derived per read with no status written to a capability? [Completeness, Spec §DR-001]
- [ ] CHK012 Does the trace reach capability, system and most recent record by opaque identity without restating business fields? [Completeness, Spec §DR-004]
- [ ] CHK013 Is tenant scope required for the record history behind each capability, not only for the capability itself? [Completeness, Spec §DR-005]
- [ ] CHK014 Do malformed, unknown, resumed and foreign identities all produce one indistinguishable not-found response? [Coverage, Spec §FR-009]

## Catalog and Consistency

- [ ] CHK015 Does the class carry the description, owner and clearing path that Spec 071 made mandatory? [Completeness, Spec §FR-011]
- [ ] CHK016 Is the pair with the failed source interpretation cross-referenced from both sides, as Spec 071 requires? [Consistency, Plan §Design, Tasks T023]
- [ ] CHK017 Is it explicit that no cause is added and the closed vocabulary is untouched? [Completeness, Spec §DR-006]

## Acceptance and Traceability

- [ ] CHK018 Are the success criteria measurable without reference to implementation? [Measurability, Spec §SC-001–SC-006]
- [ ] CHK019 Does every FR and DR map to an acceptance scenario and a named executable proof? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy]
- [ ] CHK020 Is the risk that this class is too quiet — rather than too loud, as in Specs 068 and 069 — recognised, and do the tests carry realistic rhythms rather than minimal ones? [Coverage, Plan §Rollout, Test Strategy]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product scope for the four decisions and the four constants was accepted on 2026-09-04.
  The domain review recorded here is still open.
