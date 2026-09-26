# Implementation Plan: Fulfillment Safety Parity

**Branch**: `275-fulfillment-safety-parity` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add one explicit `PaymentTerm.requires_prepayment` policy and a shared read-time
fulfillment-readiness service. The service derives stock/reservation/hold state and qualifying
allocated customer payments through existing order-line → invoice-line → ledger/allocation links.
Shipment review and execution consume that service, so Web, Chat and MCP cannot diverge. Extend
proposal failure finalization to deterministic effect-free refusals, keep genuinely unknown effects
executing, publish the already-supported purpose-specific shipment schemas consistently, and prove
the whole contract with focused service/adapter tests plus one deterministic business story.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript only for payment-term presentation/input parity
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite
**Storage**: PostgreSQL; one non-null boolean payment-term policy column with a false server default
**Testing**: pytest unit/service/business-story/MCP/API; frontend build and focused component/API tests
**Project Type**: backend services/API/CLI plus independent React frontend and HTTP MCP runtime
**Constraints**: Decimal money/quantities; UTC; opaque IDs; lossless evidence; strict tenant scope;
mutations use proposals and confirmation; no derived status columns on documents
**Scale/Scope**: one payment-term policy, one shared readiness observation, shipment proposal and
execution enforcement, proposal lifecycle repair, public schemas/docs, one parity story

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Payment remains Source/Document/Ledger/Settlement evidence; readiness follows order line → billed invoice line → ledger/allocation and links every value. | PASS |
| Reality owns operational state | `ship_ready` remains a read-time observation from Commitments, Reservations, Holds, Movements and Ledger allocations; no document delivery/payment status is added. | PASS |
| Proven schema only | The one new boolean is repeatedly calculated against and constrains dispatch; the reproduced Web/MCP mismatch proves the use case. | PASS |
| Tenant + shared service boundaries | All queries include `tenant_id`; readiness lives in `services/` and all transports call application tools/services. | PASS |
| Spec/test traceability | FR-001–FR-021 map to tests below and ordered tasks; tests precede behavior changes. | PASS |
| Explainable web behavior | Readiness returns blocker codes, amounts and opaque evidence links; Web only presents the shared result. | PASS |
| Received values not recomputed | Required amount uses the order's stated gross; received amount sums recorded active allocations. It does not reconstruct price, tax or invoice totals. | PASS |
| Smallest coherent design | One boolean and one service reuse existing links/tables; no payment-status, fulfillment-status or duplicate allocation authority is stored. | PASS |

Post-design re-check: **PASS**. The data model adds only the proven commercial policy, the
contract is a derived observation, and adapters contain no rules.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0099_payment_term_prepayment.py
packages/reality-core/src/reality/db/core.py
packages/reality-core/src/reality/services/core.py
packages/reality-core/src/reality/services/fulfillment_readiness.py
packages/reality-core/src/reality/services/projections.py
packages/reality-core/src/reality/services/shipment_actions.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/config/resource_catalog.yaml
packages/reality-core/tests/test_payment_terms.py
packages/reality-core/tests/test_fulfillment_readiness.py
packages/reality-core/tests/test_shipment_actions.py
packages/reality-core/tests/test_application_tools.py
packages/reality-core/tests/test_ai_mcp.py
packages/reality-core/tests/test_master_data_api.py
packages/reality-core/tests/scenarios/test_fulfillment_safety_parity.py
apps/web/src/unified/*payment-term/master-data files as discovered
apps/docs/content/tool-usage/* (generated)
apps/docs/.vitepress/data/tool-usage.json (generated)
docs/features/order_to_cash.md
docs/features/shipments.md
```

**Files/layers affected**: schema/model → core payment-term service → new readiness service →
shipment review/execution and operational projection → application tools → MCP/API/Web adapters →
generated docs. Exact frontend component paths are selected during implementation by locating the
existing payment-term editor; no new page or parallel rule is introduced.

## Design

### Reality flow

```text
PaymentTerm.requires_prepayment
  → sales-order Document.payment_term_id
  → DocumentLine
  → customer-delivery Commitment

order DocumentLine
  ← sales-invoice DocumentLine.billed_document_line_id
  → posted invoice control LedgerEntry
  ← active SettlementAllocation
  → customer-payment LedgerEntry / payment Document

Commitment
  → active Reservation + physical Movements + active Commitment/Party Holds
  → FulfillmentReadiness (derived, never stored)
  → dispatch review token and execution guard
```

The order's received `gross_amount` is the required amount for a prepayment agreement. Qualifying
received money is the sum of active settlement allocations against posted sales invoices whose
invoice lines unambiguously bill this order's lines, with matching tenant, customer and currency.
Credits, reductions, unallocated money, reversed allocations and unrelated invoices do not become
payment. If invoice attribution is missing or ambiguous, readiness blocks with an evidence-specific
reason instead of guessing.

### Service and adapter flow

1. `fulfillment_readiness.py` owns a batch-capable tenant-scoped read for one or more customer
   commitments/documents and returns normalized order and line observations.
2. Operational queue/blocker projections call the service rather than reconstructing payment
   readiness; their existing stock/hold fields are normalized into the same response.
3. `shipment_actions.review_shipment_action` calls readiness for every customer-delivery movement,
   refuses an unready intent before creating a proposal, and includes the complete relevant-state
   fingerprint in its review token.
4. Confirmation recomputes that review under the delivery-state lock; a payment reversal,
   allocation, hold or inventory/reservation change makes the old token stale.
5. `record_packaged_execution` or its shared precondition calls the same readiness service again so
   direct/shared execution cannot bypass preparation.
6. Web, Chat and MCP retain their existing application-tool calls. Payment-term fields and readiness
   observations are serialized, not reinterpreted, by adapters.
7. MCP shipment definitions use one exported schema builder shared with executable validation;
   generated docs consume the catalog after `make docs-generate`.

### Data and migration impact

- Add `payment_term.requires_prepayment BOOLEAN NOT NULL DEFAULT FALSE`.
- Existing rows remain false. There is deliberately no code/name-based backfill.
- Creation/update services, events, read contracts, API models, MCP schemas, CLI and Web editor
  accept and expose the field. Source payload fallback includes it only for manual creation; an
  actual supplied source payload remains lossless and unchanged.
- Orders already retain `payment_term_id`; no new order, invoice, commitment or status column is
  added. Invoice inheritance is exposed in review where existing contracts require it, but
  readiness follows the order's agreement and existing billed-line links.
- Downgrade drops only the new column. It is safe structurally but loses policies explicitly set
  after rollout; production rollback must therefore disable the feature before downgrade.

### Failure, security, and tenant behavior

- Every readiness query filters all tables by tenant and treats foreign opaque IDs as not found.
- Preparation and execution take the existing delivery-state lock; finance allocation writes that
  can affect readiness already serialize through finance locks and emit state visible on re-review.
- Known `InvalidOperation`/`NotFound` before effect and known complete transaction rollbacks finalize
  `failed` with a structured no-effect receipt for all eligible proposals, including finance and
  non-delivery families. Unexpected exceptions remain `executing` until reconciliation proves an
  outcome.
- A failed proposal is immutable and replay returns/refuses from that terminal state; it is never
  silently reset to proposed.
- Confirmation and owner rules remain unchanged. The new policy cannot grant authority.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-006 | migration/service/API | payment-term create/update/read plus qualifying allocation cases | no explicit policy; unpaid prepayment reports ready |
| FR-007–FR-010 | service/projection/shipment | shared readiness with stock, reservation, holds and payment blockers | projections and shipment review omit payment evidence |
| FR-011–FR-012 | service/application | review token changes only for relevant allocation/hold/readiness changes | token is identical before/after payment |
| FR-013–FR-015 | application/MCP/Web read | deterministic refusal terminalization and unknown-outcome control | finance/unreviewed refusals remain executing |
| FR-016–FR-019 | MCP/catalog/docs | schema snapshot, unknown-field/enum rejection, capability describe | deployed/derived contract is incomplete or inconsistent |
| FR-020–FR-021 | business story/adapter | 30 receive, two 10-unit orders, prepayment refusal/payment/ship, final reconciliation | MCP path can prepare unpaid dispatch |

Tests are added first and the focused failing assertions are observed before implementation. The
story uses only public application/MCP adapters for mutations; fixtures may create authentication
and tenant membership but not business effects directly.

## Rollout and Rollback

1. Deploy migration and code together; the false default preserves all existing terms and orders.
2. Existing terms require explicit owner update to become prepayment terms. No guessed conversion
   runs in the background.
3. Monitor proposal failure counts, stale-review refusals and prepayment blockers through existing
   interaction/decision telemetry; add stable codes if current metrics cannot distinguish them.
4. Roll back behavior by ceasing to set the policy and reverting service/adapters. Retain the column
   during operational rollback so stated policies are not lost; drop it only in a deliberate DB
   downgrade after confirming no true values need preservation.

## Review Risks

- Allocations can cover consolidated or partial invoices. The service must block ambiguity and must
  not over-credit an order from an invoice line that does not map uniquely to it.
- Order gross and invoice allocations may differ because of credits, discounts or partial billing.
  This feature counts only customer-payment allocations and exposes the remaining stated order
  amount; it does not reinterpret commercial reductions as payment.
- Batch projections must avoid per-order query growth. Build one bounded read over the selected open
  commitments and their linked evidence.
- Broad proposal failure finalization must distinguish a known rollback from an unexpected exception
  whose effect is uncertain.
- MCP schemas currently appear complete in source but were reported empty by the live client; tests
  must cover the serialized HTTP/tool-list contract, not only the Python registry object.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
