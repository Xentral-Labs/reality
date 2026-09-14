# Domain Checklist: Overdue Payables

**Purpose**: Validate derivation, reuse and catalog-authority requirements before implementation  
**Created**: 2026-09-04  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Reuse Rather Than Repetition

- [ ] CHK001 Is the payable required to consume the same due-date rule and the same outstanding amount as the receivable, so the two sides cannot disagree? [Consistency, Spec §FR-002, DR-002]
- [ ] CHK003 Is it clear that the extraction is the substantive change, and that a mistake in it breaks both sides together? [Clarity, Plan §Review Risks]

## Derivation Correctness

- [ ] CHK004 Are settled, reversed, undue and wrong-type invoices each defined for the payable, and is the reversal judgement inherited rather than restated? [Completeness, Spec §FR-003]

## Scope That Was Deliberately Cut

- [ ] CHK009 Is the absence of the full three-way match explained by what the model cannot express, rather than by effort? [Clarity, Spec §Non-Goals, Clarifications]
- [ ] CHK010 Are the three dropped conditions stated precisely enough to serve as the proven use case for a later schema change? [Completeness, Spec §Non-Goals]
- [ ] CHK011 Are the rejections of negative stock and of over-delivery each justified by the guards that already prevent them, and is the temporal stock variant separated from them? [Clarity, Spec §Non-Goals, Clarifications]
- [ ] CHK012 Is under-delivery excluded with the reason that the existing classes already report it? [Clarity, Spec §Non-Goals]

## Reality, Authority and Tenancy

- [ ] CHK013 Is the class derived per read with no status written to an invoice? [Completeness, Spec §DR-001]
- [ ] CHK014 Does the trace reach its records by opaque identity without restating business fields? [Completeness, Spec §DR-003]
- [ ] CHK015 Is tenant scope required for every read in the derivation? [Completeness, Spec §DR-004]
- [ ] CHK016 Do malformed, unknown, cleared and foreign identities all produce one indistinguishable not-found response? [Coverage, Spec §FR-006]

## Catalog, Ordering and Consistency

- [ ] CHK017 Does the class carry the description, owner and clearing path that Spec 071 made mandatory? [Completeness, Spec §FR-008]
- [ ] CHK018 Are the two new confusable pairs — payable against receivable, payable against overdue supplier delivery — required to name each other from both sides? [Consistency, Spec §DR-006]
- [ ] CHK020 Is it explicit that no cause is added? [Completeness, Spec §DR-005]

## Acceptance and Traceability

- [ ] CHK021 Are the success criteria measurable without reference to implementation? [Measurability, Spec §SC-001–SC-006]
- [ ] CHK022 Does every FR and DR map to an acceptance scenario and a named proof or a stated review? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy]
- [ ] CHK023 Is the first-deployment payable volume treated as a measurement to take rather than assumed to match the receivable? [Measurability, Plan §Rollout, Tasks T904a]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product scope for the three decisions was accepted on 2026-09-04. The domain review
  recorded here is still open.
