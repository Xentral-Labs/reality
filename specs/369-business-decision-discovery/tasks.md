# Tasks: Executed Decisions by affected order
## Specification and design gates
- [x] T001 Review accepted scope in spec.md and checklists/requirements.md.
- [x] T002 Complete Constitution PASS in plan.md, research.md, data-model.md and contracts/reads.md; analyze requirements before implementation.
## US1: Find and verify executions
- [x] T003 [US1] [FR-001,FR-002,FR-004] Add fail-first execution, deduplication, association, privacy and follow-up proofs in packages/reality-core/tests/test_business_decision_discovery.py.
- [x] T004 [US1] [FR-001,FR-002,FR-003,FR-004] Implement canonical executed selection and payload-free records in packages/reality-core/src/reality/services/core.py; qualify page metadata in services/read_contracts.py.
- [x] T005 [US1] [FR-001,FR-003,FR-004,DR-001] Expose existing family/input through mcp/catalog.py; update docs/features/mcp_reads.md and generated catalog, preserving tools/application.py adapter.
## US2: Safe traversal
- [x] T006 [US2] [FR-003,DR-001] Add page/legacy, tenant, shortest-link, cursor, no-write and grant proofs in tests/test_business_decision_discovery.py and tests/test_mcp_http_runtime.py; run focused regression, Ruff/spec/docs and update docs/SPEC_COVERAGE_MATRIX.md.
## Completion
- [ ] T007 [FR-004,DR-001] Complete fresh read-only MCP acceptance, actual external Claude observation, cleanup, full final-head CI and diff review in verification.md and review.md.
## Dependencies and strategy
T001 → T002 → T003 → T004 → T005 → T006 → T007. No parallel implementation required. US1 supplies the minimum complete discovery/verification flow; US2 proves safe traversal of that same service. All FR/DR requirements map tests and implementation in spec.md. No schema or Web behavior change; required frontend and full backend gates run through complete CI.
