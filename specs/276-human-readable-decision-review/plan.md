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

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Exact proposal ID and technical disclosure remain available; no record links change. | PASS |
| Reality authority | Browser only renders the existing review; it derives no operational state. | PASS |
| Proven schema | No schema or stored field change. | PASS |
| Tenant and service boundaries | Existing tenant-scoped reads and canonical confirm/reject calls remain unchanged. | PASS |
| Spec and test evidence | Spec, traceable tasks and focused tests precede implementation. | PASS |
| Explainable Web | Business meaning leads and exact technical review remains secondary. | PASS |
| Simplicity | Existing components and payloads are reused; no dependency or abstraction layer is added. | PASS |
| Received values | Displayed amounts and quantities come directly from the stored review payload. | PASS |

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

## Test Strategy

- Source contract test for decision-card semantics, routing and hidden internal tool label.
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
