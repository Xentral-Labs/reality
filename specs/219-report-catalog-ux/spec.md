# Feature Specification: Report catalog experience
**Language**: English
**Status**: Approved scope
## Context and Intent
The Calculated views page exposes technical projections and views before explaining their business use. Replace the two disclosure columns with a searchable report directory sharing the Actions tree pattern. Keep navigation and existing data readers.
### Non-Goals
No new reports, reporting engine, calculations, schema changes, navigation relocation or changed source authority.
## User Scenarios & Testing
### US1 — Find a useful report (P1)
Users browse workspace folders, scan localized titles, expand summaries, search across report metadata and open a report with a keyboard-accessible action.
### US2 — Read and understand a report (P1)
Opening shows the existing data preview with the report title and summary. Technical explanation, documentation and code are secondary details. Closing returns focus and retains filters.
## Requirements
- **FR-001**: Replace projection/view columns with a report directory using the same shared folder branches as Actions, localized report names and expandable summaries. Each report appears once under its first workspace category; all workspace tags remain in its details. Combine entries only when their exact data destination matches; preserve distinct stored/live readers and unknown catalog entries.
- **FR-002**: Provide report search across names, descriptions and aliases. Search automatically opens matching directory groups; clear search restores manual group expansion. Include Expand all/Collapse all controls matching Actions, disabled during search, and explain empty results.
- **FR-003**: Report entries use keyboard-accessible disclosures with a clear Open report or Show details action. Opening reuses existing tenant-scoped readers, freshness/error/empty states and preview limits. Price resolution retains details-only access because its data requires business inputs.
- **FR-004**: Keep technical definitions, code, documentation and application links in secondary Details within the opened report. Preserve confirmation and source traceability.
- **FR-005**: Support English/German/Dutch/Spanish, desktop/mobile, keyboard opening/closing and focus restoration without changing navigation.
- **FR-006**: In an opened report, keep title, summary and Close visible while data scrolls. Show the catalog explanation initially expanded beside data on desktop and as a collapsed disclosure before data on narrow screens, with a bounded scroll area and keyboard-operable disclosure. Explanation access must not require scrolling through data. Preserve details-only reports, raw preview limits and existing readers. Show one canonical explanation; group code and technical definitions under a single initially collapsed Technical details disclosure. FR-007 replaces alias cards with workspace text links and one documentation link.
- **FR-007**: Compose report explanation once, with one localized business explanation, deduplicated workspace text links, one documentation text link and one secondary calculation/source section. Never render complete alias-specific catalog cards. Keep code as a text-styled button, original definitions/contracts accessible and unknown reports supported.
- **FR-008**: Present known dispatch fields in business order (customer, order reference, due date, readiness, blockers, priority, items) with localized labels, date and boolean formatting. Technical identity and every original value remain in expandable row details. Render nested values as readable counts/details, never raw JSON in the main table. Other reports use conservative field labels and preserve unknown fields. Do not calculate new business values or convert exact decimal strings to floats. Provide a real final row-details action, neutral table controls, and omit the nonfunctional filter affordance in report tables.
## Assumptions and Dependencies
User explicitly approved presentation-only redesign. Existing application-reference catalog remains the authority for available entries; UI metadata only describes and categorizes them. No unresolved clarifications.
## Success Criteria
All requirements pass contract/browser validation; frontend build, localization audit and spec policy pass.
## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001 | T001,T002 | Catalog grouping tests and browser |
| FR-002 | T001,T002 | Filter/search tests and browser |
| FR-003 | T001,T003 | Routing preservation tests and keyboard/data browser |
| FR-004 | T003,T004 | Browser details and source links |
| FR-005 | T002,T004 | Four-language responsive browser and frontend gates |

## Report context refinement (2026-09-17)
The user requested visible report context alongside data. This refinement implements that presentation scope only. Acceptance: a long report retains its header while scrolling; desktop shows explanation beside data; mobile shows explanation before data without viewport overflow; disclosure, Escape and focus restoration work. Report-specific filters and a new report engine remain out of scope. FR-008 adds presentation-only column formatting.

| Requirement | Tasks | Proof |
|---|---|---|
| FR-006 | T005,T006 | Four-language desktop/mobile report browser and frontend gates |

## Designer-reviewed report reading (2026-09-17)
The user explicitly requested a whole-screen design review and implementation. The review identified alias-level component duplication and raw API field ordering as the primary problems. Acceptance: expanded technical information shows one set of source/calculation metadata and one code action; navigation uses text links; dispatch opens with readable business columns, while each original value remains accessible in row details. Unknown reports and input-dependent price determination retain safe fallback behavior.

| Requirement | Tasks | Proof |
|---|---|---|
| FR-007 | T008,T009 | Sidebar browser assertions and four-language audit |
| FR-008 | T008,T010 | Presentation unit tests, row-details browser and responsive screenshots |

## Navigation ownership (spec 218 refinement)
Calculated views now belongs to Tools alongside Actions. Business Facts retains All records and Fact rules. Report URLs and behavior are unchanged.

## Shared directory refinement (2026-09-17)
The user explicitly selected the existing Actions directory-tree pattern. FR-001/002/003 now replace the custom report cards and workspace filter buttons with shared directory branches and compact report disclosures. Existing report dialogs, Tools ownership, data readers, deduplication, focus restoration and company context remain unchanged. T011 covers tests, shared rendering, browser verification and frontend/spec gates.
