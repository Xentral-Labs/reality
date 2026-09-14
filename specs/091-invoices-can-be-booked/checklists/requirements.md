# Specification Quality Checklist: An Invoice Somebody Can Actually Book

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
- [x] The defect is named as a defect, with what it cost
- [x] The classes that were unreachable are listed rather than summarised
- [x] The structural reason it went unnoticed is stated, with a measurement
- [x] The separation of recording and booking is argued rather than assumed

## Author Notes

This was found by changing the question. Every survey so far asked *what can the operational
queue not see*. This one came from asking *what can a person not do*, and the first answer was
that nobody outside the demo can book an invoice — the document both process chains hang on.

Five classes were specified, tested, documented and shipped against a posted invoice that no
surface could produce. The tests passed because the tests post invoices themselves, calling the
service directly. That is the same failure mode as the dependency-override leak fixed in #130: a
contract that held everywhere it was checked and was never checked where it mattered.

The structural cause is measured rather than hinted at, and the first framing was wrong. Counting
endpoints against commands gave 85 against 44, which overstates it: endpoints share commands.
Counting services gives 72 reached by mutating endpoints, 64 declared, and 18 undeclared — of
which half are reads shaping a response and most of the rest are tenant administration and chat.
One is a business operation, and it is in scope here.

So the gap is small, specific and ungated, because the tenant isolation catalog is complete by
discovery while the command catalog is hand-maintained. A gate would be cheap. That it does not
exist is the more interesting fact, and it is named as the next structural item rather than
folded in here.

The one thing worth arguing about is giving an agent the ability to record and book invoices.
It is a real widening of what an agent can do to money. The credit note has had it since 084, and
matching the credit note is this specification's yardstick throughout — but a reviewer should
read it as a decision rather than as symmetry.
