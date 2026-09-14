# Domain Checklist: Eighty of the Hundred

**Purpose**: Validate the statement, the rules and what is deliberately left alone  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Reversing A Non-Goal

- [ ] CHK001 Is Spec 093's "a different quantity is a different promise" reversed openly, with why it was right then and wrong now? [Clarity, Spec §Problem, Checklists §Author Notes]
- [ ] CHK002 Is the argument the sentence — that a date and a quantity arrive together — rather than convenience? [Clarity, Spec §Clarifications]

## One Statement, Not Two

- [ ] CHK003 Is a second table argued down on the ground that it splits one sentence into two records with two timestamps? [Completeness, Plan §Simpler alternatives]
- [ ] CHK004 Is a column on the promise argued down by the same received-value rule Spec 093 settled? [Consistency, Plan §Simpler alternatives]
- [ ] CHK005 Is a statement restating neither figure refused? [Completeness, Spec §FR-002]
- [ ] CHK006 Is a quantity of zero or less refused, with cancellation named as the operation that already exists for it? [Clarity, Spec §FR-003]

## Two Rules, Side By Side

- [ ] CHK007 Is the quantity in force the latest revision that stated a quantity, not simply the latest revision? [Completeness, Plan §Two rules, side by side]
- [ ] CHK008 Is there exactly one rule, with a test that nothing else computes it? [Consistency, Spec §DR-003]
- [ ] CHK009 Are all four call sites named, so a reviewer can check none was missed? [Coverage, Plan §Two rules, side by side]
- [ ] CHK010 Is the promise's own quantity required to stay untouched? [Completeness, Spec §FR-008, §DR-002]

## Falling To Nothing, And Below

- [ ] CHK011 Is a promise that shrinks to what arrived settled at that moment, with the reason that there may be no next movement? [Clarity, Spec §FR-007, Plan §Falling to nothing]
- [ ] CHK012 Is the one stored write justified against the movement path that already sets the same field? [Consistency, Plan §Falling to nothing, §Review Risks]
- [ ] CHK013 Is a quantity below what already moved accepted, with the same argument Spec 093 used for a past date? [Clarity, Spec §FR-006, §Clarifications]
- [ ] CHK014 Is it acknowledged that fulfilment can then exceed the promise? [Completeness, Plan §Review Risks]

## What Is Left Alone

- [ ] CHK015 Is the reserved-stock limit stated, including that nothing releases it and nothing reports it? [Clarity, Spec §Non-Goals, §Assumptions, Plan §Review Risks]
- [ ] CHK016 Is the reason given — that releasing stock as a side effect would be a decision nobody asked for? [Clarity, Plan §What this deliberately leaves alone]
- [ ] CHK017 Is reopening a closed promise excluded, with the reason? [Completeness, Spec §Non-Goals]
- [ ] CHK018 Is a class for a repeatedly shrunk promise argued down on the same unmeasured-threshold ground as Spec 093? [Consistency, Spec §Non-Goals]

## The Rename

- [ ] CHK019 Is the rename argued from the name becoming untrue, rather than from tidiness? [Clarity, Plan §The rename]
- [ ] CHK020 Is its cost stated — five declarations, no external consumer? [Completeness, Plan §Review Risks]

## Nothing Else Moves

- [ ] CHK021 Is every existing class required to behave exactly as today for an unrevised promise? [Coverage, Spec §FR-010]
- [ ] CHK022 Is the migration one revision with no backfill and a working downgrade? [Completeness, Plan §Data and migration impact]
- [ ] CHK023 Is the closed exception registry untouched? [Consistency, Spec §DR-005]
