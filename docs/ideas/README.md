# Product idea inbox

This directory contains early product and domain ideas that have not yet passed the
Spec Kit workflow. Content here is exploratory: it may contain alternatives, open
questions, and unproven schema concepts.

When an idea is selected for implementation, create a numbered change specification
under `specs/` with `$speckit-specify`. Do not treat an idea as approved behavior or
turn it directly into implementation tasks.

## Proposed product migrations

- [Unified product migration](unified-product-migration.md): consolidate Product App
  and Playground into one application, with shared case work, action cards, Chat,
  Analytics, master data and an explicit legacy-retirement gate.
- [Unified capability inventory](unified-capability-inventory.md): post-Spec-115
  coverage, proposed remaining actions, intentional deferrals and cutover conditions.

- [Unified app completion plan](unified-completion-plan.md): accepted scope freeze, read-only retirement audit and bounded functional closure before the owner’s UI changes.

## Proposed demo and simulation extensions

- [Demo Data pays its orders](demo-order-to-cash.md): let the continuous synthetic
  source also issue invoices and customer payments with realistic e-commerce
  differences, through the normal intake path and a bounded automation authority.
  Specified as [feature 168](../../specs/168-demo-order-to-cash/spec.md).
- Payment matching guide: shipped with feature 168 as the product guide
  `apps/docs/content/concepts/payments-and-matching.md` (English and German); the
  contract lives in [payment_matching.md](../features/payment_matching.md).
- [Deterministic external-system simulator](integration-simulator.md): provider-shaped
  webhooks, pull APIs and files that prove the full integration boundary.
