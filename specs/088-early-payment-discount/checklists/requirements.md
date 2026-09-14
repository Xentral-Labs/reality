# Specification Quality Checklist: The Discount Nobody Is Watching

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-06
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] Every functional requirement has an acceptance scenario or a named edge case
- [x] Every domain requirement states what may not be computed or leaked
- [x] The schema change is justified as something the model cannot derive
- [x] The refusal to compute a discount amount is stated as a rule, with its reason
- [x] The defect being fixed is named as a defect rather than dressed as a gap
- [x] The class's asymmetric silence is stated before it is built

## Author Notes

This feature was recorded in the project's notes as needing schema, and unlike the last one that
turned out to be true: `PaymentTerm` carries `due_days` and nothing else, and a rate and a
window are not derivable from anything the model holds. The check was still worth making, and
the answer is in the Complexity Tracking table rather than assumed.

Two things a reviewer should be suspicious of are answered in the specification rather than left
to the implementation.

The first is that putting a rate in the model looks like a licence to compute money with it. It
is not: the rate appears only on the comparing side of a comparison, with both sides multiplied
out so nothing is divided, and the only money figure any entry reports is one the ledger already
holds. That constraint is written as DR-007 so it can be reviewed as a rule, not inferred from
the code.

The second is that this is the first feature in the series that fixes a defect. On any business
that grants an early-payment discount, `overdue_receivable` today reports every invoice a
customer settled correctly, for ever. Saying that plainly matters more than the feature: a class
that produces a false positive per invoice is not a partially useful class, it is an unusable
one, and it shipped that way without anybody noticing.
