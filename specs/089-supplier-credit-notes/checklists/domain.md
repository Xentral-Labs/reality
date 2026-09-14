# Domain Checklist: The Credit That Comes the Other Way

**Purpose**: Validate the mirror, its postings and what it deliberately leaves out  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Postings

- [ ] CHK001 Is the credit note the exact reverse of the supplier invoice, with the argument that this needs no judgement and invents no figure? [Clarity, Plan §Why the reverse]
- [ ] CHK002 Is every posted amount the document's own gross amount, with nothing apportioned, split or rounded? [Completeness, Spec §DR-007]
- [ ] CHK003 Is posting without an open invoice deliberate, and is the case it exists for named? [Clarity, Spec §FR-001, §Clarifications]
- [ ] CHK004 Is the choice of `inventory` as the account the credit moves back named as a place a bookkeeper might argue, with the reason it is not adjudicated? [Clarity, Plan §Review Risks]
- [ ] CHK005 Are the refusals stated — a second posting, an amount not above zero, another party, another type? [Completeness, Spec §FR-002, §FR-004]

## One Settlement, Not Two

- [ ] CHK006 Does netting go through the one existing allocation service, so no second way of reducing a payable appears? [Consistency, Spec §DR-003, Plan §The mirror]
- [ ] CHK007 Is it argued that nothing downstream needs telling a credit was involved, rather than each consumer being taught about credits? [Clarity, Plan §The mirror]
- [ ] CHK008 Do the remainders of both documents stay open when a netting covers only part? [Completeness, Spec §FR-005]
- [ ] CHK009 Is the refund bounded by what the credit still claims? [Completeness, Spec §FR-007]

## Two Classes, Not One

- [ ] CHK010 Is splitting the classes by direction argued from owner and exit rather than from symmetry? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK011 Does the unbooked class share the learned *rule* while learning from its own history, and is sharing the number argued down rather than merely avoided? [Consistency, Spec §FR-009a, Plan §The two classes]
- [ ] CHK012 Is the unclaimed class threshold-free, with the reason that the claim exists from the moment it is booked? [Clarity, Spec §FR-010]
- [ ] CHK013 Is the separation between the two sides asserted by a test rather than left to reading? [Coverage, Spec §FR-011, Plan §The two classes]
- [ ] CHK014 Do the new classes and their selling-side mirrors name each other? [Consistency, Spec §FR-015]

## What Is Deliberately Missing

- [ ] CHK014a Is the recorded blocker note corrected rather than repeated — such a document could always be created, only never posted, settled or seen? [Clarity, Plan §Review Risks]
- [ ] CHK015 Is it stated that a supplier return cannot be recorded at all, so a credit for returned goods has no movement behind it? [Clarity, Spec §Non-Goals, §Assumptions]
- [ ] CHK016 Is building the money half alone argued from the cases that need no goods, rather than from expedience? [Clarity, Plan §Simpler alternatives]
- [ ] CHK017 Is the unread link from a supplier credit line to a purchase order line named, with the reason it is not used yet? [Completeness, Spec §Non-Goals]
- [ ] CHK018 Is the remaining gap recorded somewhere a future reader will find it, rather than only in this specification? [Coverage, Tasks]

## Mirrors Drift

- [ ] CHK019 Is the drift risk named as a risk about the next change rather than about this diff? [Clarity, Plan §Review Risks]
- [ ] CHK020 Is every existing class and operation required to behave exactly as it does today, with evidence? [Coverage, Spec §FR-018]

## Catalog Authority, Evidence And Surfaces

- [ ] CHK021 Do both classes carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-015]
- [ ] CHK022 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks]
- [ ] CHK023 Is every new operation declared in the command catalog, the tenant isolation catalog and the capability guidance? [Coverage, Spec §FR-016]
- [ ] CHK024 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]
