# Implementation Plan: Attention Reads from the Stored Exceptions Projection

**Language**: English

## Constitution Check

- No new authority: the reads consume disposable projection rows that feature 179 keeps
  current; the explanation stays on the canonical live derivation.
- One rule, one place: filtering, ordering and paging move unchanged onto the stored rows; the
  enrichment (`_targets`) is reused as is.
- Tenant scope: every read goes through `get_tenant`; projection rows are tenant-scoped.
- Reads perform no refresh, enqueue, commit or cache write (179 FR-006).

## Order

1. **Service.** `attention_register` and `attention_summary` take their rows from
   `projection_rows(session, tenant_id, "exceptions")` and attach `projection_metadata` for the
   same generation (read rows and checkpoint in one consistent read as `projection_snapshot`
   does). Filtering, ordering, paging and `_targets` stay. Tests first: stored rows with builders
   forbidden, filters, unknown severity and class refusal, uninitialized company, metadata in the
   response.
2. **Detail.** `attention_detail` keeps `explain_operational_exception`. When it raises
   not-found for an id that exists in the stored generation, answer on the existing 404 path with
   the classification `finding_cleared` and the generation's completed time (owner decision, see
   the spec's Decisions section). Test: clear a
   finding by reserving, do not refresh, explain.
3. **API.** Response shapes keep their fields and gain `metadata`; the detail's cleared case is a
   safe 404 body the Web app can distinguish. HTTP boundary assertions.
4. **Web.** `AttentionPage` renders `ProjectionFreshness` above the list, keeps rows while
   pending, shows "awaiting first calculation" for `uninitialized`, and renders the cleared case
   in the preview. `ExceptionRulesRegister` shows the same freshness line and takes the counts
   from the stored summary. Localization for de, nl, es.
5. **Browser.** Fixtures for the four states in `unified-operations-browser.mjs` and the rules
   section of `unified-inspector-browser.mjs`.
6. **Measure.** Time register and summary against the local stack company with the harness used
   for PR #227; record before/after in the PR.

## Risks

- A stored generation can list a finding whose target record was deleted; the detail path must
  not crash on a missing target (covered by step 2).
- If 179 changes the metadata shape before merge, step 1 adopts the final shape; nothing here
  defines its own.

## Outcome

Implemented as planned. One addition: the builder records each stored row's canonical
`position` so the register keeps the live order; the projection version stays, older generations
fall back to severity, class rank and record id until the minute-level refresh republishes.


## Stable refresh feedback refinement (2026-09-17)
The owner's reported flicker is a presentation correction to FR-009. Keep the existing
read services and timestamps. In ProjectionFreshness.tsx keep a fixed-label button and
keep outcome feedback screen-reader-only. Group the timestamp and button in one wrapping
row with a 12px gap; render calculation state/backlog beneath and read errors visibly.
Use no opacity change; keep the focus-preserving aria-disabled behavior with guarded activation. Pass read errors
from all five consumers so retained metadata cannot imply success after a failed read.
No new dependency, schema, scheduling or service behavior. Rollback is the component,
consumer props and copy. Constitution Check: PASS for all eight principles.
Test first: extend projection-freshness-browser.mjs for repeated fast/slow reads,
unchanged/newer/failed calculations, read errors, four languages and mobile/desktop
geometry. Required checks: browser regression, web contracts, build, i18n audit, changed
file formatting and spec-check. Backend/migration checks are not applicable to this
frontend-only correction. Review: scope matches the owner's refresh UX complaint;
no unresolved clarifications or additional product scope.

Owner refinement: show a permanent 14px refresh-arrows icon beside the button label.
It stays still when idle and rotates immediately for at least 1000 ms after activation,
and longer while the read is pending. Never leave an empty icon slot. Dimensions stay
fixed across idle/loading/completed states. Keyboard activation uses the same action.
Keep duplicate activation disabled throughout this feedback interval; announce checking
to assistive technology until it ends. Reduced motion keeps the indicator static. Clear the timer on
unmount. Data can arrive immediately; the minimum interval only affects feedback.
