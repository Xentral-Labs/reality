# Feature Specification: History Table

**Feature Branch**: `269-history-table`
**Language**: English
**Created**: 2026-09-25
**Status**: Draft
**Input**: Owner, comparing the two tables under Activities: the live monitor's interaction table reads well; the Activities table does not ("item · itm_2d4b700073", a plain "Completed"). The Activities tab becomes History (spec 266 FR-015) and should read as well.

## Context and Intent

### Problem

The Activities (History) register shows each business event with four facts that a reader has to decode:

- a raw subject (`item · itm_2d4b700073`), although the timeline already returns the business name of what the event concerns (`business_context`: party, item, name, SKU, reference)
- the event title without its technical type
- a plain-text status
- one "Inspect event" button

The event's area (sources, operations, finance, master data), which the timeline already classifies, is not shown at all.

### Scope

- The register names the record by its business name; the opaque id moves into the row's details.
- The event title is shown with its technical type as the tooltip.
- The area appears as a chip; only attention events carry a status badge.
- Each row opens an inline preview with the business context, the identifiers, the payload, "Inspect event" and, where the record is inspectable, "Open record".

### Non-Goals

- Any change to what the timeline returns, its filters, paging or grouping; the server is unchanged.
- A decision or decider column: decisions stay in the detail view only (spec 263 FR-013, #175).
- The drawer (non-embedded) presentation of Activities.

### Existing Contracts

- [Clear Inspector navigation](../218-clear-inspector-navigation/spec.md)
- [Business Inspector names](../216-business-inspector-names/spec.md)
- [Decision Trail](../263-decision-trail/spec.md) — decisions only in detail views
- [Live monitor](../266-engine-room/spec.md) — FR-015 names the tab History

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read what changed at a glance (Priority: P1)

As an owner, I open History and can tell from each row what happened, to which business record, in which area, and whether it needs attention, without decoding ids.

**Why this priority**: It is the whole change.

**Independent Test**: With a party, an item and an order event recorded, open History and read each row.

**Acceptance Scenarios**:

1. **Given** an item was created, **When** History lists it, **Then** the row shows "Item created" (with `item.created` as its tooltip), the record by its SKU "LAMP-1" (item events carry the SKU, not the name), and the area as a chip; a completed event carries no status badge.
2. **Given** an event whose context names no business record, **When** History lists it, **Then** the record column shows its kind and a short form of its id rather than nothing.
3. **Given** a row, **When** I open its preview, **Then** it shows the business context, the event, subject and source ids, the payload, and actions to inspect the event and, where the subject is inspectable, to open the record.
4. **Given** an attention event, **When** History lists it, **Then** its status badge uses the caution tone and the words "Attention event", never colour alone.

### Edge Cases

- Long names truncate with the full value in the tooltip; a row never widens the register.
- The German, Dutch and Spanish editions label every new element.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The History register MUST name each event's record by the business name the timeline returns (name with SKU, or party, item, SKU, reference), and fall back to a short id when no name is known.
- **FR-002**: The register MUST show each event's title (its technical type as the tooltip), its area as a chip, and a labelled badge for attention events only; a completed event, the norm, carries none. The recording time is compact (day, month, time) with the full value as the tooltip, and the register fits its width without horizontal scrolling next to the chat dock.
- **FR-003**: Each row MUST open an inline preview with the business context, the event, subject and source ids, the payload, and actions to inspect the event and, where inspectable, to open the record.
- **FR-004**: Every new English string MUST carry German, Dutch and Spanish translations.

### Domain and Traceability Requirements

- **DR-001**: Presentation only; the timeline read, its tenant scope and the business events are unchanged, and no decision or decider is added to rows (spec 263 FR-013).

## Success Criteria *(mandatory)*

- **SC-001**: No row of the History register shows a raw record id; every id is one click away in the preview.
- **SC-002**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The timeline's `business_context`, `area` and `status` fields (spec 216 and earlier) stay as they are.
- The tab is named History by spec 266 (PR #179); this change works under either tab name.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 1–2 | `history-table.test.mjs` (record naming, SKU fallback, short id); `history-table-browser.mjs` |
| FR-002 | US1 1, 4 | `history-table-browser.mjs` (tooltip, area chip, no completed badge, no table overflow) |
| FR-003 | US1 3 | `history-table-browser.mjs` (preview ids and actions) |
| FR-004 | Edge case | i18n audit |
| DR-001 | — | no server change in the diff; the rows carry no decision (browser check) |
