# Domain Checklist: A Best-Before Can Be Corrected

**Purpose**: Validate the correction, what it costs, and the shape that was not used  
**Created**: 2026-09-08  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## A Correction, Not A Restatement

- [ ] CHK001 Is the distinction settled before the design, with the reason a best-before does not move? [Clarity, Spec §What kind of change this is]
- [ ] CHK002 Is Spec 093's own words used to draw the line, rather than a fresh argument? [Consistency, Spec §Clarifications, Plan §A correction, not a restatement]
- [ ] CHK003 Is an append-only statements table argued down, including that it would be the first correction record in the product? [Clarity, Spec §Non-Goals]
- [ ] CHK004 Is it stated that keeping both dates would be recording a contradiction as history? [Clarity, Plan §A correction, not a restatement]

## What A Correction Costs

- [ ] CHK005 Is a reason required and an empty one refused? [Completeness, Spec §FR-002]
- [ ] CHK006 Is the caller required to name the date currently stated, including naming that none is? [Completeness, Spec §FR-003]
- [ ] CHK007 Is the confirmation argued from the three operations that already work that way, rather than asserted? [Clarity, Plan §Simpler alternatives, §What a correction costs]
- [ ] CHK008 Is a correction that changes nothing refused, on the same ground as a revision that restates nothing? [Consistency, Spec §FR-004]
- [ ] CHK009 Is an unreadable date refused in both positions, through the one date rule? [Coverage, Spec §FR-005, Plan §What a correction costs]

## Correcting To Nothing

- [ ] CHK010 Is removing the date allowed, with the real mistake it answers? [Completeness, Spec §Clarifications, Plan §Correcting to nothing]
- [ ] CHK011 Is the loss stated — that the record afterwards looks like one nobody dated? [Clarity, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK012 Is the second column that would fix it argued down as more schema than the case deserves? [Clarity, Plan §Correcting to nothing]

## The Refusal That Sends People Here

- [ ] CHK013 Does `state_lot_expiry` go on refusing a different date? [Consistency, Spec §FR-007, §Non-Goals]
- [ ] CHK014 Does its refusal now name the correction, and is the reason given — a refusal without a way forward? [Clarity, Plan §The refusal that sends people here]

## The Source Record Question

- [ ] CHK015 Is refusing a correction on a source-backed lot considered, given that a document correction refuses exactly that? [Completeness, Spec §Non-Goals]
- [ ] CHK016 Is the rejection measured — that no import path creates lots — rather than argued from taste? [Clarity, Plan §Simpler alternatives]

## The Queue

- [ ] CHK017 Does the queue follow the corrected date on the next read, with nothing stored? [Coverage, Spec §FR-008]
- [ ] CHK018 Are both directions recorded — an entry going and an entry appearing? [Completeness, Plan §The queue needs nothing]
- [ ] CHK019 Is it acknowledged that this makes an entry movable by hand, and argued? [Clarity, Plan §Review Risks]

## What Is Left Alone

- [ ] CHK020 Is correcting a lot's number excluded, with the reason that movements were recorded against it? [Completeness, Spec §Non-Goals, §Assumptions]
- [ ] CHK021 Is it required that the product does not judge which reading was right? [Consistency, Spec §DR-004]
- [ ] CHK022 Is the confirmation's race acknowledged, and a revision counter argued down as schema for a hypothetical? [Clarity, Plan §Review Risks]
- [ ] CHK023 Is it confirmed that no migration, record type, class or cause is added? [Completeness, Spec §DR-001, §DR-002, §DR-003]
- [ ] CHK024 Is it required that a lot nobody corrects behaves exactly as today? [Coverage, Spec §FR-010]
