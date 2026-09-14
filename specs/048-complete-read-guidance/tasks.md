# Tasks: Complete Read Capability Guidance

## Phase 1 — Tests

- [x] T001 [US1] Add public-read completeness and planted-drift tests to `packages/reality-core/tests/test_capability_guidance.py`.
- [x] T002 [US2] Add six-read semantic proof/non-proof tests to `packages/reality-core/tests/test_capability_guidance.py`.
- [x] T003 [US3] Add shared pending-proposal and read parity tests to `packages/reality-core/tests/test_agent_command_parity.py` and `test_ai_mcp.py`.

## Phase 2 — Implementation

- [x] T004 [US1] Enforce complete public business-read coverage in `packages/reality-core/src/reality/catalogs.py`.
- [x] T005 [US2] Add six validated entries to `packages/reality-core/config/command_catalog.yaml`.
- [x] T006 [US3] Route pending proposals through `packages/reality-core/src/reality/tools/application.py` and `mcp/catalog.py`.

## Phase 3 — Documentation and verification

- [x] T007 [US1] Document the complete read matrix in `apps/docs/content/concepts/agent-capabilities.md`.
- [x] T008 [US1] Extend Docs contracts and `docs/SPEC_COVERAGE_MATRIX.md`.
- [x] T009 Run spec, lint, Core, Docs, Site, Web, and final diff gates.

FR-001–FR-008 and DR-001–DR-004 map to T001–T008; T009 supplies completion evidence.
