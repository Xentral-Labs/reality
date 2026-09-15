# Implementation Plan: Delete Empty Chat Sessions

**Branch**: `feat/delete-empty-chat` | **Date**: 2026-09-15 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Derive session emptiness from tenant-scoped Chat Messages. The existing removal service deletes
only a message-free session and archives every other session. The Copilot projection exposes a
server-derived message count so Web can label and confirm the consequence without owning the rule.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: One session-removal service, one existing HTTP route, one projection field, and
one conversation-list action; no schema or migration.

## Constitution Check _(blocking gate)_

| Principle                          | Evidence in this plan                                                                                      | Result |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------ |
| Source → Evidence → Reality        | N/A: only a message-free UI container can be deleted; source, evidence, and Reality records are untouched. | PASS   |
| Reality owns operational state     | No Document or operational state changes.                                                                  | PASS   |
| Proven schema only                 | Message existence is derived; no flag, count column, or migration.                                         | PASS   |
| Tenant + shared service boundaries | Service queries both session and messages by tenant; API and Web reuse it.                                 | PASS   |
| Spec/test traceability             | FR-001–FR-007 map to service, API, and Web tests below.                                                    | PASS   |
| Explainable web behavior           | UI labels the server-projected consequence and does not infer from titles.                                 | PASS   |
| Received values not recomputed     | No received business values are involved.                                                                  | PASS   |
| Smallest coherent design           | Reuses DELETE and archive state; rejects a new endpoint or stored emptiness flag.                          | PASS   |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/       # pure rules, if needed
packages/reality-core/src/reality/services/     # application behavior
packages/reality-core/src/reality/tools/        # shared agent/CLI tools
packages/reality-core/src/reality/web/          # transport only
packages/reality-core/tests/                    # unit, service, story, adapter proof
apps/web/src/                     # presentation only
```

**Files/layers affected**:

- `packages/reality-core/src/reality/services/core.py`: tenant-scoped message counts and removal.
- `packages/reality-core/src/reality/web/api.py`: projection field; existing DELETE delegates.
- `packages/reality-core/tests/test_master_data_api.py`: business-story and tenant proofs.
- `apps/web/src/api.ts`: typed server projection.
- `apps/web/src/unified/ChatPage.tsx`: delete/archive labels and confirmations.
- `apps/web/src/localization.tsx`: translated destructive wording.
- `apps/web/scripts/chat-archive-contract.test.mjs`: presentation contract.

## Design

### Reality flow

No business flow is changed. ChatSession → ChatMessage is the shortest true relationship used to
derive whether conversational history exists. No source, evidence, or Reality row is deleted.

### Service and adapter flow

`remove_chat_session` loads the tenant-owned session, derives message existence through a
tenant-scoped query, deletes the session only when empty, and otherwise applies `archived_at`.
The existing DELETE route remains transport-only. Copilot list payloads carry `message_count`; Web
uses that field only to describe the action, while the service rechecks at mutation time.

### Data and migration impact

No schema change. ChatMessage already references ChatSession. A deletion runs only after proving
the absence of referencing messages, so no cascade or migration is introduced.

### Failure, security, and tenant behavior

Unknown and foreign-tenant sessions remain not found. A stale UI that showed delete while a
message arrived is safe because the service rechecks and archives instead. Repeating removal of a
deleted session is not found; repeating removal of a non-empty session remains idempotent archive.

## Test Strategy and Traceability

| Requirement                   | Test level                   | Planned test                                          | Expected initial failure                                     |
| ----------------------------- | ---------------------------- | ----------------------------------------------------- | ------------------------------------------------------------ |
| FR-001, FR-002, FR-005–FR-007 | API/business story           | `packages/reality-core/tests/test_master_data_api.py` | Existing empty-session call archives and remains restorable. |
| FR-003                        | API projection               | `packages/reality-core/tests/test_master_data_api.py` | Session payload omits server message count.                  |
| FR-004                        | Web contract                 | `apps/web/scripts/chat-archive-contract.test.mjs`     | Every active row currently says archive.                     |
| DR-001–DR-004                 | Service/API review and tests | Same tests plus `make spec-check`                     | Existing alias maps delete directly to archive.              |

## Rollout and Rollback

Deploy backend before or with Web. Existing DELETE callers remain compatible with HTTP 204 and
gain safe empty cleanup. Rollback restores archive-only behavior; deleted empty containers contain
no messages to recover. No migration or data backfill exists.

## Review Risks

- A message created concurrently after the list read must force archive, never deletion.
- Message counts must remain tenant-scoped and must not introduce per-row query growth.
- UI wording must not become the authority for deletion eligibility.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| ---------------------- | ---------- | ---------------------------- | -------- |
| None                   | —          | —                            | —        |
