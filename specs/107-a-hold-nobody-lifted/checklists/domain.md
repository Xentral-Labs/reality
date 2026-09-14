# Domain Checklist: The Hold Nobody Lifted

**Purpose**: Validate the two classes, the two histories, and what is deliberately left standing  
**Created**: 2026-09-08  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Before Anything Was Designed

- [ ] CHK001 Was it checked, and recorded, that a person can lift both kinds of hold from every declared adapter? [Coverage, Spec §Clarifications, Plan §The reachability check]
- [ ] CHK002 Is the Spec 091 mistake named as the reason that check comes first? [Clarity, Plan §The reachability check]

## Why A Forgotten Hold Matters

- [ ] CHK003 Is it stated that the stale-promise sweep skips held promises and that the protection has no expiry? [Clarity, Spec §Problem, Plan §Why a forgotten hold is worse]
- [ ] CHK004 Is it stated that a customer delivery hold refuses shipments for orders taken after it was raised? [Completeness, Spec §Problem]
- [ ] CHK005 Is the count of times the queue currently reads these records given, rather than asserted vaguely? [Clarity, Spec §Problem]

## Two Classes, Two Histories

- [ ] CHK006 Is two classes argued from the catalog's one-record-type constraint rather than presented as a domain distinction? [Clarity, Plan §Simpler alternatives, §Review Risks]
- [ ] CHK007 Do the two classes share one derivation body, following the established pattern? [Consistency, Spec §FR-001]
- [ ] CHK008 Does each class learn from its own population, with the Spec 089 precedent named? [Consistency, Spec §DR-003, Plan §One body, two classes]
- [ ] CHK009 Is the floor argued from what a hold means rather than picked? [Clarity, Spec §FR-003, Plan §One body, two classes]
- [ ] CHK010 Is silence below the minimum required, and distinguished from a lenient threshold? [Completeness, Spec §FR-002]
- [ ] CHK011 Is the severity difference argued from blast radius? [Clarity, Spec §FR-008]

## What A Hold Is Holding Back

- [ ] CHK012 Is the held-back figure justified as what makes the class useful rather than decorative? [Clarity, Plan §What the entry says]
- [ ] CHK013 Is a summed quantity across items refused, with the Spec 076 rule named? [Consistency, Spec §FR-005]
- [ ] CHK014 Is a party hold blocking nothing still reported, with the reason? [Completeness, Spec §US2 scenario 2]
- [ ] CHK015 Is the weakness of a count acknowledged, with what was rejected instead? [Clarity, Plan §Review Risks]

## Every Hold Type

- [ ] CHK016 Is reporting every party hold type argued against filtering to the one that exists? [Clarity, Plan §Every hold type, named]
- [ ] CHK017 Is the consequence stated — that a future hold type must bring its own release path? [Completeness, Spec §Non-Goals, §Assumptions]

## What Is Left Standing

- [ ] CHK018 Is automatic release refused, and for both of its reasons? [Clarity, Spec §Non-Goals, Plan §Simpler alternatives]
- [ ] CHK019 Is it required that nothing is suppressed while a hold stands? [Coverage, Spec §FR-010]
- [ ] CHK020 Are holds on closed promises excluded, with the Spec 088 ground named? [Consistency, Spec §FR-006, Plan §Simpler alternatives]
- [ ] CHK021 Is the underlying oddity — cancelling a promise leaves its holds — named as a limit and a separate specification? [Clarity, Spec §Non-Goals, §Assumptions, Plan §Review Risks]
- [ ] CHK022 Is splitting the threshold by reason code argued down on measurement grounds? [Clarity, Spec §Non-Goals, Plan §Simpler alternatives]

## Nothing Else Moves

- [ ] CHK023 Is it required that no existing class, operation, register or projection changes? [Coverage, Spec §FR-011]
- [ ] CHK024 Is it confirmed that no migration, operation or cause is added? [Completeness, Spec §DR-001]
- [ ] CHK025 Is the closed exception registry required to stay closed, with exactly two classes added? [Consistency, Spec §DR-002]
- [ ] CHK026 Is the standing risk acknowledged — that this adds two more classes to an unmeasured threshold? [Clarity, Plan §Review Risks]
