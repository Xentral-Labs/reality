# Specification Quality Checklist: A Fee Is a Charge, Not a Smaller Credit

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

- [x] The claim that nothing is broken is backed by a measurement, not by reasoning
- [x] Both recordings are required to be pinned, not only the intended one
- [x] The remaining limit — a tenant recording it the other way — is stated rather than solved
- [x] The alternatives that would have added a second way to say one thing are argued down

## Author Notes

This was on the list as a suspected defect and it is not one. Measuring it took one throwaway
test and produced the whole specification:

```
fee as a reduced credit quantity   -> uncredited_quantity 2.0000
fee as a full credit plus a charge -> no entry, credit note total 72.00
```

The model already expresses a restocking fee, a damage deduction and a write-off with one shape:
credit the goods that came back, charge for what is being kept. The crediting comparison counts
lines that name the order line, a charge names none, and `line_type` appears nowhere in the
exceptions module — which is what a rule looks like when it has stayed simple.

So what is delivered is two tests and a paragraph. **The more important of the two tests is the
one asserting the partial credit still reports**, because it is correct, it looks like the bug,
and somebody acting on a report titled "false entry on restocking fees" would remove it.

The honest limit: a tenant that records the fee as a smaller credit gets a true statement about
its own document and an entry that never clears. Reality cannot know what was meant, so guidance
is the only remedy — which is why a paragraph is worth a specification here.
