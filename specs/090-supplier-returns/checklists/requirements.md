# Specification Quality Checklist: Goods Going Back the Other Way

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
- [x] The one shipped class this corrects is named, and the one it deliberately does not is too
- [x] A new physical fact is argued as the smallest one that could work
- [x] The mirror that is deliberately not built is argued as unbuildable, not as out of scope

## Author Notes

This is the last gap the 2026-09-05 trading survey found, and it is the half spec 089 named as
missing on the day it shipped rather than being discovered later.

Two things in it deserve a reader's suspicion.

The first is that it adds a new movement kind. A movement is a plain statement about what
physically happened, and the vocabulary is a contract with every integration that will ever
write one — so the specification argues down the three cheaper alternatives (reuse `return`,
record a `shipment`, infer the direction from the commitment) rather than presenting the new kind
as obvious.

The second is that it corrects one shipped class and pointedly does not correct its neighbour.
`receipt_unbilled` must stop accruing an invoice for goods the company sent back;
`billed_not_received` must keep counting the raw receipt, because the goods did arrive and
subtracting there would accuse a supplier of failing to deliver something it delivered. Those
look inconsistent until the question each class asks is written down, which is why both are
requirements rather than implementation details.

The happiest part of the design needed nothing new. Spec 082 already let a return name the
movement that settles it and already listed "a shipment to the supplier" among the things that
settle one — the movement simply did not exist. The two chains meet with no new concept at all.
