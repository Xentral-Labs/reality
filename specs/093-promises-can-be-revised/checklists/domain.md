# Domain Checklist: When the Other Side Says a New Date

**Purpose**: Validate the record, the rule and the loosening before implementation  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Why A Table And Not A Column

- [ ] CHK001 Is the schema change argued as protecting a received value from being overwritten, rather than as convenience or completeness? [Clarity, Plan §Complexity Tracking, §Simpler alternatives]
- [ ] CHK002 Is it explicit that a column would have been smaller and would have destroyed the first statement? [Completeness, Plan §Simpler alternatives]
- [ ] CHK003 Is the promise's own date required to stay untouched, and is the reason given — that it is what makes "originally due" answerable? [Completeness, Spec §FR-001, Plan §One statement, appended]
- [ ] CHK004 Is the record append-only, in the grain of movements and ledger entries? [Consistency, Spec §DR-001]

## The Date In Force

- [ ] CHK005 Is there exactly one rule answering what date is in force, with a test that no class computes it for itself? [Consistency, Spec §DR-003, Plan §Review Risks]
- [ ] CHK006 Is the ordering of two statements in the same instant defined, so every read resolves the same way? [Completeness, Plan §The date in force]
- [ ] CHK007 Is it required that the date in force is derived and never stored on the promise? [Completeness, Spec §DR-002]
- [ ] CHK008 Is the effect on the undated-order class named as the one existing class this changes? [Coverage, Spec §FR-005, Plan §Review Risks]

## The Loosening

- [ ] CHK009 Is judging against a revised date named as a loosening rather than presented as obviously right? [Clarity, Plan §Review Risks, Checklists §Author Notes]
- [ ] CHK010 Is what limits it stated — the reason on the entry, and the original date kept and reported? [Completeness, Spec §FR-006, Plan §Why a revision cannot buy silence]
- [ ] CHK011 Is the entry required not to be suppressed or otherwise altered by the reason? [Completeness, Spec §FR-007]
- [ ] CHK012 Are the added causal values conditional, so an unrevised promise's entry is unchanged? [Consistency, Plan §Why a revision cannot buy silence]
- [ ] CHK013 Is the class deliberately not built — a threshold for moving too often — argued down on the ground that nobody has measured it? [Clarity, Spec §Non-Goals, Plan §Simpler alternatives]
- [ ] CHK014 Is the remaining blind spot stated: a supplier that always beats its revised date is never reported? [Coverage, Spec §Assumptions, Plan §Review Risks]

## What A Revision Is And Is Not

- [ ] CHK015 Is a revision distinguished from a correction — the record was right and the world changed, rather than the record was wrong? [Clarity, Spec §Non-Goals]
- [ ] CHK016 Is revising anything but the date excluded, on the ground that a different quantity is a different promise? [Completeness, Spec §Non-Goals]
- [ ] CHK017 Is a date already past accepted, with the reason that admitted lateness is a useful statement? [Completeness, Spec §FR-008, §Clarifications]
- [ ] CHK018 Is a held promise still revisable, with the reason that a hold stops execution and this records a statement? [Clarity, Spec §FR-009]
- [ ] CHK019 Are both directions covered, and argued as the same act with different parties? [Consistency, Spec §FR-010]

## Catalogs And Surfaces

- [ ] CHK020 Is the operation declared in the command catalog, the tenant isolation catalog and the capability guidance, and reachable from the API and the agent tools? [Coverage, Spec §FR-011]
- [ ] CHK021 Is the new cause declared in the closed vocabulary with authority and evidence? [Completeness, Spec §DR-006]
- [ ] CHK022 Is every class required to behave exactly as today for an unrevised promise? [Coverage, Spec §FR-013]
- [ ] CHK023 Is the migration one revision with no backfill and a working downgrade? [Completeness, Plan §Data and migration impact]
