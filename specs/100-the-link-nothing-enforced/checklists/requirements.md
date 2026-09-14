# Specification Quality Checklist: The Link Nothing Enforced

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
- [x] Every domain requirement states what may not be guessed, generated or drifted
- [x] Both failure directions are named, with the classes in each
- [x] What the gate cannot prove is stated as a limit rather than implied
- [x] The findings the gate produces on its first run are written down before it exists

## Author Notes

The recorded risk that started this said *"absence is load bearing in three classes"*. Measuring it
first changed three numbers.

**It is four references, not three.** Discovering them from the mapper rather than from memory
turned up `Commitment.document_line_id`, which six classes reach through a single inner join. A
hand-written list would have been wrong on the day it was written, which is the argument for the
gate in one sentence.

**It is eleven classes, not three.** A third of the catalog reads one of these references.

**And it is two failure directions, not one.** The recorded risk said the classes would go
"quietly wrong", which is half right and the less important half. Six classes conclude *from
absence* and therefore **cry wolf** — they report work that was actually done, and the cost is a
queue nobody believes. Five classes *start* from the reference and therefore **go blind** — they
never look at the record at all. `billed_not_received` going blind means a company pays for goods
that never arrived and nothing notices. That is the direction worth losing sleep over, and the
original note did not distinguish it.

Two things a reviewer should weigh.

**A gate cannot make a person type.** Every path will be able to carry the reference and nobody is
forced to set one, because each of the four records legitimately exists without it. The gate buys
that the next writing path and the next surface cannot silently lack the ability — not that the
field is filled. Saying so plainly is better than a gate whose name promises more than it does.

**A passthrough is a capability for a person and an absence for an agent.** MCP has always
forwarded `billed_document_line_id` if it was sent, because `lines` is a free-form object array.
No agent has ever sent it, because nothing told an agent the field exists. That is why an MCP
schema may never be exempted on passthrough grounds, and it is the most transferable idea in this
specification.
