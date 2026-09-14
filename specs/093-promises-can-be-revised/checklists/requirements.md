# Specification Quality Checklist: When the Other Side Says a New Date

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
- [x] The schema change is justified as protecting a received value, not as convenience
- [x] The loosening this introduces is named, with what limits it
- [x] The class deliberately not built is argued down rather than deferred silently
- [x] The one existing class whose behaviour changes is named

## Author Notes

The interesting thing here is that the schema change exists to *prevent* an overwrite rather than
to record something new. A column called `confirmed_due_at` would have been smaller and would
have destroyed a supplier's first statement the moment it made a second. A date somebody stated
is a received value, and the one rule this product will not bend is that received values are
kept. So the table is the smallest design that obeys the Constitution, not the larger of two
options.

Two things a reviewer should weigh rather than accept.

**Judging against a revised date is a loosening.** An order that was three weeks late stops being
late because somebody typed a new date. That is right — the queue should measure against the date
people are working to — and it is still a loosening. What limits it is that the promise says it
was moved once it is late again, and that the original date is kept and reported. Anyone who
wants more than that is asking for the class this specification argues down: a threshold for how
often a promise may be moved, which nobody has measured.

**And a supplier that keeps moving dates and always beats the revised one is never reported.**
Arguably correct, since it is meeting the promises it actually made. A company that agreed to the
first date may disagree, and Reality has nothing to say about the difference. That is stated in
the assumptions rather than left for somebody to notice on a real tenant.
