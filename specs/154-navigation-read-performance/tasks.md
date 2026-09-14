# Tasks

## Setup and review
- [x] T001 Record approved scope, baseline and Constitution PASS in spec.md, research.md and plan.md (FR-001–005).

## US1 — Browser lookup
- [x] T002 [US1] Add failing parity, collision, late-initialization and bounded-scan cases in apps/web/scripts/localization-contract.test.mjs (FR-001–002, FR-005).
- [x] T003 [US1] Add lazy catalog resolver in apps/web/src/localization-core.ts and integrate apps/web/src/localization.tsx (FR-001–002).

## US2 — Payments
- [x] T004 [US2] Add failing selective refresh, parity, freshness, totals, reversal and isolation tests in packages/reality-core/tests/test_payment_projection_performance.py (FR-003–005).
- [x] T005 [US2] Extract payment builder and extend selective refresh in packages/reality-core/src/reality/services/projections.py (FR-003–004).

## Final validation
- [x] T006 Run required complete gates and review scoped diff; record results in quickstart.md (FR-005, SC-003).
- [x] T007 Apply scoped changes to the local integration, deploy and measure; create a separate follow-up PR and record evidence in quickstart.md (FR-005, SC-001–002).

Dependencies: T001 → analysis → T002 → T003; T004 precedes T005; both stories precede T006/T007. Independent story tests could run in parallel; no agents are required. No unrelated UI or domain changes.
