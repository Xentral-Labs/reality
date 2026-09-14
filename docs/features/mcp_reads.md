# MCP read contracts

Feature 145 implements seven read improvements: balances separated by currency,
ledger discovery, explicit quantity units, location inventory, retained-order
explanation, pagination, and observation/persistence metadata. It adds no schema,
unit conversion, exchange rates, historical snapshots, or business mutations.

## Migration and access

The public MCP tools `business_records_discover`, `inventory_read`,
`commitments_list`, `fulfillment_queue`, `fulfillment_blockers`, and
`item_supply_demand` now default to `response_format: "page"`. Clients must read
`records` instead of treating the response itself as an array. Existing tool names,
tenant authorization, and permission requirements remain unchanged; the generated
MCP tool catalog lists the required permission for each tool.

For a staged migration, explicitly request `response_format: "legacy"` on these
six tools. Internal application-tool callers still default to legacy lists.
Legacy discovery is bounded, and legacy operational reads can refresh and commit
projection caches. Inventory filters and location views require page mode.
`finance_balances` always uses the new currency-safe response; its old hardcoded
single-currency object has no compatibility mode.

## Complete traversal

Send `limit` from 1 through 100 (default 25) and optionally `cursor`. A page has:

```json
{
  "records": [],
  "next_cursor": null,
  "has_more": false,
  "metadata": {}
}
```

When `has_more` is true, pass `next_cursor` unchanged with the same tenant, tool,
and filters. Continue until false. A cursor from another scope is rejected; the
limit can change. No total count is promised. Records sort by opaque ID or stable
record key. This is live keyset traversal: concurrent changes can alter later
pages, and inserted keys before the cursor will not appear. Restart against a
quiescent dataset for reproducible comparisons. Finishing traversal proves only
coverage of matching retained records under those limitations, not upstream
completeness. Operational derivation currently reads the full relevant tenant
state before slicing; bounded output does not promise bounded computation.

## Physical shipments

`shipments_list` returns tenant-scoped real consignments with Package tracking references,
effective Movement contents and current unsuperseded observations. `shipment_explain` follows one
opaque Shipment ID through Packages, Movements, events and SourceRecord references. These reads do
not treat Delivery Commitments as shipments and do not infer old Movements into Packages.

## Money, units, and locations

`finance_balances` returns `balances`, an array ordered by currency, plus
`metadata`. Each entry contains `currency`, `receivables`, and `payables`; money is
a decimal string. Receivables are debit minus credit on accounts receivable;
payables are credit minus debit on accounts payable. Represented zero and negative
positions remain visible. An empty tenant returns an empty array. There is no FX
conversion or combined currency total. These are ledger account positions, not
net revenue, profit, or bank settlement. Ledger discovery exposes `debit_credit`
and the matching compatibility alias `side`.

Operational quantities include the item's recorded `unit`, `unit_status`, and
`quantity_basis`. Missing units are null/unknown. Where document-line units are
available, they remain visible and `unit_mismatch` flags disagreement. Quantities
are not converted. Commitment quantities and due dates reflect revisions while
original values remain available.

`inventory_read` defaults to `view: "aggregate"`, explicitly labelled
`item_all_locations`. Request `view: "location"` for item/location rows, or pass
`location_id` to select that scope. `item_id` can narrow either view. A location
view includes zero-stock item/location combinations for stock-capable locations;
an explicit valid location can also be inspected. Physical, reserved, and
available quantities use the same location predicates. Incoming commitments are
promises, not received goods or an arrival forecast. An allocation gap does not
by itself establish a physical shortage.

## Retained orders and observation

`order_explain` resolves a tenant-owned order document ID or delivery commitment
ID, including fulfilled and cancelled cases. Display numbers/external references
remain conveniences and ambiguous matches are refused. It returns retained
source, document lines, commitments, reservations, movements, and derived
fulfillment. Closed lines remain visible but have no actionable open quantity;
closed orders are not ship-ready. It does not reconstruct state at a past date.

Page reads, finance, and order explanation return `metadata` containing
`contract_version: 2`, tenant and applied filters, UTC `observed_at`, known
`projection_version` or null, observed local `event_sequence` or null,
`upstream_freshness: "unknown"`, and `consistency` (`live_keyset` or `live_read`).
The local event sequence is an observation, not a snapshot ID or proof that every
external change was imported. Individual SQL reads use the active database
transaction's isolation; no atomic multi-query snapshot is promised.

These diagnostics suppress autoflush, do not write business/projection records,
and do not commit. `metadata.persistence` states those guarantees. Transport
authentication can separately persist token-use telemetry. The guarantee does not
apply to explicitly selected legacy projection reads or to other tools such as
cached price resolution. Business actions still use their existing proposal,
confirmation, execution, and verification contracts.
