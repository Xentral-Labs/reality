# Pre-implementation review
User request authorizes the two Home additions and existing session authorizes local rollout. No schema, permission, business action or external integration expansion. Scope/plan/traceability analyzed: FR001–007 and DR001–002 map to T001–005; no unresolved clarification, constitutional exception or critical finding. The existing event read is reused. Private in-memory readiness is the smallest cross-container signal without a heartbeat table. Existing permission gates are unchanged. No extension hooks configured.

Implementation sequence: core readiness tests were added first and initially failed
with the expected missing module. Browser proof was added during UI implementation,
rather than before it; completion depends on executable browser acceptance.

## Implementation review
- Home uses existing tenant activity projection and event Inspector; no new business authority.
- Private readiness reads do not persist, execute jobs or disclose URLs/secrets.
- Successful idle sweeps count as available; failed business jobs remain separate outcomes.
- Missing, stale, failed and wrong-role signals cannot produce ready.
- Home polling is single-flight, visibility-aware, abortable and disposed on company changes.
- Keyboard-accessible event buttons and scroll list preserve stable event identity.
- Browser screenshots reviewed for the new panel in desktop and mobile, light and dark.
- The eight-second read deadline closes the stale-positive case for hanging network reads.
- Existing tenant not-found errors use the standard HTTP error adapter.

## Approved graph refinement review
FR-008–011 supersede the initial list default. The pre-implementation checklist was
already complete; the owner's approval covers this concrete replacement. No new
schema, scheduling or mutation authority. Four explicit recorded-entity categories
exclude source/processing/commitment chatter; deduplication precedes time filtering
so aggregate/drilldown identities remain consistent. SQL totals are complete, while
matching event detail is capped at50 with explicit truncation. Unknown coverage is
hatched; stale fetched counts remain without extending measured zeros into outages.
The graph uses server observation time plus elapsed client time, not a potentially
incorrect client wall clock. Source buckets remain30minutes; mobile/desktop grouping
is labelled and capped at24hours to match the detail contract. Final desktop/mobile,
light/dark screenshots were reviewed after fixing the SVG's responsive height.

An initial full suite was interrupted after a source-inspection failure caused by
formatting `web/api.py` during the run: the loaded list_items function's old line
number pointed at patch_party_active in the rewritten file. The unchanged-source
focused regression passed. Completion requires a fresh full suite with frozen source;
no expectation was weakened to dismiss the failed run.


Hover correction review (2026-09-09): FR-011 is restored with stable intrinsic summary sizing, accessible inactive content, and responsive date/count layout. The regression reproduced the original height change before the fix. Exact Docker artifact passed 16 browser combinations and was verified on local 8080. No schema or service changes; no unresolved critical findings for this correction.


Range preference release (2026-09-09): FR-008 now defaults to 24 hours; FR-012 remembers explicit selection under an opaque user-scoped browser key, across reload and company navigation. Invalid/blocked storage safely falls back, without disabling range changes. Browser regression first failed with 30 instead of 1 day. Final full 16-case graph matrix and focused 16-case image matrix passed, including user isolation and storage failure acceptance. Frontend production build, 43 contracts, localization audit, formatting, spec and diff checks passed. No backend behavior or schema changes.
Local web image: `reality-web:activity-range-20260909`, assets `index-BoeiTI5R.js` / `index-BBt5dvwI.css`; only web recreated. Build snapshot and pinning override: `/private/tmp/reality-range-release/compose.range.json`. Logs: `/tmp/reality-range-red.log`, `/tmp/reality-range-browser.log`, `/tmp/reality-range-image-browser.log`, `/tmp/reality-range-contracts.log`, `/tmp/reality-range-build.log`. Review: requirement/test mapping complete, no critical findings; browser-local scope documented explicitly, without promising device synchronization.
