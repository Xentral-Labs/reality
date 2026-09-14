# Specification Quality Checklist: The Credit That Comes the Other Way

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
- [x] The missing goods half is named as a gap rather than left for a reader to notice
- [x] Where the two sides of the business could have differed, the reason they do not is stated
- [x] Splitting the classes by direction is argued rather than assumed

## Author Notes

This is the last of the five gaps the trading survey found, and it is deliberately half a
feature. The money half of a supplier credit — the posting, the netting, the refund, the two
classes — is built. The goods half is not, because a `supplier_delivery` commitment accepts
receipts only and a physical return to a supplier cannot be recorded at all.

Building the money half alone is right rather than expedient. A credit for a price correction,
an allowance or a rebate involves no movement, and those are the common cases; and where goods
did go back, the money is still the half that changes what the company owes. But it does mean a
credit for returned goods is recorded with no evidence of the goods behind it, and that is
stated in the specification, in the plan's review risks and in the remaining-gap note rather
than discovered later.

The other thing worth a reader's attention is that this is a mirror, and mirrors drift. The
protection is not care: it is that both sides share one settlement service and one learned
threshold, and that the separation between the two pairs of classes is asserted by a test.
