# Domain Checklist: Say When the Units Do Not Meet

**Purpose**: Validate the comparability rule and its declines before implementation  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Converting Is Not Computing

- [ ] CHK001 Is the distinction between an observation over stated figures and a stored second authority argued against principle VIII rather than asserted? [Clarity, Spec §Clarifications, Plan §Constitution Check]
- [ ] CHK002 Is it explicit that both figures — the quantity and the factor — were written down by the company, and that nothing is stored? [Completeness, Spec §FR-002, §DR-002]
- [ ] CHK003 Is the refusal to convert prices stated as a rule with a reason, rather than as something merely out of scope? [Clarity, Spec §FR-006, §Non-Goals]
- [ ] CHK004 Is the refusal to convert inexactly argued as avoiding rounding rather than as a simplification? [Clarity, Spec §FR-003, §Non-Goals]

## What Counts As A Stated Relation

- [ ] CHK005 Is the relation confined to the item's own stock and purchase units, with a third unit explicitly declined? [Completeness, Spec §FR-005, §Edge Cases]
- [ ] CHK006 Is a factor of zero or less treated as no statement rather than as a number? [Completeness, Spec §FR-004]
- [ ] CHK007 Is inferring a factor from history named and refused? [Clarity, Spec §Non-Goals]
- [ ] CHK008 Is it clear that Reality learns no unit system and knows only what a company said about its own items? [Clarity, Spec §Non-Goals]

## One Decision, Not Three

- [ ] CHK009 Is a single shared comparability decision required, so no two classes can disagree about it? [Consistency, Spec §DR-003, Plan §One decision, three callers]
- [ ] CHK010 Is the price class held to a deliberately narrower rule, and is that separation visible rather than incidental? [Consistency, Plan §One decision, three callers]
- [ ] CHK011 Is the requirement that no existing class changes behaviour for matching units stated and given evidence? [Coverage, Spec §FR-015, Plan §Test Strategy]

## The Entry

- [ ] CHK012 Is one entry per item argued against one per line, in terms of what an operator does about it? [Clarity, Spec §Clarifications, Plan §The class]
- [ ] CHK013 Does the entry state both units and the number of lines affected, so the decline is legible? [Completeness, Spec §FR-008]
- [ ] CHK013a Does the entry distinguish a relation nobody stated from one that is stated and does not divide, given that the two have different exits? [Completeness, Spec §FR-008, Plan §The class]
- [ ] CHK013b Is a price decline excluded from the class, on the ground that no statement would resolve it? [Consistency, Spec §FR-008a, §Non-Goals]
- [ ] CHK014 Is the ordering deterministic despite there being no meaningful instant for the condition? [Completeness, Spec §FR-014, Plan §The class]
- [ ] CHK015 Does the entry clear by stating the relation, with no acknowledgement step? [Completeness, Spec §FR-010]

## Volume and Honesty

- [ ] CHK016 Is it recorded that the class is loud on a tenant with no maintained conversions, and that this is intended? [Coverage, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK017 Is it recorded that requiring exactness produces repeated declines for a company delivering odd pieces from boxes? [Coverage, Plan §Review Risks]
- [ ] CHK018 Is this the first class whose subject is the company's own master data rather than a transaction, and is that noted? [Clarity, Plan §Review Risks]

## Catalog Authority and Evidence

- [ ] CHK019 Does the class carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-012]
- [ ] CHK020 Does its guidance name the checks that are being declined, so the cost of not acting is visible? [Coverage, Spec §FR-012]
- [ ] CHK021 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks §T021]
- [ ] CHK022 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]
