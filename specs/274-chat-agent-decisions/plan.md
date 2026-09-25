# Implementation Plan: Chat Agent Decisions

**Branch**: `274-chat-agent-decisions` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

## Summary

Give ordinary Chat the existing `confirm` tool class, replace human-only guidance with a decision-first rule, and durably attribute settlement to the Chat agent. The existing proposal executor remains the only execution path and retains tenant, replay, review and operation-specific authority checks. Playground Chat remains read-only.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, httpx provider adapters
**Storage**: PostgreSQL; one nullable decision-attribution column
**Testing**: pytest unit/service/PostgreSQL stories/provider adapters; migration, catalog and docs gates
**Project Type**: shared core with Chat, MCP, API and Web adapters
**Constraints**: UTC, opaque IDs, tenant scope, proposal-before-execution, truthful attribution
**Scale/Scope**: Two lifecycle tools in ordinary Chat; no new business tool or UI

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Control records change only; executed tools retain existing evidence links. | PASS |
| Reality owns operational state | Only the existing proposal executor and services mutate Reality. | PASS |
| Proven schema only | History must retain Chat settlement after seven-day Interaction telemetry expires; one nullable closed-vocabulary field is the smallest durable fact. | PASS |
| Tenant + shared service boundaries | Chat dispatches the canonical catalog tool; executor tenant and role checks remain authoritative. | PASS |
| Spec/test traceability | Every requirement maps to tests below. | PASS |
| Explainable web behavior | Existing decision reads gain truthful `chat_agent` attribution. | PASS |
| Received values not recomputed | No source-stated business value changes. | PASS |
| Smallest coherent design | Existing tools, executor, recorder and attribution read are reused. | PASS |

Post-design re-check: all rows remain PASS. The new field records an observed channel, not business authority, and needs no backfill.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0098_chat_agent_decisions.py
packages/reality-core/src/reality/db/core.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/src/reality/agent/mcp_chat.py
packages/reality-core/src/reality/services/decision_attribution.py
packages/reality-core/config/command_catalog.yaml
packages/reality-core/tests/
docs/features/chat.md
apps/docs/content/tool-usage/
apps/docs/.vitepress/data/tool-usage.json
```

Persistence records settlement channel; application execution sets it; shared attribution reads it; Chat exposes the existing lifecycle tools. Generated docs follow catalog wording.

## Design

### Reality flow

The agent calls a proposal tool, persisting exact input and returning an opaque ID without business effect. A later Chat call invokes the existing approve or reject tool. The executor settles that proposal, records `decided_at` plus `decided_via_channel=chat`, and writes the same Action-linked events as other paths.

### Service and adapter flow

Both provider adapters offer `("read", "propose", "confirm")` for ordinary Chat and `("read",)` for read-only Playground. Chat supplies settlement channel through server-owned context, never model arguments. MCP retains token context; Web retains signed-in principal. The prompt permits a separate exact decision call and rejects authority inferred from untrusted text. Protected operations still require their existing person/owner principal.

### Data and migration impact

Add nullable `ChangeProposal.decided_via_channel`, constrained to `chat`. Person decisions use `decided_by_user_id`; MCP uses `decided_via_token_id`; Chat uses the new channel. Existing rows remain null. Downgrade drops constraint and column; no backfill.

### Failure, security, and tenant behavior

Foreign, rejected, stale or executing proposals retain existing behavior. `approved=true` is the agent's explicit decision, not a claim of human approval. Protected operations retain principal/review checks. Failed execution must not leave false Chat attribution.

## Test Strategy and Traceability

| Requirement | Test level | Planned proof | Initial failure |
|---|---|---|---|
| FR-001-FR-004, FR-012 | provider | Chat schemas, prompt and two-call loops in both adapters | Confirm absent/forbidden |
| FR-002-FR-003, FR-007, FR-010 | PostgreSQL story | Proposal → unchanged → confirm → one effect; replay/refusal | Chat rejects confirm |
| FR-005, FR-008-FR-009 | security | Injection, protected operations, Playground | Existing blanket refusal |
| FR-006, FR-011, DR-003-DR-005 | service/integration | Chat/person/MCP/unknown attribution and interaction correlation | No durable Chat mode |
| Schema | migration | Upgrade/downgrade/check/legacy null | Column absent |
| Catalog/docs | contract | Catalog validation and generated-doc check | Human-only wording |

Tests are changed before implementation and observed failing where practical.

## Rollout and Rollback

Apply the additive migration before code writes the value. Older code ignores it. Roll back Chat confirm access before dropping the column. Downgrade loses only the Chat attribution label, not decisions, receipts or events.

## Review Risks

- Broad language must not become bulk approval; decisions remain exact by ID.
- Passing the browser principal would fabricate personal approval.
- Expiring telemetry cannot own durable attribution.
- Generic confirm access must not bypass protected principals or reviews.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
