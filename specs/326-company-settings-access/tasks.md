# Tasks: Company Settings Access

## Setup
- [x] T001 Record approved scope and research in specs/326-company-settings-access/spec.md and research.md.
- [x] T002 Review Constitution and design in specs/326-company-settings-access/plan.md.

## US1 - Owner Settings
- [x] T003 [US1] Add failing production/config independence proofs in packages/reality-core/tests/test_mcp_http_runtime.py and test_master_data_api.py (FR-001/FR-002/DR-001/DR-002).
- [x] T004 [US1] Separate public URL validation and canonical issuer fallback in packages/reality-core/src/reality/mcp/config.py (FR-001/FR-002).

## US2 - Accurate Membership
- [x] T005 [US2] Add missing-role browser assertions in apps/web/scripts/unified-settings-browser.mjs (FR-003/FR-005/FR-006).
- [x] T006 [US2] Render absent membership explicitly in apps/web/src/unified/CompanySettings.tsx and localization dictionaries (FR-003/FR-006).

## US3 - Private Library Explanation
- [x] T007 [US3] Add service/API denial and non-disclosure regression tests in packages/reality-core/tests/test_reporting_graph_lifecycle.py and test_reporting_graph_surfaces.py (FR-004/FR-005).
- [x] T008 [US3] Explain list membership refusal through packages/reality-core/src/reality/services/analytics/reports.py and apps/web/src/unified/analytics/ReportLibrary.tsx with localized messages (FR-004/FR-005/FR-006).
- [x] T009 [US3] Add browser refusal/recovery assertions in apps/web/scripts/analytics-save-clarity-browser.mjs (FR-004/FR-006).

## Verification and Review
- [x] T010 Update docs/WEB_SPEC.md and applicable MCP contract; run generated catalog checks (FR-001–FR-006).
- [x] T011 Complete tests/lint/spec/docs/browser gates and record evidence in specs/326-company-settings-access/quickstart.md.
- [ ] T012 Review final diff, publish PR, obtain green complete hosted CI, merge/deploy under explicit session authorization and verify logged-in UI.
