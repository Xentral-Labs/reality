# Domain Checklist: The Discount Nobody Is Watching

**Purpose**: Validate the discount rule, its refusals and the defect it fixes before implementation  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Schema Change

- [ ] CHK001 Is the schema change argued as something the model cannot derive, rather than as a convenience? [Clarity, Plan §Complexity Tracking]
- [ ] CHK002 Was the "this needs schema" note re-checked rather than believed, given that the same note was wrong about the last feature? [Completeness, Checklists §Author Notes]
- [ ] CHK003 Is nullability itself treated as a statement — most terms grant no discount — rather than as a default? [Clarity, Spec §DR-001, Plan §The two columns]
- [ ] CHK004 Is the stored precision defended against silently rounding a rate somebody stated? [Completeness, Plan §The two columns]
- [ ] CHK005 Are the halves refused — a rate without days, days without a rate — with a reason? [Completeness, Spec §FR-003]

## Refusing To Compute

- [ ] CHK006 Is the refusal to produce any discount amount stated as a rule with its reason, rather than as an omission? [Clarity, Spec §FR-006, §Non-Goals]
- [ ] CHK007 Is the no-division constraint written as a reviewable requirement rather than left to be inferred from the code? [Completeness, Spec §DR-007, Plan §The cause]
- [ ] CHK008 Is it explicit that every money figure reported comes from the ledger and not from the rate? [Completeness, Spec §FR-006]
- [ ] CHK009 Is the buying-side entry still useful without an amount, and is that argued rather than asserted? [Clarity, Spec §Clarifications]

## The Defect On The Selling Side

- [ ] CHK010 Is the false positive in `overdue_receivable` named as a defect rather than presented as a missing feature? [Clarity, Spec §Problem]
- [ ] CHK011 Is the decision not to suppress the entry argued from what is true, rather than from convenience? [Clarity, Spec §Non-Goals, §FR-011, Plan §Why the entry stays]
- [ ] CHK012 Is a cause the right carrier, on the precedent that this catalog already rides a reason on an entry rather than producing two rows? [Consistency, Plan §The cause]
- [ ] CHK013 Does the reason require every settlement to be inside the window, and is the two-part payment case argued? [Completeness, Plan §The cause, Spec §Edge Cases]
- [ ] CHK014 Is the gross-versus-net ambiguity named, with the direction of the error and why that direction is the safe one? [Completeness, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK015 Does the reason apply on both sides of the business, and is that argued as the same condition rather than two? [Consistency, Spec §FR-012]

## The Class And Its Silence

- [ ] CHK016 Is it stated, before the class is built, that it goes quiet both when the discount is taken and when it is lost? [Clarity, Spec §FR-009, Plan §The class]
- [ ] CHK017 Does the operator-facing guidance carry that, rather than only the specification? [Coverage, Spec §FR-009]
- [ ] CHK018 Is a class for a discount already lost rejected on the ground that nothing clears it? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK019 Is the ordering by deadline argued from what an operator would want? [Clarity, Plan §The class]
- [ ] CHK019a Is a term whose window outlasts its due date left alone deliberately, rather than given an invented precedence rule? [Clarity, Plan §The class, Spec §Edge Cases]
- [ ] CHK020 Is the class's silence for a company recording no discount terms named? [Coverage, Spec §Assumptions]

## One Rule, Not Two

- [ ] CHK021 Does the discount deadline live beside the due-date rule, so the two cannot drift? [Consistency, Spec §DR-003, Plan §One rule for the window]
- [ ] CHK022 Is the existing term resolution reused rather than re-decided? [Consistency, Spec §FR-005]

## Catalog Authority, Evidence And Surfaces

- [ ] CHK023 Do the class and the cause carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-015]
- [ ] CHK024 Is activation atomic, so the registry, both order constants, the cause vocabulary and the catalog change together? [Consistency, Tasks]
- [ ] CHK025 Is every surface that records a payment term required to state the two figures, with its own requirement and test rather than as cleanup? [Coverage, Spec §FR-018, Plan §Review Risks]
- [ ] CHK026 Do this class and the overdue classes name each other, given that one concerns an invoice not yet due and the others one past due? [Consistency, Tasks]
