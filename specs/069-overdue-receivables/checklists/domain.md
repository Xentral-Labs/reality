# Domain Checklist: Overdue Receivable Visibility

**Purpose**: Validate derivation, layering and catalog-authority requirements before implementation  
**Created**: 2026-09-04  
**Feature**: [spec.md](../spec.md)

**Ownership**: Reviewer-owned. `[x]` means the reviewer accepts the requirements'
quality; it does not mean implementation is complete. Left unchecked by the author.

## Due Date and Aging

- [ ] CHK001 Is the due-date rule stated once, with the invoice date, the payment term and the no-term fallback all named? [Clarity, Spec §FR-003]
- [ ] CHK002 Is an unreadable or absent invoice date defined as "no assertion" rather than as an error or as due immediately? [Completeness, Spec §FR-003, US1 scenario 6]
- [ ] CHK003 Is the consequence of the no-term fallback stated plainly — that importing invoices without terms makes them due on issue? [Clarity, Spec §Assumptions, Plan §Rollout]
- [ ] CHK004 Is the party-level payment term addressed rather than silently ignored, given that the field exists and is populated? [Coverage, Plan §Review Risks, Tasks T905]
- [ ] CHK005 Are days overdue counted against a given evaluation instant rather than the wall clock, so the queue is reproducible? [Measurability, Spec §FR-009, US2 scenario 3]

## Layering and Single Rule

- [ ] CHK006 Is it required that no transport or read model computes a due date, and is that testable? [Clarity, Spec §FR-009, DR-004]
- [ ] CHK007 Is the consolidation of the two existing dead copies specified as one rule with consumers, rather than as a deletion or a third copy? [Completeness, Spec §Scope, Plan §Simpler alternatives]
- [ ] CHK008 Does the specification acknowledge that the refactor has no live consumer besides the new class, so the class carries its proof? [Clarity, Plan §Design, Review Risks]

## Derivation Correctness

- [ ] CHK009 Is the reported amount the outstanding remainder from the existing settlement derivation, never a recomputed balance? [Consistency, Spec §FR-004, DR-002]
- [ ] CHK010 Are fully settled, partially settled, reversed and supplier invoices each defined, and is the reversal judgement inherited rather than restated? [Completeness, Spec §FR-002, US1 scenarios 3, 7]
- [ ] CHK011 Is the boundary at the due date unambiguous, with no grace period and an invoice due exactly at the instant not yet late? [Clarity, Spec §Assumptions, Edge Cases]
- [ ] CHK012 Is a credit note that reduces the remainder to zero or below covered? [Coverage, Spec §Edge Cases]

## Reality, Authority and Tenancy

- [ ] CHK013 Is the invoice Document the authoritative record, with a reason, and is it clear this adds no operational state to it? [Clarity, Spec §Clarifications, DR-001]
- [ ] CHK014 Does the trace reach invoice, control entry and SourceRecord by opaque identity without restating their business fields? [Completeness, Spec §DR-003]
- [ ] CHK015 Is tenant scope required for every read, the payment-term lookup included? [Completeness, Spec §DR-005]
- [ ] CHK016 Do malformed, unknown, settled and foreign identities all produce one indistinguishable not-found response? [Coverage, Spec §FR-007]

## Scope, Acceptance and Traceability

- [ ] CHK017 Is the exclusion of payables argued from the operator's action rather than from effort? [Clarity, Spec §Non-Goals, Clarifications]
- [ ] CHK018 Is it explicit that no aging view, bucket or due-date column is delivered, so the rule's only consumer is the queue? [Clarity, Spec §Non-Goals]
- [ ] CHK019 Does every FR and DR map to an acceptance scenario and a named executable proof? [Traceability, Spec §Requirement Traceability, Plan §Test Strategy]
- [ ] CHK020 Is the first-deployment receivable volume treated as a measurement to take rather than an assumption to state? [Measurability, Plan §Rollout, Tasks T904a]

## Notes

- `$speckit-implement` reads this review state but does not change its markers.
- Product scope for the three decisions in the spec's Clarifications section was accepted
  on 2026-09-04. The domain review recorded here is still open.
