# Consistency and Implementation Review

## Scope and traceability
The approved request is real free-form chat inside the existing Storyline Sandbox,
with actual tool evidence. FR-001/002/005 map to the browser handoff, explicit send,
reload and 32 layout checks. FR-003/004 and DR-001 map to the PostgreSQL attribution,
proposal lifecycle, failure, retention and ownership tests. No clarification remains.

## Constitution and implementation review
- Existing company chat/provider/tool services remain the only execution path.
- Mutations remain proposals until ordinary explicit confirmation; no new write API.
- Every evidence query scopes both tenant and owned run; message identity is checked.
- Exact call IDs and proposal IDs provide attribution; no timestamp range is used.
- Internal reply associations contain identifiers only and share existing bounded
  trace retention. No migration, source mutation or derived business authority.
- Missing evidence is explicit. Partial/truncated evidence says calls are not included
  in this view, without claiming that every omitted call has been deleted.
- Existing marker deltas include later Sandbox activity, so the chat labels and
  explanation disclose this limit instead of claiming exclusive causal changes.
- Trace association failure does not fail or repeat an already-persisted chat reply.
- Existing draft clearing, history, provider failures, allowance and voice input are
  reused. The run-keyed Player and tenant-keyed ChatPage isolate Sandbox drafts.
- Export includes confirmed calls only; internal association rows cannot become
  scripted chapters. Normal protocol reads also exclude internal association rows.

No critical or high finding remains. The full completion verification
is recorded in verification.md; human PR/merge review remains separate.

FR-006 follow-up review: pending focus belongs to an explicit send, survives a
composer remount, waits for loading to settle and does not steal focus from another
control. Read-only inputs preserve focus across later refreshes. No domain, API,
schema or confirmation changes; browser regressions and web gates pass.

FR-007 review: direct entry uses the existing run and shared company-opening flow,
clears stale session/context selection and dispatches only reads. Visibility depends
on a run existing, so completed runs are supported and unstarted cards retain Start.
Existing translations and wrapping button layout are reused; no unresolved finding.

## Independent Free Play review (FR-007–009)
The standalone run is a normal canonical practice Sandbox with null Storyline
identity. The immutable owner request key provides idempotent entry using existing
setup services and admission/capacity rules. GET is read-only; POST confirms creation.
An ordinary-company receipt collision is refused. Archive is never undone.
Only the designated practice run joins existing Storylines in trace eligibility;
chapter APIs remain strict. Evidence keeps tenant/owner/call/proposal scope.
The dedicated route is registered for both SPA navigation and direct entry/reload.
Library cards no longer repeat Free Play. Independent and contextual histories are
separate in browser fixtures and real service tests. No critical finding remains.

## Company selection review
Scope follows the owner's current-company/other-company/new-Sandbox request. Shared
bootstrap is the selection authority; server tenant access remains authoritative.
No fake PlaygroundRun is attached to ordinary companies. Trace absence is explicit.
No critical findings; existing context/reset routing is reused.

## Narrator exit review
Owner requested removal of the remaining footer Free Play shortcut and a clearer
return to selection. Scope is a presentation/navigation correction to FR-007.
Test absence, clear label and read-only return in the browser. No critical findings.

## Sidebar correction review
Owner wants Free Play only as a tile under Storyline. Test absent sidebar link,
retained tile, Storyline active state and return to selection. No critical findings.

## Pending status review
Owner requested a more visible modern loading indicator. Existing pending lifecycle
and browser tests cover success/failure. Add reduced-motion verification. No critical
findings, backend claims or progress estimates.

## Conversation presentation review
Owner requested ChatGPT-like left/right visual differentiation. Shared CSS/tokens
cover dock, Free Play and full chat. Verify bubble position/background, assistant
background, pending echo and mobile/light/dark overflow. No critical findings.

## Allowance review
Owner requested less visual clutter. Count stays visible; exact reset information is
keyboard/touch accessible. Exhaustion remains explicit. No critical findings.

## Header usage review
Owner approved moving usage into the header and adding settings usage. Preserve
exhaustion at input; test header disclosure, settings read, and absence near composer.
No schema/backend changes or critical findings.

## Scroll review
Owner reports document/navigation movement while scrolling chat. Replace competing
viewport/minimum heights with a bounded route-specific flex chain. Verify long message
history, wheel scrolling, boundary containment and unchanged header/composer geometry.
No critical findings.

## Notebook toolbar review
Owner requests substantially less height above chat. One toolbar removes duplicate
headings, retains all controls and bounds notebook height. Test mobile overflow and
existing scroll geometry. No critical findings.
