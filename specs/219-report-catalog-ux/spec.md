# Feature Specification: Report catalog experience
**Language**: English
**Status**: Approved scope
## Context and Intent
The Calculated views page exposes technical projections and views before explaining their business use. Replace the two disclosure columns with a searchable report list, visible summaries and workspace filters. Keep navigation and existing data readers.
### Non-Goals
No new reports, reporting engine, calculations, schema changes, navigation relocation or changed source authority.
## User Scenarios & Testing
### US1 — Find a useful report (P1)
Users scan localized titles and visible summaries, narrow by workspace and search, and open a report with one keyboard or pointer action.
### US2 — Read and understand a report (P1)
Opening shows the existing data preview with the report title and summary. Technical explanation, documentation and code are secondary details. Closing returns focus and retains filters.
## Requirements
- **FR-001**: Replace projection/view columns with one report list with visible localized names, summaries and workspace tags. Combine entries only when their exact data destination matches; preserve distinct stored/live readers and unknown catalog entries.
- **FR-002**: Provide report search and All/Sales/Purchasing/Warehouse/Finance filters, with other relevant areas available for remaining reports; combine search and filter and explain empty results.
- **FR-003**: Entire report rows are accessible buttons. Opening reuses existing tenant-scoped readers, freshness/error/empty states and preview limits. Price resolution retains details-only access because its data requires business inputs.
- **FR-004**: Keep technical definitions, code, documentation and application links in secondary Details within the opened report. Preserve confirmation and source traceability.
- **FR-005**: Support English/German/Dutch/Spanish, desktop/mobile, keyboard opening/closing and focus restoration without changing navigation.
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
