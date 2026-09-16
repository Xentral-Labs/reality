# Feature Specification: Register notice spacing

**Language**: English
**Status**: Approved scope
**Input**: The user requests a central fix for the flush-edge stored-result notice in Finance.

## Context and Intent
The shared freshness notice has internal padding but no horizontal margin. As a direct child of a zero-padding register surface, its background touches both card edges.

### Non-Goals
No copy, projection freshness, refresh behavior, business logic, schema, or unrelated card redesign.

## User Scenarios & Testing
### US1: Read an inset register notice (P1)
At desktop and mobile widths, every freshness state inside a register card has the same 16px outer horizontal inset as other content. Refresh remains usable and wrapping causes no horizontal overflow.
### US2: Preserve already-padded contexts (P1)
Nested notices in Inspector catalogs, payment forms and dialogs retain their current spacing; no doubled inset. Standalone attention notices remain unchanged.

## Requirements
- **FR-001**: Centrally inset a direct-child projection freshness notice 16px on both sides of a register surface in all four states.
- **FR-002**: Preserve existing vertical/internal spacing, refresh behavior, wrapping and layouts in already-padded or standalone contexts.

## Success Criteria
Browser geometry proves both insets at 390px and desktop; all four states retain a working refresh button; nested/standalone notices receive no new margin. Existing web checks pass.

## Assumptions and Dependencies
User approved a central CSS correction. InspectorCatalog already wraps the Exception catalog notice in p-4; the previous read-only assessment overstated that specific exposure. Only direct children of register-surface need correction. Existing data-projection-freshness is the shared semantic selector. No clarifications remain.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001 | T001,T002 | Existing finance browser fixture with geometry assertions |
| FR-002 | T001,T003 | Nested/standalone geometry check; full web checks |
