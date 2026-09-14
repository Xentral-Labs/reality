# Domain Checklist: Goods Going Back the Other Way

**Purpose**: Validate the movement, its bounds and the two classes before implementation  
**Created**: 2026-09-06  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## A New Physical Fact

- [ ] CHK001 Is a separate movement kind argued from direction — goods out rather than in — rather than presented as obvious? [Clarity, Spec §Clarifications, Plan §One movement kind]
- [ ] CHK002 Are the cheaper alternatives named and argued down: reusing `return`, recording a `shipment`, inferring direction from the commitment? [Completeness, Plan §Simpler alternatives]
- [ ] CHK003 Is it acknowledged that a movement vocabulary is a contract with every integration that will ever write one? [Clarity, Plan §Review Risks]
- [ ] CHK004 Is every refusal stated — wrong commitment type, wrong item, no location to take goods from? [Completeness, Spec §FR-003]

## What Bounds It

- [ ] CHK005 Is the bound what actually arrived less what has gone back, rather than the promise's open quantity, and is the reason given? [Clarity, Spec §FR-004, §Clarifications]
- [ ] CHK006 Is it explicit that fulfilment does not change, with the same reason the selling side gives? [Clarity, Spec §FR-005, §Non-Goals]
- [ ] CHK007 Does a corrected movement stop counting, on this side as on every other? [Consistency, Spec §FR-008]

## Where The Chains Meet

- [ ] CHK008 Is it recorded that spec 082 already named "a shipment to the supplier" as a resolution and that the movement simply did not exist? [Clarity, Spec §Problem, Plan §The chains meet]
- [ ] CHK009 Are the existing settlement rules reused unchanged rather than restated? [Consistency, Spec §FR-007]
- [ ] CHK010 Is the case an operator most often has — customer returns a faulty item, company sends it on — the one the acceptance story uses? [Coverage, Spec §User Story 2]

## The Two Classes

- [ ] CHK011 Do both directions share one body, so neither can drift in what "returned" and "credited" mean? [Consistency, Spec §DR-003, Plan §Two classes, one body]
- [ ] CHK012 Does the uncredited class count only what a supplier invoice actually billed, with the reason? [Completeness, Spec §FR-009]
- [ ] CHK013 Is the over-credited class silent where nothing went back, so a rebate, an allowance or a price correction is never reported? [Completeness, Spec §FR-010]
- [ ] CHK014 Does one order line produce at most one of the pair? [Consistency, Spec §FR-011]
- [ ] CHK015 Do the new classes and their selling-side mirrors name each other? [Consistency, Spec §FR-017]

## One Correction, And One Deliberate Non-Correction

- [ ] CHK016 Is `receipt_unbilled` required to count what the company still holds, and is that tied to the same correction spec 079 made? [Clarity, Spec §FR-012, Plan §One correction]
- [ ] CHK017 Is `billed_not_received` deliberately left alone, with the argument that a return does not unmake a receipt? [Clarity, Spec §FR-013, Plan §Review Risks]
- [ ] CHK018 Is the apparent inconsistency between those two resolved by writing down the question each class asks? [Clarity, Checklists §Author Notes]

## What Is Deliberately Not Built

- [ ] CHK019 Is the `return_unresolved` mirror rejected because it could never be true, rather than because it is out of scope? [Clarity, Spec §Non-Goals, Plan §Simpler alternatives]
- [ ] CHK020 Is a class for goods returned that nobody invoiced rejected on the ground that nothing is owed back? [Clarity, Plan §Simpler alternatives]
- [ ] CHK021 Is the window before the supplier's invoice arrives named as a silence the queue keeps? [Coverage, Spec §Assumptions, Plan §Review Risks]

## Units, Catalogs and Surfaces

- [ ] CHK022 Does the comparison go through the one comparability rule, with an unreconcilable pair reported rather than judged? [Consistency, Spec §FR-019]
- [ ] CHK023 Do both classes carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-017]
- [ ] CHK024 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks]
- [ ] CHK025 Is the new movement kind reachable from the surfaces that already reach a customer return? [Coverage, Spec §FR-018]
- [ ] CHK026 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-006]
