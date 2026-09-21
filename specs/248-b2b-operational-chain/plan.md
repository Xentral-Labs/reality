# Implementation Plan: Explainable B2B Operational Chain

**Branch**: `245-demo-setup-finance-readiness` | **Date**: 2026-09-21 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Complete the ordinary empty-company B2B path by preserving invoice-line evidence through the
existing confirmed invoice action, matching billed lines to delivered quantities and retained cost,
and preparing the existing finance/contribution projections after confirmed writes. Add one small,
tenant-scoped, append-only supply-assignment relationship between supplier and customer
commitments (or an explicit stock purpose). Reuse the existing return movement resolution model for
all physical return dispositions and add a shared explanation read model for movements. Prove the
whole design with one deterministic, service-driven multi-day story and thin Web/tool adapters.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React for Web presentation
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite
**Storage**: PostgreSQL
**Testing**: pytest unit/service/business-story/adapter tests; Vitest UI tests; browser acceptance run
**Project Type**: backend domain/services/tools/API plus independent frontend and public docs
**Constraints**: Decimal quantities/money; UTC instants; opaque IDs; lossless source; tenant scope;
preview/confirm/idempotency for mutations; received values never recomputed
**Scale/Scope**: Manual assignment and disposition for one company/base unit; one focused multi-day
acceptance story; no planner, tax engine, WMS, payment transport or automatic procurement

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Invoice values remain SourceRecord → Document/DocumentLine; assignments retain their stated source; physical outcomes are Movements | PASS |
| Reality owns operational state | Fulfilment, stock, supply coverage and unresolved returns are derived from commitments, assignments and movements—not document status | PASS |
| Proven schema only | Only the repeatedly joined/constrained supply-purpose relationship is new; invoice lines, return dispositions and explanations reuse existing records | PASS |
| Tenant + shared service boundaries | All reads/writes are tenant-scoped services used by Web, CLI, MCP and the story runner | PASS |
| Spec/test traceability | Every FR/DR maps to a named test family and quickstart proof below | PASS |
| Explainable web behavior | Invoice contribution, supply coverage, returns and movements link to Reality, Evidence and Source records | PASS |
| Received values not recomputed | Prices, costs, quantities and reasons are retained as stated; DB and reconciliation figures are read-time observations | PASS |
| Smallest coherent design | Existing invoice, costing, movement-resolution, correction, projection and exception models are reused; one new table handles the missing relationship | PASS |

Planning may proceed: all gates pass and no constitutional exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0090_supply_assignments.py
packages/reality-core/src/reality/db/core.py
packages/reality-core/src/reality/domain/supply.py
packages/reality-core/src/reality/services/supply_assignments.py
packages/reality-core/src/reality/services/invoice_actions.py
packages/reality-core/src/reality/services/contribution_reviews.py
packages/reality-core/src/reality/services/movement_explanations.py
packages/reality-core/src/reality/services/delivery_actions.py
packages/reality-core/src/reality/services/projections.py
packages/reality-core/src/reality/services/demo_profile.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/config/resource_catalog.yaml
packages/reality-core/tests/
apps/web/src/unified/
apps/web/src/localization.tsx
apps/docs/content/getting-started/demo-data.md
docs/features/
```

Exact filenames may be narrowed during tasks when an existing module already owns the behavior;
new business rules remain in domain/services and never move into adapters.

## Design

### Reality flow

1. **Invoice and contribution**: incoming/confirmed action SourceRecord → sales or supplier invoice
   Document → DocumentLine linked to the billed order line → existing delivery Commitment and
   Movements → retained acquisition-cost consumption → read-time contribution observation. The
   action records every stated line and rejects ambiguous or over-billed quantities; it never creates
   a balancing line or recalculates a source total.
2. **Supply intent**: operator/action SourceRecord → existing supplier Commitment plus existing
   customer Commitment → append-only SupplyAssignment. Stock replenishment has an explicit purpose
   and no customer commitment. Effective assignment is the original quantity less explicit reversal
   records; unassigned supply and shortages are derived.
3. **Return disposition**: original delivery Commitment/Movement → ReturnAnnouncement → inbound
   return Movement → resolving Movement. Transfer to sellable stock, transfer to quarantine,
   adjustment to scrap/loss and outbound supplier-return movement are the dispositions. No parallel
   status or stock balance is stored. Customer/supplier credits remain separate Document/Ledger
   evidence.
4. **Movement explanation**: a read service follows, in order, correction, return-resolution,
   return-announcement, commitment, shipment package and SourceRecord links; adjustments without an
   allowed link retain the existing stated reason. The explanation is a projection, not authority.

### Service and adapter flow

- Extend the confirmed invoice workflow so preview returns exact candidate lines and execution uses
  the reviewed snapshot. Web/API/tools call the same service. Existing request identities and
  unresolved-outcome checks remain the idempotency boundary.
- Add supply-assignment preview/confirm/reverse services. They lock referenced commitments,
  calculate current effective quantities in the same transaction, enforce tenant/item/location
  compatibility and write one append-only assignment or reversal.
- Add return-disposition preview/confirm orchestration over the existing movement service. It maps a
  user choice to validated movement arguments but creates no new business rule or persistence path.
- Add shared supply-coverage, return-resolution and movement-explanation reads. Operational pages
  render those responses and link opaque IDs to the Inspector.
- After confirmed commercial writes, enqueue/mark due the existing projection jobs through the
  shared job registry. Setup readiness waits for their durable completion marker; browsers do not
  poll a second queue or calculate finance.
- The deterministic story calls application services, never ORM fixture shortcuts. Its manifest
  publishes exact business references and expected outcomes for docs and browser validation.

### Data and migration impact

- Add `supply_assignment`, tenant-scoped with opaque ID, supplier commitment, optional customer
  commitment, purpose (`customer_demand` or `stock_replenishment`), positive quantity, source record,
  optional reversed-assignment link and creation timestamp.
- Composite tenant foreign keys prevent cross-company links. Checks enforce customer commitment
  presence exactly for `customer_demand`, absence for `stock_replenishment`, positive quantity and
  no self-reversal. Service constraints enforce compatible commitment types, item/location, open
  quantity and cumulative effective bounds under row locks.
- Corrections are append-only reversal rows followed by a new assignment when required. Existing
  data needs no backfill; absence means unassigned, never stock replenishment.
- No new invoice, contribution, return-disposition, movement-reason or projection table is added.
  Existing `DocumentLine.billed_document_line_id`, `Movement.resolves_movement_id`,
  `Movement.return_announcement_id`, source links and action/audit evidence are sufficient.
- Migration rollback first requires an application version that no longer writes or reads supply
  assignments. Dropping the new table loses only explicit future planning relationships, not
  documents, commitments, inventory or finance history.

### Failure, security, and tenant behavior

- Cross-tenant identities behave as not found; malformed or incompatible links fail without naming
  foreign records.
- Invoice, assignment and disposition execution revalidates the previewed state under transaction
  locks. Partial failure rolls back the whole action.
- Replayed request/source identities return the existing result and create no duplicate line,
  assignment, movement, posting or human number.
- Missing cost/revenue/review/conversion basis produces stable unavailable reason codes and a next
  action. Zero is shown only when retained evidence states or derives a genuine zero.
- Projection lag keeps the last completed result visible with freshness metadata. Failed refresh
  never promotes incomplete results.
- Unexplained adjustments warn in preview; a deliberately confirmed exception stays visible until
  corrected rather than being hidden by UI logic.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003, DR-001–DR-002 | service/story | extend invoice action and partial-invoicing tests | confirmed ordinary invoice loses or rejects candidate lines |
| FR-004–FR-006 | service/projection/story | contribution and setup-readiness tests | ordinary billed line is unsupported or first projection is absent |
| FR-007–FR-010, DR-003, DR-005 | domain/service/tenant | new supply-assignment tests | no durable relationship or reconciliation exists |
| FR-011–FR-013, DR-004, DR-007 | service/story/adapter | extend return and credit-mismatch tests | primitives exist but no guided mixed disposition/read model exists |
| FR-014–FR-015 | service/adapter/UI | movement-explanation and warning tests | explanation is fragmented and warning is absent |
| FR-016–FR-018 | business story/docs/browser | new empty-company B2B story and catalog contract | no single executable reference story proves the chain |
| FR-019, DR-006 | policy/tool/API | confirmation, idempotency and adapter-parity tests | new actions are not yet registered across shared adapters |
| FR-020 | projection/UI | freshness and failed-refresh tests | readiness/freshness is not guaranteed after each covered write |
| DR-008 | architecture/migration review | schema-shape and forbidden-link assertions | supply relationship does not yet exist |
| SC-001–SC-009 | end-to-end acceptance | quickstart plus visible browser run | complete empty-company proof is currently impossible |

Tests are added before their implementation where practical. The complete gate includes migration
upgrade/downgrade, backend suite, frontend tests/build, i18n audit, generated catalog check, spec
check and a browser run against a newly created company.

## Rollout and Rollback

1. Deploy migration 0090 before application code that writes supply assignments.
2. Deploy compatible read services and adapters, then enable the UI actions and reference story.
3. Existing companies retain unchanged behavior; no inferred assignments or dispositions are
   backfilled. Demo/profile versioning adds the story only to newly prepared or explicitly upgraded
   sandboxes.
4. Monitor rejected assignment reasons, projection completion, contribution-unavailable reasons and
   unexplained-movement count.
5. Roll back UI/actions first. The application can ignore the new table while documents,
   commitments, movements and ledgers remain intact; drop migration 0090 only after ensuring no
   explicit assignment history must be retained.

## Review Risks

- A source total must never be silently forced to equal retained lines.
- Billed quantity must not exceed the eligible delivered/order scope across multiple invoices.
- Supply assignment must never be confused with reservation, receipt or ownership.
- Concurrent assignment/reversal must not over-allocate either supplier supply or customer demand.
- Return resolution must not duplicate inventory or imply a credit.
- Quarantine must use a genuinely non-sellable location and must not inflate available stock.
- Movement explanation ordering must expose all relevant evidence without inventing causality.
- Projection readiness must use the shared scheduler/worker contract and remain idempotent.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
