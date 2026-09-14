# Feature Specification: Daily work lists

**Language**: English
**Status**: Approved for implementation by the owner on 2026-09-09

## Context and Intent
### Problem
Commitments use an ERP register and exceptions/decisions use large cards with permanent explanatory sidebars. Large queues are difficult to scan.
### Scope
Compact task-like lists for daily Commitments, Exceptions and Decisions, using the application design system and existing business services.
### Non-Goals
No editable task status, assignment, bulk approval, new schema, fabricated priority, or new exception engine. Existing workspace registers remain available outside daily work. No manual completion of a commitment or dismissal of a finding.

## User Scenarios & Testing
### US1 — Work through commitments
Customer side and Supplier side show only open commitments, with exact server counts. Search and due-date order apply before pagination. Compact rows show party, item, outstanding quantity and due date; opening a row preserves the list behind a side panel with existing actions and evidence links. No history/all toggle in daily work.
### US2 — Investigate deviations
Severity-grouped compact rows show cause and business context. Search and severity filter select current findings; details and next steps open on demand, not in a permanent empty sidebar. Findings clear through underlying records only.
### US3 — Decide on proposed changes
Only pending decisions appear, oldest first. Search and tool filter work before counting/paging. Rows lead with readable business action labels; selecting a row reveals the received proposal and existing review/confirmation routes. Approval/rejection retains shared services.

## Requirements
- **FR-001**: All three pages share compact responsive rows, header count, accessible search, appropriate filters, loading/error/empty states and 50-row initial loads with explicit Load more. Do not fetch all pages up front; suppress duplicates and obsolete filter/company responses.
- **FR-002**: Daily commitments have only customer/supplier tabs, always request open scope, count both sides through shared reads and sort by due date with unknown dates last. Details retain existing reserve/ship/receive and evidence controls; no fake completion checkbox.
- **FR-003**: Exceptions retain canonical severity ordering, current findings and trace links. Group visible rows by severity without claiming a partial group is the full count. Search/filter reset loaded pages and selected details. No speculative merging of distinct findings.
- **FR-004**: Decisions are pending-only, oldest first with deterministic ID ties, searchable and filterable by tool before SQL pagination and count. Raw input remains lossless behind details; known actions have localized business labels and unknown tools retain their exact names.
- **FR-005**: Details open in an accessible side dialog with Escape, focus restoration, mobile width and existing explicit confirmation. Preserve the underlying list while inspecting. Successful business actions refresh open work.
- **FR-006**: Preserve tenant isolation, current service-derived quantities, four-language coverage and both themes. Daily navigation and Home continue to target the same commitment view. Historical workspace data remains in its existing register, not in a daily-work toggle.

## Assumptions and Dependencies
The owner accepted the proposed task-list design. No open clarification remains. Existing delivery service already filters/counts/pages in PostgreSQL. Existing exception evaluation derives a full tenant finding set before slicing; this inherited engine cost is documented rather than hidden by UI pagination. Rewriting all exception derivations is separate infrastructure/domain work. First iteration groups canonical severity, not inferred shared incidents. Side tab counts are unfiltered open counts; list header count follows search.

## Success Criteria
SC-001: More than 50 records do not require loading or rendering the entire queue on entry.
SC-002: Changing side/filter/company does not display obsolete rows; opening/closing details retains list position.
SC-003: Completed commitments and decided proposals are absent from daily work. Tenant isolation and confirmation regressions pass.

## Requirement Traceability
FR-001/005/006 → T001/T003/T004/T005. FR-002 → T001/T003/T005. FR-003 → T001/T004/T005. FR-004 → T001/T002/T004/T005. SC-001–003 → T005.

FR-002 presentation refinement, approved 2026-09-09: customer and supplier commitment rows use the same decorative package icon. Do not use an empty circle that suggests a completion checkbox. Acceptance: both sides show package icons; row selection still opens details.

Daily-work totals appear beside the shared content title, with no separate empty header row. Existing side-tab counts and filtered totals retain their meaning. Header tab underline moves 4px closer to its label while preserving its hit target.
