# Feature Specification: Guided Analysis Builder

**Feature Branch**: `main` (explicitly requested)
**Language**: English
**Created**: 2026-09-18
**Status**: Implemented and verified
**Input**: Match the supplied Analysis Builder screenshots: editable sentence, Result / Connections / Cypher, and private saved analyses. The owner accepted the ten-point scope in conversation.

## Context and Intent

### Problem
The current business-record selection requires model knowledge before users can ask a business question. The reference explains the interpreted question before presenting its answer.

### Scope
Replace the analytics builder presentation with the reference hierarchy while preserving the reporting platform's checked semantics, catalog, private reports, templates and company isolation. This supersedes spec224's result-first browser presentation and retirement of its path editor only.

### Non-Goals
No new business database, source fields, fabricated sample numbers, unrestricted Cypher execution, inferred settlement status, or alternate financial calculations. No changes to the global sidebar or unrelated report-proposal work. Unsupported questions must be explained, never disguised as supported presets.

## User Scenarios & Testing

### User Story 1 - Ask and refine a business question (Priority: P1)
A reader opens a template, catalog selection or default analysis and adjusts colored sentence controls.
**Independent Test**: Choose a declared example, change period/filter/grouping, and see the same checked question and fresh result.
**Acceptance Scenarios**:
1. Opening a template fills the sentence and results consistently without creating a saved report; the Builder contains no separate question header or input panel.
2. Given a free-text question submitted through the retained shared interpretation tool, submitting it produces a checked interpretation or an actionable clarification/refusal. Unsupported accounting concepts are not silently replaced with order value.
3. Given a sentence, changing a record, connection, measure, period or grouping updates the query; removing a condition removes all its bounds.
4. Given a slow read followed by a newer change or company switch, the old response cannot overwrite the new question.

### User Story 2 - Understand results and connections (Priority: P1)
A reader switches between results and a diagram of the actual question.
**Independent Test**: Build a branched question, inspect its connections, select a node, edit filters and return to results.
**Acceptance Scenarios**:
1. Results show localized table values and summary cards with explicitly stated meanings, units and scope. No totals are inferred from a truncated grouped table.
2. Connections show actual direction and branch origin. Node controls reveal the selected record's fields and conditions; real counts are shown only when supported by the same scoped read.
3. Empty data, unknown filter vocabulary, loading and refused questions remain distinct. Result metadata describes the last successful read, not upstream completeness.

### User Story 3 - Edit the technical query and save (Priority: P1)
An experienced reader edits the admitted path syntax, executes it, and saves the checked question.
**Independent Test**: Execute a generated path, change it, switch tabs, save and reopen the same question.
**Acceptance Scenarios**:
1. Generated path plus parameters round-trip without changing filters, aliases, branch origins, grouping, ordering or limits.
2. Expert text survives tab switches and unsuccessful execution. A question that cannot be represented by the simple sentence remains lossless in expert mode; switching back requires an explicit reset, never implicit deletion.
3. Saving is explicit, private and revision-checked. Reopening re-executes the stored question. Invalid or unexecuted expert edits cannot accidentally save the previous query.

### Edge Cases
- Ambiguous questions, unavailable AI/provider, empty catalog, unavailable examples, mixed units, unknown properties, unsupported finance measures.
- Multiple same-name records, branched/repeated nodes, long labels, missing dates, syntax and parameter errors, advanced existence/aggregate conditions.
- Racing reads, failed requests, company/language changes, model-version drift, stale report revisions, compact mobile and docked chat.

## Requirements

### Functional Requirements
- **FR-001**: Start directly with analysis configuration and save action, sentence and removable conditions, then Result, Connections and Cypher tabs. Omit the separate Builder title/subtitle/read-state badge and question input/example panel.
- **FR-002**: Preserve the shared question interpretation capability and its validation, AI eligibility and usage controls. Browser entry uses existing templates, catalog transitions and sentence controls; the removed free-text panel is not required.
- **FR-003**: Expose record, connection, measure, period, grouping, condition and ordering controls with catalog-backed choices and business labels. Preserve multi-measure and branched analyses and required unit axes.
- **FR-004**: Maintain one checked query across presentations, retain unexecuted expert drafts, cancel/ignore obsolete reads, and prevent old results appearing current.
- **FR-005**: Results use real values only, shared localized formatting and tenant-scoped reads. Summary cards identify their scope; unavailable business KPIs/comparisons are not invented. Preserve table sorting/filtering/limits and technical derivation access.
- **FR-006**: The connection diagram follows true declared links and direction, supports branches and selected-node editing, and never uses row counts as distinct-node counts.
- **FR-007**: Provide an editable Cypher-near path and parameters with explicit execution, read-only enforcement and visible syntax errors. Generated text must round-trip; advanced clauses must survive without being silently simplified.
- **FR-008**: Save/create/update/reopen existing private reports through shared services, preserve revision/idempotency checks, and keep templates and report library reachable. Saving changed analysis is explicit; invalid drafts are not saved.
- **FR-009**: Define pending, success, stale, empty, refusal, error and unavailable-AI states. Successful-read labeling never asserts all upstream data is current.
- **FR-010**: Use the existing flat register geometry, compact typography, shared controls and theme-aware semantic colors throughout Builder and Explore data, wrap the sentence and controls on mobile, constrain horizontal scrolling to results/diagram/editor, use accessible labeled controls/tabs, and localize new copy in supported languages.
- **FR-011**: Preserve PostgreSQL, tenant checks on every read, bounded execution, declared measure semantics, evidence traceability and existing confirmation boundaries. No new persisted business authority.
- **FR-012**: Add tests before implementation where practical, including query round trips, unsupported expert shapes, racing responses, sentence/graph edits and saved-report behavior; run required repository checks and report any blocked evidence honestly.

- **FR-013**: Provide Explore data with searchable object/field catalog, actual object/edge/field counts, Fields / Relationships / View data tabs, bounded tenant-scoped previews, and Use in analysis / Add field / Open path transitions into the builder. Do not fabricate record counts. Preserve the builder draft when browsing the catalog.

### Key Entities
- Analysis draft: checked question, current view, optional unexecuted path/parameters.
- Analysis result: bounded live observation of that exact question, with derivation and successful-read time.
- Private report: existing owner-scoped saved question and revision; no stored result.

## Success Criteria
- **SC-001**: Each declared example opens a consistent question, editable interpretation and result without requiring technical identifiers.
- **SC-002**: All three reference tabs are reachable by keyboard; switching between them retains the current query and expert draft.
- **SC-003**: Round-trip and persistence scenarios preserve the full supported question; stale-response scenarios never replace newer results.
- **SC-004**: At 390px and 1440px widths there is no page-level horizontal overflow, and the sentence/results hierarchy is present without the removed header/input panel.

## Assumptions and Dependencies
The owner’s subsequent design review supersedes screenshot styling: omit the Builder heading, read-state badge, question input and example pills; use the existing flat application design throughout Builder and Explore data. The hosted reference was subsequently inspected through the existing signed-in Chrome app, including Explore data and sentence menus. Its catalog has a searchable left column and Fields / Relationships / View data on the right. Literal mock data and its inconsistent revenue/open-invoice headings are intentionally not copied. Supported examples come from the executable catalog; unavailable open-invoice aging and product-group revenue must not be promised. Existing global shell remains. User approval covers implementation on main; unrelated working-tree edits are preserved.

## Requirement Traceability

All repository content is English. Each FR maps to test and implementation tasks in [tasks.md](tasks.md#requirement-coverage). Acceptance scenarios are exercised by the focused graph tests and final browser review; required suite outcomes are recorded in verification.md.

## Shared workspace components (owner-approved refinement)
- **FR-014**: All four analytics views use RegisterWorkbench and the shared header action slot; primary tabs are the only page titles. Local tabs reuse RegisterHeader local placement and register-tabs. Inputs/actions use shared controls; result and catalog tables use shared ERP table geometry and footer. Templates and reports use compact flat lists. Preserve query state when switching views and expose Builder header actions only while its view is active.

## Three-area analysis workflow (owner-approved)
- **FR-015**: Primary tabs are My reports, Analysis, Explore data in that order. Default entry is My reports with an explicit first-analysis action when empty. Existing template links open templates inside Analysis. Analysis offers Create with chat, Use a template, and Build it yourself only before an analysis is opened; templates open unsaved drafts. Existing drafts survive catalog/report browsing.
- **FR-016**: Reuse the global chat, never a second chat surface. Create/adapt actions prefill an editable prompt without sending; adaptation attaches the current checked query snapshot (no result rows) as visible removable context. Preserve existing composer text, tenant isolation, usage policy and confirmation. Disable adaptation for pending/unexecuted/failed queries.
- **FR-017**: Graph report proposals in chat offer Open in analysis for supported create/update definitions. Load via the existing authenticated proposal API, execute as an unsaved draft, preserve the full query, and never approve or save automatically. Loading/refusal remains explicit.

## Clear question hierarchy (owner-approved)
- **FR-018**: Restore one bordered question section headed How Reality understands your question, with Adapt with chat beside it. Emphasize the editable sentence with larger tokens; show selected measures in that sentence. Display additional conditions once in a labeled row, excluding the period already represented in the sentence. Keep that period removable from its menu. Put measure/output-column configuration and sorting in a collapsed Measures and columns disclosure. Result/navigation remain outside the question section and retain the shared app design. Technical identity axes remain in the query but are subordinate in presentation; never drop required currency/unit grouping.

## Compact editable question (owner-approved refinement)
- **FR-019**: Supersede FR-018's oversized colored tokens with normal 14px typography,
  neutral bordered controls and compact spacing. Present meaningful grouping labels
  without technical identity columns or truncated +N captions; retain every actual
  grouping key in the query and advanced controls. Integrate snapshot date into the
  sentence with an accessible UTC explanation. Show a clear unrestricted filter state
  and a compact add-filter control. Keep chat adaptation a secondary header action.

FR-019 visual correction: sentence dropdown indicators use consistently sized,
non-shrinking chevrons with an explicit gap rather than font-dependent glyphs.
