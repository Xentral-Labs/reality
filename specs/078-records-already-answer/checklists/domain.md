# Domain Checklist: Two Answers the Records Already Hold

**Purpose**: Validate the two derivations and the catalog authority before implementation  
**Created**: 2026-09-05  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Reading a Field Nobody Reads

- [ ] CHK001 Is it argued that `credit_limit` needs no schema work because it has been carried, validated and audited since the master-data baseline? [Clarity, Spec §Problem]
- [ ] CHK002 Is zero fixed as "no limit recorded" with the consequence stated — that a deliberate cash-only customer stays silent? [Clarity, Spec §Clarifications, Plan §Review Risks]
- [ ] CHK003 Is the outstanding amount required to come from the shared open-item derivation rather than a second sum over postings? [Completeness, Spec §FR-003, §DR-002]
- [ ] CHK004 Is the currency rule the same rule Spec 076 applied to units — compare what is comparable, never convert? [Consistency, Spec §FR-004]
- [ ] CHK005 Is measuring money owed rather than total exposure recorded as a deliberate narrowing, with what it understates? [Clarity, Spec §Non-Goals, §Assumptions]

## Judging Rather Than Refusing

- [ ] CHK006 Is the choice to report a duplicate instead of refusing it argued from lossless recording and from two connectors carrying one invoice? [Clarity, Spec §Problem, Plan §Simpler alternatives]
- [ ] CHK007 Is "the earlier document" defined so that repeated reads name the same one, including when two arrive on the same day? [Completeness, Spec §FR-008, Plan §Design]
- [ ] CHK008 Is number normalisation bounded — whitespace and case only, never content matching? [Clarity, Spec §FR-007, §Non-Goals]
- [ ] CHK009 Is an empty number excluded from both reporting and matching, with the reason? [Completeness, Spec §FR-007]
- [ ] CHK010 Does the duplicate entry carry both SourceRecords, so an operator can tell a connector duplicate from a typed one? [Completeness, Plan §Design]

## A Party as a Carrier

- [ ] CHK011 Is the Party argued as the right carrier because the condition is about a relationship rather than any one invoice? [Clarity, Plan §Design]
- [ ] CHK012 Is the ninth record type treated as a contract change, with every `record_type` consumer checked as `document_line` was in Spec 076? [Completeness, Plan §Review Risks]
- [ ] CHK013 Is it explicit that no Party gains a flag and no Document gains a marker? [Clarity, Spec §DR-001]

## Catalog Authority and Evidence

- [ ] CHK014 Does each class carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-013]
- [ ] CHK015 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks §T020]
- [ ] CHK016 Are the confusable pairs mutual — the credit class with the receivable, the duplicate class with the payable and with billed-not-received? [Consistency, Tasks §T024, §T026]
- [ ] CHK017 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]

## Proof That Proves Something

- [ ] CHK018 Does every negative test carry a positive control in the same test, so it cannot pass because the class is absent? [Coverage, Plan §Test Strategy, Tasks §Sequencing]
- [ ] CHK019 Is the shared-open-item requirement proven by a test rather than asserted in prose? [Coverage, Tasks §T007]
- [ ] CHK020 Is the claim that no adapter changes proven by explaining a `party`-carried entry, rather than stated? [Coverage, Tasks §T022]
- [ ] CHK021 Is the demo measurement required to report a number rather than assert that it is small? [Coverage, Tasks §T904a]

## Scope Discipline

- [ ] CHK022 Is the specification honest that its two conditions share a shape and nothing else, so a reviewer can reject the pairing? [Clarity, Plan §Review Risks]
- [ ] CHK023 Is enforcement excluded, leaving blocking to the existing explicit hold operation? [Clarity, Spec §Non-Goals]
- [ ] CHK024 Is sales-invoice numbering excluded with a reason rather than forgotten? [Clarity, Spec §Non-Goals]
