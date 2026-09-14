# Tasks
- [x] T001 Add readiness freshness/config/HTTP/API regression tests before implementation.
- [x] T002 Implement optional process health and scoped readiness adapter; configure private deployment probes.
- [x] T003 Add Home activity/readiness browser acceptance (UI proof added during implementation).
- [x] T004 Implement localized Home pulse with existing event rendering/Inspector and safe polling.
- [x] T005 Run backend/frontend/browser/spec/docs gates, review and update local8080; record evidence.

- [x] T006 [FR-008–010] Add graph aggregation/detail regression tests first; implement shared read services and tenant API.
- [x] T007 [FR-009–011] Implement responsive localized rolling graph, detail inspection and compact status; browser verification.
- [x] T008 [FR-008–011] Verify full backend/frontend/browser/doc gates, update local stack and record actual runtime evidence.

- [x] T009 [FR-011] Add hover-height regression, stabilize summary layout, verify frontend/browser gates and update local web.

- [x] T010 [FR-008, FR-012] Add range-preference browser regressions; implement per-user browser persistence and 24-hour default; verify frontend/spec/browser gates and local web.

- [x] T011 [FR-013–014] Share menu/card destinations, add commitments and localized labels/open qualifiers in Shell, HomePage and localization; verify frontend contracts/build/i18n/spec and review; update local web.

- [x] T012 Stabilize Home loading order, add delayed-dashboard geometry regression and verify frontend/browser.

FR-015 verification: build, 61 frontend contracts and spec policy passed. HOME_LOADING_ONLY=1 browser matrix passed all 16 language/theme/viewport combinations with delayed dashboard responses and activity position delta below 2px. Broader existing graph suite stopped at an overlapping last-bucket hover target; polling/graph behavior was not changed or claimed verified. Local web rebuilt on port 8080.
