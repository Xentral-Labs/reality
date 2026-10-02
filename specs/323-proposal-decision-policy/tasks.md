# Tasks: Consistent Proposal Decision Policy

## Setup and foundational review

- [x] T001 Record approved scope and authority inventory in specs/323-proposal-decision-policy/spec.md and research.md (FR-001–FR-008).
- [x] T002 Complete Constitution Check, contract and test strategy in specs/323-proposal-decision-policy/plan.md and contracts/decision-policy.md (DR-001, DR-002).

## US1 — Accurate requirements and enforcement

- [x] T003 [US1] Add failing action matrix and real credit owner/member, changed membership and ordinary action proofs in packages/reality-core/tests/test_proposal_decision_policy.py (FR-001–FR-004, FR-007, DR-002).
- [x] T004 [US1] Add immutable policy in packages/reality-core/src/reality/domain/proposal_decisions.py and shared resolution/enforcement in packages/reality-core/src/reality/services/proposal_decisions.py (FR-001–FR-004, FR-007).
- [x] T005 [US1] Use policy in packages/reality-core/src/reality/services/proposal_reviews.py and packages/reality-core/src/reality/tools/application.py; expose identical metadata in packages/reality-core/src/reality/services/delivery_actions.py while preserving phase ordering (FR-001, FR-003, FR-004, FR-007, DR-001, DR-002).

## US2 — Channel and decision limits

- [x] T006 [US2] Extend packages/reality-core/tests/test_proposal_decision_policy.py and update exact handoff expectations in tests/test_ai_mcp.py and tests/finance/test_owner_handoff.py; run existing Chat, MCP and attribution proofs (FR-002, FR-005, FR-006, DR-002).
- [x] T007 [US2] Add policy type and accurate approval-only presentation in apps/web/src/api.ts, apps/web/src/unified/ProposalReviewCard.tsx, shared DecisionReview.tsx, specialized delivery cards and apps/web/src/localization.tsx; extend apps/web/scripts/proposal-review-browser.mjs and source contract (FR-008).

## Verification and review

- [x] T008 Update docs/WEB_SPEC.md and docs/features/proposal-decision-policy.md, regenerate executable catalog documentation with make docs-generate (FR-006, FR-008).
- [x] T009 Run full backend, lint, spec, frontend and documentation gates and relevant browser proof; record evidence in specs/323-proposal-decision-policy/quickstart.md (all FR/DR).
- [x] T010 Review scoped diff, preserved authorization and requirement coverage; update task status only with green evidence in specs/323-proposal-decision-policy/tasks.md (all FR/DR).

## Dependencies and execution

T001–T002 → analysis → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010.
US2 shares the US1 policy. Independent research may run alongside read-only planning;
implementation edits are sequential. MVP is the shared policy and corrected owner
handoff, followed by additive channel metadata and compatible presentation.
