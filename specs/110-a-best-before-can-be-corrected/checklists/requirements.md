# Specification Quality Checklist: A Best-Before Can Be Corrected

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
- [x] The kind of change is settled before the shape is chosen
- [x] What a correction costs is argued from existing precedent, not invented
- [x] What correcting to nothing loses is stated as a limit
- [x] The rejected alternative that a sibling operation uses is measured before being rejected

## Author Notes

The input for this was a limit I wrote down myself one specification earlier, and the useful part
of the work was deciding **what kind of change a corrected best-before is** before choosing a
shape.

Spec 093 built an append-only record and said, in its own docstring, that it was *not* a
correction: *"a correction says the record was wrong; this says the record was right and the world
moved."* A counterparty moving a delivery date is the world moving. A best-before is printed on a
box — it does not move, so a second date means the first reading was wrong. Keeping both as equally
valid statements would record a contradiction as though it were history. So this is a correction,
and the product already has a shape for one: correct the value, require a reason, and put the
before and the after in a business event, exactly as a manual document's line correction does.

Two things a reviewer should weigh.

**A correction costs a confirmation as well as a reason.** The caller has to name the date they
believe is stored, including naming that none is. That is not novelty: the confirmed count of Spec
085, the confirmed total of Spec 098 and the expected revision of a document correction all make a
caller say what they are acting on, for the same reason — an operation that overwrites what
somebody got wrong should not be reachable by somebody who has not looked. It also makes the intent
legible: *"I saw the fifteenth, it is the sixteenth."*

**Correcting to nothing is lossy in the record.** Afterwards a lot looks exactly like one nobody
ever dated, and only the event history says otherwise. The alternative is a second column recording
why the field is empty, which is more schema than a misread label deserves. It is stated as a limit
rather than left to be discovered.

One smaller decision worth flagging because it was measured rather than felt: the sibling operation
`correct_manual_document_lines` **refuses** to correct a document that came from a source record —
external evidence is not overwritten. Applying that here would have been the consistent-looking
move, and it is wrong: **no import path creates lots at all.** `create_lot` is reached only from
the agent tool, the API and the command line, so a lot's source record says where the *batch* came
from and never where the *date* came from. Refusing on it would block a correction to a hand-typed
date because the goods happened to arrive by import.
