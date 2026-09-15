# Feature Specification: Independent Free Play and Recorded Chat Evidence

**Branch**: `feat/storyline-free-chat` | **Created**: 2026-09-15
**Language**: English
**Status**: Owner requested a separate Free Play entry with existing-company selection or new Sandbox creation.

## Context and Intent
Free Play is an alternative to a guided Storyline. It must not require a story or
appear as an action repeated on each story. People need a real company agent in a
selected company or persistent private Sandbox, with actual evidence where recorded.

## Scope
One standalone Free Play entry in navigation and the exploration library, leading to
`/app/free-play`. The entry defaults to the current company and lists accessible companies and Sandboxes.
Opening one is read-only. Alternatively, explicit creation uses the canonical static
international demo profile in a dedicated practice Sandbox. Chat URLs retain the selected
company on reload. Use ordinary
company chat, tools, proposal confirmation and per-reply What happened evidence.

Existing contextual chat in a Storyline Sandbox remains compatible and is labeled
Sandbox chat. Own words entered in a scripted narrator retain their editable draft
there. It is distinct from the independent Free Play entry and its separate data.

## Non-Goals
No new model/provider, business rules, automatic confirmation, schema migration,
automatic live simulation, microphone implementation, production deployment or reset
of existing Storyline/company data. No migration of old conversations into Free Play.

## User Scenarios & Testing
### US1 — Explore freely (P1)
1. Choose Free Play separately from guided Storylines. No card contains a Free Play action.
2. Opening the entry only reads and offers accessible companies, defaulting to the current
   company. Open the selected company without creating or seeding anything. Real companies
   are labeled as using real data. Explicit Create Sandbox and start confirms creation
   with sample data, without creating a Storyline or prescribed steps.
3. Reload of an opened chat resumes its selected company and persistent chat; no duplicate
   company or message. Initialization retry reuses the durable request receipt.
4. Archive is preserved until explicitly restored in Companies. Existing admission,
   capacity, provider and allowance handling still apply.
5. Creating a new Sandbox keeps Storyline data separate. Selecting a Storyline Sandbox
   deliberately uses its existing data without advancing scripted chapters.

### US2 — Explain actual actions (P1)
1. What happened shows exact recorded calls for a reply and proposal-linked decisions.
2. Reads and proposals do not claim execution. Writes require ordinary confirmation.
3. Existing marker deltas are labeled as changes since a call and may include later
   Sandbox activity; they do not claim exclusive causation.
4. Reload preserves attribution. Unrelated/concurrent calls are not joined by time.
5. Missing/pruned evidence is explicit. Trace failure never repeats a saved reply.

### US3 — Continue typing (P2)
Enter or Send returns focus to the active composer on success or failure, including
first-session remounts. Initial load does not focus automatically. A different control
selected while waiting keeps focus. Busy refreshes preserve the cursor using read-only
input while preventing edits/submission.

## Requirements
- **FR-001**: Standalone and contextual chat reuse the normal persistent company agent,
  tools, provider, allowance, voice composer and explicit proposal confirmation.
- **FR-002**: Own words from a scripted narrator remain an editable draft in its
  contextual Sandbox chat; no automatic send or draft URL/storage.
- **FR-003**: Evidence uses exact server-recorded call/proposal IDs, is owner/tenant
  scoped, survives reload within bounded retention and never uses time-range attribution.
- **FR-004**: What happened exposes real calls/refusals and existing confirmed deltas;
  missing and partial evidence are explicit. Companies without eligible Sandbox traces
  show unavailable evidence; ordinary proposal review and record links remain available.
- **FR-005**: Mobile/desktop, light/dark, en/de/nl/es, failure/retry and allowance remain usable.
- **FR-006**: Restore post-send focus without stealing another control's focus.
- **FR-007**: Free Play is removed from individual Storyline cards; guided story actions remain. The narrator footer has no Free Play/Sandbox chat
  action and offers a full-size Back to selection button, visually primary after
  completion, returning to the exploration library without writes.
- **FR-008**: One independent entry offers all companies in the shared bootstrap, defaults
  to the current company, and opens the selected company read-only. Company identity and
  Sandbox/real-data meaning are visible. Switching clears stale chat context; reload
  preserves the opened company. Creating a canonical practice Sandbox is a separate
  option without storyline identity/chapters. Confirmed POST remains idempotent and
  respects archive. An existing dedicated Sandbox can be reopened from the selector.
- **FR-009**: Trace eligibility adds only the designated standalone practice run to
  existing Storylines. Chapter APIs remain Storyline-only; temporary lesson boundaries hold.
- **DR-001**: Source → Evidence → Reality, shared services, admission and tenant scope
  remain authoritative. No adapter business writes or new schema.

## Success Criteria and Evidence
PostgreSQL tests prove creation confirmation, reuse, no Storyline identity, archive,
exact evidence, proposal lifecycle, owner/tenant isolation and trace-failure behavior.
Browser tests prove a separate entry, no per-card actions, explicit creation, correct
Sandbox selection, reload, draft/send/focus behavior and localized responsive layouts.

## Assumptions and Dependencies
All accessible companies can be selected, matching the company switcher shown by the owner.
No new general-purpose trace store is introduced: What happened is unavailable for
companies without eligible recorded Sandbox traces. One created Free Play Sandbox per account; canonical static sample data with no
live simulation. Existing configured provider is needed for arbitrary LLM chat.
Existing company setup and ordinary proposal review pages remain authoritative.

## Open Questions
None. The owner explicitly requested the independent entry and removal from each card.

## Requirement Traceability
| Requirements | Verification |
|---|---|
| FR-001–002, FR-005 | Storyline/contextual and independent browser interactions and layouts |
| FR-003–004, DR-001 | PostgreSQL exact evidence, proposal lifecycle, scope and retention tests |
| FR-006 | Shared composer failure/button/Enter focus and deliberate alternate-focus tests |
| FR-007–008 | Library/standalone browser entry, direct routing, explicit creation/reopen tests |
| FR-008–009, DR-001 | Confirmed setup, no story identity, collision/archive and owned evidence tests |
