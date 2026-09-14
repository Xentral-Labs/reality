# Domain Checklist: Sold for Less Than It Costs to Buy

**Purpose**: Validate the comparison and its four silences before implementation  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Why This Is Possible At All

- [ ] CHK001 Is the wrong assumption — that margin needs a cost model — stated and corrected rather than quietly dropped? [Clarity, Spec §Problem, Checklists §Author Notes]
- [ ] CHK002 Is it explicit that both figures are received values, and that a cost model would have made Reality the author of a number nobody stated? [Clarity, Spec §Clarifications, Plan §Constitution Check]
- [ ] CHK003 Is the class named for what it compares rather than for "margin"? [Clarity, Spec title, §Non-Goals]

## The Four Silences

- [ ] CHK004 Is each silence a stated rule with its own requirement — no purchase price, a currency or unit that differs, a line with no item, a line agreed at zero? [Completeness, Spec §FR-004, §FR-006, §FR-008, §FR-009]
- [ ] CHK005 Does each silence have a positive control in its own test, so it cannot pass because the class is absent? [Coverage, Tasks §Sequencing, Phase 2]
- [ ] CHK006 Is excluding a zero-priced line argued as a judgement about samples and replacements, and is the risk of that judgement named? [Clarity, Plan §The comparison, §Review Risks]
- [ ] CHK007 Is selling at exactly the purchase price excluded, with the reason that thin is a decision? [Clarity, Spec §FR-005]

## Which Price, and When

- [ ] CHK008 Is the standing default argued against a supplier-specific price, on the ground that it is the company's own statement of what an item costs it? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK009 Is the purchase price required to be the one valid when the sale was agreed, with the consequence of the alternative stated? [Completeness, Spec §FR-003]
- [ ] CHK010 Is the narrow lookup justified against `resolve_price`, including why a customer party cannot be passed to that one? [Clarity, Plan §The standing purchase price, Tasks §T018]
- [ ] CHK011 Is the bluntness of a single default list named — a company buying one item at two very different prices? [Completeness, Plan §Review Risks]

## What It Cannot See

- [ ] CHK012 Is it stated that the class understates, because freight, duty and handling are not in the figure? [Clarity, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK013 Is it stated that the class is silent for a company keeping no purchase prices, and that this may be most of them? [Clarity, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK014 Does the operator-facing guidance carry both of those, rather than only the specification? [Coverage, Spec §FR-014, Tasks §T021]

## Catalog Authority and Evidence

- [ ] CHK015 Does the class carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-014]
- [ ] CHK016 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks §T020]
- [ ] CHK017 Do this class and `invoice_price_differs` name each other as the two things that can be wrong about a price? [Consistency, Tasks §T024, §T025]
- [ ] CHK018 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]

## The Demo

- [ ] CHK019 Is it recorded that the demo keeps no purchase price list, so an unchanged demo queue proves nothing about volume? [Coverage, Plan §Rollout, Tasks §T904a]
