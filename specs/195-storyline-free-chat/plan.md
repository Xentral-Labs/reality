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
A separate `/app/free-play` route, navigation entry and exploration-library card use
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
