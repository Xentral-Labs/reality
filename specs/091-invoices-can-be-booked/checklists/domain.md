# Domain Checklist: An Invoice Somebody Can Actually Book

**Purpose**: Validate the reachability fix and what it deliberately leaves open  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Defect

- [ ] CHK001 Is this named as a defect, with the classes it disabled listed rather than summarised? [Clarity, Spec §Problem, §SC-002]
- [ ] CHK002 Is it stated that the tests passed because the tests post invoices themselves? [Clarity, Checklists §Author Notes]
- [ ] CHK003 Is the split between a working goods half and an unreachable money half stated precisely, rather than as "the money side is broken"? [Completeness, Spec §Problem]
- [ ] CHK004 Is the question that found it recorded, so the next survey can ask it too? [Coverage, Checklists §Author Notes]

## Two Acts, Not One

- [ ] CHK005 Is booking kept separate from recording, with the reason tied to `credit_note_unposted`? [Clarity, Spec §FR-008, §Non-Goals]
- [ ] CHK006 Is it explicit that collapsing them would post figures nobody asked to post? [Clarity, Plan §Simpler alternatives]

## The Credit Note Is The Yardstick

- [ ] CHK007 Is every surface decision justified as matching the credit note, rather than invented? [Consistency, Plan §The credit note is the yardstick]
- [ ] CHK008 Is the shape comparison written down so a reviewer can diff the two rather than trust the claim? [Coverage, Plan §The credit note is the yardstick]
- [ ] CHK009 Is the absence of a CLI command explained by the same yardstick rather than left as an omission? [Clarity, Spec §Non-Goals]

## Nothing Below The Surface Moves

- [ ] CHK010 Is it required that no service logic and no schema change, and is that written as something a reviewer checks in the diff? [Completeness, Spec §DR-001, Plan §Nothing in the service layer moves]
- [ ] CHK011 Are the refusals proven to arrive as API errors rather than re-proven as rules? [Coverage, Plan §Test Strategy]
- [ ] CHK012 Is it required that no figure is introduced at any surface? [Completeness, Spec §DR-002]

## What Becomes Reachable

- [ ] CHK013 Are the five previously unreachable conditions named, and are at least two driven end to end through the API alone? [Coverage, Spec §SC-002, Plan §What becomes reachable]
- [ ] CHK014 Is a booked invoice required to be settleable by both a payment and a credit note, through the existing relation? [Completeness, Spec §FR-010]

## What Stays Open

- [ ] CHK015 Is the declaration gap named with a measurement rather than as a feeling, and is the first, overstated framing corrected rather than quietly replaced? [Clarity, Spec §Non-Goals, Checklists §Author Notes]
- [ ] CHK016 Is the asymmetry stated — isolation catalog complete by discovery, command catalog hand-maintained — as the reason this went unnoticed? [Clarity, Spec §Non-Goals]
- [ ] CHK017 Is the missing recorded-but-unbooked class named as the next specification, with the reason it cannot come first? [Clarity, Spec §Non-Goals, §Clarifications]
- [ ] CHK018 Is `POST /documents` accepting any document type named as pre-existing and out of scope, rather than silently inherited? [Completeness, Plan §Review Risks]

## Agents And Money

- [ ] CHK019 Is giving an agent the ability to record and book invoices treated as a decision to be read, not as symmetry? [Clarity, Plan §Review Risks, Checklists §Author Notes]
- [ ] CHK020 Are the new tools confirmation-required proposals like every other mutation? [Consistency, Spec §FR-004, §FR-005]

## Catalogs

- [ ] CHK021 Are all three operations declared in the command catalog with mode, adapters, reads, writes and effect, and classified in the agent coverage map? [Completeness, Spec §FR-006]
- [ ] CHK022 Are the new tools declared in the tenant isolation catalog, in their counterparts' family? [Consistency, Spec §FR-007]
- [ ] CHK023 Is the closed exception registry untouched? [Consistency, Spec §DR-004]
- [ ] CHK024 Is the demo's queue required to be unchanged? [Coverage, Spec §DR-005]
