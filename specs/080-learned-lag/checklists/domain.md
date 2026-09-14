# Domain Checklist: Long by This Company's Own Standard

**Purpose**: Validate the learned norm and the two derivations before implementation  
**Created**: 2026-09-05  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Learning Rather Than Configuring

- [ ] CHK001 Is the refusal to expose a setting argued from what happens to a typed number over time, rather than asserted as a principle? [Clarity, Plan §Simpler alternatives]
- [ ] CHK002 Is the departure from Spec 072's statistic — median here, longest there — argued from the difference between a bounded and an unbounded lag? [Clarity, Spec §Clarifications]
- [ ] CHK003 Are all eight constants recorded with reasoning and marked as untested judgements? [Completeness, Plan §Design, §Review Risks]
- [ ] CHK004 Is it explicit that a tenant below the minimum history is one the rule cannot speak about, rather than one with a lenient threshold? [Clarity, Spec §FR-004, Plan §The learned norm]
- [ ] CHK005 Are unfinished cases excluded from the norm, so a backlog cannot raise the bar that measures it? [Completeness, Spec §Clarifications]
- [ ] CHK006 Is the floor justified separately from the multiple, and are the two different floors justified by the two businesses? [Clarity, Plan §Design]

## Two Classes, No Overlap

- [ ] CHK007 Is the disjointness from `overdue_outgoing_customer_commitment` achieved by construction — undated only — rather than by a precedence rule? [Consistency, Plan §Order stalled]
- [ ] CHK008 Is the size of the blind spot stated: that a reserved, undated consumer order is reportable by nothing today at any age? [Clarity, Spec §Problem]
- [ ] CHK009 Is the reversal of Spec 076's non-goal stated openly, with time named as the only thing that changed? [Clarity, Spec §Problem, Checklists §Author Notes]

## Honest Arithmetic

- [ ] CHK010 Is a negative lag clamped rather than recorded, and is the way one arises — a backdated movement — named? [Completeness, Spec §FR-016, Plan §Negative lags]
- [ ] CHK011 Are quantities required to come from the existing correction-aware helper rather than a second count? [Consistency, Spec §DR-003]
- [ ] CHK012 Is a document with no readable date skipped rather than guessed at? [Completeness, Plan §Receipt unbilled]

## A Norm That Moves

- [ ] CHK013 Is it stated that an entry can clear because the company got slower rather than because anything happened? [Clarity, Plan §Review Risks]
- [ ] CHK014 Is that behaviour carried into the operator guidance rather than left in the plan? [Coverage, Tasks §T029]
- [ ] CHK015 Is the bimodal-business failure named as the most likely way the rule is wrong in practice? [Completeness, Plan §Review Risks]

## Tenancy

- [ ] CHK016 Is it explicit that a norm learned across tenants would be a leak, and is that tested rather than assumed? [Coverage, Spec §DR-005, Plan §Failure, security, and tenant behavior]

## Catalog Authority and Evidence

- [ ] CHK017 Does each class carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-013]
- [ ] CHK018 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks §T025]
- [ ] CHK019 Are the confusable pairs mutual across all nineteen classes? [Consistency, Tasks §T028, §T030]
- [ ] CHK020 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]

## Proof That Proves Something

- [ ] CHK021 Is the norm proven on its own before either class is built on it? [Coverage, Tasks §Sequencing, Phase 2]
- [ ] CHK022 Does every negative test carry a positive control in the same test? [Coverage, Plan §Test Strategy]
- [ ] CHK023 Is the demo measurement required to report a number and to update the pinned demo queue deliberately if it changes? [Coverage, Tasks §T904a]
