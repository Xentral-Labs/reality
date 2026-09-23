# Tasks

## Phase 1 — Specification and tests

- [x] T001 Validate spec, plan, data model and contract against the Constitution in `specs/258-party-email-lookup/`
- [x] T002 [US1] Add failing exact-match, ambiguity and tenant-isolation tests in `packages/reality-core/tests/test_party_email_lookup.py`
- [x] T003 [US2] Add failing Party proposal/create/update/removal tests in `packages/reality-core/tests/test_party_email_lookup.py`

## Phase 2 — Model and service

- [x] T004 [US2] Add `PartyEmailAddress` and migration 0092 in `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0092_party_email_addresses.py`
- [x] T005 [US2] Extend Party validation, snapshots and atomic persistence in `packages/reality-core/src/reality/services/core.py`
- [x] T006 [US2] Extend Party application/MCP schemas in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`

## Phase 3 — Read path and catalogs

- [x] T007 [US1] Add exact email filtering and deterministic email serialization in `packages/reality-core/src/reality/services/core.py`
- [x] T008 [US1] Update model/resource/tenant catalogs and durable docs in `packages/reality-core/config/` and `docs/`
- [x] T009 Regenerate catalog reference, run migration/spec/lint/tests and record evidence in `specs/258-party-email-lookup/quickstart.md`

## Dependencies

T001 → T002/T003 → T004 → T005 → T006/T007 → T008 → T009. Tests precede implementation.
