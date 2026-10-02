# Tasks

## Foundation
- [x] T001 Specify and review user-approved private-per-user scope and resolve research (FR-001–FR-006, DR-001/DR-002).
- [x] T002 Complete plan, contracts and Constitution Check; generate requirement checklist and analyze coverage.

## US1/US2 Private Analytics
- [x] T003 Add failing lifecycle/current-authority/privacy tests in test_reporting_graph_lifecycle.py, test_requested_analysis.py, test_reporting_graph_surfaces.py and test_proposal_decision_policy.py (FR-001/FR-002/FR-003/FR-005).
- [x] T004 Implement shared persisted eligibility in services/analytics/reports.py and delegate requests._member without changing owner/tenant filters (FR-001/FR-002/FR-003, DR-002).

## US3 Truthful Presentation
- [x] T005 Add failing four-language admin/member/nonmember switcher/card browser assertions in apps/web/scripts/unified-settings-browser.mjs (FR-004/FR-006).
- [x] T006 Add shared companyAccess helper, explicit identity props and localized access copy in CompanySwitcher/CompanySettings/Shell/SettingsPage/localization (FR-004/FR-005/FR-006).

## Verification and Release
- [x] T007 Update docs/WEB_SPEC.md and spec coverage; reconcile older spec membership prerequisites with spec329 (FR-001–FR-006).
- [ ] T008 Run complete related service/API/proposal suites, browser journeys, frontend contracts/build/i18n, lint/spec/docs gates; review privacy and current-authority regression evidence.
- [ ] T009 Publish PR, require full green hosted CI, merge/deploy and perform read-only live admin/library/switcher checks; record final evidence.

## Requirement Coverage
FR-001: T003/T004/T008/T009. FR-002: T003/T004/T008. FR-003: T003/T004/T008. FR-004: T005/T006/T008/T009. FR-005: T003/T004/T006/T008. FR-006: T005/T006/T008. DR-001: T007/T008 diff/schema review. DR-002: T003/T004/T008.
Dependencies: T003 before T004; T005 before T006; T007 and T008 after implementation; T009 after all required checks pass.
