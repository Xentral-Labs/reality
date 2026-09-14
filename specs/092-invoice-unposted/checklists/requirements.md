# Specification Quality Checklist: The Invoice Nobody Booked

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
- [x] Each class carries the description, owner and clearing path the catalog requires
- [x] The dependency on Spec 091 is stated as an ordering argument, not as a footnote
- [x] The split into two classes is argued from owner and direction
- [x] Where this class is stronger than its siblings, and where it inherits their weakness, are
      both named

## Author Notes

This is the class Spec 084 argued for and did not build. Its own catalog text says recording and
booking are two acts *"exactly as they are for an invoice"*, and the invoice case sat unwritten
through 084, 089 and the whole trading survey.

It could not have been built earlier, and the reason is worth keeping: until Spec 091 nothing
outside the demo could book an invoice, so no tenant could have a booking rhythm. A class that
learns a norm from behaviour nobody could perform would have been silent everywhere or, on the
demo, wrong everywhere. Ordering was not politeness — it was the difference between a class that
works and one that lies.

Two things a reviewer should weigh.

These will be the first learned classes that are **live on almost every tenant**. The
credit-note ones are usually silent because credit notes are rare and the minimum history is
never reached; invoices are the opposite. So if the unmeasured constants behind the learned rule
are wrong, this is where it shows first — an argument for shipping and watching, not for
waiting.

And four unposted classes is a wide taxonomy for one idea. The split follows the rule Spec 089
set — different owner, different exit — and all four share one body. A reviewer who thinks the
taxonomy is getting wide is arguing about the split, which is the right thing to argue about.
