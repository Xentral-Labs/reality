# Tasks: MCP Permission Presets

## Phase 1: Specification and acceptance proof

- [x] T001 Record approved scope and measurable requirements in `specs/264-mcp-permission-presets/spec.md` (FR-001–FR-006).
- [x] T002 Record the passing Constitution Check and test/rollback design in `specs/264-mcp-permission-presets/plan.md`.
- [x] T003 [US1] Add failing full-access and explicit-allowlist browser assertions in `apps/web/scripts/unified-ai-access-browser.mjs` (FR-001, FR-002, FR-005).
- [x] T004 [US2] Add read-only replacement and clear-selection browser assertions in `apps/web/scripts/unified-ai-access-browser.mjs` (FR-003, FR-004).

## Phase 2: Implementation

- [x] T005 [US1] Add the full-access preset to `apps/web/src/unified/MCPAccess.tsx` (FR-001, FR-002, FR-004, FR-005).
- [x] T006 [P] [US1] Add supported-language labels in `apps/web/src/localization.tsx` (FR-006).
- [x] T007 [P] Document the durable behavior in `docs/WEB_SPEC.md` (FR-001–FR-006).

## Phase 3: Verification and review

- [x] T008 Run focused browser acceptance and frontend localization/build checks (FR-001–FR-006; SC-001–SC-003).
- [x] T009 Run specification and repository-relevant lint/test gates and review the diff against the Constitution.
