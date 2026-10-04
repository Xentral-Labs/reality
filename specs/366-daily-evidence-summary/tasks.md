# Tasks: Daily evidence summary

Input: spec.md, plan.md, research.md. Gate: Constitution PASS; user scope accepted.

## Phase 1: Gates
- [x] T001 Record scope acceptance and research in `spec.md` and `research.md`.
- [x] T002 Record Constitution PASS in `plan.md`.
- [x] T003 Analyze traceability and record review in `analysis.md`.

## Phase 2: US1 and US2 (P1)
- [x] T004 [US1] [FR-001] [FR-003] [FR-005] Add failing asymmetric return, read-only/tenant/legacy tests in `packages/reality-core/tests/test_mcp_read_contract.py` and `packages/reality-core/tests/test_mcp_http_runtime.py`.
- [x] T005 [US2] [FR-002] Add failing limited, final-cursor and empty-page proofs in `packages/reality-core/tests/test_mcp_read_contract.py`.
- [x] T006 [US1] [FR-001] [FR-003] [FR-005] Add deterministic shown-record summaries in `packages/reality-core/src/reality/services/read_contracts.py` and canonical item labels in `packages/reality-core/src/reality/services/core.py`.
- [x] T007 [US2] [FR-002] Add exact returned-page coverage to the same service helper in `packages/reality-core/src/reality/services/read_contracts.py`.

## Phase 3: US3 (P1)
- [x] T008 [US3] [FR-004] Add failing ready/blocked/partial/closed cause-boundary tests in `packages/reality-core/tests/test_mcp_read_contract.py`.
- [x] T009 [US3] [FR-004] Preserve canonical readiness and add unknown/not-applicable cause in `packages/reality-core/src/reality/services/projections.py`.

## Phase 4: Shared adapters and documentation
- [x] T010 [DR-001] Add return context/refusal proofs for both providers in `packages/reality-core/tests/test_chat_scope_security.py`.
- [x] T011 [DR-001] Use canonical return context and guidance in `packages/reality-core/src/reality/agent/mcp_chat.py`; update `packages/reality-core/src/reality/mcp/catalog.py` and `apps/docs/content/getting-started/demo-company.md` and German locale.
- [x] T012 [DR-001] Regenerate catalog docs with `make docs-generate` and check output in `apps/docs/content/tool-usage/` and `apps/docs/.vitepress/data/tool-usage.json`.

## Final Phase: Verification and Review
- [x] T013 Run focused tests/lint/spec/docs/full Quality CI and record results/actual-model limitations in `verification.md`.
- [x] T014 Review final diff/requirements and prepare PR with `review.md`.

## Dependencies and parallel opportunities
T001–T003 before code. T004/T005 before T006/T007; T008 before T009; T010 before T011.
US3 tests are independent from US1/US2. Documentation generation follows catalog changes.
No implementation delegation; research/review use the Spec-Kit research reviewer.

## Requirement coverage
| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T004 | T006 |
| FR-002 | T005 | T007 |
| FR-003 | T004 | T006 |
| FR-004 | T008 | T009 |
| FR-005 | T004 | T006 |
| DR-001 | T010,T012 | T011,T012 |

MVP: accurate return page observations, then coverage and order cause boundaries.
