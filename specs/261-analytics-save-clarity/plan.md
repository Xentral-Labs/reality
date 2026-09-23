# Plan: Saving an analysis is visible and named

One new web module, one rewritten component, one resolved field in an existing read model. No schema, no migration, no new endpoint, no new service.

## Backend (FR-009)

`services/analytics/proposals.py::preview` gains `report_id` in its result. For an operation that names an existing report it is `arguments["report_id"]`. For a `create` or `duplicate` whose proposal is confirmed it is the row the change wrote, found by the retry key the row already stores (`AnalyticsReport.create_request_id == arguments["request_id"]`, owner- and tenant-scoped through the existing `require_author`), and `None` when that row was since deleted. A proposal still awaiting confirmation resolves to `None` because nothing was written. This reads one indexed column; it adds no field to the report and no new authority — the link already exists, it was simply never returned.

## Web

**`analytics/reportName.ts` (new, FR-003 – FR-005)** — `suggestedName(plan, nodes)` composes the analysis in the reader's own catalog labels: the records it reads, then its measures, then `groupCaptions`, joined with `·` and cut to the stored 120-character limit. `analysis-empty` cases fall back to the root node's label. Pure, so it is unit-tested without a browser.

**`analytics/GraphSteps.tsx`** — `Save` stops going through `PageActionBar` and renders where it is, inside the analysis card, as one identity row: the report's name or the draft's carried name on the left with its state, the save controls on the right, and the naming field in the same row when it opens (FR-001, FR-002, FR-006). `Builder` gains `initialName` (the name a template or proposal carried in), a `baseline` of the last saved question captured on the first answer after a load or a save, and sets `activeReport` from a successful save — today it never does, so a second save of the same analysis silently creates a second report. A stable-key JSON compare of `canonical` against `baseline` is the unsaved-changes state (FR-006). `onSaved` and a new `onLibrary` carry the rest to the page (FR-007). A failed save keeps the field and the name (FR-008).

**`AnalyticsPage.tsx`** — the draft carries a name; `onAdopted` receives the template's label and `ProposalAnalysis` the proposal's name (FR-003). `onSaved` records the report in the address without remounting the builder: `currentTarget` is advanced first, exactly as `open`/`start` already do, so the target effect does not reset the draft, and the `report` prop stays as it was so `Builder`'s key does not change and the answer on screen is not thrown away (FR-007).

**`analytics/GraphTemplates.tsx`** — passes its label with the question, and states that adopting fixes the window to dates (FR-003, FR-012).

**`analytics/ReportLibrary.tsx`, `analytics/DataExplorer.tsx`** — `presentation="inline"`, the existing flat-button presentation the chat page already uses, so "New analysis" and "Use in analysis" are visible without opening "More actions" (FR-001).

**`analytics/GraphReportProposal.tsx`** — reads `status` and the new `report_id`: awaiting confirmation it offers "Open in analysis" and says that is an unsaved preview; confirmed it says the report was saved and opens the saved report by id; rejected or deleted it offers nothing (FR-010).

**`localization.tsx`** — German (and any other edition with the same collision) distinguishes the template toggle from the row action; new strings for the draft states, the save confirmation and the period wording (FR-011, FR-012).

## Constitution Check

PASS. No schema, migration, table or column (Hard rule 4: nothing becomes typed). Hard rule 11: nothing is derived and stored — the suggested name is composed at read time, never written unless a person confirms it, and the unsaved-changes state is compared in the browser, not recorded. Hard rule 5: the confirmed create resolves through the retry key the row already carries, the shortest true link, rather than a new foreign key. Hard rule 7 and the Web UI invariant: the surface calls the same `graph.reports.change` service and proposal confirmation as CLI and chat; no alternative business rule. Hard rule 8: every read stays tenant- and owner-scoped through `require_author`. Hard rule 10: saving stays an explicit confirmed action and the proposal boundary is untouched.

## Verification and rollback

`packages/reality-core/tests/test_analytics_report_proposals.py` covers FR-009 including the deleted-report and unconfirmed cases. `apps/web/scripts/analytics-report-naming.test.mjs` covers the suggestion and the unsaved-changes comparison. `apps/web/scripts/analytics-save-clarity-browser.mjs` walks US1 – US6 against the fixtures in English and German. Re-run `make spec-check`, `npm run format:check`, `npm run test:i18n`, `npm run i18n:audit`, the web build, and the backend suite for the analytics package. Revert the commit to roll back; there is no migration and nothing was written.
