# Tasks: Enterprise operations cockpit

## Compact Operations workspace (FR-065–067)

- [x] T100 Add failing compact frame/default/selection and scoped shipping disclosure proof; preserve control/evidence coverage and extend lifecycle switch-state assertions.
- [x] T101 Add the mounted three-view workspace and contextual counted shipping blockers; localize and unify the two card surfaces without reader/business changes.
- [x] T102 Run required presentation checks, activate only web, inspect actual company, record evidence and update PR 383.

## Shared analysis including shipping (FR-062–064)

- [x] T097 Add failing default/six-option/shared-location and shipping-state restoration browser proof; adapt approved hierarchy assertions without dropping existing flow/source/control coverage.
- [x] T098 Reuse shipping in the sole analysis frame, keep all panels/state and day-versus-company scope, and stack Responsibility/log/Agents beside it.
- [x] T099 Run frontend/matrix/lifecycle/spec checks, inspect and activate web only, record evidence and update the existing PR.

## Hierarchy and quiet observation controls (FR-059–061)

- [x] T094 Add failing priority geometry, single analysis frame, shared rhythm/natural height and accessible icon-control browser regressions.
- [x] T095 Move Responsibility before monitoring, unify card structure/styles and replace only observation utilities with shared labelled icons.
- [x] T096 Run affected frontend/browser/lifecycle/spec checks, inspect and activate the real frontend, update PR and verification record.

## Stable analysis interaction (FR-057–058)

- [x] T091 Add failing one-selector, read-only summary, focus/viewport stability and bookmark/refresh/company-reset browser proofs.
- [x] T092 Implement local analysis selector, remove duplicate instrument navigation and replace hash state without scrolling; update four-language copy and shared styling.
- [x] T093 Run affected frontend/browser/lifecycle/spec checks, inspect the real local company, activate web only and update PR evidence.

## Preview parity follow-up (FR-052–056)

- [x] T087 Add failing service proofs for complete risk partitions, deduplication, canonical due-soon and unknown urgency, and browser proofs for the requested two-row geometry, legend, Agent/manual visibility.
- [x] T088 Derive additive risk partitions in the shared operating-flows reader from existing complete scoped cohorts; add the nullable DTO and truthful mixed instrument meters.
- [x] T089 Arrange shipping/log/Agent and selected analysis/responsibility rows; preserve rate and detail diagrams, evidence, live state and reviewed manual controls.
- [x] T090 Run affected checks, inspect both themes/narrow views and the real local company, update PR 383 and record exact evidence without closing earlier rollout gates.


## Instrument console follow-up (FR-047–051)

Dependency order: T082/T083 before T084/T085; T086 after both implementations.
Existing incomplete enterprise/soak tasks are not part of this bounded increment.

- [x] T082 [US5] Add failing console selection, preserved curves/evidence, refresh/disclosure and responsive proofs in `apps/web/scripts/operations-cockpit-browser.mjs` and fixture data (FR-047–048, FR-050–051).
- [x] T083 [US5] Add failing mail bucket reconciliation, exact lineage and missing-company coverage proofs in `packages/reality-core/tests/test_operating_flows.py` (FR-049).
- [x] T084 [US5] Implement console/selected analysis and labelled responsive charts in `apps/web/src/unified/OperatingFlowsPanel.tsx`, `OperationsCockpitPage.tsx`, `operationsCockpit.css` and four-language `localization.tsx` (FR-047–048, FR-050–051).
- [x] T085 [US5] Add canonical local incoming/first-reply buckets in `packages/reality-core/src/reality/services/operating_flows.py` and nullable web DTO fields in `apps/web/src/unified/cockpitModel.ts`, with no extra reads or rules (FR-049).
- [x] T086 Run affected backend/frontend/browser/live/build/i18n/format/spec/lint/doc gates, review the bounded diff and activate API/web only; record local viewing evidence in `specs/378-enterprise-operations-cockpit/quickstart.md` and `docs/features/operations-cockpit.md` (FR-047–051).

**Language**: English
**Input**: Approved product `spec.md`, proposed `plan.md`, research/data model/contracts and `quickstart.md`.
**Execution gate**: Owner approved the prepared concept and concrete proposal on 2026-10-06. The input/schema/model and live/Agent scope gates are satisfied; see `review.md` for the no-CRITICAL analysis and permission to proceed with the still-unmarked review checklists. Implementation is authorized; only proven tasks may be completed. Production rollout and runtime acceptance remain separate.

All paths below are repository-relative. Tests precede the implementation they prove. `[P]` means independent files after stated prerequisites; it does not authorize a second agent or bypass a gate.

## Phase 1 — Design authorization

- [x] T001 Record explicit owner input/schema and forecast-policy approval in `specs/378-enterprise-operations-cockpit/data-model.md`, `contracts/shipping.md` and `plan.md`; do not infer it from product scope approval.
- [x] T002 Record Constitution design conformance, reviewer-owned requirements-quality review and no-CRITICAL artifact analysis in `specs/378-enterprise-operations-cockpit/checklists/requirements.md` and the review record; stop on unresolved approval or critical findings.

## Phase 2 — Shared input and entry foundations

- [x] T003 [US1] [FR-003] [FR-006] [FR-007] [FR-008] [FR-009] [DR-001] [DR-002] [DR-003] Add failing reviewed-input/source/version/quantity/unit/confirmation/replay tests in `packages/reality-core/tests/test_shipping_plan_inputs.py`, including stale commitment meaning and foreign IDs.
- [x] T004 [US1] [DR-003] Add failing upgrade/downgrade, composite tenant-FK and immutable-source preservation proof in `packages/reality-core/tests/test_shipping_plan_migration.py`; inspect the current migration head without applying it to a real company.
- [x] T005 [US1] [FR-003] [FR-006] [FR-007] [FR-008] [FR-009] [DR-002] Implement approved closed input validation and completion-slot units in `packages/reality-core/src/reality/domain/shipping_performance.py`.
- [x] T006 [US1] [DR-003] Add approved mappings/constraints in `packages/reality-core/src/reality/db/core.py`; allocate the next free migration file under `packages/reality-core/migrations/versions/` and record its exact path in `plan.md`, then implement only the approved three input tables.
- [x] T007 [US1] [FR-003] [FR-006] [FR-007] [FR-008] [FR-009] [DR-001] [DR-002] [DR-003] Implement exact reviewed statement creation/revision/withdrawal through source versioning, business locks and replay in `packages/reality-core/src/reality/services/shipping_plans.py`.
- [x] T008 [US1] [DR-003] Register proposal producers through `packages/reality-core/src/reality/tools/shipping_operations.py`, existing proposal adapters in `mcp/server.py` and `cli/app.py`, and `config/command_catalog.yaml`/`resource_catalog.yaml`; do not introduce a new mandate or direct writer.
- [x] T009 [US4] [FR-001] [FR-016] [FR-017] Add failing optional-entry/URL-round-trip/company-reset tests in `apps/web/scripts/operations-cockpit-routing.test.mjs` and capability/member/disabled-route checks in `packages/reality-core/tests/test_operations_cockpit_adapters.py`.
- [x] T010 [US4] [FR-001] [FR-016] [FR-017] Add default-off capability in `packages/reality-core/src/reality/web/operations_cockpit.py`, mount through `web/app.py`, and the additive route/nav/context shell in `apps/web/src/unified/routing.ts`, `UnifiedApp.tsx`, `Shell.tsx`, `pageIntroduction.ts` and `api.ts`; preserve Home/Engine Room/adoption semantics.

## Phase 3 — User story 1: shipping by end of day (P1)

**Goal**: A populated three-series panel with exact site/day/quantity/evidence meaning.
**Independent proof**: The fixed-time two-site oracle plus missing/conflicting-input variants; no takeover or general company-SLA implementation is required.

- [x] T011 [US1] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] [FR-012] [DR-001] [DR-002] Add failing independent quantity/time/site/capacity domain proofs in `packages/reality-core/tests/test_shipping_performance_domain.py`, including split orders, partials, missing time, supersession, confirmed versus requested windows and DST.
- [x] T012 [P] [US1] [FR-010] [FR-018] [DR-001] [DR-003] [DR-005] Add failing full-cohort/service/basis/no-write/tenant tests and the populated business oracle in `packages/reality-core/tests/test_shipping_performance.py` and `test_shipping_performance_story.py` using shared service fixtures.
- [x] T013 [P] [US1] [FR-002] [FR-008] [FR-009] [FR-010] [FR-018] Add populated/missing/stale panel and supporting-order fixture assertions in `apps/web/scripts/operations-cockpit-browser.mjs` before panel implementation.
- [x] T014 [US1] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] [FR-012] [DR-002] Implement the approved pure effective-coverage/Soll/forecast/risk rules in `packages/reality-core/src/reality/domain/shipping_performance.py`; no random or AI-generated trajectory.
- [x] T015 [US1] [FR-010] [FR-018] [DR-001] [DR-003] [DR-005] Implement cohort-bounded shared reads, consistent current basis, full-result totals and supporting-order pagination in `packages/reality-core/src/reality/services/shipping_performance.py` and `operations_cockpit.py`.
- [x] T016 [US1] [DR-003] Expose canonical reads through `packages/reality-core/src/reality/tools/shipping_operations.py`, `web/operations_cockpit.py`, `mcp/server.py`, `cli/app.py` and the executable catalogs; retain membership and feature-availability guards.
- [x] T017 [US1] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] [FR-010] [FR-012] [FR-018] Implement returned-series presentation, cut-offs/site table/basis disclosure and paged order links in `apps/web/src/unified/ShippingDayPanel.tsx`, `ShippingSupportingOrders.tsx`, `OperationsCockpitPage.tsx` and `api.ts`; no UI business calculations.
- [x] T018 [US1] Run the independent populated and unavailable shipping stories and record real outcomes/limitations in `specs/378-enterprise-operations-cockpit/quickstart.md`; preserve shipment/outbound-delivery/readiness/revision/DST regressions.

## Phase 4 — User story 2: deviations and evidenced response (P1)

**Goal**: Explain the cause, responsibility and actual response without a human task or invented progress narrative.
**Independent proof**: One blocked case with no reaction and one with a recorded proposal/receipt awaiting external outcome.

- [x] T019 [US2] [FR-011] [FR-012] [FR-013] [DR-001] Add failing causal-reference/recorded-reaction/absence/uncertain-outcome tests in `packages/reality-core/tests/test_operations_cockpit.py`; status executed must not prove email delivery or carrier handover.
- [x] T020 [US2] [FR-011] [FR-012] [FR-013] [DR-001] Enrich canonical case/action reads in `packages/reality-core/src/reality/services/operational_cases.py` and cockpit assembly in `operations_cockpit.py` from exact existing reviews/receipts/recorded check evidence; no generated reasons or new correspondence workflow.
- [x] T021 [US2] [FR-011] [FR-012] [FR-013] [DR-001] Present actual cause/impact/responsibility/response and exact source/action links in `apps/web/src/unified/OperationsCockpitPage.tsx`; identify unknown/unsupported measures and do not relabel existing metrics.

## Phase 5 — User story 3: supported takeover and continuation (P1)

**Goal**: Exact reviewed case takeover, discoverable human ownership and contextual specialist continuation/handback.
**Independent proof**: Supported fulfillment case with a related independent return and an already claimed action, including lost-response replay and stale handback.

- [x] T022 [US3] [FR-013] [FR-014] [FR-015] [FR-017] [DR-001] [DR-004] [DR-005] Add failing filtered-register/full-count/control-attribution tests in `packages/reality-core/tests/test_operational_cases.py` and `test_operational_case_adapters.py`; extend existing `test_case_control_retries.py` only where new UI integration needs regression proof.
- [x] T023 [US3] [FR-014] [FR-015] [FR-016] [FR-017] [DR-004] Add failing case-register/control/reason/return-context/browser assertions in `apps/web/scripts/operations-cockpit-browser.mjs`, retaining existing `operational-cases-browser.mjs` behavior.
- [x] T024 [US3] [FR-013] [FR-014] [FR-015] [FR-017] [DR-001] [DR-004] [DR-005] Implement the new paged canonical register and derived exact control attribution in `packages/reality-core/src/reality/services/operational_cases.py`, `tools/operational_cases.py`, `web/operational_cases.py`, `mcp/server.py` and catalogs; preserve old list/control contracts and never auto-adopt history.
- [x] T025 [US3] [FR-013] [FR-014] [FR-015] [FR-016] [FR-017] [DR-004] Extract existing reviewed controls into `apps/web/src/unified/useOperationalCaseControls.ts`, connect `OperationalCaseDetail.tsx`/`OperationalCaseRegister.tsx`/cockpit, and serialize safe origin through existing workspace/Inspector routes in `routing.ts`; use actual business context for chat.
- [x] T026 [US3] Execute the supported takeover/handback/navigation story and record its real scope/execution limitations in `specs/378-enterprise-operations-cockpit/quickstart.md`; rerun existing control races/member/replay/related-case proof.

## Phase 6 — User story 4: resilient additive product entry (P2)

**Goal**: Optional surface, context preservation and readable missing/stale states without loss of existing product or authority boundaries.
**Independent proof**: Entry enabled/disabled, auth loss, company switch, failed refresh, on-demand chat and existing genuine approvals.

- [x] T027 [US4] [FR-001] [FR-010] [FR-017] [FR-018] [DR-003] [DR-005] Add failing Web/tool parity, feature-off, active-member/revocation, foreign-reference and read-only failure proofs in `packages/reality-core/tests/test_operations_cockpit_adapters.py` and `test_operations_cockpit.py`.
- [x] T028 [US4] [FR-001] [FR-016] [FR-018] [FR-019] [FR-020] Extend `apps/web/scripts/operations-cockpit-browser.mjs` with safe return URLs/company reset, chat on demand, four languages/themes/keyboard, 1440/390 screenshots, three-action journey and C01–C25 preservation/deferred-status audit.
- [x] T029 [US4] [FR-001] [FR-016] [FR-018] [FR-019] [FR-020] Complete readable unavailable/stale/refusal/access-loss states and responsive/localized UI in `apps/web/src/unified/OperationsCockpitPage.tsx`, related components, `Shell.tsx`, `routing.ts`, `localization.ts` and existing styles; preserve accessible approval routes and explicit deferred inventory status.
- [x] T030 [US4] [FR-001] [FR-010] [FR-017] [FR-018] [DR-003] [DR-005] Finish shared service/adapter availability, current-basis re-evaluation, source-coverage/error and access guards in `packages/reality-core/src/reality/services/operations_cockpit.py` and `web/operations_cockpit.py`; keep owner Engine Room and case authority unchanged.

## Phase 7 — User story 5: all-day live observation (P1)

**Goal**: Continuous truthful business observation with stable investigation and bounded all-day operation.
**Independent proof**: Real recorded fixture changes, quiet/failure/recovery intervals and an eight-hour controlled-time session; the real-time soak remains a separate pre-pilot gate.

- [x] T031 [US5] [FR-021] [FR-023] [FR-024] [DR-001] [DR-003] [DR-005] Add failing rolling-activity classification/deduplication/recording-time/partial-coverage/complete-total/no-write tests in `packages/reality-core/tests/test_operations_cockpit.py` and adapter parity/member/filter tests in `test_operations_cockpit_adapters.py`; preserve `test_activity_volume.py` semantics. Include named manual/OAuth access, duplicate/shared identity, complete paging, last-use versus runtime state, exact action attribution, owner-only disclosure and secret-redaction proof.
- [x] T032 [US5] [FR-021] [FR-022] [FR-023] [FR-024] [SC-007] Add failing lifecycle and controlled eight-hour assertions in `apps/web/scripts/operations-cockpit-live.test.mjs` and real fixture-change browser assertions in `operations-cockpit-browser.mjs`: five-second cadence, ten-second healthy display, no overlapping reads, timeout/backoff, hidden/resume, stale gaps, bounded buffers, stable inspection/chat/reviews, following versus case control, company switch/revocation and Today versus pinned-date rollover; verify compact named access panel, expansion, no fabricated working/connected labels and non-owner restricted state.
- [x] T033 [US5] [FR-021] [FR-023] [FR-024] [DR-001] [DR-003] [DR-005] Implement canonical rolling read through `packages/reality-core/src/reality/services/activity_volume.py` with shared existing classification, assemble live data in `services/operations_cockpit.py`, and expose `operations_cockpit_activity` through `tools/shipping_operations.py`, `web/operations_cockpit.py`, `mcp/server.py`, `cli/app.py` and catalogs; add `operations_cockpit_agents` through those shared layers, reusing existing token/client effective-state and interaction-attribution rules with owner-only redacted inventory and full totals/keyset paging. Retain Home's current contract and no-write/scheduling boundary.
- [x] T034 [US5] [FR-021] [FR-022] [FR-023] [FR-024] Implement bounded refresh/context lifecycle in `apps/web/src/unified/useCockpitLiveRead.ts`, compact returned-series/recent-event presentation in `OperationsActivityPanel.tsx`, compact named access overview in `AgentAccessPanel.tsx` and integration in `OperationsCockpitPage.tsx`, `api.ts`, `routing.ts` and `localization.ts`; follow `contracts/live-observation.md`, preserve exact control reviews and label presentation-only following distinctly from takeover.

## Final phase — Workload, docs and completion proof

- [x] T035 [DR-005] [SC-004] Add the reproducible failing 10,000-active/100,000-historical/500,000-observation, ten-reader workload, five-second sustained live refresh with concurrent committed fixture changes and independent parity/query-budget assertions in `packages/reality-core/tests/test_operations_cockpit_performance.py`; record hardware/distribution and cold/warm method.
- [ ] T036 [DR-005] [SC-004] Meet the measured workload through approved cohort-bounded grouping/batching and indexes in `packages/reality-core/src/reality/services/shipping_performance.py`/`operations_cockpit.py`; do not reduce totals or add stale authority. Any additional schema change requires its own reviewed proof.
- [ ] T037 [FR-020] [DR-001] [DR-003] Register complete executable vocabulary/model/refusals and German ERP labels in `packages/reality-core/config/`; update implemented contract in `docs/features/operations-cockpit.md`, `docs/WEB_SPEC.md` and existing case docs, then run `make docs-generate` and retain generated references.
- [ ] T038 Run `make spec-check`, `make lint` and the complete required PostgreSQL backend suite; record actual results in `specs/378-enterprise-operations-cockpit/quickstart.md` and keep completion unchecked while failures remain.
- [ ] T039 Run `make web-build`, applicable browser regressions and the new proof; add the passing script/duration to `apps/web/scripts/browser-suite.json` and record actual screenshot/reference evidence in `quickstart.md`.
- [ ] T040 Review approved migration head/upgrade/disposable downgrade and run `make docs-catalog-check`; record no startup migration, no live-company backfill and non-destructive presentation rollback in `quickstart.md`.
- [ ] T041 [FR-020] [FR-021] [FR-022] [FR-023] [SC-007] [SC-001] [SC-002] [SC-003] [SC-004] [SC-005] [SC-006] Record real populated two-site, three-action, responsive/reference, workload, deterministic live-session and separate eight-hour real-time-soak acceptance evidence for every protected first-increment item in `specs/378-enterprise-operations-cockpit/quickstart.md` and `migration-map.md`; placeholders alone are not completion.
- [ ] T042 Review final implementation diff against `specs/378-enterprise-operations-cockpit/spec.md`, Constitution and every FR/DR/SC; mark only verified task/status items after all required checks pass. Production enablement, merge and default-route replacement remain separately governed.

## Dependencies and implementation strategy

T001–T002 gate every executable task. Input proof T003–T004 precedes validation/model/service/adapter T005–T008. T009 precedes entry T010. Shipping tests T011–T013 precede T014–T017, then T018 independently demonstrates US1. Response T019 precedes T020–T021. Case proof T022–T023 precedes T024–T025/T026. Resilience proof T027–T028 precedes T029–T030. Live proof T031–T032 precedes shared read T033 and presentation T034. T035 precedes workload changes T036. T037–T042 finalize only after all stories pass.

US1, US2 and US3 can be demonstrated independently after the common foundations; US4 cross-checks their product integration; US5 verifies continuous observation across them. Deliver US1 first, preserving a populated three-series panel rather than an unavailable-only shell. Do not enable a real-company pilot or replace Home as part of these tasks.

Parallel examples: after foundations, T012 service/story tests and T013 browser fixtures use independent files; no implementation runs before failing proof. T022 backend register proof can be prepared alongside T023 browser fixture work, but shared case/UI implementation stays ordered. Final backend and web checks may run independently once code stops changing.

## Requirement coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
| --- | --- | --- | --- |
| FR-001 | T009, T027, T028 | T010, T029, T030 | Functional proof passes; rollout gates open |
| FR-002 | T011, T013 | T014, T017 | Functional proof passes; rollout gates open |
| FR-003 | T003, T011 | T005, T007, T014, T017 | Functional proof passes; rollout gates open |
| FR-004 | T011 | T014, T017 | Functional proof passes; rollout gates open |
| FR-005 | T011 | T014, T017 | Functional proof passes; rollout gates open |
| FR-006 | T003, T011 | T005, T007, T014, T017 | Functional proof passes; rollout gates open |
| FR-007 | T003, T011 | T005, T007, T014, T017 | Functional proof passes; rollout gates open |
| FR-008 | T003, T011, T013 | T005, T007, T014, T017 | Functional proof passes; rollout gates open |
| FR-009 | T003, T011, T013 | T005, T007, T014, T017 | Functional proof passes; rollout gates open |
| FR-010 | T012, T013, T027 | T015, T017, T030 | Functional proof passes; rollout gates open |
| FR-011 | T019 | T020, T021 | Functional proof passes; rollout gates open |
| FR-012 | T011, T019 | T014, T017, T020, T021 | Functional proof passes; rollout gates open |
| FR-013 | T019, T022 | T020, T021, T024, T025 | Functional proof passes; rollout gates open |
| FR-014 | T022, T023 | T024, T025 | Functional proof passes; rollout gates open |
| FR-015 | T022, T023 | T024, T025 | Functional proof passes; rollout gates open |
| FR-016 | T009, T023, T028 | T010, T025, T029 | Functional proof passes; rollout gates open |
| FR-017 | T009, T022, T023, T027 | T010, T024, T025, T030 | Functional proof passes; rollout gates open |
| FR-018 | T012, T013, T027, T028 | T015, T017, T029, T030 | Functional proof passes; rollout gates open |
| FR-019 | T028 | T029 | Functional proof passes; rollout gates open |
| FR-020 | T028, T041 | T029, T037, T041 | Functional proof passes; rollout gates open |
| FR-021 | T031, T032, T035 | T033, T034 | Functional proof passes; rollout gates open |
| FR-022 | T032 | T034 | Functional proof passes; rollout gates open |
| FR-023 | T031, T032 | T033, T034 | Functional proof passes; rollout gates open |
| FR-024 | T031, T032 | T033, T034 | Functional proof passes; rollout gates open |
| DR-001 | T003, T011, T012, T019, T022, T031 | T007, T015, T020, T021, T024, T033, T037 | Functional proof passes; rollout gates open |
| DR-002 | T003, T011 | T005, T007, T014 | Functional proof passes; rollout gates open |
| DR-003 | T003, T004, T012, T027, T031 | T006, T007, T008, T015, T016, T030, T033, T037 | Functional proof passes; rollout gates open |
| DR-004 | T022, T023 | T024, T025 | Functional proof passes; rollout gates open |
| DR-005 | T012, T022, T027, T031, T035 | T015, T024, T030, T033, T036 | Functional proof passes; rollout gates open |

SC-001/002/003/005/006 map to the above story/browser/coverage tasks and T041–T042; SC-004 has explicit workload proof T035–T036. SC-007 maps to T032, sustained workload T035–T036 and recorded soak evidence T041. All status rows are pending actual implementation/verification, not missing specification coverage.

### Verified first-increment task status

T003–T035 are verified by the actual source/migration/domain/service/adapter/
component/browser/live-session and full-cohort evidence in `quickstart.md`;
owner review checklists are unchanged. The measured backend/JSON portion of
T036 now passes, but T036 and final aggregate tasks remain open until their
enterprise-display/rollout boundaries are reviewed. The separate eight-hour
real-time soak in T041 is unrun. No open criterion is represented as complete.

## Owner-requested usability follow-up

- [x] T043 Add and run a failing browser proof for bounded collection/deviation previews, exact expandable details, adjacent focused shipping inspection, understandable case navigation and mobile layout (FR-025–027).
- [x] T044 Implement presentation and four-locale labels in ShippingDayPanel, OperationsDeviationsPanel, OperationalCaseRegister, ShippingSupportingOrders and OperationsCockpitPage, preserving business reads and control guards (FR-025–027).
- [x] T045 Run frontend contracts, formatting, i18n, build and cockpit desktop/mobile browser proof; review source/evidence and live-refresh preservation (FR-025–027).

## Owner-requested operating flows follow-up

- [x] T046 Add failing independent PostgreSQL tests in `tests/test_operating_flows.py` for complete scope, messages/replies/acks, partial/corrected goods/returns, first-recorded orders, exception severity, unknown dates and read-only tenant isolation (FR-028–033).
- [x] T047 Implement `services/operating_flows.py` using canonical shared readers/SQL and assemble its additive DTO in `services/operations_cockpit.py`; existing CLI/MCP/HTTP all share this reader (FR-028–033).
- [x] T048 Add compact `OperatingFlowsPanel.tsx`, model/locale/shared-style changes and browser fixtures covering truthful units/curves/evidence, stale/unknown, all five areas and preserved shipping/deviations at desktop/mobile widths (FR-028–033).
- [x] T049 Run affected backend/adapter/snapshot and frontend/browser gates, lint/spec/annotation/generated-doc checks; rebuild/restart API/MCP/web and record actual live observations/local timing without claiming enterprise/soak approval (FR-028–033).

## Owner-requested visual consistency follow-up

- [x] T050 Add failing layout/selector browser proofs to `apps/web/scripts/operations-cockpit-browser.mjs` for aligned desktop metric/chart starts, matching section rhythm/headings, grouped time/case selection, narrow panels, expanded evidence and four-locale/theme/mobile reachability (FR-034–036).
- [x] T051 Refine `OperatingFlowsPanel.tsx`, `operationsCockpit.css`, `OperationsActivityPanel.tsx`, `OperationalCaseRegister.tsx`, `AgentAccessPanel.tsx`, `OperationsDeviationsPanel.tsx` and `ShippingSupportingOrders.tsx` with shared layout slots, wrapping selection groups and footer styles; preserve all existing data/control semantics (FR-034–036).
- [x] T052 Verify frontend contracts/format/i18n/build, full cockpit browser regression, spec/lint/annotation and generated-reference freshness, then web-only local activation and actual responsive/live proof; record review evidence without closing enterprise/soak/rollout gates (FR-034–036).


## Owner-requested central status overview

- [x] T053 Add a failing browser proof in `apps/web/scripts/operations-cockpit-browser.mjs` for summary placement, all five canonical states, metric parity, keyboard detail navigation, stale/missing neutrality and responsive/localized reachability (FR-037–038).
- [x] T054 Implement shared OperatingStatusPanel/anchor targets in `OperatingFlowsPanel.tsx`, place it above shipping in `OperationsCockpitPage.tsx`, and add shared scoped styling/four-locale labels without business/read/control changes (FR-037–038).
- [x] T055 Verify full frontend/browser, formatting/i18n/build, spec/lint/docs freshness and real local web-only activation/live responsive proof; record final review without closing enterprise/soak/rollout gates (FR-037–038).


## Permanent Control Tower navigation

- [x] T056 Add failing `operations-cockpit-shell-browser.mjs` proofs for persistent root/Home/company-change navigation, unavailable and failed capability, no operational reads before enablement, same-company isolation and consistent brand labels; update the routing title assertion (FR-039–040).
- [x] T057 Refine `Shell.tsx` capability resolution/display gating, persistent destination and unavailable feedback, plus `OperationsCockpitPage.tsx`, `pageIntroduction.ts` and four-locale display/return labels with `apps/web/scripts/i18n-invariants.mjs` product-name registration; preserve routes, business permissions and company preferences (FR-039–040).
- [x] T058 Run frontend/format/i18n/build, shell/cockpit browser regressions, spec/lint/docs freshness and actual fresh-root/company-switch local web proof, recording reviewed results without closing prior enterprise/soak/rollout gates (FR-039–040).


## Workspace surface consistency

- [x] T059 Add and observe failing shared-workspace canvas and preserved card/selection/detail surface assertions in `apps/web/scripts/operations-cockpit-browser.mjs` (FR-041).
- [x] T060 Change only the canvas surface role in `apps/web/src/unified/operationsCockpit.css`, preserving existing layout and behavior (FR-041).
- [x] T061 Verify frontend contracts/format/build, full cockpit browser regression, spec/lint and actual web-only activation; record review and screenshots without closing earlier rollout gates (FR-041).


## Case takeover discoverability

- [x] T062 Add failing placement/compact disclosure/keyboard count-entry and retained review-state browser proofs in `apps/web/scripts/operations-cockpit-browser.mjs` (FR-042–044).
- [x] T063 Move/refine the single register in `OperationsCockpitPage.tsx`/`OperationalCaseRegister.tsx`, shared scoped CSS and four-locale copy, without changing case services or confirmation semantics (FR-042–044).
- [x] T064 Verify full frontend/browser/format/i18n/build and spec/lint, review exact scope, activate web only and capture real live UI evidence; retain prior rollout gates (FR-042–044).


## Classic traffic-light palette

- [x] T065 Extend existing cockpit browser proof with failing three-color assertions for all canonical summary/detail signals, both themes/locales and stale unknown coverage (FR-045).
- [x] T066 Apply scoped three-color status styling and four-locale legend while preserving canonical labels and read/control behavior (FR-045).
- [x] T067 Verify cockpit browser regression, frontend contracts/format/i18n/build and spec policy; activate web only and capture actual company evidence. Record review without closing earlier enterprise/soak gates (FR-045).


## Current-main PR integration

- [ ] T068 [FR-017] [FR-018] [DR-004] Restore spec 377 default coordination in the register; add regression proof for visibility without legacy adoption, read-only canonical readiness and unchanged scalar/batched case evidence. Show existing rollout/migration messages rather than an activation prompt.
- [ ] T069 [DR-003] Rebase the approved shipping-input migration after current-main migration 0145, regenerate combined executable catalogs/fixtures and verify exact catalog coverage plus disposable upgrade/downgrade.
- [ ] T070 [SC-006] Run integrated backend/frontend/browser/documentation gates, review the final diff and record actual results and open pre-pilot gates before preparing the PR. No merge or production enablement is included.

- [ ] T071 [SC-004] Restore enterprise snapshot read performance with bounded deduplicated action metadata and exact original proposed-review inputs; first reproduce large shared-action transfer, preserve scalar parity, the 55-query budget and source/control/authority boundaries, then run the unchanged full enterprise and final CI gates.

- [ ] T072 [FR-033/SC-004] Separate independent company flow observations into the existing activity snapshot/lifecycle; verify exact authority, stale/filter/isolation semantics and complete four-read enterprise cadence.

- [ ] T073 [FR-023/SC-004] Bound dense daily shipping series with disclosed exact cumulative five-minute aggregation; verify full counts, exact source/supporting trace, endpoints and enterprise/browser gates.

- [ ] T074 [DR-005/SC-004] Bound current commitment exception tracing to its exact open-promise document/line/source cohort; first reproduce historical payload materialization after a real unreserved order, preserve full scalar/snapshot source-trace parity, then run the unchanged live cadence and final CI gates.

- [ ] T075 [FR-033/SC-004] Remove the UI-unused duplicate register calculation from shipping snapshots; first prove independent complete register authority and absent duplicate work, preserve all four live readers and case-linked deviation evidence, then run the unchanged enterprise and full CI gates.

- [ ] T076 [FR-046/SC-004] First reproduce full-cohort readable-readiness allocation, then use a versioned complete canonical-field fingerprint with bounded unchanged readable preview/order details. Prove full/scalar/supporting parity and complete canonical-field coverage; rerun unchanged enterprise latency and complete CI.

- [ ] T077 [DR-005/SC-004] First reproduce current promise/physical ORM allocation, then project exact metadata and reuse canonical grouped net fulfillment in clean stock reads. Preserve independent unit/revision/correction/kit/tenant/source parity; rerun the unchanged full four-reader enterprise and complete CI gates.

- [ ] T078 [FR-018/DR-005/SC-004] First reproduce redundant viewer queries; add a fresh joined canonical member read preserving all original checks/callers. Prove stale-cache and committed user/company/member/role revocations plus independent coalesced waiter authority; run unchanged enterprise/full CI.

- [ ] T079 Preserve exact immutable scalar metadata and latest-stated revision/correction parity while removing repeated row dispatch and correlated revision work; rerun unchanged complete enterprise CI before readiness.

- [ ] T080 Preserve exact current-source metadata and standard v2 fingerprint bytes while reducing shipping-only transfer/allocation; verify complete source/refusal/supporting parity and unchanged full CI before readiness.

- [ ] T081 Avoid unused preloaded cohort construction and fresh scalar ORM allocation while preserving typed metadata, the same transaction, dirty-reader/autoflush behavior, exact canonical parity and all unchanged enterprise/CI gates.

## Compact instrument inspection

- [x] T103 [FR-068–070] Add failing service membership/limit/parity tests in packages/reality-core/tests/test_operating_flows.py and product modal/focus/empty/stale/viewport proofs in apps/web/scripts/operations-cockpit-browser.mjs; update preview fixtures.
- [x] T104 [FR-069] Extend shared operating_flows.py partitions with bounded exact-member previews, batched tenant labels and evaluator shortfall, preserving existing counts and read-only authority.
- [x] T105 [FR-068/070] Implement compact count/group inspection dialog in OperatingFlowsPanel.tsx, cockpitModel.ts, operationsCockpit.css and four-language localization, preserving all reader/analysis/control state.
- [ ] T106 [FR-068–070] Run backend/frontend/browser/audit/build/spec/review checks, activate scoped API/web locally and inspect actual stock/order/message membership. Record evidence and update PR without closing remaining rollout gates.

## Missing daily plan recovery

- [x] T107 [FR-071/072] Add failing shipping physical-activity, no-plan overview and frontend no-plan browser proofs before implementation.
- [x] T108 [FR-071/072] Implement independent tenant/day/site physical activity, bounded source trace and unknown deviations in existing services; render honest actual units without extra readers.
- [x] T109 [FR-071/072] Verify affected backend/frontend/browser/spec/build/localization checks, inspect real current-day activity and record review; preserve open enterprise/CI gates.


## Single selected-topic heading

- [x] T110 [FR-073] Add failing product browser proof of one selected-topic h2 per primary card and shared typography across six analysis/three workspace views.
- [x] T111 [FR-073] Centralize visible topic headings in OperatingFlowsPanel/OperationsWorkspacePanel with explicit embedded child presentation and stable accessible region names; retain context, controls and state.
- [x] T112 [FR-073] Run required frontend/browser/build/audit/policy checks, inspect and activate the local web, review the diff and update existing PR while retaining enterprise/CI gates.
