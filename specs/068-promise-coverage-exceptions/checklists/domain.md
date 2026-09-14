# Domain Checklist: Customer Promise and Stock Coverage Exceptions

**Purpose**: Validate derivation, taxonomy and catalog-authority requirements before implementation  
**Created**: 2026-09-04  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete.

## Taxonomy and Authority

- [x] CHK001 Is each new class defined by exactly one authoritative record, so its derived identity stays unambiguous? [Clarity, Spec §FR-001, FR-005, DR-003]
- [x] CHK002 Is the closed catalog still the single product authority, with both classes carrying an authority reference and named executable evidence? [Completeness, Spec §FR-010]
- [x] CHK003 Is the reuse of one business reason across two classes specified as a vocabulary rule rather than as a relaxation of drift detection? [Clarity, Spec §DR-006]
- [x] CHK004 Is `item` as an authoritative record type justified against every consumer that reads the record type? [Consistency, Plan §Design, Review Risks]

## Derivation Correctness

- [x] CHK005 Are the boundaries of lateness unambiguous for an absent due date, a due date equal to the evaluation instant, a non-open status, and a fully shipped commitment? [Completeness, Spec §FR-002, Edge Cases]
- [x] CHK006 Is the exclusivity rule specified so that no information available today is lost when the overdue class supersedes the at-risk class? [Coverage, Spec §FR-003, US1 scenario 5]
- [x] CHK007 Is over-subscription defined against observed stock from the shared inventory derivation, so the queue and the Inventory view cannot disagree? [Consistency, Spec §DR-004]
- [x] CHK008 Is the exclusion of blame attribution stated as a domain rule with its reason, not as a temporary simplification? [Clarity, Spec §DR-007]

## Reality and Provenance

- [x] CHK009 Is it explicit that both classes are derived per read and add no persisted state to any Evidence record? [Completeness, Spec §DR-001]
- [x] CHK010 Does each class carry the shortest true trace without duplicating provenance already reachable through it? [Clarity, Spec §DR-002, DR-003]
- [x] CHK011 Are clearing paths defined for both classes, and is it stated where no remediation exists? [Coverage, Spec §FR-007, US1 scenario 2, US2 scenarios 2-3]
- [x] CHK012 Is the identity change when a commitment crosses its due date specified rather than left as incidental behavior? [Coverage, Spec §Edge Cases, US3 scenario 2]

## Tenant and Failure Behavior

- [x] CHK013 Is tenant scope required for every read, including the candidate selection for over-subscribed items? [Completeness, Spec §DR-005]
- [x] CHK014 Do malformed, unknown, cleared and foreign identities all produce one indistinguishable not-found response? [Coverage, Spec §FR-008]

## Acceptance and Traceability

- [x] CHK015 Are the success criteria measurable without reference to implementation? [Measurability, Spec §SC-001–SC-006]
- [x] CHK016 Does every FR and DR map to an acceptance scenario and a named executable proof? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy]
- [x] CHK017 Is the expected overdue backlog on first deployment recorded as a true finding with an owner-visible consequence rather than as noise to suppress? [Clarity, Spec §Assumptions, Plan §Rollout]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product scope for the four decisions in the spec's Clarifications section was accepted
  on 2026-09-04.
- The domain review was completed on 2026-09-04. Four items were open at review time and
  were closed by amending the artifacts rather than by accepting them as written:
  - CHK001: `item` stays the authoritative record for `reservation_exceeds_stock`. The
    alternative — an `uncovered_reservation` cause on every competing commitment — is now
    recorded and reasoned about in the plan's rejected alternatives instead of being left
    unaddressed.
  - CHK003: DR-006 now states that the cause vocabulary is closed and that a new reason
    needs the same authority and evidence as a new class. Previously that closure existed
    only in the plan.
  - CHK006: FR-003a now requires the impact summary to append one clause per attached
    cause, so the unreserved portion of an overdue promise stays visible in the queue row
    instead of moving into the explanation.
  - CHK017: T904a makes the first-deployment overdue volume an actual review step on a
    realistic demo tenant, rather than an expectation stated only in the plan.
