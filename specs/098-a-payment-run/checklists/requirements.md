# Specification Quality Checklist: One Friday, Forty Payments

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-07
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
- [x] The arithmetic the feature refuses to do is argued, not merely omitted
- [x] The one unusual refusal — a duplicate — is argued and has a clearing path
- [x] The missing per-invoice block is stated as a limit with its cost

## Author Notes

The most useful thing to say about this specification is what it does **not** do.

An ERP payment run is, mechanically, a discount calculator. It walks the open payables, checks
each against its early-payment window, and pays gross minus a rate. That single multiplication is
the largest source of money nobody agreed to in an ERP: `2%` of `1,234.56` is `24.6912`, somebody
has to round it, and the rounded figure is what the supplier is told they were paid. Principle
VIII was written before this specification and this is the case it was written for.

So the run states no amount. The preview says what is open, what the term promises and when the
window closes; a person states 98 and the 98 is a received value like every other figure in the
product. What the feature actually contributes is the three things that were genuinely missing:
a read that assembles what is worth paying, a transaction so a Friday cannot half-happen, and a
record that forty payments were one decision.

Two things a reviewer should weigh.

**The run refuses to pay an invoice reported as a duplicate.** This queue reports rather than
refuses, almost everywhere, so this is a deliberate exception. Paying a duplicate is
unrecoverable money, the class is the only payable condition marked high, and it has a clearing
path — reverse the wrong posting, or confirm the numbers differ. A reviewer who disagrees is
arguing for a warning in the preview and no refusal in the run, which is a coherent position.

**There is no durable way to say "do not pay this one".** Holding an invoice back means leaving
it out of the run, and it reappears in next week's preview. That is strictly correct — it is
unpaid, and this queue reports what is unresolved — and it is mildly annoying every week for an
invoice under dispute. The alternative is a schema change with a lifecycle and a release path,
which is a separable feature rather than a corner of this one.
