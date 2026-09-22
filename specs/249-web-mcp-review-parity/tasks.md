# Tasks: Web and MCP Proposal Review Parity

**Input**: `spec.md`, `plan.md`, `research.md`, `contracts/proposal-review.md`
**Gate**: Approved scope, Constitution Check PASS, no unresolved clarification

## Phase 1: Failing parity proof

- [ ] T001 [P] [US3] [FR-001] [FR-010] Add a failing registry contract for every MCP proposal binding in `packages/reality-core/tests/test_proposal_review_parity.py`
- [ ] T002 [P] [US1] [FR-002] [FR-010] Add a failing Web routing contract in `apps/web/scripts/proposal-review-parity.test.mjs`
- [ ] T003 [P] [US1] [FR-003] [FR-004] Add failing descriptor, nested-value and redaction tests in `packages/reality-core/tests/test_proposal_review_parity.py`
- [ ] T004 [P] [US2] [FR-005] [FR-006] [FR-007] [FR-008] Add failing tenant, stale, replay, malformed, rejection and receipt tests in `packages/reality-core/tests/test_proposal_review_parity.py`

## Phase 2: Canonical review service and API

- [ ] T005 [US1] [FR-001] [FR-003] [FR-004] Implement scoped classification, labels, validation and redaction in `packages/reality-core/src/reality/services/proposal_reviews.py`
- [ ] T006 [US1] [FR-001] [FR-009] Delegate existing specialized review classes in `packages/reality-core/src/reality/services/proposal_reviews.py`
- [ ] T007 [US2] [FR-005] [FR-006] [FR-007] [FR-008] Expose routing metadata and descriptor/recovery in `packages/reality-core/src/reality/web/api.py`
- [ ] T008 [US3] [FR-010] Export stable proposal binding/classification metadata without a transport cycle in `packages/reality-core/src/reality/mcp/catalog.py` and `packages/reality-core/src/reality/services/proposal_reviews.py`

## Phase 3: Unified Web routing and common review

- [ ] T009 [P] [US1] [FR-002] Add client types and one route helper in `apps/web/src/api.ts` and `apps/web/src/unified/proposalRouting.ts`
- [ ] T010 [US1] [FR-002] [FR-009] Replace Chat and Decisions allowlists in `apps/web/src/unified/ChatPage.tsx`, `apps/web/src/unified/DecisionsPage.tsx`, and `apps/web/src/unified/UnifiedApp.tsx`
- [ ] T011 [US1] [FR-003] [FR-004] [FR-005] [FR-006] Implement the common review in `apps/web/src/unified/ProposalReviewCard.tsx`
- [ ] T012 [US2] [FR-007] [FR-008] Implement reload, refusal and receipt states in `apps/web/src/unified/ProposalReviewCard.tsx`
- [ ] T013 [P] [US1] [FR-011] Add four-language labels in `apps/web/src/localization.tsx`

## Phase 4: Acceptance, documentation and review

- [ ] T014 [US1] [US2] [FR-001] [FR-005] [FR-007] Add browser journeys for lot, payment term, pricing, cost/finance and shipment proposals in `apps/web/scripts/proposal-review-browser.mjs`
- [ ] T015 [P] [US3] [FR-012] Document production-tool parity and prohibit demo-only tools in `docs/WEB_SPEC.md` and `docs/features/company-setup-demo.md`
- [ ] T016 [FR-001] [FR-010] Run backend/Web tests, spec check, build and i18n; record results in `specs/249-web-mcp-review-parity/quickstart.md`
- [ ] T017 [FR-005] [FR-008] [FR-009] Review tenant scope, stored-input execution, redaction and no-schema rollback in `specs/249-web-mcp-review-parity/checklists/requirements.md`

## Dependencies and implementation strategy

T001–T004 establish failing proof. T005–T008 are foundational. T009 may proceed after the response
contract is fixed; T010–T012 follow. T013 and T015 are parallel. T014–T017 are the completion gate.
The MVP is US1 plus the registry contract; US2 recovery is required before completion.
