# Tasks: The Capability Catalog Names the Company's Purpose

Gate: scope accepted in the specification; Constitution PASS; no clarification remains.

## Foundation

- [x] T001 [FR-001/FR-002/DR-001] Record scope in `spec.md` and design in `plan.md`.

## US1 — Know the company's purpose before proposing

- [x] T002 [US1] [FR-001] Add service and read-tool tests in `packages/reality-core/tests/test_capability_catalog.py`.
- [x] T003 [US1] [FR-001/FR-002/DR-001] Read the stored purpose for the calling tenant in `packages/reality-core/src/reality/services/capability_catalog.py`.
- [x] T004 [US1] [FR-001/FR-002/DR-001] Add the MCP boundary test with two server-verified bearer tokens in `packages/reality-core/tests/test_capability_catalog.py`.

## Verify and review

- [x] T005 [FR-001/FR-002/SC-001] Describe the `tenant` object in `specs/270-mcp-capability-discovery/contracts/capability_catalog.md` and add the spec 362 rows to `docs/SPEC_COVERAGE_MATRIX.md`.
- [x] T006 [FR-001/FR-002/DR-001] Run focused gates and record actual results in `verification.md`.
- [x] T007 Attach to the pull request; no merge or deployment.

Dependencies: T001 → T002 → T003 → T004 → T005 → T006 → T007.
