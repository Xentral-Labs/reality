# Specification Quality Checklist: A Credit Note Gives the Money Back

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
- [x] The new class carries the description, owner and clearing path the catalog requires
- [x] The change to an existing class's guidance is its own requirement, not a side effect
- [x] The removal of a public operation is stated as a requirement with its own review

## Author Notes

This feature exists because a question was asked that the previous four specifications had not
answered: was the returns chain actually finished? It was not. A credit note recorded a
quantity and never touched the money, and `returned_not_credited` cleared on the paper record —
so a queue said "credited" and meant "noted as credited".

That is written as the problem rather than softened, because the defect is in what an operator
reads, not in what the model can express.

The weakest part is the new class's threshold. Credit notes are low-volume, the learned rule
needs a minimum history, and a business issuing a handful a year may never be judged. Named in
the plan's review risks rather than left for somebody to discover.
