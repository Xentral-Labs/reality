# Specification Quality Checklist: Eighty of the Hundred

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
- [x] Reversing Spec 093's non-goal is argued rather than done quietly
- [x] The reserved-stock limit is stated as a limit, with why it is not solved here
- [x] The one stored write is named and justified against the existing precedent

## Author Notes

This reverses a non-goal from Spec 093 — *"a different quantity is a different promise"* — and it
is worth saying why rather than quietly widening the scope. That sentence was right for a
specification about dates: it kept it honest and shippable. It is wrong as a permanent answer,
because in trade the two arrive together. *"Eighty pieces, two weeks later"* is one sentence, and
a model that forces it into two records has two timestamps that can disagree about when the
supplier said it.

So the record is the same record, with one nullable column added. The statement is the unit, not
the field.

Two things a reviewer should weigh.

**A promise can now shrink out from under reserved stock**, and nothing releases the reservation
or reports it. That is the largest gap this feature leaves. Releasing stock as a side effect of
recording a sentence would be Reality deciding something nobody asked it to, so it is named
rather than solved — and anyone who disagrees is arguing for a class or a release step, both of
which are separable.

**Accepting a quantity below what already arrived** means fulfilment can exceed the promise. The
alternative is refusing to record what the supplier actually said, which is the same trade Spec
093 made for a date already past and settled the same way: keep the statement.
