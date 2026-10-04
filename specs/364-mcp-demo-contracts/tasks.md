# Tasks: Complete Live Demo Agent Contracts

Gate: owner accepted scope; Constitution PASS; no clarification remains.

## Foundation

- [x] T001 [DR-001/DR-003] Record scope/design in `spec.md`, `plan.md`, `research.md` and `data-model.md`.
- [x] T002 [US1] [FR-001/FR-002/DR-002] Add failing two-provider evidence/access tests in `packages/reality-core/tests/test_chat_scope_security.py`.
- [x] T003 [US2] [FR-004/FR-005/FR-006/DR-001/DR-002] Add failing Playground review/handoff/receipt regressions in `packages/reality-core/tests/test_demo_mcp_workflow.py`.
- [x] T004 [US3] [FR-003/DR-002] Add failing real HTTP schema choices/typed-call proof in `packages/reality-core/tests/test_mcp_http_runtime.py`.

## US1 — Current operations, read-first

- [x] T005 [US1] [FR-001/FR-002/DR-001/DR-002] Implement shared shipping context and current-turn access guard in `packages/reality-core/src/reality/agent/mcp_chat.py`.

## US2 — Exact initial review and executable handoff

- [x] T006 [US2] [FR-004/DR-001/DR-002] Retain canonical initial demo reservation review in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/services/tenant_policy.py`; preserve authored lesson context.
- [x] T007 [US2] [FR-005/FR-006/DR-002] Derive full handoff and callable guidance in `packages/reality-core/src/reality/services/proposal_reviews.py` and `packages/reality-core/src/reality/mcp/catalog.py`.

## US3 — True HTTP choices

- [x] T008 [US3] [FR-003/DR-002] Preserve executable schema in `packages/reality-core/src/reality/mcp/server.py` without weakening typed calls.

## Verify and review

- [x] T009 [FR-001/FR-004/FR-005/FR-006/DR-003] Update EN/DE public guides, `docs/features/company-setup-demo.md`, `docs/SPEC_COVERAGE_MATRIX.md`; generate catalog references.
- [x] T010 [FR-001–FR-006/DR-001–DR-003] Run focused/full required gates and record actual results in `verification.md`; review privacy, tenant, immutable receipts and lesson compatibility.
- [x] T011 [FR-001–FR-006] Create/attach PR and verify its final head green; no merge/deployment.

Dependencies: T001 → T002/T003/T004 → T005/T006/T007/T008 → T009 → T010 → T011.
Independent reads/tests may run concurrently; no delegated execution. US1 and US2
remain independently testable. Implement service authority before adapter changes.
