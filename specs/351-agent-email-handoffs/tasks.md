# Tasks: Agent Email Handoffs

- [x] T001 Write source/file/version/partial-capture tests (US1; FR-001–003, DR-001–002).
- [x] T002 Write exact dispatch decision, actor, claim and retry tests (US2; FR-004–007, DR-004).
- [x] T003 Write report/reconciliation/deviation/history tests (US3; FR-008–010, DR-003–005).
- [x] T004 Write MCP/API/tenant/migration and discovery tests (US4; FR-011–012).
- [x] T005 Add closed domain schemas, dispatch model and migration.
- [x] T006 Implement shared capture/file/authorization/claim/report/history services.
- [x] T007 Bind application and MCP tools; expose shared API routes and review links.
- [x] T008 Publish canonical agent contract, labels and generated documentation.
- [ ] T009 Run all required checks, review diff and record verification evidence.
- [ ] T010 Create PR and resolve required CI/review findings until green.

## Analysis

No unresolved scope clarifications or critical design conflicts. Approval does not
mean dispatch occurred; capture/report permissions do not mean decision authority;
claim ownership is authenticated, never a caller-supplied agent name. Original
external metadata stays in payload. No provider-specific network execution is added.
Each FR/DR maps to the story/test tasks above and the specification traceability table.
