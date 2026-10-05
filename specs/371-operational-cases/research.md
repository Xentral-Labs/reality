# Source-grounded design decisions

Inspected 2026-10-05; repository inspection is not a live-runtime verification.

1. `services/core.py:emit_business_event` writes ordered tenant-scoped BusinessEvents in the current transaction. `db/core.py:BusinessEvent` supplies subject/source/action/causation references. Use this committed event stream; do not create another emitter or broker.
2. `config/business_event_catalog.yaml` declares event vocabulary and affected read models. `config/resource_catalog.yaml` groups business resources and process steps, but does not own case instances. Add explicit case policy rather than infer ownership from read-model invalidation.
3. `services/projection_jobs.py`, `services/projections.py`, `jobs/handlers/projections.py` show checkpoint-based dispatch and shared worker execution. Reuse scheduling infrastructure, with a separate coordination consumer; projections remain non-authoritative caches.
4. `services/shopify_intake.py:order_state` freezes collection membership and authoritative order state. `services/intake.py:_validate_current_plan` rechecks source and business state. Extend canonical applicability guards; never assume event consumption alone makes execution safe.
5. `services/intake_review.py` implements finite owner-granted agent intake review mandates. Case ownership neither replaces these mandates nor widens business approval.
6. `docs/maintainer-guides/integrations/shopify.md` distinguishes implemented order/refund support from missing live transport and fulfillment interpreters. A completed refund is evidence, not a future payout intent. Return/refund and external execution scope must stay capability-gated.
7. `docs/ARCHITECTURE.md` defines correlation metadata as observability, not business identity. Existing producers sometimes set correlation ID to action ID. The owner clarified that this value is supplied by external systems for tracing. Preserve it unchanged and separately from case/action identity. Existing internal action-ID assignments are an audit finding, not automatically a proven defect. Correct conflicting touched paths with preservation tests; keep historical events and defer broad cleanup.
8. `docs/features/scheduled-jobs.md` prohibits direct network effects in initial handlers. Consumer applies coordination only; live Shopify preflight/dispatch needs its own adapter design and cannot be promised by this layer.

## Decisions and rejected alternatives

One fulfillment case per order; one return case per announcement; one refund case per explicit intent. Takeover is scoped to owned work, not related graph traversal. Business completion stays derived. Consumer follows current truth; execution gates are synchronous. Adoption explicitly selects outstanding historical roots. Controls and stable identity survive policy rebuild.

Reject one case per event (duplicates goals), one global order-to-cash case (overbroad ownership), model-decided grouping (unstable boundaries), correlation-ID grouping (not typed authority), and cache-only ownership checks (unsafe under lag).

## Completed static entrypoint inventory

[Entrypoint coverage](contracts/entrypoint-coverage.md) now records 49 exact canonical symbols, real adapter/direct/dynamic callers, planned guard/ensure placement, baseline tests and unavailable goal-root cases. It confirms exchange replacements can lack document anchors, returns can lack announcements, Finance refund booking is distinct from provider payout, and generic durable claim plus specialized intake paths have different transaction boundaries. At initial discovery the migration head was 0143_intake_review_mandates; the approved additive implementation adds 0144_operational_cases. This is discovery evidence, not executable case-layer verification or release approval.

## Cross-business candidate review

Reviewed resource_catalog procure_to_pay/returns/finance processes, business_event_catalog, core models and receipt_deviations/stock_blocks/stock_counts/purchase_match services. Supplier delivery commitments, purchase-order documents, Misdelivery, StockBlock and invoice evidence supply candidate anchors. Payment/count/transfer results are not pending intents. No canonical production-order model was established by this inspection. Candidate-only boundaries and dependencies are recorded in contracts/case-candidates.md; enabled scope is unchanged.

## Implementation follow-up

The owner approved the concrete five-table schema after the initial discovery. Shared leaves now ensure anchored cases atomically and guard automated effects, including party/document hold batches. The consumer reuses ScheduledJobRun and stores only its atomic checkpoint. Focused runtime and browser evidence is recorded in quickstart.md; initial static discovery alone is not runtime proof.
