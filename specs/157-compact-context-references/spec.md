# Compact context references

**Language**: English

## Context and Intent
Reference-only records currently stack in the first column and inflate an entire timeline lane even while their cards are off-screen. The user approved fixing this layout.
### Scope
Place reference-only records in a separate untimed area to the left of recorded events, with at most two cards per column in each lane. Preserve every identity, edge and detail action.
### Non-Goals
No record aggregation, inferred dates, domain/schema changes or data loss. Numeric Inspector presentation is the separate restoration of spec138 FR-028, implemented alongside this correction. References remain visible and reachable through scrolling and direct-neighbor navigation.
## User Scenarios & Testing
### US1 — Compact and explainable history
Given many earlier references, opening the graph keeps each reference lane at two card rows or fewer unless observed records themselves require more. All references remain individually selectable. Given older history containing a reference's subject event, it moves to that recorded event without duplication. Recorded event positions and order remain truthful.
## Requirements
- **FR-001**: Reference-only cards occupy at most two slots per column, in an untimed left area; they cannot inflate the global lane height with growing reference counts.
- **FR-002**: Every loaded record/event and explicit edge remains selectable and unchanged in identity and meaning.
- **FR-003**: Recorded timestamps label only recorded-event columns; earlier references have no invented creation time. Older loading and initial newest focus remain intact.
## Success Criteria
A 100-event fixture with hundreds of earlier references retains every card/edge and a maximum of two reference slots per lane. Existing graph tests, full web gates and a visual local check pass.
## Assumptions and Dependencies
Refines spec138 FR-026: its left boundary becomes an explicitly untimed area of multiple columns. No missing history is inferred. Follows spec155 only to share its corrected specification numbering; no runtime dependency.

## Requirement Traceability

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001 | T002–004 | Dense reference occupancy regression and visual check |
| FR-002 | T002–004 | Identity, edge and connected selection tests |
| FR-003 | T002–004 | Older-event promotion test and undated header review |

## Approved interaction refinement
The owner approved a quiet default with no relationship lines; selecting a card shows only its incident explicit edges and direct neighbors, never the full transitive component. Unrelated cards dim. Selecting a neighbor moves focus one step. Reference remains a normal always-visible numbered lane (01), matching the other lanes. It has no collapse control; untimed references remain limited to two rows per column. Direct neighbors outside the horizontal/vertical viewport have counted navigation hints; only edges with both endpoints visible are drawn. Preserve original graph records/edges, pagination, exact Inspector targets and tenant scope. Localized labels and keyboard buttons are required.

- **FR-004**: No relationship paths render without selection; selection renders only directly incident visible edges.
- **FR-005**: Always-visible Reference and counted off-screen navigation retain reachability of every loaded record without changing event placement.

FR-004–005 map to T005–T007, direct-neighborhood/viewport regression tests and browser verification with dense loaded history.

Owner correction (supersedes collapse behavior in the first refinement): Reference is always visible and numbered 01. The owner also requested the Inspector numeric-format restoration specified in spec138 FR-028.
