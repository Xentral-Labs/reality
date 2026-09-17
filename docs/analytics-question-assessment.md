# SMB analytics question assessment

Date: 2026-09-13. Status: repository assessment and proposal, not an approved implementation specification.

Spec impact: none. This document assesses existing behavior and describes candidate work; it changes no schema, service, tool, or product behavior.

## Scope and method

The 30 questions below come from the product discussion. They are a candidate evaluation set, not measured customer demand. The assessment reads model definitions, application services, MCP schemas, feature contracts, and existing test cases. It does not inspect a live company's data, run these 30 queries, benchmark PostgreSQL against a graph engine, or certify the existing tests as passing.

“Data present” means the model can represent it. It does not establish that each connector supplies it, each retained record has it, or the retained history covers the business's whole lifetime.

Classification:

- **E — Existing read:** a current public read answers the question under its documented operational meaning, sometimes with client filtering or paging.
- **C — Composition gap:** recorded data or existing derivations provide the principal ingredients; a reusable analytical query, grouping, or complete read surface is missing. Ordinary metric definitions still apply.
- **D — Domain decision:** the wording requires an additional substantial definition, allocation/scenario policy, historical interpretation, or evidence not established by the inspected model. A narrower descriptive question may already be possible.

Classification is deliberately conservative: an agent collecting many records and calculating in its context is not considered a complete analytical query service.

## Assessment of all 30 questions

| # | Question | Class | Existing basis | Remaining work or qualification |
|---|---|---|---|---|
| 1 | Which customers ordered product X in ISO week 7? | C | Document.party_id / ordered_at; DocumentLine.item_id / document_id [M] | Join and distinct customer query; require ISO year and business timezone. Missing order dates stay unknown. Apply retained-order/source-version policy. |
| 2 | Which customers have not ordered for three months? | C | Parties and dated sales orders [M] | Last-order aggregation / anti-join. Define previously buying customers versus all customer-role parties. Report history coverage. |
| 3 | Which customers ordered for the first time this month? | C | Dated sales orders [M] | Minimum order date by customer. Claim only first observed order in retained history unless earlier history is known complete. |
| 4 | Which customers increased or reduced order value most versus the previous quarter? | C | Stated order or line amounts, currency, order date [M] | Period comparison and ranking; distinguish absolute and relative change, zero baseline, partial current quarter, and cancellation treatment. Never duplicate header totals through line joins. |
| 5 | Which customers buy A but not B? | C | Order/customer/product relationships [M] | Existence and anti-existence queries with a defined history window. Absence means no matching retained purchase. |
| 6 | Which products were ordered most this month? | C | Order lines with quantities, items and units [M] | Group and rank; choose units, order count, or distinct customers. Do not add incomparable units. |
| 7 | How do weekly order quantity and value develop by product? | C | Order timestamps and stated line quantities/amounts [M] | Time buckets, grouping and period completion; separate currencies/units. Preserve stated amounts rather than recreating them from price times quantity. |
| 8 | Which products are frequently ordered together? | C | Multiple product lines linked to one order [M] | Distinct product pairs within each order and support counts; exclude self-pairs and repeated-line inflation. Customer-wide association is a different metric. |
| 9 | At which agreed prices did we sell X to different customers? | C | DocumentLine.unit_price, unit, currency via document [M] | Historical price grouping and selection. Use agreed evidence, not today's price resolver; distinguish comparable price bases. |
| 10 | Which products are frequently cancelled or returned? | C | Commitment cancellation/status, return Movements and return announcements [M, O] | Separate cancellation and physical-return counts/quantities; define denominator and period. An announced return is not received goods; an operational cancellation is not automatically a source order cancellation. |
| 11 | Which customer orders are not fully shipped? | E | commitments_list, fulfillment_queue, order_explain [T, R, P] | Existing operational interpretation: open customer delivery promises with remaining quantity. Cancelled remainders are not actionable; documentless promises are not invented orders. |
| 12 | Which delivery promises are overdue, and which customers are affected? | E | exceptions_list / exception_explain; effective promise dates [T, X, D] | Existing overdue outgoing commitment rule; unknown dates are not declared overdue. This measures dispatch fulfillment, not proof of customer receipt. |
| 13 | Which orders can we fulfill completely from available stock? | D | Inventory, reservations, fulfillment queue, holds [R, P] | Existing ship_ready means reservation/hold readiness. Define individually feasible versus simultaneously feasible orders, competing demand, locations and priorities. Do not relabel queue readiness as an allocation simulation. |
| 14 | Which products and quantities are missing for open orders? | D | item_supply_demand, inventory, fulfillment_blockers [P, R] | Define physical shortage versus reservation gap and time/location scope. Current uncovered_demand sums unreserved open quantity; free stock may still exist. Incoming promises are not physical stock. |
| 15 | How long from order to complete delivery, by customer/product? | D | ordered_at; effective shipment Movements; shipment observations; promise revisions [M, D, O] | Choose dispatch completion or customer receipt, original or revised quantity, correction treatment, cancellations and partial orders. No universal stored completion timestamp answers all meanings. |
| 16 | Where is stock of X and how much is reserved? | E | inventory_read with item_id and location view [T, R] | Existing physical/reserved/available values, units and location filters; only retained inventory truth is promised. |
| 17 | Which stocked items have no outbound movements for 90 days? | C | Current stock and timestamped Movements [M, R] | Current-positive-stock filter plus anti-join; define sales shipment versus any outbound movement, including transfers/returns/write-offs. Apply correction semantics. |
| 18 | Which stocks do not cover already promised customer quantities? | C | Physical stock and open_customer_demand [P] | For a present, company-wide quantity comparison, aggregate and compare using existing meanings. Location/date feasibility or assignment to particular orders moves into questions 13/14. |
| 19 | Which open supplier orders are due next week? | C | Supplier commitments, effective due dates, remaining receipts [D, R] | Filter by commitment type and date window, then group by evidence order. This is the supplier's current promise, not a predicted arrival. |
| 20 | Which customer orders might be affected by a late supplier delivery? | D | Supplier promises and customer demand share item identities; blocked_order_keys [P, M] | An item overlap can identify candidate exposure. No general supplier-promise-to-customer-promise allocation was established. Define time-phased coverage and competing supply before claiming causal impact. |
| 21 | How often does each supplier deliver late? | D | Original/revised commitments and receipt timestamps [M, D] | Define original versus latest agreed date, partial/full receipt, open overdue promises, quantity or order weighting and missing dates. Current overdue exceptions alone cannot measure historical delivery performance. |
| 22 | How have agreed purchase prices changed by product? | C | Purchase-order evidence and unit_price [M] | Historical grouping and comparison by currency/unit/price basis; do not substitute current price lists. |
| 23 | From which suppliers did we buy X, at which prices and quantities? | C | Purchase document parties and lines [M, O] | Group by supplier/product/date; distinguish ordered, received and invoiced quantities. |
| 24 | For which products are we dependent on a single supplier? | D | Retained purchase history can count observed suppliers [M] | “Only one observed supplier in this period” is answerable by grouping. Actual dependence requires evidence about qualified/available alternatives; history alone does not establish it. |
| 25 | Which purchase orders are only partly received or invoiced? | C | Supplier fulfillment and exact billed_document_line_id relationships; _order_line_billing [D, B, O] | Compose complete order/line read using existing partial billing and receipt rules. Handle reversals, returns and unit comparability explicitly. |
| 26 | Which customer invoices are open or overdue? | C | financial_open_items, aging_register; party balances and overdue exceptions [F, T, X] | Core services exist. Public balances aggregate by party; overdue exceptions are not a complete open-invoice list. Expose/reuse invoice-level reads with complete traversal. Unposted evidence is a separate category. |
| 27 | How many days after due date does each customer pay on average? | D | Payment effective_at, allocations, invoice dates and payment terms [M, F] | Payment time differs from allocation time. Define partial payments, weighting, credits/noncash reductions and historical due dates. Current mutable/fallback payment terms are not proof of terms in force for every past settlement. |
| 28 | Which shipped order lines are not fully invoiced? | C | shipped_not_billed exception, billing line links and fulfillment [X, B, D] | A current exception already answers its defined discrepancy case. A complete analytical register must reuse and reconcile applicable return, reversal and unit rules; dispatch is distinct from customer receipt. |
| 29 | Which payments still have unallocated amounts? | E | finance_payments with only_unallocated [T] | Existing allocated/unallocated payment read. Honor any list limit; do not infer upstream completeness from a bounded response. |
| 30 | What are open receivables/payables by due week and currency? | C | aging_register, open items, currency-safe finance services [F, R] | Group existing invoice-level results by side, ISO due week/year and currency. Keep unknown due dates separate; this is due-date exposure, not a cash receipt forecast. |

Summary: 4 existing-read cases, 19 composition cases and 7 substantial domain-decision cases. These counts classify this wording and are not a product coverage percentage. Several C cases already have useful specialized reads, and D cases often have useful narrower answers.

## Findings that affect the design

1. **The primary access gap is composability.** The MCP catalog exposes discovery, fixed operational reads and focused finance tools. The inspected public catalog has no general analytical request combining arbitrary supported dimensions, measures, joins and time filters. Discovery mainly offers family, text query and ID; it does not replace analytical aggregation.
2. **Operational definitions must survive reuse.** `uncovered_demand` currently means unreserved open demand. `ship_ready` derives from reservations and holds. Neither establishes simultaneous stock feasibility. A generic query must not silently give these fields a stronger business meaning.
3. **The model already holds more history than the dashboard exposes.** Order dates, line prices, promise revisions, physical returns and exact invoice-line links are present. The legacy `company_insights` (retired by spec 221) exposed fixed metrics and 7/30/90-day windows; its created series uses commitment creation time, which is not order placement time.
4. **Retained history is not historical reconstruction.** Read metadata explicitly reports retained-record scope and unknown upstream freshness. Source streams version external evidence; Shopify versions above the first require review in the inspected interpreter. Neither a latest-source pointer nor a raw document count is a general order-version reconciliation rule. An analytics implementation must establish each supported intake path's order identity and version policy before counting.
5. **Pagination does not establish analytical consistency or bounded cost.** Current live keyset reads are not an atomic multi-query snapshot. Operational derivation can read the full relevant tenant state before slicing. Loading every page into an agent is therefore a weak foundation for exact totals at scale.
6. **Missing business evidence must remain visible.** Unknown order dates, incomplete historical imports, missing item identity and incomparable units should produce explicit coverage information. Database defaults alone do not prove that a source supplied a zero price or amount.

## Candidate next feature, subject to the normal specification workflow

Keep PostgreSQL as operational authority. Build a general, read-only analytical application service, exposed through the same tools to CLI, chat and MCP. Reuse established calculations; do not let adapters or the model independently redefine fulfillment, open financial amounts, corrections or effective promises.

Candidate discovery describes datasets, record grain, fields, units, measures, supported joins, date meanings and coverage. Candidate execution accepts a composable analytical request and returns database-computed results plus applied definitions, observation/consistency metadata and drill-down references. These are proposed capabilities, not existing tool names.

Start with order-line evidence and existing current inventory/fulfillment observations. Add financial due-date aggregation over the current shared services. An implementation plan should choose a structured query representation or validated SQL on approved read surfaces; this assessment does not pre-approve either mechanism. Tenant scope and read authority must be enforced by execution, not merely requested in a model prompt.

Support composition such as filters, distinct counts, sums of stated values, grouping, date buckets, ranking, existence/anti-existence and period comparisons. Deduplicate order/customer/product identities and pre-aggregate one-to-many relations before combining totals. Pair analysis can follow after basic order queries. New business measures still need a definition and evidence; general query syntax does not make them automatic.

Do not require schema expansion for descriptive order/product/customer grouping without a demonstrated missing input. Do not promise historical supplier reliability, actual sourcing dependence or a supply allocation simulation in the first increment.

## Verification contract

Use deterministic fixtures with exact expected answers, not just successful query execution. Plan them in the feature's specification and tasks before implementation:

- Two tenants with similar names/SKUs and foreign IDs; all discovery, joins and drill-down remain isolated.
- ISO year boundaries, non-UTC business weeks, missing dates and late imports.
- Multiple lines for one item, several invoices/payments per order and partial shipments; no multiplication of header amounts or quantities.
- Source replay, reviewed/new/uninterpreted versions and incomplete history; no invented “first ever” or globally absent relationship.
- Multiple currencies, incomparable units, supplied prices and totals that differ from multiplication; stated values stay authoritative.
- Cancellations, corrected movements, returns, quantity/date revisions and invoice reversals; compare analytics with canonical service answers.
- Unreserved but sufficient stock and competing orders; reservation gap cannot masquerade as physical shortage or a feasible allocation plan.
- Payments allocated later than their effective date, partial settlement and changed terms; unsupported historical claims are explicit.
- Complete aggregation across more rows than a tool page, repeatable result/trace consistency as designed, timeout/row limits and representative tenant-size performance.

Existing tests provide reusable setup and expected behavior, not proof that the candidate tool exists. Relevant files include `test_mcp_read_contract.py`, `test_commitment_revisions.py`, `test_partial_invoicing_rebilling.py`, `test_inventory_and_fulfillment.py`, `test_unified_payment_entry.py`, `test_returns.py`, and operational exception derivation tests under `packages/reality-core/tests/`.

## What this establishes about a graph database

The inspected questions primarily require grouping, filtering, explicit relationships and reuse of business definitions. No question in this set establishes a need to migrate operational storage. Product-pair analysis is a finite same-order relationship. Supplier impact is presently constrained by business meaning and allocation evidence; storing the same records as a graph would not supply that evidence.

If later questions require extensive variable-depth relationship exploration, compare a rebuildable graph read model with PostgreSQL against the same expected answers and representative data. Measure correctness, latency, development effort, freshness and operational cost. No comparative performance claim is established by this assessment.

## Evidence map

- **[M] Model:** [core ORM definitions](../packages/reality-core/src/reality/db/core.py), [data model contract](DATA_MODEL.md).
- **[T] Agent access:** [MCP catalog and input schemas](../packages/reality-core/src/reality/mcp/catalog.py).
- **[R] Read semantics:** [MCP read contract](features/mcp_reads.md), [read services](../packages/reality-core/src/reality/services/read_contracts.py).
- **[P] Operational derivations:** [projection builders](../packages/reality-core/src/reality/services/projections.py), [projection catalog](../packages/reality-core/config/projection_catalog.yaml).
- **[D] Effective delivery state:** [delivery reads](../packages/reality-core/src/reality/services/delivery_reads.py).
- **[B] Billing:** `_order_line_billing` and invoice operations in [core services](../packages/reality-core/src/reality/services/core.py); [partial invoicing tests](../packages/reality-core/tests/test_partial_invoicing_rebilling.py).
- **[F] Finance:** `financial_open_items`, `aging_register`, `invoice_due_date`, `effective_payment_term` in [core services](../packages/reality-core/src/reality/services/core.py); [party balances](../packages/reality-core/src/reality/services/finance/balances.py).
- **[O] Operational contracts:** [order to cash](features/order_to_cash.md), [procure to pay](features/procure_to_pay.md), [physical shipments](features/shipments.md).
- **[X] Exceptions:** [exception definitions and test references](../packages/reality-core/config/operational_exception_catalog.yaml).
- **Dashboard scope:** [retired company insights](../specs/221-remove-analytics-overview/spec.md).
