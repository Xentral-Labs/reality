# Implementation Plan: Decision points in the business timeline

## Summary
Reuse the existing bounded change-proposal API in the web adapter. Convert its stated creation and settlement timestamps into presentation-only decision markers, add a sixth lane, and keep markers absent in selected-order mode. No storage or service rule changes.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | ChangeProposal remains the authority; no new record is created. |
| Reality authority / shortest links | PASS | No payload or temporal relationship inference. |
| Proven schema | PASS | No schema change. |
| Tenant/service boundaries | PASS | Existing tenant-scoped change-proposal endpoint is reused. |
| Spec and tests first | PASS | Spec/tasks precede implementation; pure layout and browser tests change first. |
| Explainable web | PASS | Each point names its lifecycle stage and links to Decisions. |
| Simplicity | PASS | Presentation adapter only; no new endpoint or abstraction beyond marker layout. |
| Received values | PASS | Held timestamps/statuses are displayed unchanged. |

## Implementation

- `apps/web/src/unified/orderJourneyLayout.ts`: add lane and pure decision marker conversion/layout.
- `apps/web/src/unified/OrderJourneyTimeline.tsx`: bounded reads, rendering, grouping and decision navigation.
- `apps/web/src/tailwind.css`: theme-aware decision color and six-lane chart geometry.
- `apps/web/src/localization.tsx`: four-language labels.
- `apps/web/scripts/order-journey-layout.test.mjs` and `order-journey-browser.mjs`: executable acceptance.
- `docs/WEB_SPEC.md`: durable contract.

## Risks and rollback

The proposal pages are bounded independently from business-event pages, so the UI must state partial decision history. A failed decision refresh retains prior decision points and reports the failure without hiding business events. Rollback removes only presentation code and this additive contract; there is no migration.
