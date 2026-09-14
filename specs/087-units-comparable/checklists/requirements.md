# Specification Quality Checklist: Say When the Units Do Not Meet

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
- [x] The class carries the description, owner and clearing path the catalog requires
- [x] The line between converting a quantity and computing a value is argued, not asserted
- [x] The refusal to convert prices is stated as a rule, not as an omission
- [x] The volume the new class will have on an unprepared tenant is named in advance

## Author Notes

Two things in this specification deserve a reader's suspicion, and both are answered in it
rather than left to the implementation.

The first is that multiplying a quantity by a factor looks like the computing this product
refuses. It is not: recomputing means producing a second authority for a figure a source
stated, and this is an observation over two stated figures, made at read time and stored
nowhere. Principle VIII allows that in as many words. The reason prices are excluded is the
same principle read the other way — a division that does not come out produces money nobody
agreed.

The second is that the new class will be loud on any tenant whose items carry no conversion
factors. That is the condition being reported and not a defect, but it is volume that was not
there before, and it is bounded by items rather than by lines for exactly that reason.
