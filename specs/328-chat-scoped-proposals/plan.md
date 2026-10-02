# Implementation Plan: Chat-Scoped Proposals

## Technical Context
Existing Python 3.12 services, SQLAlchemy 2, Alembic, PostgreSQL, React/TypeScript and four-language
dictionaries. One additive nullable column on `action` (Change Proposal). No new dependency.

## Constitution Check
| Principle | Result | Reason |
|---|---|---|
| Source/evidence and operational authority | PASS | No business authority changes; the link records where a proposal was made. |
| Proven schema and storage discipline | PASS | One nullable tenant-scoped reference with a named use case (FR-001, FR-003); placement and counts are read-time. |
| Shortest true link | PASS | Proposal → Chat Session. No message link, no reverse link, no duplicated FKs. |
| Tenant/service boundaries | PASS | Composite FK `(tenant_id, chat_session_id)`; reads filter by tenant and session in the service layer. |
| Chat/CLI parity | PASS | The link is set inside `create_change_proposal`, the one shared creation path; CLI and MCP pass no session. |
| Specification and executable evidence | PASS | Approved scope; service/API tests before code; browser proof. |
| Explainable Web | PASS | Settled proposals keep their decision line linking to the decision. |
| Received values | PASS | Nothing recomputed or stored as derived authority. |
Post-design check: PASS. No constitutional exception.

## Research and Design
See research.md.

- **Carrying the session**: a `ContextVar` `CHAT_SESSION` in `tools/application.py`, set by `send_chat_message`
  for the whole turn (try/finally), read by `create_change_proposal`. This covers the model-backed providers (tool
  calls run synchronously inside `asyncio.run`, which copies the context) and the deterministic local provider.
  It follows the existing `decision_channel` pattern in `mcp/catalog.py`.
- **Column**: `action.chat_session_id` nullable, composite FK to `chat_session(tenant_id, id)`, index
  `(tenant_id, chat_session_id)`. Declared `server_default=FetchedValue(), deferred=True` with
  `eager_defaults False`, so historical-schema tests that insert proposals keep working (spec 299 trap).
- **Turn timing**: the user message gets `created_at=now()` at construction, which is when it was sent.
  The assistant message keeps its insert time. A proposal made during the turn then lies between both.
- **Reads** (`services/core.py`): `chat_proposals(session, tenant_id, session_id)` returns the session's proposals
  in every state, oldest first; `pending_proposals_elsewhere(session, tenant_id, session_id)` counts pending ones
  with another or no session. `proposal_anchor(messages, proposal)` derives the message a proposal follows.
- **Payload** (`web/api.py` `copilots_payload`): `proposals` becomes the session's proposals for active and archived
  sessions, each with `after_message_id` and decider attribution; new `pending_elsewhere` count.
- **Removal**: `remove_chat_session` archives instead of deleting when the session holds a proposal.
- **Web** (`ChatPage.tsx`): render each proposal after its anchor message (end of list when none). Pending ones keep
  the review button (`ChatDecisionList` entry, one card per proposal) or `GraphReportProposal`. Settled ones show a
  `DecisionLine`. A compact `pending_elsewhere` link in `chatControls` opens Decisions → Pending approvals.

## Tests Before Implementation
- Service: chat turn on the local provider links the proposal; outside a turn no link; MCP/`create_change_proposal`
  without context has none; session A/B isolation; settled proposals stay; archived session returns them; legacy
  null proposals appear nowhere; elsewhere count excludes the session's own; anchor placement over three turns;
  removing an otherwise empty session with a proposal archives it; foreign tenant session refused.
- Model-backed path: a fake provider tool call creating a proposal records the session (existing fake-provider
  test seam in chat tests).
- Schema: migration up/down; FK index gate; historical migration suites stay green.
- Web: browser proof for placement, outcome after approve/reject, empty new chat, hint navigation; i18n audit.

## Execution and Verification
Migration + model → service reads and context → payload → web → docs/translations. Run the chat, proposal,
decision, migration, finance-history, isolation-catalog and schema-index suites, then CI. Regenerate docs.

## Rollback and Risks
Downgrade drops the column; nothing else depends on it. Risk: browser scripts that expected non-chat proposals in
the chat list; their fixtures move to Decisions or to chat-created proposals. Risk: contextvar leaking beyond the
turn; reset in `finally`, tested.
