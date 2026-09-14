# Domain Checklist: The Invoice Nobody Booked

**Purpose**: Validate the split, the learned rhythms and the silences before implementation  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Why Now And Not Before

- [ ] CHK001 Is the dependency on Spec 091 argued — no tenant could have a booking rhythm until an invoice could be booked — rather than mentioned? [Clarity, Spec §Problem, §Assumptions]
- [ ] CHK002 Is it stated that this class was argued in 084's own catalog text and left unbuilt? [Clarity, Spec §Problem]

## Two Classes, Not One

- [ ] CHK003 Is the split argued from owner and from whose money is wrong, rather than from symmetry? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK004 Is it consistent with the rule Spec 089 set for the credit classes? [Consistency, Plan §Simpler alternatives]
- [ ] CHK005 Is four unposted classes acknowledged as a wide taxonomy, so a reviewer can argue the split rather than discover it? [Clarity, Plan §Review Risks]

## Four Rhythms, One Rule

- [ ] CHK006 Does each class learn from its own document type alone, with no history shared between any two? [Consistency, Spec §FR-003, Plan §Four rhythms, one rule]
- [ ] CHK007 Is the concrete harm of sharing named — a company that books sales daily and supplier invoices monthly being accused of both? [Clarity, Plan §Four rhythms, one rule]
- [ ] CHK008 Is the account that means "booked" the same one the posting operation itself uses to refuse a second posting? [Consistency, Spec §FR-015, Plan §The body already fits]
- [ ] CHK008a Is the inconsistency this turned up in Spec 089 corrected and written down, rather than fixed quietly or left alone? [Clarity, Plan §The body already fits, §Review Risks]

## The Silences

- [ ] CHK009 Is a tenant below the minimum history told nothing, and is that named as both a protection and a weakness? [Completeness, Spec §FR-004, Plan §Review Risks]
- [ ] CHK010 Is a document with no readable date excluded, with the reason? [Completeness, Spec §FR-006]
- [ ] CHK011 Is a reversed posting excluded, and is the mechanism — the reversing entries carry no document reference — written down rather than assumed? [Clarity, Spec §FR-005, Plan §The reversal case answers itself]
- [ ] CHK012 Is the imported-history flooding case answered by the same minimum-history rule rather than by a special guard? [Coverage, Spec §Clarifications]

## What Is Being Hidden

- [ ] CHK013 Does each class say what it hides while it stands — no aging, no reminder, no payment run, no discount? [Coverage, Spec §Problem, §FR-011]
- [ ] CHK014 Do the new classes and their credit-note counterparts name each other? [Consistency, Spec §FR-011]

## One Body

- [ ] CHK015 Do all four unposted classes share one body, so none can drift in what "booked" means? [Consistency, Spec §DR-003, Plan §The body already fits]
- [ ] CHK016 Is the rename of the shared helpers argued — they were named after their only caller — rather than done silently? [Clarity, Plan §The body already fits]
- [ ] CHK017 Is the risk of renaming code four shipped classes depend on named, with the evidence that nothing moved? [Coverage, Plan §Review Risks]

## Where This Is Stronger, And Where It Is Not

- [ ] CHK018 Is it stated that these will be the first learned classes live on almost every tenant, unlike their credit-note siblings? [Clarity, Plan §Why this class will actually speak]
- [ ] CHK019 Is the consequence drawn — that wrong learned constants will show here first, and that this is an argument for shipping and watching? [Completeness, Plan §Review Risks, Checklists §Author Notes]

## Catalog Authority And Evidence

- [ ] CHK020 Do both classes carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-011]
- [ ] CHK021 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks]
- [ ] CHK022 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]
- [ ] CHK023 Is the demo's queue required to be unchanged, and is the reason given? [Coverage, Plan §Rollout]
