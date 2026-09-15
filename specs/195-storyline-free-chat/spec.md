# Feature Specification: Free Play Chat with Recorded Evidence

**Branch**: `feat/storyline-free-chat` | **Created**: 2026-09-15
**Language**: English
**Status**: Owner requested implementation after reviewing the distinction between scripted Storyline and real LLM chat.

## Context and Intent

### Problem
Free Play shows an empty instruction panel. The scripted composer discards the
person's own message when switching modes. Scripted explanations cannot describe
arbitrary user actions.

### Scope
Embed the existing company chat in the same Storyline Sandbox. Preserve an own-words
message as an editable draft when entering Free Play. Show recorded tool evidence
under each assistant reply with What happened and allow inspection of confirmed
changes. Keep the normal proposal review/confirmation destinations and Storyline return.

### Non-Goals
No new agent, provider, business rules, automatic confirmation, workflow completion,
new schema or migration, AI-generated business authority, microphone implementation,
or deployment. Reuse existing voice input and normal chat retry/provider handling.

### Existing Contracts
[Chat](../../docs/features/chat.md), [Web](../../docs/WEB_SPEC.md),
[Storyline](../182-storyline-mode/spec.md), [company setup](../../docs/features/company-setup-demo.md).

## User Scenarios & Testing

### US1 — Speak freely in the Sandbox (P1)
An eligible person opens Free Play and chats with the existing company agent.
1. Entering Free Play reads only; no message, session or proposal is created automatically.
2. Own words from Storyline arrive unchanged in an editable draft; explicit Send
   dispatches through normal chat once. Returning to the story preserves its progress.
3. Provider failure, missing provider and exhausted allowance use existing chat behavior;
   no scripted successful outcome substitutes for a free-form request.
4. Tenant/session changes cannot leak drafts or associate another conversation's evidence.

### US2 — Explain the actual action (P1)
1. Expanding What happened on an assistant reply displays only calls recorded for
   that reply and subsequent decisions linked by the same proposal ID.
2. Reads and proposals never claim business execution. Confirmed calls expose the
   existing event/record/fact/finding delta, labeled as changes since the call
   which may include later Sandbox activity rather than exclusive causation. Refusals remain visible as refusals.
3. Reload preserves attribution. Concurrent replies and unrelated manual calls must
   not be attached by timestamps or ordinal ranges.
4. Missing/pruned evidence is explicitly unavailable, not proof nothing happened.

### Edge Cases
Concurrent chats, old messages without evidence, bounded trace pruning, empty recorded
calls, rejected/failed proposals, unmount during send, mobile scrolling, all four
languages/themes, foreign tenant/message IDs, missing AI configuration and quota exhaustion.

## Requirements
- **FR-001**: Free Play MUST reuse normal persistent company chat, tools and explicit confirmation.
- **FR-002**: Own-words handoff MUST preserve the draft without automatically sending it or putting it in a URL.
- **FR-003**: Per-reply evidence MUST use exact server-recorded call IDs and proposal IDs, remain tenant/owner-scoped and survive reload within existing retention.
- **FR-004**: What happened MUST expose real calls, refusals and existing confirmed deltas; missing evidence MUST be explicit.
- **FR-005**: Entry/return, mobile/desktop, light/dark, en/de/nl/es and existing failure/allowance handling MUST remain usable.
- **DR-001**: Shared services, Source → Evidence → Reality, tenant boundaries and shortest true links remain authoritative; no direct adapter writes or new schema.

## Success Criteria
All own-word handoffs retain exact text. Free chat uses the same provider/tool path
as company chat. Evidence never includes concurrent/unrelated calls. Tests prove
confirmation, isolation, missing evidence and responsive/localized behavior.

## Assumptions and Dependencies
The existing provider must be configured for arbitrary LLM chat. Existing ordinary
proposal review pages remain the confirmation surface. A handoff is an editable draft
and is sent only from the real chat. Trace retention remains bounded and may remove
old evidence. Existing history and AI allowance are reused.

## Open Questions
None; the owner explicitly approved this scope.

## Requirement Traceability
| Requirement | Evidence |
|---|---|
| FR-001–002, FR-005 | Frontend contracts and browser interaction tests |
| FR-003–004, DR-001 | Recorder/service/API attribution, isolation, proposal lifecycle and retention tests |

## Follow-up: composer focus
- **FR-006**: After an explicit send settles (success or failure), restore focus to
  the active chat input. Do not focus on initial load or steal focus from another
  control deliberately selected while waiting.
