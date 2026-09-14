# Tasks: Analytics and Master Data

## Phase 1 — Gates
- [X] T001 Review owner-authorized scope and constitution in spec.md and plan.md; record research, contracts and no-schema decision.
- [X] T002 Analyze spec/plan/tasks coverage before implementation; record technical review in quickstart.md after the read-only analysis.

## Phase 2 — Analytics (US1)
- [X] T003 [US1] [FR-002 FR-003 FR-004 FR-008] Add failing SQL metric/contributor, period/correction/tenant/empty tests in packages/reality-core/tests/test_company_insights.py.
- [X] T004 [US1] [FR-002 FR-003 FR-004 FR-008] Implement shared analytics in packages/reality-core/src/reality/services/company_insights.py and typed read adapters in web/api.py; document metric definitions and coverage in contracts/workspaces.md.

## Phase 3 — Reference maintenance (US2, US3)
- [X] T005 [US2 US3] [FR-005 FR-006 FR-007 FR-008] Add failing role/register/detail, four-family preservation, stale/concurrent/foreign/idempotency tests in packages/reality-core/tests/test_reference_workspace.py and test_unified_workspace_api.py; register families in docs/SPEC_COVERAGE_MATRIX.md.
- [X] T006 [US2 US3] [FR-005 FR-006 FR-007 FR-008] Implement bounded reference service and canonical preparation in packages/reality-core/src/reality/services/reference_workspace.py, batch guard in services/business_locks.py and pre-handler stale checks in tools/application.py.
- [X] T007 [US2 US3] [FR-005 FR-006 FR-007 FR-008] Expose scoped read/prepare/confirm/detail contracts in packages/reality-core/src/reality/web/api.py with strict bodies and current authorization.

## Phase 4 — Unified presentation (US4)
- [X] T008 [US4] [FR-001 FR-003 FR-004 FR-005 FR-006 FR-007 FR-009 FR-010] Add route/selection contracts and executable browser journeys in apps/web/scripts/unified-app-contract.test.mjs and unified-workspaces-browser.mjs.
- [X] T009 [US4] [FR-001 FR-002 FR-003 FR-004 FR-009 FR-010] Build AnalyticsPage.tsx and shared Home preview in apps/web/src/unified/; wire API types, routing and Shell using existing controls and accessible chart/contributors.
- [X] T010 [US4] [FR-001 FR-005 FR-006 FR-007 FR-009 FR-010] Build MasterDataPage.tsx and MasterDataCard.tsx; connect delivery references and master proposals from Decisions/Chat; preserve scope and outcome recovery.
- [X] T011 [US4] [FR-010] Complete apps/web/src/localization.tsx and run visual/keyboard review at both widths/themes and four languages; record evidence in quickstart.md.

## Phase 5 — Verification and review
- [X] T012 Run complete PostgreSQL, lint/spec, web/i18n/contracts/browser and docs gates; record results in quickstart.md. Review no-schema diff, stale checks, query bounds and rollback.
- [X] T013 Update docs/WEB_SPEC.md, docs/WEB_UX_MATRIX.md, apps/docs/content/product-guides/daily-control.md and feature status after green checks; record owner review separately from rollout.

## Dependencies
T001 → T002 → service tests T003/T005 → services T004/T006 → adapters T007 → browser contracts T008 → presentation T009/T010 → polish T011 → verification/review T012/T013. Independent read-only fixture research can run alongside other work; no parallel agents or overlapping edits are required.

## Requirement Coverage
| Requirement | Test tasks | Implementation tasks |
| --- | --- | --- |
| FR-001 | T008 | T009, T010 |
| FR-002 | T003 | T004, T009 |
| FR-003 | T003, T008 | T004, T009 |
| FR-004 | T003, T008 | T004, T009 |
| FR-005 | T005, T008 | T006, T007, T010 |
| FR-006 | T005, T008 | T006, T007, T010 |
| FR-007 | T005, T008 | T006, T007, T010 |
| FR-008 | T003, T005 | T004, T006, T007 |
| FR-009 | T008 | T009, T010 |
| FR-010 | T008, T011 | T009, T010, T011 |
