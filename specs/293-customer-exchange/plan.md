# Implementation Plan: Customer Exchange

**Branch**: `293-customer-exchange` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

## Summary

Add one append-only record, `customer_exchange`, that links a customer return (a received return movement or an open return announcement) to a document-less, zero-amount replacement delivery promise. One reviewed tool records it on every surface. The return exception classes subtract the exchanged-and-arrived quantity. The announcement class names an advance exchange, and one new class reports an advance exchange whose announcement was withdrawn. Explanations link both sides. F07 is then promoted in the Business Journey Guide.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.8 / React 19 for the Web card

**Primary Dependencies**: SQLAlchemy 2, Alembic, Pydantic v2, Typer, FastAPI; existing delivery-review framework

**Storage**: PostgreSQL; one new table, migration `0101_customer_exchanges`

**Testing**: pytest on disposable PostgreSQL (service, derivation, adapter, isolation, catalog gates, business story); Node contract tests and i18n audit for Web

**Target Platform**: Reality core service, Web, MCP/Chat, CLI

**Project Type**: Domain capability across the full stack

**Performance Goals**: The exception derivation reads exchanges once per evaluation; there is no per-commitment query (spec 181, spec 241)

**Constraints**: No document status fields; no stored exchange flag; supplier return classes unchanged; tenant-scoped everywhere; confirmation required

**Scale/Scope**: 1 table, 1 service module, 1 action module, 2 tools, 4 derivation changes, 3 adapters, about 15 catalog files

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The confirmed request is a manual source record; the exchange and the replacement promise are Reality derived from it. |
| II. Reality is the operational authority | PASS | Settlement is derived from the exchange, movements and promises; documents gain no status (DR-001). |
| III. Proven schema only | PASS | `customer_exchange` is joined and filtered by four derivations, the credit and explanation reads and the delivery reads on every evaluation (research R1). No typed field is added elsewhere. |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; service writes only; tools shared by Web, MCP/Chat and CLI (DR-004). |
| V. Specification and test evidence | PASS | Approved spec; tests are planned before each implementation task. |
| VI. Explainable Web product | PASS | Return, replacement and exchange link to each other and to the decision (FR-012). |
| VII. Simplicity and storage discipline | PASS | One link table on the `supply_assignment` pattern; the replacement reuses `create_commitment`. |
| VIII. Received values are recorded, never recomputed | PASS | Quantities, items and reason are stated by the person; nothing is derived into storage. |

Post-design check: PASS. [data-model.md](data-model.md) adds no column to existing tables, and [contracts/customer-exchange.md](contracts/customer-exchange.md) reuses the delivery review.

## Design

### Flow

```text
return movement ─┐
                 ├─ customer_exchange ── replacement commitment (customer_delivery, amount 0, no document)
announcement ────┘        │                        │
                     source_record            reserve / dispatch as usual
                     (proposal id)
```

### Service (`services/customer_exchanges.py`)

- `preview_customer_exchange(session, tenant_id, arguments)`: resolves the return side, the returned delivery (commitment of the movement or announcement), the customer and the exchangeable quantity; raises the coded refusals of the contract.
- `record_customer_exchange(...)`: `_require_business_mutation("record_customer_exchange")`, locks the returned delivery, previews again, writes the source record, `create_commitment(..., amount=0, _commit=False)`, the exchange row, and emits `exchange.recorded`, all in one transaction.
- `customer_exchange_detail(...)`: the read of the contract.
- `exchanged_quantities(session, tenant_id)`: one query returning, per returned delivery, the exchanged-and-arrived quantity and the per-announcement exchanges; used by the derivations through `exception_inputs`.

### Derivations (`services/exceptions.py`, `services/exception_inputs.py`)

As in research R3. `returned_not_credited` and `credited_not_returned` gain `exchanged_quantity` in their causal values. The new class `exchange_without_return` gets a catalog entry, `CLASS_ORDER`, `DERIVATION_REGISTRY` and a four-language label.

### Explanations

- `movement_explanation`: a return movement or announcement-based return names its exchange and replacement; a replacement shipment names its exchange and the returned delivery.
- `delivery_reads.delivery_case`: the replacement's links include the exchange and the returned delivery.
- Decision history through `record_decisions` from the `exchange.recorded` event.

### Adapters

Web: `DeliveryActionPrepare.tool`, a read endpoint `GET /tenants/{tenant}/customer-exchanges/{id}`, the sandbox read allowlist, an exchange form on the Warehouse return movement row and in action discovery, `MovementExplanation` labels. MCP: `customer_exchange_propose` and the `customer_exchange` read with strict schemas. CLI: `customer-exchange`, `customer-exchange-propose`, `customer-exchange-confirm`.

### Catalogs and gates

Every file in research R6, with the pinned counts raised in the same commit as their cause.

## Project Structure

```text
specs/293-customer-exchange/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md
├── contracts/customer-exchange.md
└── checklists/requirements.md

packages/reality-core/
├── migrations/versions/0101_customer_exchanges.py
├── src/reality/db/core.py                               # CustomerExchange model
├── src/reality/services/customer_exchanges.py            # new
├── src/reality/services/customer_exchange_actions.py     # new, delivery review
├── src/reality/services/{delivery_actions,exceptions,exception_inputs,movement_explanations,delivery_reads,tenant_policy,business_locks,interactions,projections}.py
├── src/reality/{tools/application,mcp/catalog,cli/app,web/api,catalogs}.py
├── config/{command_catalog.yaml,tool_catalog.json,action_discovery.json,resource_catalog.yaml,service_refusals.json,refusal_ratchet.json,tenant_isolation_catalog.yaml,business_event_catalog.yaml,operational_exception_catalog.yaml,data_model.yaml,reporting_graph.yaml,business_journey_catalog.yaml}
└── tests/
    ├── test_customer_exchanges.py                        # new: service, refusals, isolation
    ├── test_customer_exchange_adapters.py                # new: Web, MCP, CLI
    ├── operational_exceptions/test_derivation.py         # exchange cases with positive controls
    ├── scenarios/test_catalog_stock_and_returns.py        # F07 proof replaces the pinned gap
    └── test_business_journey_catalog.py                  # F07 in PROVEN_BY_STORY

apps/web/src/unified/{actionDiscovery.ts,ActionCard.tsx,ExchangeCard.tsx,WarehousePage.tsx,MovementExplanation.tsx}
apps/web/src/localization.tsx
apps/web/scripts/fixtures/action-reference.json
docs/features/operational_exceptions.md, docs/SPEC_COVERAGE_MATRIX.md, docs/scenarios/coverage.md
apps/docs generated output
```

**Structure Decision**: A service and action module pair modelled on `return_dispositions` and `return_disposition_actions`, so returns-side mutations share one shape.

## Rollback

Revert the commit and downgrade `0101_customer_exchanges`. Exchanges recorded in between leave their replacement promises as ordinary zero-amount promises. Rolling back therefore re-exposes the two findings the feature removed, and nothing else.

## Complexity Tracking

No Constitution violations. The new table is justified in research R1.
