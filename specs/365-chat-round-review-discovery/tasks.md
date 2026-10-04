# Tasks

## Phase 1 - Specification and Design

- [x] T001 Record accepted scope and scenarios in specs/365-chat-round-review-discovery/spec.md.
- [x] T002 Prepare Constitution PASS and research in specs/365-chat-round-review-discovery/plan.md and research.md.
- [x] T003 Review requirement quality and analyze FR/DR coverage in specs/365-chat-round-review-discovery/checklists/contracts.md and analysis.md before implementation.

## Phase 2 - Reliable Shipment Selection (US1)

Independent proof: unrelated early IDs cannot displace matching shipment evidence.

- [x] T004 [US1] Add failing padded discovery, cursor/legacy and scope regressions in packages/reality-core/tests/test_mcp_read_contract.py and test_demo_mcp_workflow.py, using the shared padded fixture in conftest.py (FR-001).
- [x] T005 [US1] Extend full-mission, multiround provider regressions in packages/reality-core/tests/test_chat_scope_security.py (FR-002).
- [x] T006 [US1] Restore shared Movement.type search in packages/reality-core/src/reality/services/core.py and update query guidance in mcp/catalog.py (FR-001, FR-002).

## Phase 3 - Generic Decision Discovery (US2)

Independent proof: review exposes confirmation and exact current permission, without mutation.

- [x] T007 [P] [US2] Add failing catalog principal and standalone metadata validation tests in packages/reality-core/tests/test_capability_catalog.py and test_tool_catalog.py (FR-003).
- [x] T008 [US2] Expose the explicit generic review entry through packages/reality-core/config/tool_catalog.json and src/reality/tool_catalog.py, preserving intake bindings (FR-003).

## Phase 4 - Documentation and Live Qualification (US3)

Independent proof: actual client behavior or explicit gaps, with preserved authority.

- [x] T009 Update apps/docs/content/getting-started/demo-company.md and content/de/getting-started/demo-company.md guidance and regenerate apps/docs/content/tool-usage, content/de/tool-usage and .vitepress/data/tool-usage.json (DR-001).
- [x] T010 [US1] Retest the actual published daily mission against corrected evidence in specs/365-chat-round-review-discovery/verification.md (FR-002).
- [x] T011 [US3] Qualify repeated external read-only mission/time/next-run/pause behavior and cleanup; record manual/scheduled/unsupported/blocked outcomes in specs/365-chat-round-review-discovery/verification.md (FR-004).

## Phase 5 - Verify and Review

- [ ] T012 Run focused/regression checks, lint, spec policy and docs-catalog-check; record results in specs/365-chat-round-review-discovery/verification.md (FR-001–004, DR-001).
- [ ] T013 Review final diff and complete Quality CI in specs/365-chat-round-review-discovery/review.md; prepare attached PR with honest remaining qualifications (FR-001–004, DR-001).

- [x] T014 Add failing undeclared-argument and provider-retry regressions, implement schema-based refusal in mcp/catalog.py and rerun actual daily mission (FR-005).

## Dependencies and Strategy

T001 → T002 → T003 → tests T004/T005/T007 → corresponding implementations T006/T008
→ T009 → T010/T011 → T012/T013. Test-first MVP is shipment selection; catalog is
independent and may be reviewed alongside it. Recurring qualification follows fixes,
never creates a timer to hide an unsupported external capability. [P] tasks have
separate files; execute sequentially unless a reviewed workflow explicitly delegates.
