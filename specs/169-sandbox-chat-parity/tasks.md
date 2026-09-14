# Tasks: The Copilot works the same in Sandbox companies

**Input**: [spec.md](spec.md), [plan.md](plan.md)
**Gate**: Constitution Check passed; no clarification markers

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Phase 1: Failing proof

- [x] T001 [US1] [FR-001] [FR-002] Add `tests/test_playground_chat.py::test_practice_company_copilot_is_admitted`: provider call admitted in a practice company, tool access read and propose, chat reply is the provider's text
- [x] T002 [US2] [FR-004] Add `tests/test_playground_chat.py::test_refused_copilot_explains_itself`: a lesson-run tenant is refused and the reply names the reason

## Phase 2: Implementation

- [x] T003 [FR-001] Add `generic_provider_call` to `_PRACTICE_APP_OPERATIONS` in `packages/reality-core/src/reality/services/tenant_policy.py`
- [x] T004 [FR-004] Catch `PlaygroundOperationDenied` in `packages/reality-core/src/reality/services/core.py::send_chat_message` with the explanatory reply
- [x] T005 [FR-003] Keep `test_companion_scope_is_read_only`, `test_provider_cannot_dispatch_mutations` and `test_generic_provider_egress_cannot_bypass_settings` green

## Phase 2b: Finance reads for the copilot

- [x] T008 [US3] [FR-005] [FR-006] Add `tests/finance/test_credit_reads.py`: available credit and payments reads return original/used/available and allocated/unallocated, and are tenant-scoped
- [x] T009 [FR-005] [FR-006] Add `finance.credits.list` and `finance.payments.list` read tools in `packages/reality-core/src/reality/tools/application.py`, the MCP definitions `finance_credits` and `finance_payments` in `mcp/catalog.py`, their capability guidance in `config/command_catalog.yaml` and the `agent_credit_reads` boundary family in `config/tenant_isolation_catalog.yaml`
- [x] T010 Regenerate the MCP tool reference pages of the docs site

## Phase 3: Documentation and review

- [x] T006 Add the practice-company section to `docs/features/chat.md`
- [ ] T007 Run `make lint`, `make spec-check`, the chat, playground and security suites, then the complete backend suite

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T001 | T003 | Done |
| FR-002 | T001 | T003 | Done |
| FR-003 | T005 | T003 | Done |
| FR-004 | T002 | T004 | Done |
| FR-005 | T008 | T009, T010 | Done |
| FR-006 | T008 | T009, T010 | Done |
| DR-001–DR-003 | T001, T002, T008 | T003, T009 | Done |
