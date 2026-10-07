# Implementation and verification tasks

- [x] T001 Review durable storage, shared scheduling and approvals; no schema expansion; tenant-before-schedule/source locking (FR-002,003,006,009).
- [x] T002 Add cross-session visibility, worker execution, restart/retry and context tests (FR-002,012).
- [ ] T003 Paced intake and causal confirmations/delays/partial receipts/arrival/payments implemented; automatic return/refund/amendment episodes and sustained rate proof remain pending (FR-001–004,007).
- [x] T004 Implement immutable inbox, cursors, acknowledgements and exact local replies with deduplication (FR-004–006).
- [ ] T005 Publish single external-agent prompt: documented in LIVE.md; actual connected model/disconnect trial remains pending (FR-008).
- [x] T006 Implement raw-source/effect reconciliation, delivery goals, fault pause and three-hour reports; tests exercise corruption and report retry (FR-009,011).
- [x] T007 Separate database-backed live UI; bounded recent views, timestamps, backlog, case counts, exact IDs and unknown liveness; Chromium manual event and mobile proof (FR-010).
- [ ] T008 Short real-clock smoke passed with three workers (6 orders/125.69 seconds); 41 live/shared-scheduler tests pass; full backend regression passed 6,448 tests with 10 skips before final purchasing/prompt changes; the final 37-test live/business/architecture group passed; head CI and sustained throughput/resource trial remains pending (FR-012).
- [x] T009 Read-only exact manual preview/injection, tenant/context refusal, stable retry, separate counting and browser proof (FR-013).

Do not describe the unchecked end-to-end/operator/capacity acceptance as passed.

- [x] T010 Implement and test staged concrete customer/supplier mail and exact requested quantities (FR-014).
- [x] T011 Implement and browser-test the live flow feed and party email/order/document workspace (FR-015).
- [x] T012 Update operating documentation/review, run relevant and required regression gates, and update PR evidence.
- [x] T013 Derive and test full-run fulfillment performance, cancellation/correction treatment and UI backlog drill-down (FR-016).
- [x] T014 Test and implement source-backed purchasing prerequisites, confirmed retained-run repair, supplier catalogue and operator instructions (FR-017).

- [ ] T015 Publish complete-round/restart acceptance instructions and verify with a real externally connected operator (FR-018); documentation alone does not close this gate.
- [x] T016 Verify simulator acceptance/replay/takeover/handback integration and document default readiness plus operator coordination duties (FR-019).

- [x] T017 Test and implement diverse early customer changes, late follow-ups and supplier clarifications; document timing and unchanged request-only authority (FR-020).

- [x] T018 Add failing carrier-observation regression for distinct handover/arrival timing, replay, mailbox pressure, corrected-only contents and unchanged announcements/history (FR-021–022).
- [x] T019 Implement bounded source-backed carrier observations before the mail gate through the existing reactions/service boundary (FR-021–022).
- [x] T020 Run live-company/shipment/cockpit regression and required lint/spec gates; restart existing workers and verify new source-linked handovers in the retained cockpit (FR-021–022).

## Local daily shipping planning fixture recovery

- [x] T090 Add failing scenario tests for day/replay/next-day/existing-plan/authority/calendar/source semantics of the trusted local daily shipping fixture.
- [x] T091 Implement scenarios/company_simulator/daily_shipping.py through existing shared source/proposal/owner-confirmation services and document the local invocation boundary in LIVE.md.
- [x] T092 Verify scenario and shipping regressions, wire the existing local supervisor without restarting its active business round, record today's accepted synthetic planning/source evidence and next-day guard proof; no production rollout.
