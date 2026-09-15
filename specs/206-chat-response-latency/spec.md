# Feature Specification: Chat response latency

**Feature Branch**: `perf/chat-response-latency`
**Created**: 2026-09-15
**Status**: Scope approved by user instruction to implement the measured recommendations on latest main.
**Language**: English

## Context and Intent

### Problem
Four measured questions took 8.09–12.65 seconds; 98.65% of time was in provider requests. The interface hid all output until completion. Repeated static instructions were not cached and inventory reads issued 130 SQL statements.

### Scope
Incremental chat answers, reusable static provider context, lossless compact tool results, bounded history loading and batched inventory reads. Preserve existing capabilities and business meaning.

### Non-Goals
Changing models, public MCP schemas, business rules, schema/index expansion, durable background jobs, guaranteed provider latency, or automatic mutation execution. No heuristic tool removal or truncated evidence.

### Existing Contracts
- [Chat](../../docs/features/chat.md)
- [Web](../../docs/WEB_SPEC.md)
- [MCP reads](../../docs/features/mcp_reads.md)

## User Scenarios & Testing

### User Story 1 - See an answer while it is written (Priority: P1)
A person sends an operational question and reads incremental text while the answer is generated.
**Why this priority**: Remove the unexplained full-answer wait.
**Independent Test**: A delayed provider emits text; the browser displays it before completion.
**Acceptance Scenarios**:
1. Given an active conversation, when answer text arrives before completion, then it is displayed incrementally and the final recorded answer replaces the provisional text without duplication.
2. Given tool-use preamble text, when tools run, then provisional round text is reset and no tool argument JSON is shown as an answer.
3. Given a stream failure or disconnection, then incomplete text is not represented as a successfully recorded answer, no automatic resend occurs, and normal recovery remains available.
4. Given unauthorized or cross-tenant access, then no provider dispatch or content is exposed.

### User Story 2 - Avoid repeated work (Priority: P1)
Repeated operational questions reuse static provider instructions while reading current company records.
**Independent Test**: Capture provider requests, verify static cache markers and unchanged allowed tools; verify exact tool result round trips and the latest twelve persisted turns.
**Acceptance Scenarios**:
1. Given repeated provider rounds, then eligible static instructions are cacheable and tool schemas are built once per invocation.
2. Given a long conversation, then only the latest twelve turns are loaded for the provider in chronological order.
3. Given any currently registered read/propose capability, then it remains available under the same permission, security, locale and confirmation boundaries.

### User Story 3 - Keep inventory reads efficient at scale (Priority: P2)
Operational stock reads return the same values and evidence with bounded query counts as item count grows.
**Independent Test**: Compare batched output with canonical per-item reads across movements, reservations, revisions, cancellations and two tenants.
**Acceptance Scenarios**:
1. Given multiple items and incoming commitments, then stock, reservations, incoming and movement links match existing services without one SQL query per item or commitment.
2. Given another tenant's data, then none contributes to the result.

### Edge Cases
Empty and non-provider chat; provider rejection after partial text; incomplete SSE tool arguments; multiple tools; six-round exhaustion; stream truncation; user navigation during send; pending proposals after disconnection; allowance exhaustion; revised/cancelled incoming commitments; transfers and movement corrections.

## Requirements

### Functional Requirements
- **FR-001**: Show provider text progressively and replace provisional text with the persisted answer on completion, without requiring a chat reload to show it.
- **FR-002**: Preserve existing JSON clients and expose an opt-in stream with explicit start, round reset, text delta, completion and error semantics. Never retry a send automatically.
- **FR-003**: Execute only complete tool calls through existing services; keep all allowed capabilities, security policy, presentation, allowance and confirmation behavior.
- **FR-004**: Make static Anthropic tool/system prefixes cacheable, build schemas once per invocation and serialize results compactly without dropping or altering values/IDs/page metadata.
- **FR-005**: Load at most twelve persisted text turns for provider history, ordered deterministically and chronologically.
- **FR-006**: Batch inventory reads with query count independent of item and incoming commitment counts, preserving all current quantities and movement references.
- **FR-007**: Record provider-round/tool timing and token/cache counts in application logs without prompts, payloads, credentials or arguments.

### Domain and Traceability Requirements
- **DR-001**: Source → Evidence → Reality links and exact values are unchanged; no schema or new authority.
- **DR-002**: Tenant and confirmation boundaries are identical for JSON and streamed chat.
- **DR-003**: Interrupted provisional output never becomes a false completed message; completed service work remains recoverable through existing chat/proposal reads.

### Key Entities
Existing ChatSession, ChatMessage and proposals only. Stream events are transient presentation, not business records.

## Success Criteria
- **SC-001**: In a controlled delayed-provider test, visible text precedes completion and survives final reconciliation without duplication.
- **SC-002**: Every FR/DR has executable coverage and final gate evidence.
- **SC-003**: Inventory query count does not increase between one and twenty items; exact values remain equal to canonical reads.
- **SC-004**: Repeat the two original questions and record first text, full response, provider/tool time and cache usage; report observations without promising deterministic external timings.

## Assumptions and Dependencies
The latest origin/main is the implementation base. Existing configured providers are used. Anthropic supports explicit caching and SSE; compatible providers use standard Chat Completions SSE. Caching reduces repeated processing without removing capabilities; deferred tool search is excluded until independently measured. Tests precede implementation where practical. No background scheduler is added: streaming is request-scoped.

## Open Questions
None. The user authorized implementation of the measured recommendations and required latest main.

## Requirement Traceability
| Requirement | Scenario | Planned proof |
| --- | --- | --- |
| FR-001–002, DR-003 | US1.1–3 | Provider/HTTP stream tests; browser delayed stream test |
| FR-003, DR-002 | US1.4, US2.3 | Existing scope, allowance, proposal and tenant tests plus stream admission test |
| FR-004, FR-007 | US2.1 | Request capture, lossless result and redacted timing tests |
| FR-005 | US2.2 | Long-history service test |
| FR-006, DR-001 | US3.1–2 | Inventory parity/query-count test and existing business stories |
