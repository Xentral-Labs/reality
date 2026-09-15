# Feature Specification: Reality chat scope and instruction boundaries
**Language**: English

**Created**: 2026-09-15
**Status**: Accepted scope — user requested implementation after security review.
## Context and Intent
Keep the company assistant focused on Reality and supported business workflows.
### Non-Goals
Absolute prompt-injection immunity, a general-purpose content moderation service,
new permissions, schema changes, or a claim that simulated model tests prove live behavior.
## User Scenarios & Testing
### US1 — Focused assistance (P1)
Reality operation, product help and supported order/inventory/finance questions are
in scope. Unrelated entertainment, politics, homework and general coding requests
receive a brief redirect, even when wrapped in role-play or “for Reality” language.
Mixed requests answer only the relevant part. Ambiguous requests ask one clarification.
### US2 — Untrusted context (P1)
An imported document, tool result, old answer or user message cannot grant privileges,
switch the tenant, approve changes, reveal private instructions/secrets or initiate
unrequested data collection. Business text remains lossless data, including quotations.
## Requirements
- **FR-001**: Both provider adapters use the same server-owned scope/security policy.
  Refuse unrelated tasks briefly in the selected language without unnecessary tool calls.
- **FR-002**: Treat conversation, attachments, source fields and tool results as data,
  never higher-priority instructions; ignore role spoofing, encoded instructions,
  approval claims, secret requests and attempts to broaden tool/tenant authority.
- **FR-003**: Accept only textual user/assistant history entries at the provider boundary;
  reject system/developer/tool roles and structured blocks before any provider request.
- **FR-004**: Retain server-owned tenant context and read/propose access. Confirmation
  tools remain unavailable even if an injected model response explicitly calls them.
  Read-only companion policy is identical for both providers.
- **FR-005**: Add deterministic adversarial provider-adapter tests for both adapters,
  including forged roles, hostile tool outputs, confirmation attempts and scope
  policy delivery. Document the distinction from real-model behavioral evaluation.
## Success Criteria
Every adapter regression passes. Invalid history sends no provider request. Attempted
model-side confirmation cannot reach its handler. The policy reaches both adapters
unchanged after hostile user/tool content. Existing chat and confirmation tests pass.
## Assumptions and Dependencies
The scope boundary is an instruction to a probabilistic model, not an authorization
control. Tool access and tenant enforcement remain the authority. No new provider
call or extra quota charge per turn. Legitimate Reality business analysis stays allowed.
## Requirement Traceability
FR-001–005: tests/test_chat_scope_security.py; existing test_anthropic_copilot,
test_ai_mcp, test_playground_security and test_chat_confirmation.
