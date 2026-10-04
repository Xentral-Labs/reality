# Research: Reviewed Shopify orders, changes and refunds

Read-only repository investigation on 2026-10-03. Findings describe the current
checkout; proposed behavior is not claimed as implemented.

## R01: Keep Shopify guard semantics

- Decision: Keep Shopify guard semantics.
- Rationale: Spec 296 currently supports only bounded changes. A review gate must not turn unsupported changes into executable operations.
- Alternatives rejected: Implementing all upstream order edits as part of admission.

## R02: Separate refund statement from payout

- Decision: Separate refund statement from payout.
- Rationale: shop_refunds creates sales_refund evidence and supported operational announcements; it does not authorize a refund payment.
- Alternatives rejected: Treating the refund payload as financial settlement authority.

## Compatibility review

Legacy tests that expect immediate accepted interpretation need deliberate updates
to prepare → review → approve assertions, preserving their existing domain refusal
checks. The roadmap is not evidence of current autonomous agent permission or
5,000-row support. No unresolved product clarification remains; engineering defaults
and limits are explicitly documented in spec/plan/contracts.
