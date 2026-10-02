# Feature Specification: Reorder Points Name Their Statement

**Feature Branch**: `320-reorder-point-source`

**Created**: 2026-10-02

**Status**: Implemented

**Language**: English

**Input**: Owner review of the tables added since 2026-09-29, the last follow-up after specs 316–318. `item_reorder_point` (spec 302) is a company statement without its source.

## Context and Intent

### Problem

A reorder point is something the company states: "reorder 48 when available plus incoming reaches 20". Spec 302 keeps only the latest value:

- Restating a point overwrites the row in place. The previous values survive only in the `reorder_point.set` event payload.
- Removing a point deletes the row. What it was survives only in the `reorder_point.removed` event payload.
- The row names no source, so the Inspector cannot trace a point to the statement behind it (AGENTS.md rule 1: Source → Evidence → Reality). The neighbouring company statements carry one, for example `dunning_schedule_level`.

### Scope

- Every setting and every removal is kept as an immutable source record. All of them are versions of one source stream per item and location (`internal_reorder_point` / `reorder_point` / `<item>@<location>`). Each version supersedes the one before.
- The row names the version in force (`source_record_id`, required). Reads show it, and the set and remove events carry it.
- A replayed confirmation records nothing twice.
- Existing points get a source record that the migration writes down and marks as recorded before this spec.

### Non-Goals

- Turning reorder points into append-only rows. The current point stays one row, because the `reorder_point_reached` derivation reads it per company.
- Changing validation, the review, units or the exception class.

## Clarifications

### Session 2026-10-02

- Q: Where does the history of a point live? → A: In its source stream. Restating creates the next version, and the row is the current Reality. This follows the rule "SourceRecords are immutable; upstream changes create versions". (Owner request: "the same as for the other tables".)
- Q: What do existing points get? → A: A source record with the row's values and `statement_id: "recorded before spec 320"`. Nothing else is claimed about who stated it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - What a point was stays readable (Priority: P1)

As a purchaser, I restate a reorder point, remove it and set it again. Every one of those statements stays readable, and the point names the statement it stands on.

**Why this priority**: It is the change.

**Independent Test**: Service tests in `tests/test_reorder_points.py`.

**Acceptance Scenarios**:

1. **Given** a point set to 20/48, restated to 30/60, removed and set to 20/48 again, **When** its stream is read, **Then** it holds four versions in that order, each superseding the one before. The removal is its own version, and the point names the fourth.
2. **Given** a confirmed setting, **When** the same confirmation is executed again, **Then** no second version is recorded.
3. **Given** a point stated before migration `0111`, **When** the database is upgraded, **Then** the point names a source record with its values, marked as recorded before spec 320, and that record is current in its stream.

### Edge Cases

- Tenant isolation: the stream and the row belong to the point's company.
- Restating values equal to an earlier statement creates a new version, because each confirmation has its own statement id. The point never falls back to the earlier version.
- A downgrade drops the column and keeps the source records, which are immutable evidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every setting and removal of a reorder point MUST be kept as a version of the item and location's reorder-point source stream.
- **FR-002**: A reorder point MUST name the version in force. Reads and the set and remove events MUST carry it.
- **FR-003**: Migration `0111` MUST give every existing point a source record that is marked as recorded before this spec.

### Domain and Architecture Requirements

- **DR-001**: A company statement MUST be traceable to its source (AGENTS.md rule 1). Earlier values MUST be read from the stream, never from event payloads alone.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every reorder point names a source record. Every earlier setting or removal is readable as a source version.

## Assumptions and Dependencies

- Builds on spec 302 (merged as #273) and on migration `0110` (spec 318).
- `core.store_source_record` keeps versions per stream and skips a version whose payload equals an earlier one. The statement id keeps distinct confirmations distinct.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, DR-001, SC-001 | US1 1–2 | `test_each_statement_is_kept_and_the_point_names_the_one_in_force`, `test_a_replayed_confirmation_states_nothing_twice`, `test_one_point_per_item_and_location_with_values_in_range` |
| FR-003 | US1 3 | `test_the_migration_gives_every_stated_point_its_evidence` |
