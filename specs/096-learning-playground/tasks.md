# Tasks: Learning Playground

Input: spec.md, plan.md, research.md, data-model.md, contracts/playground.md, quickstart.md.
Status: implementation approved and in progress. Reviewer-gate override is recorded in
quickstart.md; Constitution PASS and read-only analysis precede implementation.
Paths below are repository-relative. New paths are planned files, not claims of existing code.

## Phase 1: Review gates

- [X] T001 Record owner/domain/security approval of specs/096-learning-playground/spec.md, data-model.md and checklists/security-ux.md; resolve any requested changes before implementation.
- [X] T002 Revalidate current main, all mutation/egress entrypoints and exact allowed tool names against specs/096-learning-playground/plan.md and contracts/playground.md; run speckit-analyze and record review evidence in quickstart.md.

## Phase 2: Foundational safety and evidence

Progress note: T005/T006 now cover business-only egress, all catalogued core mutations,
generic proposals/decisions, company lifecycle, rule/upload paths and the shared owner
resolver. Generic tenant HTTP reads now require the run owner even in local mode;
company selectors exclude sandboxes and pending accounts remain barred from business reads.
Focused evidence is in quickstart.md. Both tasks remain open pending the complete
entrypoint drift audit and scoped execution policy. Authenticated start/list/detail HTTP
endpoints and the internal browser entry are implemented; account-aware tool/CLI adapters
and confirmed lesson controls remain pending.

- [X] T003 [DR-003] [DR-004] Add failing PostgreSQL purpose/default/run/step FK, uniqueness and tenant registry tests in packages/reality-core/tests/test_playground_runs.py and test_migrations.py.
- [X] T004 [DR-003] [DR-004] Implement metadata and validation in packages/reality-core/src/reality/db/core.py and domain/playground.py; create the next unused migration under packages/reality-core/migrations/versions/ per data-model.md.
- [ ] T005 [FR-003] [DR-003] Add fail-closed policy coverage and direct HTTP/tool/CLI/MCP/service/egress negative tests in packages/reality-core/tests/test_playground_security.py, including auth-disabled anonymous, secrets, provider URLs, tokens, invitations and archived writes.
- [ ] T006 [FR-003] [DR-003] Implement central operation registry/policy in packages/reality-core/src/reality/services/tenant_policy.py and wire shared mutators in services/core.py, services/memberships.py, security/secrets.py, agent/settings.py, mcp/auth.py and tools/application.py; cover actual delivery-worker and connector egress boundaries identified by T002.
- [X] T007 [FR-005] [DR-001] [DR-002] Add causal action-ID, reservation consumption/remainder and commitment fulfilment event tests in packages/reality-core/tests/test_playground_steps.py; retain regression coverage in the existing test_inventory_and_fulfillment.py and test_inventory_tracking_reservations.py without altering expected domain balances.
- [X] T008 [FR-005] [DR-001] [DR-002] Extend allowed handler action context and co-committed automatic-effect events in packages/reality-core/src/reality/tools/application.py and services/core.py; retain existing tool outputs and lifecycle semantics.

## Phase 3: US1 — Private entry and prepared references

Goal: verified user starts one ready private run without company/model setup.
Independent proof: US1 acceptance scenarios, pending production admission remains restricted.

- [X] T009 [US1] [FR-002] [FR-011] [DR-001] Add failing bootstrap, versioned seed, repeated-key/concurrent-start, initialization-failure and run-quota tests in packages/reality-core/tests/test_playground_runs.py.
- [X] T010 [US1] [FR-002] [FR-011] [DR-001] Implement owner-locked run lifecycle and retryable seed in packages/reality-core/src/reality/services/playground.py and playground/catalog.py; reuse shared master-data services and preserve zero initial stock.
- [X] T011 [US1] [FR-001] [FR-003] Add pending/active/unverified/disabled account, same-owner production and foreign-run admission tests in packages/reality-core/tests/test_playground_api.py and test_playground_security.py.
- [ ] T012 [US1] [FR-001] [FR-002] [FR-003] Implement account-aware run endpoints/admission in packages/reality-core/src/reality/web/playground.py, web/api.py, web/app.py and web/auth.py; register shared services/tools and safe adapter access in tools/application.py, mcp/catalog.py and cli/app.py.
- [X] T013 [US1] [FR-002] [FR-013] Add entry/loading/error/sandbox-banner contracts to apps/web/scripts/playground-contract.test.mjs before implementing apps/web/src/playground/PlaygroundPage.tsx, App.tsx and api.ts entry; include test in apps/web/package.json gates.

## Phase 4: US2 — Five-step lesson, recorder and live picture

Goal: demonstrate cause and effect using actual application state with no provider dependency.
Independent proof: golden sequence exact quantities/IDs, no Fact mirrors, valid Inspector links.

Progress note: T014/T015 now include the internal pinned-connection serialization primitive
and PostgreSQL tests for commit/rollback contention, failed/lost lock replies, disconnects,
post-acquisition admission, independent runs and continued read access. This grants no action
permission and is not exposed by an adapter. The internal opening-stock prepare service now
uses it to persist one normal proposal and step atomically, with exact-intent authorization,
owned-reference validation, request replay and unresolved/applied-capacity guards. Opening stock
now also has internal confirm/reject/read services, preview-state checks, execution-time capacity,
exact-action authorization, common-executor Movement verification and historical observations.
Interrupted execution remains unsettled and is not retried. Other action types, explicit
settlement of interrupted proposals, complete Facts/Exceptions/current-picture reads and CLI/MCP/chat
adapters remain pending; authenticated private HTTP step routes are now covered. Both tasks remain unchecked.

- [ ] T014 [US2] [FR-004] [FR-005] [FR-009] Add proposal/rejection/stale-preview/concurrent-confirmation, action-status and crash-window receipt tests in packages/reality-core/tests/test_playground_steps.py; initial failures must be observed.
- [ ] T015 [US2] [FR-004] [FR-005] [FR-009] Implement one-action step preparation/confirmation, pinned-connection serialization, correlated reconciliation and observational receipts in packages/reality-core/src/reality/services/playground.py; extend existing tools/application.py executor/status narrowly, not a parallel engine.
- [ ] T016 [US2] [FR-006] [DR-002] [DR-004] Add shared read parity, exact quantities, scoped Facts/Exceptions, unknown-vs-zero and projection-failure-after-success tests in packages/reality-core/tests/test_playground_reads.py.
- [ ] T017 [US2] [FR-006] [DR-002] [DR-004] Implement bounded run/step read models and freshness in packages/reality-core/src/reality/services/playground.py and web/read_models.py using services/projections.py and services/exceptions.py; preserve historical versus current distinction.
- [ ] T018 [US2] [FR-004] [FR-005] [FR-006] [DR-001] [DR-002] [DR-004] Add golden five-step service/adapter story in packages/reality-core/tests/scenarios/test_learning_playground.py with fixed time and exact actual exception identities; assert supplied order amounts remain unchanged.
- [ ] T019 [US2] [FR-004] [DR-001] [DR-004] Implement versioned order-stock-v1 lesson in packages/reality-core/src/reality/playground/catalog.py with declared example values and real application-tool steps; leave demo/normal_month.py unchanged.
- [ ] T020 [US2] [FR-005] [FR-006] [FR-013] Add receipt/current-picture/loading/unknown/Inspector contracts in apps/web/scripts/playground-contract.test.mjs before UI implementation.
- [ ] T021 [US2] [FR-005] [FR-006] [FR-013] Implement apps/web/src/playground/StepReceipt.tsx and ScenarioControls.tsx, integrate PlaygroundPage.tsx with existing Inspector/Views and api.ts; render automatic effects and relevant unchanged values without client business calculations.

## Phase 5: US3 — Chat and custom master data

Goal: resolve or create references and prepare bounded dependent actions in ordinary language.
Independent proof: ambiguity choices, article then stock, separate confirmation, provider outage.

- [ ] T022 [US3] [FR-007] [FR-008] [DR-001] [DR-003] Add reference ambiguity, duplicates, cross-tenant IDs, dependent newly created IDs, defaults and article-versus-stock tests in packages/reality-core/tests/test_playground_chat.py using deterministic provider responses.
- [ ] T023 [US3] [FR-007] [FR-008] [DR-001] [DR-003] Implement run-bound discover/propose handling in packages/reality-core/src/reality/services/playground.py, tools/application.py and mcp/catalog.py; use business_discover/suggestions and existing creation services, pause on ambiguity or unsupported operations.
- [ ] T024 [US3] [FR-008] [FR-011] Add managed-only provider selection, production-context leakage, tool escalation, timeouts, concurrent turn limits and quota-fallback tests in packages/reality-core/tests/test_playground_chat.py and test_playground_security.py.
- [ ] T025 [US3] [FR-008] [FR-011] Implement sandbox-only provider context and allowlist in packages/reality-core/src/reality/agent/mcp_chat.py plus services/playground.py; reserve account-wide turn quota before outbound work and preserve deterministic controls on failure.
- [ ] T026 [US3] [FR-007] [FR-008] [FR-013] Add chat/combobox/defaults/confirmation UI contracts in apps/web/scripts/playground-contract.test.mjs, then integrate existing shared autocomplete/chat components in apps/web/src/playground/PlaygroundPage.tsx and api.ts.

## Phase 6: US4 — Persistence, recovery and fresh restart

Goal: resume safely and create a fresh run without undoing history.
Independent proof: lost response/unknown execution, restart failure, archive denied across routes.

- [ ] T027 [US4] [FR-009] [FR-010] [FR-011] Add resume, interrupted multi-step, restart concurrency/failure, retained-run/step quota and archived generic-route tests in packages/reality-core/tests/test_playground_runs.py, test_playground_steps.py and test_playground_api.py.
- [ ] T028 [US4] [FR-009] [FR-010] [FR-011] Implement resume/archive/restart and atomic capacity checks in packages/reality-core/src/reality/services/playground.py, tenant_policy.py and web/playground.py; preserve old run until replacement ready and never auto-delete or blindly retry.
- [ ] T029 [US4] [FR-009] [FR-010] [FR-013] Add saved-run/archive/recovery UI contracts in apps/web/scripts/playground-contract.test.mjs, then implement run selector/restart preview/recovery states in apps/web/src/playground/PlaygroundPage.tsx and api.ts.

## Phase 7: US5 — Public discovery and finished learning surface

Goal: discover publicly, enter after verification and inspect within sandbox on desktop/mobile.
Independent proof: Docs/Site account return path and all required languages/accessibility states.

- [ ] T030 [US5] [FR-012] [FR-013] Add configured-origin/local-return-route, no anonymous writes and bilingual-preview contracts in provider-site/scripts/site-contract.test.mjs, apps/docs/scripts/docs-contract.test.mjs and apps/web/scripts/playground-contract.test.mjs.
- [ ] T031 [US5] [FR-012] Implement restrained Playground discovery link in provider-site/src/LandingPage.tsx/site-routing.ts, labelled preview in apps/docs/content/getting-started/playground.md and de equivalent, navigation in apps/docs/.vitepress/config.mts and safe account return handling in apps/web/src/App.tsx.
- [ ] T032 [US5] [FR-013] Add keyboard, responsive, state-label and full locale coverage contracts in apps/web/scripts/playground-contract.test.mjs and localization-contract.test.mjs.
- [ ] T033 [US5] [FR-013] Complete shared responsive styles and en/de/nl/es strings in apps/web/src/playground/ and localization.tsx, plus provider-site/src/localization.tsx; preserve the original public presentation and Docs learning paths.

## Final Phase: Release evidence, not unchecked promises

- [ ] T034 [SC-003] Add a repeatable ten-run timing harness at packages/reality-core/tests/performance/test_playground_latency.py; record profile, hardware, p95 and sample counts in specs/096-learning-playground/quickstart.md.
- [ ] T035 [SC-002] [SC-004] Run make spec-check, make lint, complete PostgreSQL backend suite, web/site/docs builds and all contract/i18n tests; record actual results in specs/096-learning-playground/quickstart.md.
- [ ] T036 [DR-003] [SC-004] Review PostgreSQL upgrade/defaults/constraints and safe disposable downgrade, feature-flag rollout and non-downgradable isolation guards in packages/reality-core/tests/test_migrations.py and specs/096-learning-playground/quickstart.md.
- [ ] T037 [SC-001] [SC-004] Perform real 390/1280px keyboard/browser acceptance and five-person learning check from specs/096-learning-playground/quickstart.md; leave unavailable human/visual checks explicitly pending.
- [ ] T038 [FR-012] [FR-013] [DR-001] [DR-002] [DR-003] [DR-004] Update docs/features/learning-playground.md, docs/WEB_SPEC.md, docs/WEB_UX_MATRIX.md, docs/DATA_MODEL.md and docs/TEST_STRATEGY.md; update docs/V0_CHECKLIST.md only after required evidence is green.
- [ ] T039 [SC-004] Review final diff, security-ux.md reviewer decisions and all requirement coverage in specs/096-learning-playground/; verify deployment flag/provider/quotas before requesting public release approval.

## Dependencies and implementation strategy

- [ ] T040 Implement and verify the approved full-screen cockpit revision in
  apps/web/src/playground/PlaygroundWorkspace.tsx and PlaygroundPage.tsx: same
  handlers, current shared reads, inline review, internal navigation, legacy fallback.
  Add regression coverage before declaring browser acceptance complete.

T001–T008 block all user-facing execution. US1 → US2 → US3/US4 → US5 → final release.
US2 is an internal testable milestone, not completion of the promised chat Playground.
US3 and US4 share service/UI files: sequence implementation unless ownership is explicitly split.
Within stories, test authoring in separate backend/frontend files may be parallel after interface
contracts settle (US1 T009/T011; US2 T016/T020; US3 T022/T024; US4 backend/UI test portions;
US5 T030/T032). Shared implementation files are never concurrent edits by assumption.
No backend schema or implementation work starts merely because the plan exists.

## Entry simplification

- [x] T064 [FR-003] [FR-013] [DR-003] Integrate PR #135 with current main without removing new domain operations; complete cockpit translations, retain fail-closed sandbox policy, verify full backend/migrations/catalogs and all frontend/site/docs gates, then update remote CI and remove draft status. Human approval remains external.

- [X] T063 [FR-024] Replace the duplicate entry catalog in PlaygroundPage.tsx with new-sandbox setup and recent history buttons; preserve confirmation/retries. Verified 97 frontend contracts, production build, isolated browser creation/cancel/direct reopening and complete trading plus legacy partial-delivery stories, and spec-check.

## Requirement Coverage

- [X] T059 [FR-022] Add durable supplier-payment/refund rollback, currency, replay and action-event tests in test_finance_payment_atomicity.py; harden the shared commands and tool handlers.
- [X] T060 [FR-023] Implement and test supplier invoice recording and narrowly scoped Playground supplier finance adapters.
- [X] T061 [FR-023] Implement and test reviewed return/credit/refund adapters and cockpit selection with exact historical references.
- [X] T062 [FR-022–023] Verify full backend, frontend/build, browser workflows, tenant denial and reload/replay; record actual deployment and remaining gates.

- [X] T058 [FR-021] Embed and test the shared cockpit operation chooser at entry and completion; verify build/browser and preserve pending reviews.

- [X] T055 [FR-020] Add purchase/receipt story and fail-closed tests before enabling adapters.
- [X] T056 [FR-020] Wire typed purchase/receipt inputs, exact policy, observations and cockpit continuation.
- [X] T057 [FR-020] Verify backend suite, browser continuation, frontend/build and spec gates; document scope.

- [X] T052 [FR-019] Add current-operation segmentation and two-operation browser regression tests.
- [X] T053 [FR-019] Add same-run continuation controls and scope evidence/progress to the current operation.
- [X] T054 [FR-019] Verify contracts/build, browser continuation and shared service regression; record remaining scope.

- [X] T048 [FR-018] Add shared invoice and private finance-step regression tests first.
- [X] T049 [FR-018] Implement shared invoice proposal, narrow sandbox policy and financial receipts.
- [X] T050 [FR-018] Add cockpit invoice/payment controls, progress and localized explanations.
- [X] T051 [FR-018] Verify backend, contracts/build and browser workflow; document actual evidence.

- [X] T045 [FR-017] Add failing durable payment rollback and action attribution tests
  in packages/reality-core/tests/test_finance_payment_atomicity.py.
- [X] T046 [FR-017] Compose the shared financial helpers atomically and propagate
  trusted action identity through tools/application.py and services/core.py.
- [X] T047 [FR-017] Run financial, tool, Playground, catalog and complete backend
  tests; record evidence without enabling unfinished Playground financial controls.

- [X] T041 [FR-014–016] Add catalog/start/restart tests in test_playground_runs.py and
  library selection/cancel/no-automatic-write coverage in playground-workspace-browser.mjs.
- [X] T042 [FR-014–016] Implement supported versioned presets, explicit selected-preset
  restart and localized scenario chooser; preserve shared command handlers.
- [X] T043 [FR-014–016] Verify focused backend suites, web contracts/build and isolated
  browser journey. Record unavailable workflows and remaining release gates honestly.
- [ ] T044 [FR-015] Implement separately tested invoice/payment, customer return,
  purchase/receipt and expense/reversal adapters before enabling those library goals.

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T011 | T012 | Pending |
| FR-002 | T009, T011 | T010, T012, T013 | Pending |
| FR-003 | T005, T011, T024 | T006, T012 | Pending |
| FR-004 | T014, T018 | T015, T019 | Pending |
| FR-005 | T007, T014, T018, T020 | T008, T015, T021 | Pending |
| FR-006 | T016, T018, T020 | T017, T021 | Pending |
| FR-007 | T022, T026 | T023, T026 | Pending |
| FR-008 | T022, T024, T026 | T023, T025, T026 | Pending |
| FR-009 | T014, T027, T029 | T015, T028, T029 | Pending |
| FR-010 | T027, T029 | T028, T029 | Pending |
| FR-011 | T009, T024, T027 | T010, T025, T028 | Pending |
| FR-012 | T030 | T031, T038 | Pending |
| FR-013 | T013, T020, T026, T029, T030, T032, T037 | T013, T021, T026, T029, T033, T038 | Pending |
| FR-017 | T045, T047 | T046 | Verified shared prerequisite; finance activation tracked under FR-018 |
| FR-018 | T048, T051 | T049, T050 | Invoice/payment increment verified; full release gates remain open |
| FR-019 | T052, T054 | T053 | Same-run sales continuation verified |
| FR-020 | T055, T057 | T056 | Purchase/receipt continuation verified; supplier finance remains unavailable |
| FR-022 | T059, T062 | T059 | Shared outgoing finance atomicity and attribution verified |
| FR-023 | T060–T062 | T060–T061 | Supplier finance and customer-return adapters verified; final 1,199-test backend suite and browser regression passed |
| DR-001 | T007, T009, T018, T022 | T008, T010, T019, T023, T038 | Pending |
| DR-002 | T007, T016, T018 | T008, T017, T038 | Pending |
| DR-003 | T003, T005, T022, T036 | T004, T006, T023, T038 | Pending |
| DR-004 | T003, T016, T018 | T004, T017, T019, T038 | Pending |
