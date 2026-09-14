# Specification Quality Checklist: Invoice Lines Know What They Bill

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

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Four scope decisions were accepted on 2026-09-05 and are recorded in the Clarifications
  section: the reference sits on the line rather than the header, no tolerance is built for
  data recorded before it exists, the reference is optional with `null` meaning "bills
  nothing from an order", and only two of the four possible quantity mismatches are reported.
- This is the first specification in this line of work with a schema change. The
  justification the Constitution asks for is three named conditions that ship with it and
  cannot be expressed without it — recorded in the Constitution Check rather than assumed.
- FR-003 is unusual: it fixes the meaning of an absent value. It exists because the first
  class reasons from absence, which is only sound while every order-billing line sets the
  reference. That contract is stated in the Assumptions together with what breaks if it is
  not kept.
- Two open threads found while researching this feature are deliberately outside it and are
  named in the Non-Goals: the financial flow does not read lines at all, and the
  `credit_note` document type has no ledger handling.
