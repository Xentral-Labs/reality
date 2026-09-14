# Domain Checklist: A Return May Say What It Reverses

**Purpose**: Validate the write-path change, the correction and the two derivations before implementation  
**Created**: 2026-09-05  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Opening the Write Path

- [ ] CHK001 Is it shown that a return can only be recorded orphaned today, and that this produces two wrong signals rather than one missing feature? [Clarity, Spec §Problem]
- [ ] CHK002 Is a return refused against a supplier-delivery promise, with the reason that goods going back to a supplier are a different flow? [Completeness, Spec §FR-002]
- [ ] CHK003 Is the open-quantity exemption argued from the fact that a fully shipped promise has none, rather than presented as a loosening? [Clarity, Plan §The two guards]
- [ ] CHK004 Is the replacement constraint the true one — a return may not exceed what went out against that promise? [Completeness, Spec §FR-003]
- [ ] CHK005 Is movement correction required to keep working for a return that carries a promise? [Coverage, Spec §DR-008]

## The Decision Not to Net

- [ ] CHK006 Is it explicit that fulfilment is deliberately not reduced by a return, and that the reason is a kept promise staying kept? [Clarity, Spec §FR-004, §Clarifications]
- [ ] CHK007 Are the consequences of the opposite choice stated — a reopened promise reported as overdue, a returned order looking undelivered? [Completeness, Plan §Simpler alternatives]
- [ ] CHK008 Is the requirement that this reason live next to the code, not only in the plan, carried as a task? [Coverage, Tasks §T024, Plan §Review Risks]
- [ ] CHK009 Is the different question `shipped_not_billed` asks — how much the customer kept — distinguished from the question fulfilment answers? [Clarity, Spec §Clarifications]

## Correcting a Class That Ships

- [ ] CHK010 Is the over-reporting of `shipped_not_billed` stated as a live defect with its own story and requirement, rather than folded into new work? [Clarity, Spec §US2, §FR-006]
- [ ] CHK011 Is a full return required to clear the entry entirely and a partial return to reduce it? [Completeness, Spec §US2 scenarios]

## Crediting at the Right Grain

- [ ] CHK012 Is the credit note line required to point at the order line, with the argument that everything else hangs off that grain? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK013 Is `credit_note` placed on the sales side so the existing validation works without a new rule? [Consistency, Spec §FR-005]
- [ ] CHK014 Is crediting summed across every referencing line, so partial and consolidated crediting need no special handling? [Completeness, Spec §FR-009]
- [ ] CHK015 Is the unit rule the same one the invoicing classes apply? [Consistency, Spec §FR-010]

## What Is Deliberately Not Reported

- [ ] CHK016 Is a refund with no return at all excluded, with the reason that it is a policy decision rather than a discrepancy? [Clarity, Spec §FR-008, §Non-Goals]
- [ ] CHK017 Is the risk named that this judgement suits consumer trade and may not suit a wholesaler? [Completeness, Plan §Review Risks]
- [ ] CHK018 Are announced returns and RMA numbers excluded because the promise vocabulary cannot express them, rather than because they do not matter? [Clarity, Spec §Non-Goals]
- [ ] CHK019 Are supplier returns and restocking excluded with reasons rather than forgotten? [Clarity, Spec §Non-Goals]

## Absence as a Statement, Again

- [ ] CHK020 Is it explicit that `returned_not_credited` concludes from a missing credit reference on the same contract Spec 076 relies on? [Clarity, Spec §Assumptions]
- [ ] CHK021 Is the risk stated that this assumption is now load bearing in two classes rather than one? [Completeness, Plan §Review Risks]

## Catalog Authority and Evidence

- [ ] CHK022 Does each class carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-016]
- [ ] CHK023 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks §T029]
- [ ] CHK024 Are the confusable pairs mutual across all seventeen classes? [Consistency, Tasks §T032, §T033]
- [ ] CHK025 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-007]

## The Demo

- [ ] CHK026 Is the demo month's orphaned return treated as a decision to make rather than a side effect to absorb? [Clarity, Plan §Rollout, Tasks §T904a]
