# Implementation Plan: Human Chat Confirmation

**Branch**: `278-human-chat-confirmation` | **Date**: 2026-09-26 | **Spec**: [spec.md](./spec.md)

## Summary

Change only the built-in Chat model capability boundary: production Chat receives `read` and
`propose`, while Playground Chat remains `read` only. Proposal settlement tools and aliases are
absent from the model schema and refused by dispatch if attempted. Existing authenticated Web
review continues to confirm or reject through the canonical application service. Correct the
server-owned Chat prompt so it describes human handoff instead of model self-confirmation.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: existing agent provider adapters, MCP catalog and application tools
**Storage**: PostgreSQL, unchanged
**Testing**: pytest unit, adapter and security tests; focused Web review regression
**Project Type**: backend application service and browser Chat adapter
**Constraints**: opaque IDs; strict tenant scope; model calls are untrusted; no new authority
**Scale/Scope**: one Chat access-policy change, one prompt correction and regression coverage; no schema, migration or frontend redesign

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Proposals and effects keep existing identities, events and evidence links; only decision authority changes. | PASS |
| Reality owns operational state | No Document status or copied readiness state is introduced. | PASS |
| Proven schema only | No schema change is required. | PASS |
| Tenant + shared service boundaries | Web review still calls the shared approval service; Chat receives a narrower server-selected access tuple. | PASS |
| Spec/test traceability | Every FR/DR maps to catalog, provider, security or review regression tests below. | PASS |
| Explainable web behavior | The existing spec 276 decision card and review remain the human handoff. | PASS |
| Received values not recomputed | No received or derived business value changes. | PASS |
| Smallest coherent design | Narrowing access and correcting the prompt avoids another confirmation credential or workflow. | PASS |

Planning may continue: every blocking gate passes and no clarification remains.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/agent/mcp_chat.py
packages/reality-core/tests/test_mcp_chat.py
packages/reality-core/tests/test_chat_scope_security.py
packages/reality-core/tests/test_chat_master_data.py
packages/reality-core/tests/test_chat_mcp_orders.py
packages/reality-core/tests/test_playground_chat.py
specs/278-human-chat-confirmation/
```

**Files/layers affected**: the provider adapter selects built-in Chat access and owns server
handoff wording. The MCP catalog and application decision tools remain unchanged so external MCP
and Web review retain their contracts. Focused tests prove omitted model tools, pending proposals,
untrusted tool-name refusal and unchanged human review.

## Design

### Reality flow

```text
Chat reads Source/Evidence/Reality
  → Chat prepares ChangeProposal (proposed, no target effect)
  → authenticated human opens canonical review
  → human confirms or rejects the exact current proposal
  → shared service records attribution and optional BusinessEvent/effect
```

No model output becomes evidence or authority. The proposal is the durable agent-to-human handoff.

### Service and adapter flow

1. The built-in adapter selects `("read", "propose")` for ordinary companies and `("read",)` for Playground.
2. `model_tool_schemas` exposes only tools allowed by that tuple; settlement requires `confirm`.
3. `_call_tool` and `dispatch_tool` enforce the same tuple, blocking unoffered calls.
4. The prompt tells the model to prepare, inspect and hand off, never to decide.
5. Web review retains authenticated principal, review token and canonical approval service.

### Data and migration impact

No schema, migration, backfill or new field. Existing pending proposals remain confirmable.
Rollback is a code revert and needs no data work.

### Failure, security, and tenant behavior

- Conversation, history, source payload and provider output cannot widen server access.
- An unoffered decision call is refused before application execution.
- Tenant-scoped proposal reads and human decisions remain unchanged.
- Human review keeps owner/principal, stale-review, idempotency and reconciliation enforcement.
- External MCP access tokens keep their independent permission boundary.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003, FR-008 | unit/security | Update `test_mcp_chat.py` and `test_chat_scope_security.py` to require read/propose without settlement tools and refuse tool-shaped prompts | Production Chat currently exposes `confirm` |
| FR-004–FR-005 | provider adapter | Provider transcript prepares a proposal and returns human-review handoff | Current prompt instructs self-confirmation |
| FR-006–FR-007 | service/Web regression | Chat-origin proposal confirmation/rejection with human attribution | Narrowing access could accidentally block Web review |
| FR-009 | adapter regression | Playground and external MCP permission assertions | Existing tests expect practice Chat confirmation |
| FR-010–FR-011 | business adapter | Preserve read/propose coverage and verify pending multi-step handoff | Current fixtures script self-confirmation |
| FR-012 | documentation gate | `make docs-catalog-check`, with no generated diff expected | Public catalog must not change |
| DR-001–DR-004 | service/security | Pending status, zero pre-review effects, tenant isolation and interaction audit | Existing fixtures expect agent decisions |

Tests change first and are observed failing where practical.

## Rollout and Rollback

Application-code-only deploy. Pending proposals remain usable. Existing interaction records expose
refused Chat decision attempts for monitoring. Rollback is a code revert with no cleanup.

## Review Risks

- Compatibility aliases might expose settlement unless tests enumerate canonical and alias names.
- Prompt-only protection is insufficient; catalog and dispatch access are the authority.
- Tests intentionally encoding self-confirmation need correction without weakening external MCP.
- Provider attempts of unoffered tools must remain zero-effect.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-design Constitution Check

All rows remain PASS. No schema, service fork or browser business rule is added.
