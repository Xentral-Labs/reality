# Tasks: Existing-tool evidence boundaries
## Setup and foundational gates
- [x] T001 Record accepted scope in spec.md and requirement-quality checklist.
- [x] T002 Research and plan shared read boundaries in plan.md, research.md and contracts/reads.md; analyze before implementation.
## US1 and US2: Existing read boundaries
- [ ] T003 [US1] [US2] [FR-001–004,FR-006] Add failing public/shared read proofs in packages/reality-core/tests/test_tool_evidence_boundaries.py.
- [ ] T004 [US1] [US2] [FR-001–004,FR-006] Implement services/read_interpretation.py and integrate services/fulfillment_readiness.py, projections.py, exceptions.py and capability_catalog.py; keep cached derivation presentation-free.
## US3: Incomplete provider output
- [ ] T005 [US3] [FR-005,FR-006] Add failing limit-stop proofs in tests/test_chat_streaming.py and test_chat_scope_security.py for both transports/providers and partial calls.
- [ ] T006 [US3] [FR-005,FR-006] Implement agent/streaming.py stop detection and agent/mcp_chat.py localized notice/reset before dispatch.
## Cross-cutting verification and review
- [ ] T007 [DR-001] Update mcp/catalog.py, agent/mcp_chat.py guidance, docs/features/mcp_reads.md and generated Tool Usage pages/JSON with make docs-generate.
- [ ] T008 [FR-006,DR-001] Run focused PostgreSQL/security/HTTP proofs, Ruff/spec/docs gates and full final-head CI; record live acceptance limitations in verification.md.
- [ ] T009 Review final diff and all requirements, record review.md and mark tasks only after required checks pass.
## Dependencies and implementation strategy
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009. Implement smallest common service boundary before adapters. Research-agent review may run independently of read-only inspection, but implementation remains sequential.
## Requirement Coverage
See spec.md Requirement Traceability. All seven requirements have test and implementation tasks; no unresolved clarification or critical analysis finding.
