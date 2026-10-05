# Tasks: Operational cases

**Status**: Product direction and concrete five-table schema approved by the owner on 2026-10-05. First-slice implementation and focused acceptance complete; final full-suite verification in progress.
**Input**: spec.md, plan.md, data-model.md, contracts/event-policy.md, research.md, quickstart.md.
**Gate**: Author Constitution assessment PASS; pre-implementation analysis complete; owner schema/domain approval recorded in chat ("ja gebe ich frei"). No production rollout authorized by these checks.

## Phase 1: Review and boundary proof

- [x] T001 Product direction was accepted in chat on 2026-10-05; obtain the distinct owner/domain review of the concrete five-table proposal in `contracts/first-slice.md` before schema implementation. **Recorded:** owner approval ("ja gebe ich frei") in this session; no unseen approval inferred.
- [x] T002 Review the now-populated static inventory and explicit unsupported-root dispositions with the owner/domain reviewer; refresh as code changes. Populate `contracts/entrypoint-coverage.md` with exact reachable scoped Web/API, CLI, MCP, import, service and worker symbols; classify creation/preparation/execution/claim, name atomic ensure/guard locations and row-level proofs. Verify goal resolvers, refund-intent capability and Alembic head; cross-reference `contracts/event-policy.md`. Keep refund unavailable if no suitable intent authority exists.
- [x] T003 Author cross-artifact analysis is recorded in `analysis.md` with resolved findings; obtain required independent schema/domain review and recheck constitutional rows before runtime changes.

## Phase 2: Tests before domain/model implementation
- [x] T004 [US1] [FR-001 FR-002 FR-008 DR-001 DR-002] Add goal classification, grouping, completed-history, partial fulfillment and correction tests in `packages/reality-core/tests/test_operational_case_policies.py`.
- [x] T005 [US1] [FR-003 FR-011 DR-002 DR-003] Add membership, adoption boundary, typed FK and tenant isolation proofs in `packages/reality-core/tests/test_operational_cases.py`.
- [x] T006 [US1] [FR-001 FR-002 FR-008 DR-001] Implement closed pure policies in `domain/operational_cases.py` and authoritative resolvers in `services/case_policies.py` under `packages/reality-core/src/reality/`.
- [x] T007 [US1] [FR-001 FR-002 FR-003 FR-004 FR-007 FR-009 FR-011 DR-002 DR-003] Implement reviewed additive models in `packages/reality-core/src/reality/db/operational_cases.py`, model registration, migration in the discovered current Alembic versions directory, and scoped repositories/services in `services/operational_cases.py`.

## Phase 3: Takeover and synchronous execution protection

- [x] T008 [US3] [FR-007 FR-012 DR-003] Inventory exact enabled action/claim paths and external-correlation propagation in this feature contracts; add preservation/absence and case/action separation proofs in `packages/reality-core/tests/test_case_action_guards.py`; add deny-by-default, multi-case and delayed-consumer stale checks in `packages/reality-core/tests/test_case_action_guards.py`.
- [x] T009 [US2] [FR-004 FR-005 FR-006 FR-010 DR-003] Add takeover/execution races, retained uncertain effects, current-review handback and revoked-member tests in `packages/reality-core/tests/test_operational_case_controls.py`.
- [x] T010 [US2] [FR-004 FR-005 FR-006 FR-010 DR-003] Implement shared exact control/read services in `packages/reality-core/src/reality/services/operational_cases.py`; reuse canonical proposal decisions and real execution receipts.
- [x] T011 [US3] [FR-003 FR-004 FR-005 FR-006 FR-007 FR-008 FR-012 DR-001 DR-003] Implement server-derived case bindings/current-state guards in `services/case_action_guards.py`; wire `tools/application.py`, governed service execution and actual claim paths under `packages/reality-core/src/reality/`, preserving executed receipt replay and manual repair. Preserve supplied external correlation IDs in touched paths; fix only proven conflicting assignments, without historical rewrites or a global cleanup.

## Phase 4: Durable consumer and adoption

- [x] T012 [US1] [FR-009 FR-011 FR-012 DR-001 DR-003] Add atomic checkpoint rollback, worker restart, policy replay, unknown/self events, source freshness and opt-in tests in `packages/reality-core/tests/test_operational_case_jobs.py`.
- [x] T013 [US1] [FR-001 FR-008 FR-009 FR-011 FR-012 DR-001 DR-003] Implement bounded database-only handler `packages/reality-core/src/reality/jobs/handlers/operational_cases.py`; integrate existing registry/scheduling discovery and atomic checkpoints, keeping producer unchanged.

## Phase 5: Adapters, operator explanation and acceptance

- [x] T014 [US2] [FR-004 FR-006 FR-010 FR-011 FR-013 DR-003] Add additive existing-read/proposal/receipt response compatibility, object-to-case discovery, forged-ID, empty-history and multi-case tests; add shared-tool/API/CLI/MCP authorization, read purity and exact-control tests in `packages/reality-core/tests/test_operational_case_adapters.py`.
- [x] T015 [US2] [FR-004 FR-006 FR-010 FR-011 FR-013 DR-003] Inventory and add case associations to existing object/inspector/proposal/receipt read envelopes without changing historical receipts. Expose operations through `tools/operational_cases.py`, `web/operational_cases.py`, existing CLI/MCP registries and application catalogs under `packages/reality-core/`.
- [x] T016 [US2] [FR-003 FR-005 FR-006 FR-010 FR-012 FR-014 DR-001] Add focused UI case discovery/list, copyable ID, responsibility marking and takeover, handback gap and actual execution explanation tests following existing harness for `apps/web/src/unified/OperationalCaseDetail.tsx`.
- [x] T017 [US2] [FR-003 FR-005 FR-006 FR-010 FR-012 FR-014 DR-001] Implement a discoverable case list, context links in existing `apps/web/src/unified/OrdersPage.tsx` and inspector views, copyable ID, real manual-takeover/review/handback controls and `apps/web/src/unified/OperationalCaseDetail.tsx`, source/object links and translations; use shared services without client-side goal rules.
- [x] T018 [US1 US2 US3] [FR-001 FR-002 FR-003 FR-004 FR-005 FR-006 FR-007 FR-008 FR-009 FR-010 FR-011 FR-012 DR-001 DR-002 DR-003] Add the integrated Shopify accepted-evidence repair story in `packages/reality-core/tests/test_shopify_case_recovery.py` and record actual results in `quickstart.md`; do not claim live connector coverage.
- [x] T022 [US4] [FR-015] Add documentation/catalog contract tests in `packages/reality-core/tests/test_operational_case_docs.py` for event classifications, ID meanings, control semantics and declared capability limits before documentation/catalog implementation.
- [x] T023 [US1 US3] [FR-016] Add row-level atomic goal/case creation and lower-level execution-bypass proofs in `packages/reality-core/tests/test_case_entrypoint_coverage.py`; derive coverage from reviewed actual entrypoint inventory, including human-repair distinctions and no-case source staging.
- [x] T024 [US1 US3] [FR-016] Wire atomic ensure/match and server-resolved guards at the exact canonical symbols listed in `contracts/entrypoint-coverage.md`, using `services/operational_cases.py` and `services/case_action_guards.py`; verify every enabled inventory row and reject unclassified adopted automation.
- [x] T019 [US1 US2 US3] [FR-001 FR-002 FR-003 FR-008 FR-010 FR-012 FR-015 DR-001 DR-002 DR-003] Add bilingual user/maintainer integration guidance under `apps/docs/content/integrations/`, `apps/docs/content/de/integrations/`, and `docs/maintainer-guides/`; wire navigation and generated tool contracts. Add validated `packages/reality-core/config/case_policy_catalog.yaml` and event/action vocabulary; update `docs/features/operational-cases.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md` and `docs/WEB_SPEC.md` only to implemented behavior.

## Final Phase: Verification and review

- [ ] T020 Run `make spec-check`, `make lint`, the complete PostgreSQL `make test`, migration upgrade/downgrade proof, `make web-build`, Web i18n audit, `make docs-generate` and `make docs-catalog-check`; retain actual evidence in `quickstart.md` and required committed-head CI.
- [ ] T021 Review final diff against all FR/DR, execution guard inventory, no-network handler contract and rollback restrictions. Mark release status only after green required checks and reviewer acceptance.

## Requirement Coverage

| Requirement | Test tasks | Implementation tasks | Status |
|---|---|---|---|
| FR-001 | T004, T018 | T006, T007, T013, T019 | Implemented; local verification passed; release CI pending |
| FR-002 | T004, T018 | T006, T007, T019 | Implemented; local verification passed; release CI pending |
| FR-003 | T005, T016, T018 | T007, T011, T017, T019 | Implemented; local verification passed; release CI pending |
| FR-004 | T009, T014, T018 | T007, T010, T011, T015 | Implemented; local verification passed; release CI pending |
| FR-005 | T009, T016, T018 | T010, T011, T017 | Implemented; local verification passed; release CI pending |
| FR-006 | T009, T014, T016, T018 | T010, T011, T015, T017 | Implemented; local verification passed; release CI pending |
| FR-007 | T008, T018 | T007, T011 | Implemented; local verification passed; release CI pending |
| FR-008 | T004, T018 | T006, T011, T013, T019 | Implemented; local verification passed; release CI pending |
| FR-009 | T012, T018 | T007, T013 | Implemented; local verification passed; release CI pending |
| FR-010 | T009, T014, T016, T018 | T010, T015, T017, T019 | Implemented; local verification passed; release CI pending |
| FR-011 | T005, T012, T014, T018 | T007, T013, T015 | Implemented; local verification passed; release CI pending |
| FR-012 | T008, T012, T016, T018 | T011, T013, T017, T019 | Implemented; local verification passed; release CI pending |
| DR-001 | T004, T012, T016, T018 | T006, T011, T013, T017, T019 | Implemented; local verification passed; release CI pending |
| DR-002 | T004, T005, T018 | T007, T019 | Implemented; local verification passed; release CI pending |
| DR-003 | T005, T008, T009, T012, T014, T018 | T007, T010, T011, T013, T015, T019 | Implemented; local verification passed; release CI pending |

| FR-013 | T014 | T015 | Implemented; local verification passed; release CI pending |
| FR-014 | T016 | T017 | Implemented; local verification passed; release CI pending |
| FR-015 | T022 | T019 | Implemented; local verification passed; release CI pending |

| FR-016 | T023 | T024 | Implemented; local verification passed; release CI pending |

## Final local verification

All local implementation and acceptance checks passed, including 6,432 complete PostgreSQL tests (10 skipped), migration, Web/browser/i18n, documentation generation/build, lint, spec policy and business annotations. See `quickstart.md` for exact evidence. T020/T021 remain unchecked solely for committed-head generated-artifact/CI and final release review: the owner authorized a feature-branch commit and CI on 2026-10-05; deployment, merge and production approval are not implied. Final author diff review preserves transactional guards, source/Finance separation, typed tenant links, no-network reconciliation and refusal to discard adoption history. Live Shopify qualification remains a separate adapter gate, now concretely described in `contracts/shopify-adapter-readiness.md`.

## Dependencies and MVP

T001–T003 gate runtime work. T004/T005 precede T006/T007; T008/T009 precede T010/T011; T012 precedes T013; T014/T016 precede T015/T017. T018 is written before final integration, not after completion. T023 precedes T024; complete T002 inventory and every enabled row proof before adopted-scope activation. No agent delegation or parallel agent work is requested.

MVP includes stable fulfillment/return cases, explicitly unavailable unsupported refund capability, atomic takeover and synchronous action guards, reliable event reconciliation and basic operator controls. It is not complete merely because cases can be listed; guard coverage and repair/handback acceptance are mandatory.
