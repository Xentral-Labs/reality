# Tasks

## Setup and foundational review

- [x] T000 Review user scope and Constitution in specs/221-remove-analytics-overview/spec.md and plan.md.

## US1 - Direct analytics navigation

- [x] T001 [US1] Add routing and rendered tab regressions in apps/web/scripts/analytics-overview-retirement.test.mjs.
- [x] T003 [US1] Remove Overview and simplify Home in apps/web/src/unified/AnalyticsPage.tsx, HomePage.tsx, routing.ts, CaseAssistant.tsx and apps/web/src/api.ts; adapt browser checks.

## US2 - Retire exclusive backend

- [x] T002 [US2] Add retired GET contract assertions in packages/reality-core/tests/test_unified_workspace_api.py before removing routes.
- [x] T004 [US2] Remove packages/reality-core/src/reality/services/company_insights.py and its web/api.py adapters; adapt company tests and delete exclusive service tests.

## Verification and review

- [ ] T005 Update docs/WEB_SPEC.md and docs/features/analytics.md; run gates and record review in specs/221-remove-analytics-overview/review.md.

## Dependencies and execution

T000 → T001/T002 → T004 → T003 → T005. Tests first, service removal before adapters.
T001 and T002 are independent test work; implementation stays sequential.

T005 remains open only for the broader legacy warehouse-menu browser assertion;
all feature-specific verification and documentation are complete. See review.md.

## Sidebar refinement (FR-005)

- [x] T006 [US1] Update sidebar grouping/order/label browser assertions in apps/web/scripts/analytics-browser.mjs and unified-shell-chat-browser.mjs before implementation.
- [x] T007 [US1] Move and rename the link in apps/web/src/unified/Shell.tsx; update docs/WEB_SPEC.md and run frontend/browser gates.

Dependency: T006 → T007. Analysis: FR-005 has scenario, implementation and test
coverage, no ambiguity or critical finding; no new backend or schema work.
