# Tasks: Simulator spectator

## Setup
- [x] T001 Write accepted scope, research, design and contracts in specs/375-simulator-spectator/ (FR-001–009).

## Foundations
- [x] T002 Write reader/HTTP boundary and incomplete-journal tests in packages/reality-core/tests/scenarios/test_simulator_viewer.py; observe failing import (FR-001,006,008).
- [x] T003 Implement read-only normalization in packages/reality-core/scenarios/company_simulator/viewer/reader.py (FR-001–006,008).

## US1 — Watch the company
- [x] T004 [US1] Add actual-run snapshot assertions in packages/reality-core/tests/scenarios/test_complete_company.py (FR-007).
- [x] T005 [US1] Implement atomic snapshot export in packages/reality-core/scenarios/company_simulator/complete.py (FR-004–007).
- [x] T006 [US1] Implement loopback HTTP adapter/CLI in packages/reality-core/scenarios/company_simulator/viewer/server.py and __main__.py (FR-001,006,008).
- [x] T007 [US1] Implement responsive timeline/status/coverage UI in packages/reality-core/scenarios/company_simulator/viewer/{index.html,app.js,style.css} (FR-004–006,009).

## US2 — Customers and suppliers
- [x] T008 [US2] Add explicit-party, original-message and absent-reply tests in packages/reality-core/tests/scenarios/test_simulator_viewer.py (FR-002,003).
- [x] T009 [US2] Implement party filters, message states, action separation and evidence expansion in packages/reality-core/scenarios/company_simulator/viewer/app.js (FR-002,003,009).

## Verification
- [x] T010 Browser-check saved runs, selection, polling, inert text and narrow viewport; retain evidence under artifacts/company_simulator/viewer/ (FR-001–009, SC-001–004).
- [x] T011 Run affected acceptance and full required backend/lint/spec/whitespace gates; document evidence in specs/375-simulator-spectator/review.md (FR-001–009).
- [x] T012 Document launch in packages/reality-core/scenarios/company_simulator/{README.md,viewer/README.md} and docs/scenarios/company-simulator.md; update docs/SPEC_COVERAGE_MATRIX.md (FR-001,009).

Dependencies: T001 → T002/T004/T008 → T003/T005 → T006 → T007/T009 → T010/T011 → T012. Reader tests and snapshot assertions can be prepared independently. MVP is read-only saved-run selection and timeline; customer/supplier filtering and active snapshots finish the accepted scope.

- [x] T013 FR-003/004/009: Label simulated local responses and unsent drafts, show reply context/day, and verify supplier conversation in Chromium.

## Live/replay stories (FR-010)

- Add endpoint regression for complete checkpoints, incomplete tails and run containment.
- Promote prototype to fixed CSP-compatible story assets; add watch/replay controls, run selection, polling, observation/error labels.
- Verify browser updates, replay isolation, run selection and existing viewer regressions; document invocation.
