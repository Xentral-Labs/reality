# Company-wide Reporting Coverage Audit

Date: 2026-09-17. Scope: local code/model/service and feature-contract inspection.
**Spec impact: none** — this is a design inventory, not a change to the accepted
sales-first delivery scope, public catalog, database schema or runtime behavior.
Data-model support is not proof that an individual tenant imported complete or
populated data.

> **Superseded framing, retained inventory.** This audit was written while the design
> published relations as database views. That approach is withdrawn; see
> [spec.md](spec.md) and [data-model.md](data-model.md). Read every "view" below as a
> candidate **node** in the reporting graph. No view name here is an installed database
> object, and none will become one. The inventory of which business areas exist, what
> they mean and where their history is incomplete remains valid and is the input for
> declaring further nodes, edges and measures after the sales slice.

## Findings

The Reality core is already relational business infrastructure, not just a generic
Fact journal. It holds evidence, promises, revisions, reservations, physical movements,
logistics events, financial postings and explicit allocations. Most trade/distribution
reporting needs reusable access to those structures, not a new business storage model.

However, many canonical observations run in Python over several queries or loaded
rows. Exposing a SQL view requires extracting shared relational expressions and proving
equivalence, not duplicating business rules or calling a paginated register as if it
were the entire population. Native SQL alone does not make these calculations scalable.

Coverage labels:
- **Foundation present**: typed records/relationships exist; a reporting contract still needs work.
- **Derivation present**: canonical service computes the observation; relational exposure needs parity proof.
- **Partial**: meaningful subsets exist but important business inputs/semantics are missing.
- **Missing domain**: no dedicated model found in inspected business database modules/catalogs.

## 1. Business partners, products and organization

Foundation present: `Party`, canonical `PartyRole`, `PartyGroup`, `PartyGroupMember`,
`Item`, `Location`, `PaymentTerm` in `db/core.py`.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| business_partners | Party ID | Retained partner identity, current name, accounting code and stated credit limit |
| partner_roles | Party ID + role | Customers/suppliers including parties with both roles; no duplicated address books |
| partner_group_memberships | Group-membership ID | Segmentation with stated validity; membership can multiply rows |
| products | Item ID | SKU, unit, tracking type, purchase unit/conversion and stated lead time |
| locations | Location ID | Warehouse/bin hierarchy; not a legal-company consolidation hierarchy |
| payment_terms | PaymentTerm ID | Due days and stated discount terms, not computed discount amounts |

Correction to the earlier narrow proposal: a company-wide `customers` convenience view
should use `PartyRole`, not infer all customers from order history. Keep a separately
named observed-sales-customer population for questions about previously buying customers.
Spec 224's first-slice population currently means the latter; do not silently change it.
General departments, employees and corporate ownership are not modeled by PartyRole.

## 2. Sales and customer development

Foundation present: `Document`, `DocumentLine`, PartyRole, Item; canonical received-value
relation in `services/analytics/orders.py::order_relation`.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| sales_orders | Sales order ID | Order intake, customer/channel mix, period comparisons; order value is not accounting revenue |
| sales_order_lines | Sales line ID | Product mix, stated quantities/prices/amounts; missing source values remain unknown |

Customer repeat purchases, order frequency, average order value and product rankings
are queries over these relations, not new views or tables per KPI. Customer acquisition
cost, conversion funnel, opportunity win rate and subscription churn lack the necessary
marketing/CRM/subscription domain. A sales channel field is not campaign attribution.

## 3. Purchase and supplier performance

Foundation present: purchase Documents/Lines, supplier PartyRole, supplier Commitments,
CommitmentRevision and receipt Movements. `order_relation` already has purchase/line
variants internally; they are not currently public Analytics relations.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| purchase_orders | Purchase order ID | Supplier spend commitments and order dates |
| purchase_order_lines | Purchase line ID | Received purchase prices/quantities and product mix |

Use common commitments/revisions/movements for open purchasing and delivery performance.
Define whether punctuality compares original, latest or historically applicable promises;
choose a partial-delivery policy before publishing OTIF. Quote/tender comparisons,
supplier scorecards from inspections and contractual rebates are not complete domains.

## 4. Fulfillment and operational backlog

Derivation present: `commitment_terms`, `fulfilled_quantity`, `open_quantity`,
`commitment_rows`, holds and reservations in `services/core.py`.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| commitments_current | Commitment ID | Effective due date/quantity, fulfilled/open quantity, direction and status |
| commitment_revisions | Revision ID | What date/quantity was restated and when; each field takes its latest stated value |
| reservations_current | Reservation ID | Active/released/consumed allocation and tracked identity |
| execution_holds | Hold kind + hold ID | Partner and commitment holds, start/release, reason; distinct scopes |
| fulfillment_blockers_current | Commitment ID + blocker reason | Current shortages/holds via canonical blocker semantics |

Commitments can exist without documents. Preserve them with nullable evidence links.
Returns do not erase fulfillment: `fulfilled_quantity` deliberately excludes return
subtraction but removes corrected original movements. A single flattened join across
lines, commitments, reservations and movements will multiply measures.

## 5. Inventory and warehouses

Foundation and derivations present: `Movement`, `Reservation`, `Item`, `Location`,
`stock_at`, `stock_by_identity`, `inventory_rows` and supply/demand projections.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| stock_movements | Movement ID | Physical journal, type/time, source/destination, correction links |
| movement_corrections | Correction ID | Original/compensating/replacement chain; original is retained |
| stock_position_current | Item ID + location ID + applicable unit | Physical/reserved/available; derive location dimensions explicitly |
| item_supply_demand_current | Item ID + comparable unit | Open incoming/customer demand and projected availability |

A movement with both source and destination has two location effects but is one
physical movement. A location-effect expansion must publish its own leg grain.
Do not infer inventory cost from purchase price. Value, COGS, FIFO/average valuation,
landed cost and exact inventory turnover in money need additional cost evidence/policy.
Current `inventory_rows` aggregates by item, not location, and loads movement records;
it is not a ready-made scalable item/location SQL view.

## 6. Lots, serial numbers, handling units and quality

Foundation present: `Lot`, `SerialUnit`, `HandlingUnit`; Movements/Reservations point to
those identities. Lot expiry and recorded source-supported quality observations exist.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| lots | Lot ID | Item and stated expiry date |
| serial_units | SerialUnit ID | Item, serial identifier, optional lot |
| handling_units | HandlingUnit ID | Opaque identity with stated NVE |
| tracked_stock_current | Item/location + handling-unit/lot/serial identity tuple | Traceable stock and reservations; no guessed tracking links |

`lot.quality_release` and `movement.damage_report` are cataloged Facts. They support
observed quality statements, not a complete inspection/nonconformance/CAPA process.
Expiry can be corrected in place with an audit event: current expiry is not an
historical label automatically. Expired stock is observable, not automatically blocked.

## 7. Shipping and transport

Foundation/derivation present: Shipment, ShipmentPackage, ShipmentEvent,
ShipmentEventSupersession, `services/shipments.py`, Movement.shipment_package_id.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| shipments | Shipment ID | Direction, purpose, counterparty; current derived observation clearly labeled |
| shipment_packages | Package ID | Carrier/tracking identifiers |
| shipment_events | Event ID | Attributed tracking observations and supersession status |
| shipment_contents | Movement ID with package link | Actual physical contents through the shortest true link |

A carrier delivery event is not a stock posting. Older movements without package links
remain unlinked. Transport charges, freight invoices and carrier SLA coverage require
actual imported evidence and an agreed metric, not invented package allocations.

## 8. Returns and after-sales

Foundation/derivation present: ReturnAnnouncement, return/supplier_return Movements,
resolves_movement_id, return_announcement_id, credit-note evidence and exceptions.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| return_announcements | Announcement ID | Announced quantity, reason, expected date, current status |
| return_movements | Return Movement ID | Actually returned goods with original commitment link |
| return_resolutions | Resolving Movement ID | Explicit quantity resolutions against a returned Movement |

Use invoice/credit views for the money side; do not equate a return with a refund.
Return ratios need a stated population and period/cohort rule. Warranty claims,
service tickets, repair work and SLA tracking are missing dedicated domains.

## 9. Invoicing and order-to-invoice reconciliation

Foundation present: sales/supplier invoice and credit Documents/Lines,
DocumentLine.billed_document_line_id and FinancialComponent.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| invoice_documents | Invoice/credit Document ID, with explicit kind | Received totals/date/currency; sales and purchasing separated by kind |
| invoice_lines | Invoice/credit line ID | Received line values and actual billed-order-line link |
| financial_components | Component identity or authorized evidence component key | Stated net/tax/gross/base only where present, with header/line scope |

The billing relationship already exists; no fuzzy match on product/date/amount is needed.
Partial and consolidated billing require line-grain joins. A null billing link can
mean freight/service/rounding, not missing data. Do not sum header and line amounts as
one measure. Recording a document and posting its ledger effects are distinct acts.
Financial components may be derived on demand by `component_context`, not all present
in the physical FinancialComponent table; a raw-table-only view would omit coverage.

## 10. Receivables, payables and cash operations

Derivation present: financial_open_items/open_invoice_amounts, aging_register,
payment_rows, active_settlement_allocations, finance/credits.py and balances.py.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| open_items_current | Settleable document/control-item identity + currency | Open amount, due date, aging and side including opening items |
| payments | Payment evidence ID + currency | Observed payment amount and posting state; avoid double-entry duplication |
| settlement_allocations | Allocation ID | Explicit links between control postings with current active/reversal semantics |
| available_credits_current | Credit control-entry identity + currency | Unused customer/supplier payment or credit balance |
| party_balances_current | Party ID + customer/supplier side + currency | Canonical open/overdue/credit totals, preserving side |
| financial_opening_coverage | OpeningScope ID | Cutover date, source namespace, scope and coverage kind |

`aging_register(as_of=...)` feeds current `financial_open_items` into aging; as_of
changes the age calculation, not the financial population's historical cutoff.
Historical debt/DSO must not be advertised from this alone. Cash due-date schedules
are possible observations, not a complete forecast. Full bank-account reconciliation,
PSP payout/fee reconciliation, FX conversion and treasury planning need separate
coverage checks. Payment recording is not proof of bank execution.

## 11. Accounting and management accounting

Foundation/partial: LedgerEntry, LedgerReversal, SubledgerAccount, FinanceReference,
ComponentAssignment and ComponentAssignmentPart, finance/components.py.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| ledger_entries | LedgerEntry ID | Debit/credit, account, effective time, posting group and evidence |
| ledger_reversals | Reversal ID | Original and reversing groups; avoid original-plus-reversal misclassification |
| subledger_accounts | Account ID | Current account and role metadata |
| financial_assignments | Assignment revision ID | Reviewed case/coding decisions with basis and history |
| cost_center_shares | Assignment part ID | Explicit amount allocated to a cost center for one assignment revision |
| finance_references | FinanceReference ID | Cost centers, case codes and coding groups |

Select the current assignment revision for current cost analysis; keep revision history
separate. Original component amounts repeat across shares and must not be summed there.
The contract explicitly defines an operational subledger, not complete statutory
accounting/tax. Complete P&L, balance sheet, depreciation, consolidation, budget/actual
and product/customer contribution margin need full account coverage and cost/attribution
models. Existing net/tax values and cost-center shares are useful subsets, not proof
that those entire domains are absent or complete.

## 12. Pricing and commercial terms

Foundation/derivation present: PriceList, PriceListEntry, PartyPriceList,
PartyGroupPriceList, validity fields and `resolve_price`.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| price_lists | PriceList ID | Direction, currency and validity |
| price_list_entries | Entry ID | Item/unit/quantity tier and stated price |
| price_assignments | Assignment kind + assignment ID | Direct partner/group applicability and priority |

Resolved price depends on party, item, time, quantity, unit and currency; expose a
parameterized query, not a universal product.current_price column. Agreed line price
remains evidence. `sold_below_purchase_price` is a comparison against a standing
purchase price, not actual realized profit or cost of goods sold.

## 13. Process control, data quality and integration

Foundation/derivation present: BusinessEvent, ChangeProposal, SourceRecord/Stream,
ImportJob, InterpretationOutcome, RealityGap, projection checkpoints and exceptions.

| Proposed view | Row grain | Questions and limits |
|---|---|---|
| operational_exceptions_current | Exception class + affected opaque subject identity | Current canonical findings, not a historical daily backlog |
| business_events | BusinessEvent ID | Recorded business changes with effective/recorded time; not a universal state replay log |
| source_versions | SourceRecord ID | Version/receipt/source metadata, selective authorized attributes only |
| interpretation_attempts | InterpretationOutcome ID | Immutable terminal attempt outcomes; ImportJob alone is mutable queue state |
| reporting_coverage | Relation/projection version and applicable scope | Checkpoint/coverage metadata; upstream completeness may be unknown |
| observed_facts | Fact ID | Reviewed predicate, opaque subject, typed value and observed/recorded time |

Source payloads and action/chat inputs must not become a generic unrestricted export.
Sensitive/system/security tables are not business reporting relations. Facts extend
source-supported attributes; do not flatten all predicates into repeated measures or
assume newest recorded fact means current business state without a predicate policy.
Existing ProjectionRow caches are rebuildable; reuse requires matching grain/version
and visible checkpoints, not treating payload JSON as a new business authority.

## 14. Domains requiring new inputs/model work

| Company area | What can be reused | Missing domain foundations |
|---|---|---|
| CRM/pre-sales | Parties and retained sales history | Leads, opportunities, stages, activities, quotes and probability history |
| Marketing | Sales channel, party groups, orders | Campaign spend, impressions/clicks, attribution identities and consent scope |
| Production | Products, stock, movements, supply promises | BOMs, work orders, operations, resources, capacity, yield and manufacturing cost |
| Projects/services | Service items and invoices, some cost-center attribution | Projects, milestones, time entries, staffing, work-in-progress rules |
| HR/payroll | Application identities are not employee records | Employee contracts, employment history, payroll, attendance and absences |
| Customer support | Returns and damage/quality statements | Tickets, conversations, assignments, SLA clocks, warranties and repair jobs |
| Subscription business | Recurring purchases may appear as orders | Subscription contracts, service periods, changes/cancellations, recurring revenue basis |
| Fixed assets | Some purchase and ledger evidence | Asset register, useful lives, depreciation and disposals |
| Corporate FP&A | Operational ledger/cost references | Budgets/scenarios, legal-entity structure, consolidation, FX and complete accounting coverage |
| Compliance/sustainability | Source trace and logistics links | Domain-specific certifications, obligations, emission factors and measurement scope |

No single universal view fills these gaps. External payloads may contain relevant data;
this audit found no dedicated typed domain in the inspected model/catalogs. Add a
source-backed relation only after a real reporting question proves its meaning and use.

## Delivery recommendation

1. Complete spec 224's PostgreSQL/ClickHouse engine comparison before the production
   sales/security/save proof. Add partner-role/product
   catalog foundations as justified by that slice, explicitly reviewing population changes.
2. Expand to purchasing, commitments/revisions, reservations, movements and stock.
3. Add invoice/line relationships, postings, allocations and canonical current open items.
4. Add logistics/returns, tracked stock, pricing, cost-center detail and process coverage.
5. Prioritize missing domains from actual customer questions rather than prebuilding
   empty views. Define historical coverage per relation and measure before materialization.

These are several dozen reusable relations with declared grains, not hundreds of
report-specific summaries. Synonyms such as customers/suppliers and sales/purchase
invoice filters may be convenience aliases rather than separate physical structures.
Do not flatten every relationship into one giant table. A customer with 3 order lines
and 2 allocations can produce 6 joined rows; independent aggregates and explicit bridges
are essential. Every relation must retain tenant, opaque keys, source trail, units,
currency, temporal coverage and access restrictions.

## Inspected evidence

- `packages/reality-core/src/reality/db/core.py` and all sibling database model modules.
- `packages/reality-core/src/reality/services/analytics/orders.py`, `reporting_relations.py`.
- `packages/reality-core/src/reality/services/core.py`: fulfillment, revision, inventory,
  settlement, payment, ledger and aging readers.
- `packages/reality-core/src/reality/services/finance/`: components, allocations,
  opening, credits and balances; `services/exceptions.py` function boundaries.
- `packages/reality-core/config/resource_catalog.yaml`, `projection_catalog.yaml`,
  `fact_catalog.yaml` and targeted searches of `command_catalog.yaml`.
- `docs/DATA_MODEL.md` and feature contracts for inventory, ledger, payments,
  commitments, shipments, master data, operational fields, order-to-cash and purchasing.

No tenant data scan, query benchmark, migration or correctness test was performed by
this audit. Documentation occasionally lags code: e.g. the commitment contract's final
sentence contradicts its revision-quantity section; use tested canonical service
semantics when exposing views, not that stale sentence.
