# Specification Quality Checklist: A Return May Say What It Reverses

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
- [x] Every domain requirement states what may not be written, recomputed or leaked
- [x] Both new classes carry the description, owner and clearing path the catalog requires
- [x] The specification says what is deliberately not reported and why
- [x] The correction to an existing class is stated as a correction, not slipped in

## Author Notes

This specification corrects a class that already ships. `shipped_not_billed` over-reports
today because nothing subtracts returns, and that is written as its own user story and its
own requirement rather than folded into the new work.

Two decisions are judgements rather than facts and are named in the plan's review risks:
that fulfilment is deliberately not reduced by a return, and that crediting without any
return is not reported.
