# Specification Quality Checklist: A Closed Promise Holds Nothing

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-08
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
- [x] The distinction from what Spec 107 refused is argued, not glossed over
- [x] The only sequence that produces the fulfilled case is written out
- [x] The invariant's limits are stated — proven per path, not enforced by a constraint
- [x] What is left untouched, including legacy rows, is stated as a limit

## Author Notes

This looks like a tidying change and it is not. The concrete harm is a **return that gets
refused**: a promise partly shipped, held for a credit check, then cancelled, still refuses the
goods coming back — with an error message about the credit check.

Two things a reviewer should weigh.

**This is not the automatic release Spec 107 refused.** That specification refused releasing a hold
*because time passed*, and that still stands: a hold is a person's statement and the clock does not
answer it. This releases a hold because its *subject is gone* — the promise it was raised against
is off, or the counterparty has said the delivery is complete. The test that separates the two
cases is worth keeping: **is anything still being blocked?** Time passing does not change the
answer; a promise closing does. And nothing is erased either way — a release sets one timestamp,
and the reason, the note, who raised it and when all survive it.

**The sequence that lets a *fulfilled* promise carry a hold is not obvious and is worth writing
down.** A held promise cannot be shipped, so it cannot become fulfilled by shipping. But Spec 093
deliberately allows a held promise to be **revised**, and Spec 097 settles a promise as fulfilled
the moment a stated quantity falls to what has already moved. So a counterparty saying *"only send
what you already sent"* fulfils a held promise, and from then on every return against it is refused
for a reason that has nothing to do with returns. Both of the other legs — you cannot hold a closed
promise, you cannot ship a held one — are pinned by tests rather than trusted, because they are the
reason this is the only path.

The largest thing this does not do is tidy the holds already sitting on closed promises in a
running tenant. No migration should edit operational records, and no rule can tell a hold left
deliberately from one forgotten. They stay, they are reachable from every surface, and Spec 107's
skip goes on ignoring them — with its wording corrected, because the reason it gives stops being
the reason.
