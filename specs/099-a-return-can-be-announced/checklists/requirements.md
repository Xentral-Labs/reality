# Specification Quality Checklist: The Parcel That Has Not Left Yet

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
- [x] Every domain requirement states what may not be computed, generated or leaked
- [x] The entity that was the obvious home is named, and rejected on a measurement
- [x] The one stored write is named and justified against the existing precedent
- [x] What an announcement deliberately does not affect is stated

## Author Notes

The interesting decision here is the one that looks wrong at first glance.

An announcement is a **directional promise**: a customer says they will send goods back. A
Commitment is the product's word for a directional promise. So a third `Commitment.type` is the
model that a reader of the Constitution would expect, and this specification does not use it.

The reason is a measurement, not a preference. `customer_delivery` appears 32 times across 8
modules, and 17 of those are a two-way branch — `"shipment" if type == "customer_delivery" else
"receipt"` and its relatives — whose `else` silently means *supplier delivery*. A third type
makes all seventeen wrong, and most of them would keep passing their tests, because no test asks
what a branch does with a type that does not exist yet. That is the shape of bug this project has
already been bitten by twice: a rule that was correct while one case existed and quietly wrong the
moment a second one did.

So the announcement is its own record, and the honest cost is one more entity in a model that
prides itself on having few. If the commitment vocabulary is ever widened deliberately — with all
seventeen branches audited — this is the first table that should be folded into it, and that is
written down rather than left for somebody to rediscover.

Two other things a reviewer should weigh.

**One class judged two ways.** An announcement is overdue past the day the customer stated, or
past this company's learned rhythm where they stated none. Spec 080 split that same shape into two
classes; this does not, because it is one condition with one owner and one clearing path, and the
only difference is how the date was arrived at. If a reviewer prefers two, the split is mechanical.

**An announced return is not supply.** Nothing about availability or the fulfilment queue changes.
A company therefore cannot plan around announced returns, which is deliberate: goods a customer
has promised to send are not goods anybody can sell, and treating them as supply is how a
warehouse commits stock that never arrives.
