# Tasks: Read Capability Guidance

## Phase 1 — Tests

- [x] T001 [US1] Add six-read description matrix tests in `packages/reality-core/tests/test_capability_guidance.py`.
- [x] T002 [US2] Add proof/non-proof/unknown semantic tests in `packages/reality-core/tests/test_capability_guidance.py`.
- [x] T003 [US3] Add planted validation and parity defects in `packages/reality-core/tests/test_capability_guidance.py` and `test_agent_command_parity.py`.

## Phase 2 — Catalog contract

- [x] T004 [US3] Implement discriminated proposal/read validation in `packages/reality-core/src/reality/catalogs.py`.
- [x] T005 [US1] Add six read entries to `packages/reality-core/config/command_catalog.yaml`.
- [x] T006 [US1] Preserve shared `capability_describe` application and MCP lookup behavior.

## Phase 3 — Documentation and verification

- [x] T007 [US2] Extend `apps/docs/content/concepts/agent-capabilities.md` with the read-selection and verification loop.
- [x] T008 [US3] Extend `apps/docs/scripts/docs-contract.test.mjs` and `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T009 Run spec, lint, backend, Docs, Site, and Web gates and final diff review.

T009 evidence: spec policy, changed-file lint, 368 Core tests, 13 Docs tests/build,
36 Site tests/build, 48 Web tests/build, and final diff review pass. Repository-wide
Ruff remains red on 56 pre-existing import-order findings outside this feature.

All FR-001–FR-009 and DR-001–DR-004 map to T001–T008; T009 supplies completion evidence.
