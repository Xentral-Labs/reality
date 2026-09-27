# Implementation Plan: Human-readable decision review

## Summary

Change presentation only: introduce a reusable Chat decision card, stabilize the generic review
dialog around shared read states, and restructure the existing order proposal review. Add focused
source contracts and localization coverage before implementation. No API, service, schema or
proposal lifecycle change is required.

## Technical Context

- **Frontend**: React, TypeScript, Tailwind utility classes, shared localization catalog
- **Primary paths**: `apps/web/src/unified/ChatPage.tsx`, `ProposalReviewCard.tsx`,
  `OrderCard.tsx`, `apps/web/src/localization.tsx`
- **Tests**: `apps/web/scripts/*.test.mjs`, TypeScript build, localization audit
- **Persistence / migrations**: none
- **Rollback**: revert frontend and catalog changes; stored proposals are unaffected

## Constitution Check

| Principle                     | Evidence                                                                                  | Result |
| ----------------------------- | ----------------------------------------------------------------------------------------- | ------ |
| Source → Evidence → Reality   | Exact proposal ID and technical disclosure remain available; no record links change.      | PASS   |
| Reality authority             | Browser only renders the existing review; it derives no operational state.                | PASS   |
| Proven schema                 | No schema or stored field change.                                                         | PASS   |
| Tenant and service boundaries | Existing tenant-scoped reads and canonical confirm/reject calls remain unchanged.         | PASS   |
| Spec and test evidence        | Spec, traceable tasks and focused tests precede implementation.                           | PASS   |
| Explainable Web               | Business meaning leads and exact technical review remains secondary.                      | PASS   |
| Simplicity                    | Existing components and payloads are reused; no dependency or abstraction layer is added. | PASS   |
| Received values               | Displayed amounts and quantities come directly from the stored review payload.            | PASS   |

## Design

1. Add a shared `DecisionReview` kit that owns dialog header/chrome, recursive business-value
   rendering and the pending action footer. Arrays of objects render as labelled sub-records;
   exact raw payloads remain confined to System details.
2. Add a small presentational Chat decision card near Chat rendering. Map known tools to the same
   business labels used by Decisions and fall back to `review_label`. Show source/purpose without
   inventing a summary from arbitrary input.
3. Keep `ProposalReviewCard` mounted as one stable dialog. Render `ReadState` inside it, with
   `review.refresh` as retry, and keep its header and close control visible for all states.
4. Reorder `OrderCard` review content: decision title, summary, effect explanation, proposal
   status, then a bordered footer. Rename pending actions to business intentions and place the
   primary confirmation last. Rename the technical disclosure to System details.
5. Route master-data, order and common reviews through the shared kit; keep their canonical
   prepare/confirm/reject services unchanged. Audit remaining review components for independent
   pending action bars and migrate them to the shared action footer where their lifecycle fits.
6. Add all text in four product languages and run the existing audit.
7. Refine the Chat card as one compact surface: bound its main-conversation width to 680 px,
   pass the existing compact/dock context into the presentational component and tighten spacing
   there without changing proposal content or routing.
8. Reduce compact card content to a localized business action, `Not yet executed` status and
   `Review` action. Add known master-data creation labels and keep richer purpose, origin and
   safety detail in the canonical review rather than repeating it in Chat.
9. Replace repeated ordinary-proposal cards with one counted list surface. Render each proposal
   as a divided row with compact pending status and an independently routed, visually secondary
   review button. Keep report proposals on their existing specialized surface and do not add a
   batch action.
10. Make Chat review in-place: set only the proposal selection and clear stale specialized
    proposal selectors, leaving the current route unchanged. Reuse the global review host, which
    already presents common and delivery reviews as dialogs and allows the current workspace to
    supply its specialized overlay where applicable.
11. Centralize proposal business labels for Chat, Decisions and common review. Translate known
    master-data purposes and Payment Term field labels through the existing catalog; never
    translate received values or internal tool identity.
12. Deduplicate only concurrent Proposal Review GETs by tenant/proposal key in the API client.
    Clear the shared promise after resolve or reject; do not retain response data and do not
    apply the mechanism to approval, rejection or any mutation.

## Test Strategy

- Source contract test for decision-card semantics, routing and hidden internal tool label.
- Source contract assertions for the bounded main-chat width, compact/dock spacing and absence of
  the former full-width status header band.
- Source contract assertions that redundant decision, purpose and origin copy is absent while the
  terse pending state, localized action title and canonical review route remain.
- Source contract assertions for one proposal list, divided rows, right-aligned independent
  actions and absence of a per-proposal card component.
- Source contract assertions that Chat does not call the workspace-destination mapper and opens
  the exact proposal without setting a replacement route.
- Source contract assertions that Chat and common review consume one label mapping, plus the
  existing four-language localization audit for purpose and field copy.
- Async unit proof for one loader call across simultaneous reads, cleanup after success/failure
  and a fresh later read; API source contract proving Proposal Review is the bounded consumer.
- Source contract test for stable loading/error dialog and retry.
- Source contract test for order decision title, effect hierarchy, one primary action and System
  details.
- `npm run build` and `npm run i18n:audit`.

## Risks and Review

- Action-specific dialogs differ. This increment deliberately changes only common review and
  order review; existing canonical routing prevents accidental lifecycle changes.
- Copy must not imply stock or money changes. The order effect repeats the existing authoritative
  review statement.
- CSS-only ordering can harm keyboard order, so DOM order follows visual order.

## Complexity Tracking

No constitutional exceptions or new complexity are introduced.
