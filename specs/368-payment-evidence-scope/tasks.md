# Tasks: Payment evidence and selection scope
## Gates
- [x] T001 Accept scope and review requirements in spec.md and checklists/requirements.md.
- [x] T002 Complete plan.md, research.md, contracts/reads.md and analyze.md; Constitution PASS.
## US1: Payment evidence
- [x] T003 [US1] [FR-001–003] Add failing shared read proofs in packages/reality-core/tests/test_payment_evidence_scope.py; extend tests/test_fulfillment_readiness.py, test_prepayment_release.py and test_shipment_actions.py for evidence boundaries and raw token compatibility.
- [x] T004 [US1] [FR-001–003] Implement services/read_interpretation.py and services/fulfillment_readiness.py; decorate existing reads only.
## US2: Selection scope
- [x] T005 [US2] [FR-004] Add limited/final/complete/empty discovery proofs in tests/test_payment_evidence_scope.py.
- [x] T006 [US2] [FR-004] Extend services/read_contracts.py deterministic summary without extra queries.
## Verification
- [x] T007 [FR-003,DR-001] Update mcp/catalog.py, agent/mcp_chat.py, demo DE/EN guidance, docs/features/mcp_reads.md, docs/SPEC_COVERAGE_MATRIX.md and generated catalog. Run PostgreSQL, HTTP/security, Ruff/spec/docs checks.
- [x] T008 [DR-001] Complete full final-head CI, actual external Claude MCP acceptance and diff review; record verification.md and review.md before marking required checks done.
## Dependencies and Coverage
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008. Each requirement maps tests and implementation in spec.md. No critical analysis finding or unresolved clarification.
