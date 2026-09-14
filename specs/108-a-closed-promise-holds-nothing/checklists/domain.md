# Domain Checklist: A Closed Promise Holds Nothing

**Purpose**: Validate the release, the invariant, and the distinction from what Spec 107 refused  
**Created**: 2026-09-08  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Why This Is Not What Spec 107 Refused

- [ ] CHK001 Is the distinction stated — time passing versus the subject being gone? [Clarity, Spec §Clarifications, Plan §Why this is not the thing Spec 107 refused]
- [ ] CHK002 Is the test for the difference given in a form somebody could apply to the next case? [Clarity, Plan §Why this is not the thing]
- [ ] CHK003 Is it stated that nothing anybody said is erased, and why that makes automation safe? [Completeness, Spec §Non-Goals, §FR-003]

## The Inconsistency Being Fixed

- [ ] CHK004 Is it stated that the same operation already releases reservations for the same reason? [Clarity, Spec §Problem]
- [ ] CHK005 Is the concrete harm named — a return against a cancelled delivery refused for a stale reason? [Completeness, Spec §Problem, §US1 scenario 3]
- [ ] CHK006 Is it stated that the record asserts something untrue while the hold stands? [Clarity, Spec §Problem]

## The One Sequence

- [ ] CHK007 Is the only path to a held-and-fulfilled promise written out, with the two specifications that make it possible? [Clarity, Spec §The sequence, Plan §The one sequence]
- [ ] CHK008 Are the two legs that make it the *only* path pinned by tests rather than asserted? [Coverage, Spec §FR-007, §FR-008]
- [ ] CHK009 Is a revision that leaves the promise open required to leave the hold active? [Completeness, Spec §FR-006]

## One Release Path

- [ ] CHK010 Is inlining the release argued down, with the reason two copies stop agreeing? [Clarity, Plan §Simpler alternatives]
- [ ] CHK011 Is emitting the event from the cancellation argued down on the one-producer-per-type rule? [Consistency, Plan §Simpler alternatives, Spec §FR-004]
- [ ] CHK012 Does the release join the caller's transaction, so a bulk closure is all or nothing? [Completeness, Spec §US1 scenario 5, §DR-002]
- [ ] CHK013 Does the cancellation event name the holds it released? [Completeness, Spec §FR-004]

## The Invariant

- [ ] CHK014 Is the invariant stated once, in one sentence, and proven from every direction? [Clarity, Spec §Scope, §FR-009]
- [ ] CHK015 Is it acknowledged that it is proven per path rather than enforced by a constraint, and why a constraint cannot express it? [Completeness, Plan §Review Risks]
- [ ] CHK016 Is it stated what a future third way of closing a promise would have to add? [Clarity, Plan §Review Risks]

## What Is Left Alone

- [ ] CHK017 Is `require_not_held` required to be untouched — when a hold ends changes, not what it blocks? [Coverage, Spec §FR-010, §Assumptions]
- [ ] CHK018 Are party holds excluded, with the reason? [Completeness, Spec §Non-Goals]
- [ ] CHK019 Are legacy holds on closed promises left alone, with a backfill argued down and the release path named? [Clarity, Spec §Non-Goals, §DR-003, Plan §Review Risks]
- [ ] CHK020 Is a hold deliberately outliving its promise argued down, with the party hold named as the thing somebody actually wants? [Clarity, Spec §Non-Goals]

## Spec 107 Afterwards

- [ ] CHK021 Is it stated that Spec 107's class keeps its behaviour and its skip becomes true by construction? [Consistency, Spec §DR-004, Plan §What Spec 107's class does now]
- [ ] CHK022 Is the guidance required to be corrected, so the next reader is not told a stale reason? [Completeness, Plan §Review Risks]

## Nothing Else Moves

- [ ] CHK023 Is it required that no existing class, operation, register or projection changes apart from a hold ending sooner? [Coverage, Spec §FR-011]
- [ ] CHK024 Is it confirmed that no migration, operation, class or cause is added? [Completeness, Spec §DR-001]
- [ ] CHK025 Is an unheld cancellation required to behave exactly as today? [Completeness, Spec §FR-005]
