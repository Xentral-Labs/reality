# Implementation Plan

Python 3.12+, PostgreSQL, SQLAlchemy, FastAPI and existing React/TypeScript.

## Constitution Check
| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Reuse existing tool recorder and deltas |
| Reality operational authority | PASS | No generated authority or document statuses |
| Proven schema | PASS | Existing bounded trace JSON stores a reply-to-call association |
| Tenant/shared services | PASS | Existing chat service and owner-scoped Storyline read |
| Test traceability | PASS | Tests first for exact attribution and handoff |
| Explainability | PASS | Real per-call evidence and proposal-linked decisions |
| Received values | PASS | No new calculations or copied source authorities |
| Simplicity | PASS | Reuse ChatPage, composer and StorylineProtocol |

## Design
Decorate the shared send_chat_message service with a request-local ContextVar collector.
Record IDs emitted by recorder.record for this invocation; persist one internal
chat.reply association in the existing trace with the assistant message ID and bounded
call IDs. It is explanation metadata, hidden from the normal call list. No prompt,
credential, alternate business fact or duplicate conversation is stored there.
A read-only storyline chat-evidence endpoint validates run owner and same-tenant
assistant message, finds the association and reads exact call IDs plus later calls
linked to their proposal IDs. Pruned/missing associations report unavailable.
Existing deltaAt remains the confirmed-effect reader. No timestamp attribution.

ChatPage gains optional initial draft and per-message rendering slot. Storyline passes
own words into local Player draft state and mounts ChatPage keyed by tenant/run in
Free Play; reads do not auto-send. A lazy What happened disclosure uses the new read
and existing protocol/delta renderer. Proposal review continues through ordinary pages.
Free-play global protocol keeps its existing polling; chat evidence refreshes on
shared settlement events and opening the disclosure. Drafts stay out of URLs/storage.

## Paths and dependency order
Recorder and core service → storyline evidence service → thin HTTP adapter → API
client and reusable ChatPage → Storyline integration and localized evidence component.

## Tests and verification
Focused PostgreSQL recorder/service/API tests for distinct concurrent scopes, exact
reply/decision association, missing/pruned evidence, foreign message/tenant and
unchanged confirmation. Frontend contracts plus browser tests of explicit draft
handoff, real send, persistent history, evidence disclosure and responsive layouts.
Full backend suite, lint, spec policy, web tests/audit/build and docs generation/build.

## Rollout and rollback
No migration. Additive read endpoint; existing chats continue unchanged. Revert UI and
decorator to roll back; historical association rows are inert within existing retention.
No deployment included. Risk: mistaken association; mitigate by IDs and scope reset,
never elapsed-time windows. Trace failure must not cause a successful chat to be resent.
