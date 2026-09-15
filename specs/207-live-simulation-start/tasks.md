# Tasks: Live simulation start and header

## Setup and foundations

- [x] T001 Record accepted scope and reviewed design in specs/207-live-simulation-start/spec.md and plan.md.
- [x] T002 Complete pre-implementation analysis of specs/207-live-simulation-start/{spec,plan,tasks}.md.

## US1 — Initial activity

Independent proof: normal intake creates three deterministic initial orders, then ordinary demand; controls/replay remain safe.

- [x] T003 [US1] Add failing timing/service tests in packages/reality-core/tests/test_scheduled_job_startup.py (FR-002, DR-002).
- [x] T004 [US1] Add failing source/intake startup tests in packages/reality-core/tests/test_demo_data_startup.py (FR-001/002, DR-001).
- [x] T005 [US1] Implement bounded initial offsets in packages/reality-core/src/reality/scheduling/timing.py and services/scheduled_jobs.py (FR-001/002, DR-002).
- [x] T006 [US1] Opt in fresh starts in packages/reality-core/src/reality/services/demo_data.py and emit one initial order in jobs/handlers/demo_data.py (FR-001/002, DR-001).

## US2 — Header link

Independent proof: fresh running status shows link, all other states hide; current-company navigation and accessible responsive presentation.

- [x] T007 [US2] Add failing browser acceptance in apps/web/scripts/live-simulation-header-browser.mjs (FR-003–006, DR-003).
- [x] T008 [US2] Implement bounded status reader/link in apps/web/src/unified/LiveSimulationIndicator.tsx, api.ts and local DemoDataIntegration.tsx control notification (FR-003/006, DR-003).
- [x] T009 [US2] Wire HeaderControls.tsx/Shell.tsx and tailwind.css with reduced-motion pulse and responsive layout (FR-004/005).

## Verification and review

- [x] T010 Update docs/features/company-setup-demo.md, scheduled-jobs.md and docs/WEB_SPEC.md to describe changed behavior.
- [x] T011 Run required backend/frontend/spec/catalog and browser gates; record actual evidence in specs/207-live-simulation-start/quickstart.md.
- [x] T012 Review full diff and traceability, record review in specs/207-live-simulation-start/review.md; mark only verified tasks complete.

## Dependencies and implementation strategy

T001 → T002 → tests T003/T004 → implementation T005/T006. T007 precedes T008/T009. US2 can run independently of US1 after analysis (parallel example: browser fixture authoring and scheduler test authoring touch separate files). Implement sequentially locally, then T010–T012. US1 is the first independently usable increment; both stories are required for this request.
