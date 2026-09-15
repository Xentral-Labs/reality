# Implementation Plan: Independent Free Play

## Constitution Check
PASS: Source → Evidence → Reality remains in shared services. Company creation uses
canonical setup/admission/profile rules. No new schema, derived business authority,
automatic confirmation, lesson permission expansion or scheduling mechanism.

## Entry and lifecycle
`GET /api/storyline/free-play` reads the owner's existing company-setup receipt.
`POST` requires a strict confirmation flag and delegates to `create_company` using
`standalone-free-play:v1`, name Free Play, sandbox/international_demo and no live
simulation. Existing setup locking, fingerprint, initialization retry, capacity and
archive rules apply. A receipt for an ordinary company is refused. The run has no
Storyline identity or chapters; it is not included in the Storyline library.

## Evidence
The recorder recognizes existing Storylines plus the designated independent practice
run. The evidence reader validates owned tenant/run; chapter/mutation APIs keep the
strict Storyline reader. Exact request-local call IDs are associated with each saved
assistant message in bounded existing trace JSON. Proposal IDs link later decisions.
Internal association rows stay out of call lists. Missing/pruned evidence is explicit;
trace failure never retries a saved reply. Existing marker deltas disclose their
later-activity scope. No time-range attribution or new schema.

## UI
A separate `/app/free-play` route and exploration-library card use
`FreePlayPage`. Both SPA and direct-entry routers recognize the route. Entry reads
never create a company; the first explicit Create Sandbox and start action does.
The chooser defaults to the current company from shared bootstrap. Opening a company
clears stale conversation/context selection. A ready dedicated receipt offers reopening
without redirecting. Reload of an opened chat resumes that company; archive offers the
existing Companies restoration path. Failures remain retryable.

Use normal ChatPage, composer, allowance, provider and confirmation destinations.
Per-message What happened reuses the evidence/protocol renderer. Existing contextual
Storyline chat is labeled Sandbox chat and retains own-word draft handoff. Remove
Free Play actions from every Storyline card. New strings cover all four languages.
Post-send focus survives busy refreshes/remounts and respects deliberate focus elsewhere.

## Planned verification and dependency order
Service/recorder and API tests precede implementation, then route/UI integration and
browser proofs. PostgreSQL tests cover confirmed/idempotent setup, no story identity,
archive preservation, collision refusal, exact evidence, proposal confirmation and
owner/tenant boundaries. Browser tests cover the separate entry, no card actions,
explicit creation, tenant switch, direct URL/reload, chat and localized responsive
layouts. Full backend suite, web tests/build/audit, lint/spec and docs/catalog checks.
Record final evidence in verification.md; do not mark completion while a check is red.

## Rollback and scope
No migration. Reverting the UI/entry leaves the existing practice company and records
intact; bounded trace metadata remains inert. Do not delete or merge Sandbox data.
Local localhost preview only; production deployment is separate. No open clarification.

## Company selection amendment
The owner requested current or selected existing company instead of forced creation.
Use shared Bootstrap tenants, preset selection.tenant, label Sandbox/company meaning,
and open without a POST. A route-local `play=chat` flag preserves an explicitly opened
chat on reload; company switching clears stale sessions. The chooser remains reachable
from the chat header. A new Sandbox still uses the existing confirmed setup service.
Do not redirect from the chooser based on the dedicated receipt.
No backend/schema change is needed. Existing evidence eligibility stays unchanged;
HTTP 404 evidence reads render the existing unavailable message, not an invented trace.
Planned browser proofs: current default, ordinary company and Storyline Sandbox opening
without writes, switching and reload isolation, real-data notice, separate creation,
chooser availability even after dedicated creation, and unavailable evidence.
Constitution review: PASS, no schema, admission, confirmation or lesson changes.

## Narrator exit correction
Remove the contextual Sandbox chat shortcut from the narrator footer. Keep existing
own-word draft handling and saved contextual URLs compatible. Use an ArrowLeft icon
and full-size Back to selection button, primary after completion. Reuse the library
callback; no API or data changes. Constitution Check: PASS.

## Sidebar entry correction
Remove the separate Free Play sidebar link. Retain the library tile and saved direct
URLs. Treat both routes as Storyline navigation for highlighting; the Storyline link
opens the library explicitly. Constitution Check: PASS; no API or data changes.

## Pending chat visibility
Replace the faint pulsing icon with a shared ChatPage status panel: accent-soft
background and border, solid accent icon tile, rotating white LoaderCircle, strong
label. Use role=status and hide the decorative icon; motion-reduce disables rotation.
Reuse sending state. Constitution Check: PASS; presentation only.

## Conversation presentation
Shared ChatPage renders role-specific attributes and neutral user bubbles on the
right; assistant responses are unboxed on the left. Remove the CSS override that
currently flattens both roles. Limit reading width, increase turn spacing and hide
visual author/time metadata with accessible text. Keep Markdown and evidence inside
their existing replies. Constitution Check: PASS; presentation only.

## Compact allowance
Use a native details/summary count pill in shared AllowanceNotice, with an Info icon
and exact localized reset time inside. Exhaustion stays expanded with existing
explanation and send restriction. Constitution Check: PASS; existing data only.

## Header usage and settings
Move positive allowance out of the composer. Shared ChatUsage uses a native popover
for keyboard, Escape and outside-click dismissal. Render it in the Free Play header
via a portal target; other chat uses its own header. Settings usage reads existing
copilot allowance and displays used/remaining/reset only. No plan API exists: do not
invent tariffs or upgrade links. Constitution Check: PASS, read-only existing services.

## Free Play scroll containment
Constrain only Free Play shell/body/main to the available dynamic viewport height.
The card flexes within main rather than adding a fixed viewport height and minimum
height. Existing message list owns scrolling with overscroll containment; navigation
keeps its independent overflow. Constitution Check: PASS; layout only.

The company-scoped UnifiedApp wrapper also needs min-height:0 and flex sizing.
Each chat article establishes positioning for its screen-reader-only author metadata;
otherwise absolute metadata contributes to document overflow outside the scrollport.

## Compact Free Play toolbar
Merge the Free Play and conversation headers into one 48px toolbar. The company is
a truncated picker button; back-to-selection is an arrow. Portal shared history/new
conversation controls into the toolbar beside Usage, retaining existing behavior.
Other chats keep their existing header. Constitution Check: PASS; UI-only.

## Free Play sessions sidebar
Render existing ChatPage sessions into a left-side FreePlayPage portal target. Use
the existing session selection/reset path. Desktop shows the list beside the card;
mobile toggles a dismissible drawer. Suppress the old dropdown for this embedding.
Remove the opened-chat Storyline return control. Constitution Check: PASS; no API changes.

## FR-016 refinement
User approved the proposed visual refinement. Change adapters only: FreePlayPage
frame/company control and ChatPage session action/zero-allowance presentation. Reuse
existing session creation and authoritative allowance. No schema or domain changes;
Constitution Check PASS. Test responsive geometry, session action placement and
zero/positive allowance transition in the focused browser fixture before implementation.
