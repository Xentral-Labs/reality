# Domain Checklist: A Fee Is a Charge, Not a Smaller Credit

**Purpose**: Validate the finding and what is deliberately not built  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Finding

- [ ] CHK001 Is the claim that nothing is broken backed by a measurement rather than by reasoning? [Clarity, Plan §Why the model is already right, Checklists §Author Notes]
- [ ] CHK002 Is the correct recording stated concretely — credit the goods, charge for what is kept? [Completeness, Spec §Problem]
- [ ] CHK003 Is it explained why a charge line is not credit for goods, in terms of the rule the class already uses? [Clarity, Plan §Why the model is already right]
- [ ] CHK004 Is the resemblance to the Spec 088 false positive named, and the difference drawn? [Clarity, Spec §Problem]

## What Is Not Built

- [ ] CHK005 Is teaching the class about charges argued down as a second answer to what counts as credit? [Clarity, Plan §Simpler alternatives]
- [ ] CHK006 Is a separate "uncreditable" marker argued down, including that it would make one shape into three? [Completeness, Spec §Non-Goals]
- [ ] CHK007 Is it clear that a fee, a damage deduction and a write-off are the same shape? [Consistency, Spec §Clarifications, §Assumptions]

## The Tests

- [ ] CHK008 Are both recordings pinned, not only the intended one? [Coverage, Spec §DR-002]
- [ ] CHK009 Is the reason the partial-credit test exists stated — that it is correct, looks like the bug, and would be removed by somebody acting on a bug report? [Clarity, Plan §What is actually built]
- [ ] CHK010 Do both recordings live in one test, so neither can change without the other being read? [Consistency, Plan §Test Strategy]
- [ ] CHK011 Is the guidance proven by a test that reads what it says, rather than that it exists? [Coverage, Spec §FR-004]

## The Limit

- [ ] CHK012 Is it stated that a tenant recording the fee the other way still gets a permanent entry, and that this is not solvable? [Clarity, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK013 Is it clear that such an entry is a true statement about the tenant's own document? [Clarity, Spec §Non-Goals, §FR-002]

## Nothing Moves

- [ ] CHK014 Is it required that no derivation, service or schema changes? [Completeness, Spec §FR-005, §DR-001]
- [ ] CHK015 Is it required that no class or cause is added? [Consistency, Spec §DR-003]
