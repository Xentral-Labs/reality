# Specification Quality Checklist: A Return Is Not Finished When It Arrives

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-05
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
- [x] Every domain requirement states what may not be written, stored or leaked
- [x] The class carries the description, owner and clearing path the catalog requires
- [x] The specification says what is deliberately not modelled and why
- [x] The schema addition is justified against the alternative that needs none

## Author Notes

The version of this feature originally proposed needed no schema and was abandoned during
specification: deriving an unresolved return from what is left standing in the returns
location cannot work, because stock is fungible and the answer would be right only sometimes.
That reasoning is in the problem statement rather than hidden, because it is the argument for
the column.

The limit that a resolution must leave the location the goods arrived at is real and is named
in both the non-goals and the review risks. It decides how a two-step returns process is
recorded, and it is the thing most likely to need revisiting with a real business.
