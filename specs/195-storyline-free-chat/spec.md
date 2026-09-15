# Feature Specification: Independent Free Play and Recorded Chat Evidence

**Branch**: `feat/storyline-free-chat` | **Created**: 2026-09-15
**Language**: English
**Status**: Owner requested a separate Free Play entry with existing-company selection or new Sandbox creation.

## Context and Intent
Free Play is an alternative to a guided Storyline. It must not require a story or
appear as an action repeated on each story. People need a real company agent in a
selected company or persistent private Sandbox, with actual evidence where recorded.

## Scope
One Free Play tile in the Storyline exploration library, with no separate sidebar
entry, leading to
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
- **FR-010**: While a chat request is pending, show a prominent status panel above
  the composer with a high-contrast rotating indicator and Reality is working label.
  Expose a polite live status, respect reduced motion, and remove it on success or
  failure. Do not imply percentages or tool activity that the server has not reported.
- **FR-007**: Free Play has one tile in the Storyline selection and no separate sidebar link.
  Storyline stays highlighted while using Free Play, and its sidebar link opens the
  selection. Free Play is removed from individual Storyline cards; guided story actions remain. The narrator footer has no Free Play/Sandbox chat
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
- **FR-011**: Chat uses right-aligned neutral user bubbles and left-aligned unboxed
  assistant responses, clear turn spacing and bounded reading width. Visible role/time
  labels do not clutter turns; accessible authorship and per-reply evidence remain.
  Pending user messages share the same style. Long content remains contained in both
  themes and on mobile.
- **FR-012**: Available AI allowance appears in the chat header, and in the outer
  Free Play header when embedded there. A compact Usage button opens consumed/remaining
  counts, exact reset time and a Settings usage link. Settings exposes the same current
  allowance through existing authorized reads. No invented plan/upgrade destination.
  Only exhaustion appears at the composer, preserving disabled sending.
- **FR-013**: Free Play occupies the viewport below the app header. Long chat
  histories scroll only within the message list; app navigation, chat headers and
  composer retain their positions, including at scroll boundaries and short screens.
- **FR-014**: An opened Free Play chat has one compact toolbar instead of separate
  company and conversation headers. Company selection, usage, history
  and new conversation remain accessible. On notebook widths the toolbar is at most
  56px high; mobile avoids horizontal overflow and preserves contained scrolling.
- **FR-015**: Free Play sessions appear as a company-scoped list to the left of the
  chat on desktop, in the surrounding neutral area. Narrow screens use a dismissible
  session drawer. Active selection is visible; choosing a session clears unsent context
  consistently with existing selection and closes the drawer. No Storyline link or
  session dropdown remains in the opened chat.
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
| FR-015 | Desktop session-list geometry, selection and mobile drawer checks |
| FR-014 | Notebook/mobile toolbar height and control-presence browser checks |
| FR-013 | Long-history browser scroll geometry and viewport checks |
| FR-012 | Free Playground browser allowance disclosure and exhaustion checks |
| FR-011 | Shared chat browser role geometry/background, echo and responsive theme checks |
| FR-010 | Shared composer browser pending/settled status and reduced-motion checks |
| FR-006 | Shared composer failure/button/Enter focus and deliberate alternate-focus tests |
| FR-007–008 | Library/standalone browser entry, direct routing, explicit creation/reopen tests |
| FR-008–009, DR-001 | Confirmed setup, no story identity, collision/archive and owned evidence tests |
