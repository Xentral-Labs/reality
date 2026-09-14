# Domain Checklist: An Operation Nobody Declared

**Purpose**: Validate the population, the gate and the exemptions before implementation  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Population

- [ ] CHK001 Is the population defined as two already-gated facts intersected, rather than as a new list? [Consistency, Spec §FR-009, Plan §The population]
- [ ] CHK002 Are the rejected populations measured, with the count each would have produced? [Completeness, Plan §Simpler alternatives]
- [ ] CHK003 Is the reason for excluding internal building blocks argued from what failed in 091 — reachability — rather than from convenience? [Clarity, Spec §Non-Goals]
- [ ] CHK004 Is excluding reads justified by the completeness rules they already have? [Clarity, Spec §Non-Goals]

## The Gate

- [ ] CHK005 Does the gate fail on an undeclared operation *and* on a stale exemption? [Completeness, Spec §DR-003, §FR-004]
- [ ] CHK006 Is the reason a stale exemption matters spelled out — that it hides the next real one? [Clarity, Plan §The gate fails in both directions]
- [ ] CHK007 Does a failure name the offending services rather than counting them? [Completeness, Spec §FR-005]
- [ ] CHK008 Is a service forbidden from being both declared and exempt? [Completeness, Spec §FR-003]
- [ ] CHK009 Is a reason required and required to be non-empty? [Completeness, Spec §FR-002]

## The Exemptions

- [ ] CHK010 Is the exemption list's failure mode named — that nothing stops somebody writing "not a command" and moving on? [Clarity, Plan §Review Risks, Checklists §Author Notes]
- [ ] CHK011 Is what limits it stated honestly, without claiming it is a guarantee? [Clarity, Plan §Review Risks]
- [ ] CHK012 Do the exemptions live in the command catalog, reviewed where commands are reviewed? [Consistency, Spec §DR-002]
- [ ] CHK013 Are the six judgement calls presented as claims a reviewer can disagree with, one line each? [Coverage, Spec §Non-Goals, Plan §What the six are not]

## What The Measurement Found

- [ ] CHK014 Is releasing a reservation declared, and is the fact that it had an agent tool and no entry stated rather than quietly fixed? [Clarity, Spec §FR-006, Plan §What the eight are]
- [ ] CHK015 Is updating a pricing group declared beside its create? [Completeness, Spec §FR-007]
- [ ] CHK016 Are the bulk operations declared as related services rather than as new commands, consistent with how the payment term pair already sits? [Consistency, Spec §FR-008, Plan §What the eight are]
- [ ] CHK017 Is it clear that none of the eight changes behaviour — they become describable, not new? [Clarity, Plan §Rollout]

## What The Gate Cannot Do

- [ ] CHK018 Is reachability described as textual detection rather than semantic, with what that misses? [Clarity, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK019 Is the dependency on the isolation catalog's classification named as a dependency rather than a guarantee? [Completeness, Plan §Review Risks]
- [ ] CHK020 Is it stated that the gate says nothing about which surfaces an operation should have? [Clarity, Spec §Non-Goals]

## No Behaviour Moves

- [ ] CHK021 Is it required that no schema, no service logic and no class changes? [Completeness, Spec §DR-001, §DR-004]
- [ ] CHK022 Is every existing operation required to behave exactly as today? [Coverage, Spec §FR-010]
