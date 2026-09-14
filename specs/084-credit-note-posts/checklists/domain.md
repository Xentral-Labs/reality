# Domain Checklist: A Credit Note Gives the Money Back

**Purpose**: Validate the posting, the removal and the derivation before implementation  
**Created**: 2026-09-05  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## The Hole That Was Found

- [ ] CHK001 Is it shown that the defect is in what an operator reads — a class saying "credited" and meaning "noted as credited" — rather than only in a missing capability? [Clarity, Spec §Problem]
- [ ] CHK002 Is it stated that a credit is recordable through no surface the product has, and that the only caller of the money path is the demo script? [Completeness, Spec §Problem]
- [ ] CHK003 Is the invoice named as the shape a credit note should already have had? [Clarity, Spec §Problem]

## What a Settlement May Settle

- [ ] CHK004a Is the finding stated plainly — that `_invoice_control_entry` refuses anything but an invoice, so a credit note can be neither settled nor measured? [Clarity, Plan §The change that makes the rest possible]
- [ ] CHK004b Are the two new rows in the settlement table — credit note and customer refund, with account and side — flagged for particular review, because a wrong side would balance and still be wrong? [Coverage, Plan §Review Risks, Tasks §T904]
- [ ] CHK004c Is the decision not to rename `open_invoice_amount` argued as a compromise rather than presented as free? [Clarity, Plan §Review Risks]
- [ ] CHK004 Is the credit required to post as a document and be settled through the relation payments use, rather than reducing a receivable some other way? [Consistency, Spec §FR-004, Plan §Settling it]
- [ ] CHK005 Is the removal of `post_sales_credit` a requirement rather than a tidy-up, with the reason that two paths would be two answers? [Clarity, Spec §DR-009]
- [ ] CHK006 Is the confirmation that nothing outside the repository calls it carried as a task rather than assumed? [Coverage, Tasks §T904a]
- [ ] CHK007 Is the outstanding figure required to keep coming from the one settlement derivation, so no consumer needs telling about credits? [Consistency, Spec §DR-004]

## The Amount

- [ ] CHK008 Is the posted amount required to be the stated total and forbidden from being summed off the lines, with principle VIII named? [Clarity, Spec §FR-002, §DR-003]
- [ ] CHK009 Is there a test proving a credit note whose lines disagree with its header posts the header? [Coverage, Tasks §T007]

## Two Acts, Not One

- [ ] CHK010 Is the decision not to post on recording argued from the invoice precedent and from the business fact the gap represents? [Clarity, Spec §Clarifications, Plan §Simpler alternatives]
- [ ] CHK011 Is every refusal enumerated, and does each have a positive control beside it? [Completeness, Spec §FR-003, §FR-006, Tasks §T008, §T011]

## One Class, One Job

- [ ] CHK011a Is the credit against an already-paid invoice — the ordinary consumer return — shown to be inexpressible today, and does a test prove it becomes expressible? [Coverage, Spec §Problem, Tasks §T006]
- [ ] CHK011b Are two classes argued from two different owners acting, rather than from two conditions existing? [Clarity, Spec §Clarifications]
- [ ] CHK011c Is it stated why `unmatched_financial_event` does not cover an unsettled credit and must not be widened to? [Clarity, Plan §The two classes]
- [ ] CHK012 Is `returned_not_credited` left measuring quantities, with the reason that one class doing two jobs would answer neither? [Clarity, Spec §Clarifications, §Non-Goals]
- [ ] CHK013 Is the guidance change to that existing class its own requirement with its own test, so it cannot be lost in a diff? [Coverage, Spec §FR-018, Tasks §T022, §T036, Plan §Review Risks]
- [ ] CHK014 Do the new classes name each other and the quantity class name them both? [Consistency, Tasks §T036, §T037]

## The Learned Norm, Again

- [ ] CHK015 Is the low-volume weakness named — that a business issuing few credit notes may never reach the minimum history and never be judged? [Completeness, Spec §Assumptions, Plan §Review Risks]
- [ ] CHK016 Is the norm required to be learned per tenant and tested as a leak if it is not? [Coverage, Spec §DR-007]

## Catalog Authority and Evidence

- [ ] CHK017 Does each class carry authority, named executable evidence, description, owner and clearing path? [Completeness, Spec §FR-015]
- [ ] CHK018 Is activation atomic, so the registry, both order constants and the catalog change together? [Consistency, Tasks §T033]
- [ ] CHK019 Is the closed cause vocabulary left untouched? [Consistency, Spec §DR-008]

## The Demo

- [ ] CHK020 Does the demo move to the new operations in the same change that removes the old one? [Consistency, Tasks §T025]
- [ ] CHK021 Is any change to the pinned demo queue required to be argued rather than absorbed? [Coverage, Tasks §T904b]
