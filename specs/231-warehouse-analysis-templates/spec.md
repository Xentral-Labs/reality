# Feature Specification: Warehouse analysis and starting templates

**Language**: English

## Context and Intent
The owner approved warehouse measures and matching templates after finance/date analysis.
Expose the same current inventory quantities as Warehouse through the shared analysis tools.

### Non-Goals
No inventory storage, valuation, historic stock reconstruction, location/lot/serial
breakdown, release eligibility or new business mutations. Available is physical minus
active reservations; holds and expiry do not become an implicit release promise.

## User Scenarios & Testing
### US1 — Current stock analysis (P1)
Given receipts, shipments, transfers and active/released reservations, stock analysis
matches the canonical inventory service and Warehouse register, including negative
availability and articles without movements. Currency is irrelevant; units stay separate.
### US2 — Useful starting questions (P1)
Choose stock by article, reserved stock or shortages to open an editable unsaved
analysis. Finance templates expose outstanding customer/supplier and overdue customer
amounts through the canonical finance nodes. Templates preserve identities and units.

## Requirements
- **FR-001**: Expose current physical, reserved and available quantities at one-row-per-
  article grain via core.inventory_rows, with original article/source relationships.
- **FR-002**: Preserve tenant scope, exact Decimal quantities, units, fanout protection,
  result/statement limits and snapshot non-additivity. Refuse derivation above 20,000
  articles or open supplier commitments, or 100,000 movements or commitment revisions, never truncate totals.
- **FR-003**: Provide six localized templates: stock by article, reserved stock,
  negative available stock, customer outstanding by partner, supplier outstanding
  by partner and overdue customer amounts by partner. Template adoption remains unsaved.
- **FR-004**: Clearly describe all-location current stock and arithmetic availability;
  require article identity and unit axes in stock templates. Existing templates stay intact.

## Assumptions and Dependencies
The registered finance derivation from spec230 is retained. inventory_rows is canonical;
Warehouse's paginated adapter is a parity target, never an aggregation input. No new
schema or service authority. English repository artifacts with existing localized labels.

## Success Criteria
Stock results match canonical and Warehouse values, no cross-tenant/unit sum or fanout
inflation, all six templates execute, and existing analysis/web checks remain green.

## Requirement Traceability
| Requirement | Story | Tasks | Tests |
|---|---|---|---|
| FR-001 | US1 | T001,T002 | Canonical/Register parity, zero/negative stock |
| FR-002 | US1 | T001,T002 | Tenant, units, snapshot, bounds, fanout |
| FR-003 | US2 | T001,T003 | Template validation/execution |
| FR-004 | US1/US2 | T003,T004 | Catalog descriptions and Chrome |
