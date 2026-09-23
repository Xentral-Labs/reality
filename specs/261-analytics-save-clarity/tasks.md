# Tasks: Saving an analysis is visible and named

| ID | Task | Paths | Requirements |
|---|---|---|---|
| T001 | Failing proof for the resolved report of a report proposal: confirmed create, confirmed update, unconfirmed create, deleted report | `packages/reality-core/tests/test_analytics_report_proposals.py` | FR-009 |
| T002 | Resolve `report_id` in the proposal preview through the retry key the report row already stores | `packages/reality-core/src/reality/services/analytics/proposals.py` | FR-009 |
| T003 | Failing proof for the suggested name and the unsaved-changes comparison | `apps/web/scripts/analytics-report-naming.test.mjs` | FR-003 – FR-006 |
| T004 | `suggestedName` and the stable question comparison | `apps/web/src/unified/analytics/reportName.ts` | FR-004, FR-006 |
| T005 | `Save` renders in the analysis card as an identity row with its state, its controls and its naming field; `Builder` carries `initialName`, a saved baseline and the active report after a save | `apps/web/src/unified/analytics/GraphSteps.tsx` | FR-001, FR-002, FR-005 – FR-008 |
| T006 | Draft carries a name; saving records the report in the address without remounting the builder; "My reports" link | `apps/web/src/unified/AnalyticsPage.tsx` | FR-003, FR-007 |
| T007 | Templates pass their label and state that adoption fixes the window | `apps/web/src/unified/analytics/GraphTemplates.tsx` | FR-003, FR-012 |
| T008 | Library and data catalog show their primary action without a menu | `apps/web/src/unified/analytics/ReportLibrary.tsx`, `apps/web/src/unified/analytics/DataExplorer.tsx` | FR-001 |
| T009 | Proposal card distinguishes awaiting, confirmed, rejected and deleted; opens the saved report by id | `apps/web/src/unified/analytics/GraphReportProposal.tsx`, `apps/web/src/unified/ChatPage.tsx`, `apps/web/src/api.ts` | FR-010 |
| T010 | German edition distinguishes the template toggle from the row action; new strings in every edition | `apps/web/src/localization.tsx` | FR-011, FR-012 |
| T011 | Styling for the identity row in light and dark | `apps/web/src/unified/analytics/AnalysisBuilder.css` | FR-001, FR-006 |
| T012 | Browser proof of US1 – US6 in English and German | `apps/web/scripts/analytics-save-clarity-browser.mjs` | all |
| T013 | Web spec note and the full gate run | `docs/WEB_SPEC.md` | all |

Order: T001 → T002, T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013.
