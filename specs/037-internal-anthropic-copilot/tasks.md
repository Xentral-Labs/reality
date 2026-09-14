# Tasks: Internal Anthropic Copilot

**Input**: Design documents from `/specs/037-internal-anthropic-copilot/`

## Phase 1: Setup

- [x] T001 Record server environment configuration in `.env.example` and `compose.yml`

## Phase 2: Foundational tests

- [x] T002 [P] [US1] Add failing Anthropic request/tool-loop tests in `packages/reality-core/tests/test_anthropic_copilot.py`
- [x] T003 [P] [US2] Add failing managed-settings API and UI contract tests in `packages/reality-core/tests/test_master_data_api.py` and `apps/web/scripts/ux-configuration-contract.test.mjs`

## Phase 3: User Story 1 - Use the Managed Copilot (P1)

- [x] T004 [US1] Implement Anthropic Messages tool adaptation in `packages/reality-core/src/reality/agent/mcp_chat.py`
- [x] T005 [US1] Select the managed environment-backed provider in `packages/reality-core/src/reality/services/core.py`

## Phase 4: User Story 2 - See Simple Copilot Settings (P2)

- [x] T006 [US2] Return managed Copilot availability without model or secret metadata in `packages/reality-core/src/reality/web/api.py` and `apps/web/src/api.ts`
- [x] T007 [US2] Replace editable provider controls with managed status in `apps/web/src/App.tsx`

## Phase 5: Documentation and verification

- [x] T008 [P] Update `docs/WEB_SPEC.md` and `apps/docs/content/reference/environment.md`
- [x] T009 Run targeted tests and required repository gates from `specs/037-internal-anthropic-copilot/quickstart.md`

## Phase 6: User Story 2 refinement - Optional company key (P2)

- [x] T010 [US2] Add failing credential-mode API, vault lifecycle, runtime precedence, and UI tests in `packages/reality-core/tests/test_ai_mcp.py`, `packages/reality-core/tests/test_chat_confirmation.py`, `packages/reality-core/tests/test_master_data_api.py`, and `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T011 [US2] Support Anthropic tenant credentials through the existing vault in `packages/reality-core/src/reality/agent/settings.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T012 [US2] Resolve an explicit tenant Anthropic key before the managed deployment key in `packages/reality-core/src/reality/services/core.py`
- [x] T013 [US2] Add preselected managed and optional company-key controls in `apps/web/src/App.tsx` and `apps/web/src/api.ts`
- [x] T014 [US2] Update behavior and environment documentation in `docs/WEB_SPEC.md` and `specs/037-internal-anthropic-copilot/quickstart.md`
- [x] T015 Run targeted tests and required repository gates after the refinement

## Phase 7: Multi-provider refinement (P2)

- [x] T016 Add curated provider and layout contract tests in `packages/reality-core/tests/test_master_data_api.py` and `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T017 Add Anthropic and OpenAI-compatible runtime selection in `packages/reality-core/src/reality/services/core.py`
- [x] T018 Add managed, Anthropic, OpenAI, Gemini, Mistral, Groq, OpenRouter, and custom presets in `packages/reality-core/src/reality/agent/settings.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T019 Replace radio controls with shared provider/model/key fields in `apps/web/src/App.tsx` and `apps/web/src/api.ts`
- [x] T020 Update multi-provider documentation and run all required gates

## Phase 8: Tailwind form-system regression fix (P2)

- [x] T021 Add a failing UI contract proving the Copilot form uses defined Tailwind primitives and no legacy `settings-form` class in `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T022 Define the shared Tailwind form primitives, migrate the Copilot markup in `apps/web/src/tailwind.css` and `apps/web/src/App.tsx`, and run the required frontend gates

## Phase 9: Copilot settings save regression (P2)

- [x] T023 Add a failing UI regression contract proving a partial save response cannot replace the complete Copilot configuration in `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T024 Reload the canonical complete configuration after save without applying partial response state in `apps/web/src/App.tsx`, then rebuild and restart Product Web

## Phase 10: Identity-linked Anthropic credential support (P1)

- [x] T025 Add a failing adapter regression test for the optional `anthropic-workspace-id` header in `packages/reality-core/tests/test_anthropic_copilot.py`
- [x] T026 Forward `ANTHROPIC_WORKSPACE_ID` through deployment configuration and the managed Anthropic adapter, update environment documentation, run required gates, and restart the API

## Phase 11: Bounded Copilot conversation layout (P2)

- [x] T027 Add a failing responsive contract proving the composer remains in the bounded conversation grid in `apps/web/scripts/ux-responsive-contract.test.mjs`
- [x] T028 Constrain the conversation grid and message scrolling in `apps/web/src/chat.css`, run frontend gates, and restart Product Web

## Phase 12: Readable and responsive Copilot answers (P2)

- [x] T029 Add failing UI contracts for safe Markdown rendering and an accessible assistant loading state in `apps/web/scripts/ux-operational-contract.test.mjs`
- [x] T030 Render assistant Markdown safely and show a scoped waiting indicator in `apps/web/src/App.tsx` and `apps/web/src/chat.css`, then run frontend gates and restart Product Web

## Phase 13: Optimistic user-message display (P2)

- [x] T031 Add a failing UI contract proving a submitted question appears before the assistant loading indicator in `apps/web/scripts/ux-operational-contract.test.mjs`
- [x] T032 Render the pending user question optimistically until the canonical conversation reload completes in `apps/web/src/App.tsx`, then run frontend gates and update the pull request

## Dependencies

T002 and T003 follow T001 and precede their implementation tasks. T004 precedes T005. T006 precedes T007. T008 follows stable runtime and UI behavior. T009 is last.

## Implementation Strategy

Deliver US1 first as the runnable managed provider, then simplify the settings surface in US2.
