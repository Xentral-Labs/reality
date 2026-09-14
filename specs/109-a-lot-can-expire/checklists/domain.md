# Domain Checklist: A Lot Can Expire

**Purpose**: Validate the stated date, the one class, and the report deliberately not built  
**Created**: 2026-09-08  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Date Is Stated, Never Computed

- [ ] CHK001 Is a shelf life in days with the date computed argued down under Principle VIII, with the concrete failure named? [Clarity, Plan §Simpler alternatives]
- [ ] CHK002 Is the date required to be a calendar date, with both alternatives argued? [Clarity, Spec §FR-001, Plan §Simpler alternatives]
- [ ] CHK003 Is stating the date after the lot exists allowed, with the operational reason? [Completeness, Spec §FR-002, Plan §The date]
- [ ] CHK004 Is re-stating a *different* date refused, and re-stating the same one accepted so a retry is safe? [Completeness, Spec §FR-003]
- [ ] CHK005 Is the absence of a correction path named as separable work rather than overlooked? [Clarity, Spec §Non-Goals, Plan §Review Risks]
- [ ] CHK006 Is a lot with no date silent in both directions, with the reason that the two cases cannot be told apart? [Clarity, Spec §FR-005, §Clarifications]

## The Report That Was Not Built

- [ ] CHK007 Is the absence of an "expiring soon" class stated prominently rather than left to be noticed? [Clarity, Spec §Non-Goals]
- [ ] CHK008 Is the reason evidence rather than effort — no stated horizon, and eleven classes on unverified numbers? [Clarity, Plan §Simpler alternatives, §Review Risks]
- [ ] CHK009 Is the count of classes already on the learned rule given, rather than asserted vaguely? [Completeness, Plan §The class, and the number that is not in it]
- [ ] CHK010 Is it stated what would unblock it, in terms of a received or measured figure? [Completeness, Spec §Assumptions]
- [ ] CHK011 Is it acknowledged that this reduces surprise rather than preventing loss? [Clarity, Plan §Review Risks]

## The Class

- [ ] CHK012 Are both measurements real — a stated date and the day of the read — with no third? [Consistency, Spec §DR-003]
- [ ] CHK013 Does the quantity held come from the one tracked-identity stock rule rather than a second count? [Consistency, Spec §DR-004]
- [ ] CHK014 Is a lot with nothing left excluded, with the reason? [Completeness, Spec §FR-007]
- [ ] CHK015 Is the ordering fully determined? [Clarity, Spec §FR-009]
- [ ] CHK016 Does the entry clear when the stock is written off, returned or gone, with nothing stored? [Coverage, Spec §FR-007]

## The Cause

- [ ] CHK017 Is one cause rather than a second class argued — same record, same owner, same clearing path? [Clarity, Spec §Clarifications, Plan §The cause]
- [ ] CHK018 Does the cause name how much is reserved? [Completeness, Spec §FR-008]
- [ ] CHK019 Does releasing the reservation remove the cause and leave the entry? [Coverage, Spec §US3 scenario 3]
- [ ] CHK020 Is it stated that no new relation was needed because both records already name a lot? [Clarity, Plan §The cause]

## Nothing Is Blocked Or Chosen

- [ ] CHK021 Is refusing a shipment of expired stock argued down — a company must be able to record what happened? [Clarity, Spec §Non-Goals, Plan §Nothing is blocked]
- [ ] CHK022 Is first-expiring-first-out excluded as a policy rather than a record? [Completeness, Spec §Non-Goals, §Assumptions]
- [ ] CHK023 Is it required that nothing is released or chosen because a lot expired? [Coverage, Spec §FR-010]

## Nothing Else Moves

- [ ] CHK024 Is it required that every existing class, register and projection behaves as today for a company that states no date? [Coverage, Spec §FR-011]
- [ ] CHK025 Is the migration one revision, one nullable column, with no backfill and a working downgrade? [Completeness, Spec §DR-001, Plan §Data and migration impact]
- [ ] CHK026 Are exactly one class and one cause added, with both closed vocabularies staying closed? [Consistency, Spec §DR-002]
- [ ] CHK027 Is serial-unit expiry excluded deliberately rather than half-built? [Completeness, Spec §Non-Goals]
