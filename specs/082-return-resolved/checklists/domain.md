# Domain Checklist: A Return Is Not Finished When It Arrives

**Purpose**: Validate the schema addition, the validation and the derivation before implementation  
**Created**: 2026-09-05  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Why a Column at All

- [ ] CHK001 Is the no-schema alternative shown to fail on fungibility rather than dismissed? [Clarity, Spec §Problem, Plan §Simpler alternatives]
- [ ] CHK002 Is the column justified by a condition that cannot otherwise be expressed, and does that condition ship with it? [Completeness, Plan §Constitution Check]
- [ ] CHK003 Is the choice of a column over a relation table argued from what a resolution carries — nothing of its own — against what a correction carries? [Clarity, Spec §Clarifications]
- [ ] CHK004 Is the reviewer told that this column is justified by one class where Spec 076's was justified by three? [Completeness, Plan §Review Risks]
- [ ] CHK005 Is the migration limited to one nullable column with a downgrade that drops it and moves no data? [Completeness, Plan §Data and migration impact]

## What the Link May Say

- [ ] CHK006 Are all four validations stated, and does each make the link mean something rather than merely constrain it? [Completeness, Spec §FR-002, §FR-003, §FR-004, Plan §Validation]
- [ ] CHK007 Is the location check named as the only physical guarantee available, with what it costs a two-step returns process? [Clarity, Spec §Non-Goals, §Clarifications, Plan §Review Risks]
- [ ] CHK008 Is a partial resolution by more than one movement handled without special cases? [Completeness, Spec §FR-005]
- [ ] CHK009 Is the meaning of a null reference fixed as "settles no return" rather than unknown? [Clarity, Spec §FR-006]
- [ ] CHK010 Are corrections excluded on both sides, so a voided resolution stops settling and a voided return stops needing one? [Completeness, Spec §FR-009]

## No Second Authority

- [ ] CHK011 Is the refusal to store an outcome label argued from the fact that the resolving movement already states what happened? [Clarity, Spec §DR-007, Plan §Simpler alternatives]
- [ ] CHK012 Is it explicit that no movement gains a status and no workflow state is introduced anywhere? [Clarity, Spec §DR-001]

## The Fourth Learned Norm

- [ ] CHK013 Is the norm required to be learned per tenant and tested as a leak if it is not? [Coverage, Spec §DR-005]
- [ ] CHK014 Is reusing Spec 080's helper argued, and is the risk stated that unmeasured constants are now wrong in more places at once if they are wrong? [Completeness, Plan §Review Risks]
- [ ] CHK015 Does the class say nothing at all for a company below the minimum history? [Completeness, Spec §FR-008]

## Absence as a Statement, a Third Time

- [ ] CHK016 Is it explicit that the class concludes from a missing resolution on the same contract Specs 076 and 079 rest on? [Clarity, Spec §Assumptions]
- [ ] CHK017 Is the risk stated that this contract is now load bearing in three classes with nothing enforcing it? [Completeness, Plan §Review Risks]

## Catalog Authority and Evidence

- [ ] CHK018 Does the class carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-014]
- [ ] CHK019 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks §T025]
- [ ] CHK020 Are the confusable pairs mutual across all twenty classes, including the two halves of a return's life? [Consistency, Tasks §T029, §T031]
- [ ] CHK021 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]

## The Demo

- [ ] CHK022 Is the demo month's unresolved return treated as a decision to make rather than a side effect to absorb? [Clarity, Plan §Rollout, Tasks §T904a]
