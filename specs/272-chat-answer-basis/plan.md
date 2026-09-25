# Implementation Plan: Compact Chat Answer Basis

**Branch**: `272-chat-answer-basis` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Capture successful canonical chat reads in the existing request-local chat scope, store one bounded JSON snapshot on the assistant `ChatMessage`, and expose it through the existing per-message evidence read. A service presenter converts known fulfillment result shapes into compact business rows and record references; the browser renders those rows under "Basis for this answer" and hides the control when no basis exists. Existing Storyline trace rows remain an optional secondary explanation for eligible runs.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React for the web adapter
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, FastAPI, React/Vite
**Storage**: PostgreSQL JSONB on the existing tenant-scoped `chat_message`
**Testing**: pytest PostgreSQL service/API tests; Node contract tests; Vite build and localization audit
**Project Type**: backend services/API plus independent frontend
**Constraints**: bounded snapshots; tenant scope; opaque navigation identity; no model-authored citations; no browser business rules
**Scale/Scope**: at most six read rounds per reply, at most four primary presentation rows, bounded stored JSON

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Returned document/commitment IDs are preserved as shortest links; existing detail routes lead onward to source payloads. | PASS |
| Reality owns operational state | Snapshots copy read results only; no Document status or derived business record is added. | PASS |
| Proven schema only | One nullable bounded snapshot is required for exact attribution outside Storylines and is read for every supported reply explanation. | PASS |
| Tenant + shared service boundaries | Canonical tool wrappers capture reads; the tenant-scoped service validates the assistant message before returning support. | PASS |
| Spec/test traceability | FR-001–013 map to focused service/API/UI/migration tests before implementation tasks. | PASS |
| Explainable web behavior | Compact support rows expose values, opaque record links, and explicit derivation labels. | PASS |
| Received values not recomputed | Stored values are the exact bounded tool result; any subtraction/status wording is a read-time observation and never stored as authority. | PASS |
| Smallest coherent design | A nullable field avoids a second lifecycle/table; model citations and Storyline-only reuse cannot meet exact ordinary-company attribution. | PASS |

Post-design review: all rows remain PASS. There is no constitutional exception.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0097_chat_answer_basis.py
packages/reality-core/src/reality/db/core.py
packages/reality-core/src/reality/storyline/recorder.py
packages/reality-core/src/reality/services/storyline.py
packages/reality-core/src/reality/web/storyline_api.py
packages/reality-core/tests/test_storyline_trace.py
packages/reality-core/tests/test_http_boundary.py
apps/web/src/api.ts
apps/web/src/unified/StorylineChatEvidence.tsx
apps/web/src/localization.tsx
apps/web/scripts/chat-answer-basis.test.mjs
docs/WEB_SPEC.md
```

**Dependency direction**: canonical tool wrapper → request-local capture → assistant message snapshot → tenant-scoped service read → API → React presentation. The web adapter receives ready-to-render business rows and does not interpret operational rules.

## Design

### Reality flow

The answer basis stores what a canonical read returned: for the open-order scenario this includes Document identity/number, Commitment identity, requested/open/reserved/shortage quantities, readiness, and blocker codes. The presentation links the Document or Commitment by opaque ID. Existing Inspector relationships provide DocumentLine and SourceRecord traversal. A label such as "Derived: 10 units uncovered → blocked" remains an observation over the recorded snapshot, not a Fact or status field.

### Service and adapter flow

`wrap_chat` always opens a `chat_call_scope`, even without an eligible Storyline. `wrap_read` appends the bounded successful operation/input/result to that scope after the canonical handler returns; errors are excluded from answer support. After `send_chat_message` persists its assistant reply, `wrap_chat` attaches the bounded call list and commits without retrying the chat. When a Storyline target exists, the current exact trace-ID association is recorded as before.

`chat_evidence` first validates tenant, role, and message identity. It presents the stored answer basis into compact rows and references. It separately reads legacy Storyline association rows when an eligible run exists. The endpoint remains read-only and backward compatible by retaining `available`, `items`, and `has_more` while adding `basis`.

### Data and migration impact

Add nullable `answer_basis` JSONB to `chat_message`, with a database byte-size check matching the bounded service contract. Existing rows remain null; no backfill. The JSON holds a version and ordered calls, not foreign keys or business authority. Downgrade removes the check and column. Rolling application rollback ignores the nullable column; migration rollback is safe after the application stops writing it.

### Failure, security, and tenant behavior

Snapshot attachment is best-effort: serialization or commit failure is logged and rolled back without rerunning the already completed provider turn. Every read selects `ChatMessage` with tenant and assistant role. Record links are emitted only from allowlisted returned ID fields and existing route mappings; unknown shapes remain unlinked. No client-supplied record identity is accepted by the evidence read.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–002, FR-012 | PostgreSQL service | ordinary company read calls persist exact bounded basis and survive reload; old row stays null | wrapper currently returns early without Storyline |
| FR-003 | API/security | foreign, user, and unknown message requests are 404 | current reader requires a Storyline run before message lookup |
| FR-004 | service | forced basis persistence failure returns one saved assistant reply | no independent basis persistence path exists |
| FR-005–008, FR-010 | service + web contract | fulfillment queue becomes ≤4 business rows; empty basis hides disclosure | UI renders technical trace/unavailable copy |
| FR-009 | regression | Storyline items and proposal-linked rows remain returned | response contract lacks separate basis |
| FR-011 | localization/build | four-language keys and responsive markup pass audit/build | new copy/markup absent |
| FR-013 | spec/docs | spec and durable Web contract mention compact basis | durable contract lacks behavior |

Tests are added and observed failing before their implementation where practical.

## Rollout and Rollback

Apply migration before application deployment. New code reads null safely for historical messages. Roll back the UI/service first, then drop the nullable column if required. No business records, SourceRecords, Documents, Facts, Commitments, Reservations, Movements, or LedgerEntries are modified.

## Review Risks

- A generic result presenter could accidentally invent semantics; only explicitly recognized shapes may create labels or derivations.
- A post-reply persistence failure must not cause provider retry or duplicate chat content.
- Existing uncommitted provider-schema changes in `mcp_chat.py`, `streaming.py`, and their tests must remain untouched.
- The current evidence endpoint assumes an eligible Storyline before reading a message; tenant validation must be separated from optional legacy trace lookup.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
