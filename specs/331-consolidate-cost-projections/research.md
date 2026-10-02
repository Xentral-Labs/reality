# Scope evidence: cost-output consolidation

**Status**: Inventory for scope review; no technical design approved.

## Candidate output tables

| Family | Superseded output tables | Retained authority |
|---|---|---|
| Inventory | cost_inventory_generation, cost_inventory_snapshot, cost_inventory_publication | Inventory review, policy, ownership and valuation inputs |
| Contribution | cost_contribution_generation, cost_contribution_snapshot | Confirmed action, contribution reviews and commercial cost assignments |
| Captured diagnostic | cost_generation, cost_inventory_row, cost_contribution_row, cost_publication | Captured basis and its inventory/contribution members |
| Company observations | cost_company_generation, cost_company_inventory_result, cost_company_contribution_result, cost_company_publication | Company manifest and its inventory/contribution inputs |

These thirteen output tables are defined in `db/cost_generations.py`,
`db/captured_report.py` and `db/company_generations.py`. The latter also defines
three retained input tables, which are explicitly outside the retirement scope.

## Known dependencies and risks

- `services/inventory_generations.py` and `services/contribution_generations.py` own
  existing builders and exact-generation readers.
- `services/analytics/costing_relation.py`, `captured_relation.py`,
  `captured_options.py` and `company_options.py` consume typed results or generations.
  A storage change cannot assume that opaque result JSON alone preserves these joins.
- `db/core.py` already supplies `projection_row` and `projection_checkpoint`, but
  their current scope identifies a current row/checkpoint rather than all historical
  generations. Reuse therefore requires a reviewed historical-selection design.
- The receipt-costing contract requires sealed immutable cache membership,
  compare-and-swap publication, exact input replay, bounded captured diagnostics,
  read-only reports and protection of published caches.
- Generic polymorphic links must not silently replace composite tenant foreign keys.
- Existing generation identifiers, pagination bindings and saved analysis selectors
  must survive the migration; changing IDs is not an acceptable shortcut.

## Review decision requested

Accept or adjust the first slice: consolidate only these output lifecycles, retain
all authority and input history, and reduce the schema by at least eight tables.
The exact shared storage design and migration sequence belong to the next plan.

## Planning decisions

- Decision: four shared typed tables plus updatable compatibility views.
  Rationale: net nine fewer stored tables while retaining exact SQL grain and IDs.
  Alternatives: existing projection_row lacks historical lifecycle and relational shape;
  ORM-only discriminator filters miss raw __table__ consumers; rewriting every reader
  together needlessly increases saved-report and identity migration risk.
- Decision: preserve family in composite identity and each shared-output FK.
  Rationale: formerly separate namespaces may contain identical opaque IDs.
- Decision: retain company manifest/input guards and dispatch output guards on physical storage.
  Rationale: views own neither data integrity nor alternative business rules.
- Decision: frozen migration DDL with exact-value parity before retirement and lossless downgrade.
  Rationale: live model imports cannot define historical schema; outputs may be populated.

Owner approved first-slice scope on 2026-10-02. No unresolved research questions remain.
