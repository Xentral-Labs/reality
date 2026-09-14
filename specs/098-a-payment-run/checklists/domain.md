# Domain Checklist: One Friday, Forty Payments

**Purpose**: Validate the rule, the refusals and the arithmetic that is deliberately not done  
**Created**: 2026-09-07  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Arithmetic That Is Not Done

- [ ] CHK001 Is it stated that the run computes no amount, and is the reason Principle VIII rather than laziness? [Clarity, Spec §Non-Goals, Plan §Constitution Check]
- [ ] CHK002 Is the discount arithmetic an ERP would do argued down with a worked figure, not an assertion? [Clarity, Plan §Simpler alternatives]
- [ ] CHK003 Does the preview name the rate and the deadline while naming no discounted amount? [Completeness, Spec §FR-005]
- [ ] CHK004 Is the residue left by a taken discount left where Spec 088 put it, rather than cleared here? [Consistency, Spec §Non-Goals, §US3]

## One Rule For What Is Payable

- [ ] CHK005 Is there exactly one payable rule, asked by both the preview and the run? [Consistency, Spec §FR-001, §DR-002]
- [ ] CHK006 Are all four exclusions named — not a supplier invoice, reversed, nothing open, a duplicate? [Coverage, Spec §FR-002]
- [ ] CHK007 Does the duplicate rule end up with one home, and is the direction of the move argued? [Clarity, Plan §The duplicate rule moves down]
- [ ] CHK008 Does every figure the preview reports come from the aging register, so the preview and the queue cannot disagree? [Consistency, Spec §DR-003]

## Selection Is A Person's

- [ ] CHK009 Is deriving the invoices to pay argued down on the ground that a confirmation only means something if what is confirmed is what runs? [Clarity, Plan §Simpler alternatives]
- [ ] CHK010 Does the preview include an invoice not yet due whose discount window is still open, and is that connected to the class that named a payment run? [Completeness, Spec §FR-004, Plan §The preview assembles]
- [ ] CHK011 Is the preview's order fully determined, so two identical reads return an identical answer? [Clarity, Spec §SC-006, Plan §The preview assembles]
- [ ] CHK012 Does the preview say what it withheld and why, rather than silently dropping it? [Completeness, Spec §FR-006]

## All Or Nothing

- [ ] CHK013 Is the single transaction required, and is the half-happened Friday named as the reason the operation exists? [Clarity, Spec §FR-011, §Problem]
- [ ] CHK014 Is every refusal made before anything is written? [Completeness, Plan §The run pays what it was given]
- [ ] CHK015 Is the confirmation figure a total, with the reason it is a total and not a count? [Clarity, Plan §Why the confirmation figure is a total]
- [ ] CHK016 Is a mixed-currency run refused, with the same no-conversion argument used for units and credit limits? [Consistency, Spec §FR-010, Plan §One currency]

## A Run Is A Decision, Not A Document

- [ ] CHK017 Is a payment-run document argued down on the ground that a run is not a financial event? [Clarity, Plan §Simpler alternatives]
- [ ] CHK018 Is a payment made in a run required to be indistinguishable from one made alone? [Completeness, Spec §FR-013]
- [ ] CHK019 Does one event carry the reason, the total, the currency and every invoice with its amount? [Coverage, Spec §FR-012]

## The Refusal That Is Unusual

- [ ] CHK020 Is refusing to pay a duplicate argued rather than assumed, including why reporting is not enough here? [Clarity, Spec §Clarifications, Plan §Review Risks]
- [ ] CHK021 Is the clearing path named, so the refusal traps nobody? [Completeness, Plan §Review Risks]

## What Is Left Alone

- [ ] CHK022 Is the absence of a durable per-invoice block stated, with what it costs an operator? [Clarity, Spec §Non-Goals, §Assumptions]
- [ ] CHK023 Is an invoice reappearing in the next preview argued as correct rather than excused? [Clarity, Plan §What this deliberately leaves alone]
- [ ] CHK024 Is it stated that Reality does not move money? [Completeness, Spec §Non-Goals, §Assumptions]

## Nothing Else Moves

- [ ] CHK025 Is it confirmed that no migration is added? [Completeness, Spec §DR-001, Plan §Data and migration impact]
- [ ] CHK026 Is the closed exception registry untouched? [Consistency, Spec §DR-005]
- [ ] CHK027 Are both operations declared commands, so the reachability gate stays satisfied? [Coverage, Spec §DR-007]
