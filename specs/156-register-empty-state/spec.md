# Feature Specification: One register empty state

**Language**: English

## Context and Intent
### Problem
A register that returns no rows explains itself differently on every page. Facts draws a
second bordered card with its own rounded corners above the still-visible empty table,
which contradicts the existing single-frame rule for register tables. Orders & deliveries
removes the table entirely and leaves one centered line; Warehouse, Finance, Data sources
and Master data print a block below the table; Reality Inspector records and Rules print a
small grey line with different padding. The same situation therefore looks like five
different states.
### Scope
One shared empty state for every register table in the existing web UI: the register that
has no rows explains that inside its own table frame, with an optional page-specific
sentence.
### Non-Goals
No new reads, routes, filters, counts, schema or service logic. No change to loading,
error or retry states, to pagination and selection behavior, or to the daily-work
card lists (Commitments, Exceptions, Decisions), which are not register tables.

## User Scenarios & Testing
### US1 — A filter that matches nothing
The user filters or searches any register (Orders & deliveries, Warehouse, Finance, Facts,
Master data, Data sources, Reality Inspector records, Rules) until it returns no rows.
Acceptance: the table keeps its single frame, column header, selection controls and
pagination; a title and one explaining sentence appear once in the table body; no second
card border or rounded corner is drawn; the wording is available in all four languages.
### US2 — A wide register with no rows
The user scrolls a wide empty register horizontally.
Acceptance: the explanation stays readable at the visible left edge instead of scrolling
out of view with the columns.

## Requirements
- **FR-001**: Render the empty state of every register table as a row of that table's own
  body, so header, selection and pagination keep their place and the register keeps one
  border and one set of rounded corners. Pages must not draw an empty-state surface above,
  below or instead of their table.
- **FR-002**: Use one shared title and hint, "No matching records" with "Try another filter
  or inspect the original records.", and let a page replace either for its own subject.
  Facts keeps "No observations found" and its source-backed observation sentence; Master
  data and Rules keep "Adjust your search or create the first record." Retain four-language
  coverage; introduce no new localization keys.
- **FR-003**: Keep the empty explanation readable at the visible left edge of a register
  that scrolls horizontally.

## Assumptions and Dependencies
Owner reported the Facts empty state and asked for one shared treatment in conversation on
2026-09-09. `docs/WEB_SPEC.md` already requires one shared visual frame per register with
empty states inside it; this specification names the state itself and makes the eight
existing registers comply. Uses the existing shared `RegisterTable`; no API change.
No unresolved clarifications.

## Success Criteria
- SC-001: All eight registers show the same empty state inside the table frame.
- SC-002: No register page contains an empty-state branch of its own.
- SC-003: Existing frontend contracts, register/page browser suites, production build,
  four-language localization audit and the spec gate pass.

## Requirement Traceability
FR-001–003 → US1, US2, T001–T003. SC-001–003 → T003.
