# Inventory Cost, DB1 and DB2

[Back to the guide overview](../business-reality-guide)

## What the two margins mean

Reality's `commercial_v1` contribution profile answers how much of received net revenue remains
after two separately reviewed cost layers:

```text
DB1 = received net revenue − consumed acquisition cost
DB2 = DB1 − direct selling cost − allocated selling cost
DB2 rate = DB2 ÷ received net revenue, when received net revenue is positive
```

DB1 therefore answers whether the sale covers the cost of the goods or directly consumed service.
DB2 additionally answers what remains after the supported selling expenses assigned to that sale. It
is a commercial contribution view, not a statutory profit-and-loss statement. Product-fixed cost,
general overhead, tax profit, cash flow and a legal inventory valuation are different questions
unless a future named profile explicitly includes them.

The most important rule is: **Reality does not invent a complete margin from incomplete inputs.** A
supported DB1 can exist while DB2 is unknown. Unknown is not zero.

## The bridge from evidence to the displayed number

```text
Supplier evidence
  → received financial components
  → explicit acquisition-cost attribution and category review
  → reviewed receipt cost
  → reviewed inventory policy, ownership and movement history
  → consumed acquisition cost for the invoiced and fulfilled sales line

Customer invoice line
  → received net revenue for that exact commercial scope
  → DB1

Selling-expense evidence
  → explicit direct or allocated attribution to the sales line
  → independent selling-cost category review
  → DB2

Every result
  → retained review and generation
  → Inspector links to the decisions, evidence and original source payload
```

The browser performs none of this arithmetic. It requests the shared costing service and presents
its result, state and trace. CLI, Chat, MCP and the web application use the same services.

## Which values enter the calculation

| Layer                  | What Reality uses                                                                                                         | What it deliberately does not infer                                              |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Revenue                | Received net revenue of the supported sales-invoice line and its matched fulfilled quantity                               | Revenue from payment, gross minus reconstructed tax, or an unrelated order total |
| Goods cost             | Cost actually consumed from reviewed receipt or opening layers under the confirmed FIFO or specific-identification policy | Current purchase price, list price, warehouse location or an invented average    |
| Acquisition additions  | Assigned inbound freight, duty, other acquisition cost and supported nonrecoverable input tax                             | Recoverable tax or an unassigned supplier charge                                 |
| Purchase reductions    | Explicitly evidenced and assigned supplier reductions                                                                     | A payment difference treated as discount without evidence                        |
| Direct selling cost    | Selling evidence assigned directly to this sales line                                                                     | A matching amount, customer or date used as an implicit link                     |
| Allocated selling cost | Selling evidence distributed by an explicitly selected supported allocation                                               | An automatically chosen allocation driver or arbitrary overhead spread           |

Acquisition cost and selling cost are mutually exclusive families. The same received component
cannot be counted in DB1 and again in DB2. The reviewed selling categories are outbound freight,
fulfilment, packaging, payment fee, marketplace commission, sales commission and other selling.

## A complete example

The canonical complete example contains 60 fulfilled and billed units:

| Contribution bridge       |      Amount |
| ------------------------- | ----------: |
| Received net revenue      |   EUR 1,200 |
| Consumed acquisition cost |   − EUR 630 |
| **DB1**                   | **EUR 570** |
| Direct selling cost       |    − EUR 90 |
| Allocated selling cost    |    − EUR 24 |
| **DB2**                   | **EUR 456** |
| **DB2 rate**              |     **38%** |

The EUR 630 is not `60 × today's purchase price`. It is the exact cost consumed from the reviewed
inventory layers. The EUR 90 and EUR 24 remain separately visible so a reviewer can see which
selling costs were direct and which were allocated.

If the selling-cost review is incomplete, this same case can still show supported DB1 of EUR 570
while DB2 remains unknown. If all seven selling categories were explicitly reviewed as zero or not
applicable, DB2 could validly equal DB1. An empty checklist never means zero.

## When a result is calculated

Reality derives the monetary observation at read time from retained inputs. It does not store DB1 or
DB2 as a new financial authority. For dependable company reporting, a background job may build a
generation from a frozen census and publish that verified generation; the values still remain
derived observations with their exact input membership.

Two times are always relevant:

- **Valuation cutoff:** the economic boundary. Only supported movements and commercial activity at
  or before this instant belong to the answer.
- **Knowledge cutoff:** what Reality had received and reviewed when the basis was sealed.

A later invoice, attribution, movement correction or relevant review does not rewrite an older
answer. It produces a need for a new review or generation. Historical selection reproduces the
retained earlier basis.

## Understand the status before reading the amount

| State                    | Business meaning                                                      | How to use it                                                               |
| ------------------------ | --------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Ready / current**      | Required membership and reviews are complete for the selected cutoffs | Use the displayed result for the stated scope                               |
| **Historical**           | An exact earlier review or generation was selected                    | Use it to explain what was known then, not as today's answer                |
| **Stale**                | Later relevant evidence exists                                        | Inspect the retained basis, then request and confirm a refreshed review     |
| **Pending**              | A requested generation is not yet verified and published              | Wait for the shared worker; do not substitute the previous value as current |
| **Unknown / incomplete** | Required evidence, assignment or review is missing                    | Resolve the named gap; never interpret it as zero                           |
| **No activity**          | The selected complete scope contains no applicable business activity  | This is a reviewed empty scope, distinct from missing evidence              |

Totals preserve coverage. A report may show known DB1 for the covered positions and separately name
how many positions are required. It must not subtract incomplete cost subtotals from all revenue and
label the result complete.

## How the process is operated

1. **Receive evidence.** Supplier invoices, credits, customer invoices and movements enter through
   normal source and application paths. Source-stated amounts remain unchanged.
2. **Assign cost components.** An owner previews and confirms where a received acquisition or
   selling component belongs. Unassigned remainder remains visible.
3. **Review receipt scope.** All acquisition categories receive a reasoned disposition. Explicit
   zero and not applicable are decisions; absence is not.
4. **Review inventory.** The owner confirms economic ownership, currency, base unit, cutoff,
   complete movement history and FIFO or specific identification. Reality checks that the request
   omitted nothing in the bounded scope.
5. **Review contribution.** Revenue and fulfilled quantity are matched to the exact sales line. This
   can finalize DB1. The independent selling-cost checklist can then finalize DB2.
6. **Build and publish reporting scope.** Company census, captured basis and generations freeze
   exact membership for repeatable reporting. Workers calculate; they do not approve financial
   decisions.
7. **Inspect and refresh.** Operational findings identify missing acquisition cost, unassigned cost,
   stale review or negative actual DB1. A person follows the trace, corrects the evidence or
   confirms a new review, and then rebuilds the affected reporting scope.

Every mutating cost decision uses preview and explicit owner confirmation. A scheduler, worker or
agent cannot silently activate a policy or approve a cost attribution.

## Reading the explanation in the product

The contribution explanation presents received net revenue, consumed acquisition cost, DB1, reviewed
selling costs, DB2, valuation cutoff and knowledge cutoff. Ordinary money follows the user's locale;
the adjacent exact retained value preserves the four-decimal service amount. Unit costs retain up to
six decimal places where supplied.

Use **Inspect cost basis** to follow the result through its contribution review, inventory review,
receipt manifests, cost assignments, documents and original source records. The Inspector is the
audit path; there is no separate browser-only calculation.

For a management review, ask these questions in order:

1. Is the result current, historical, stale, pending or incomplete?
2. What are the valuation and knowledge cutoffs?
3. How many required positions are covered?
4. Which amount is received revenue, consumed acquisition cost, direct selling cost and allocated
   selling cost?
5. Which owner-confirmed reviews and source records support them?
6. Are currencies, base units and economic ownership compatible, or is conversion evidence named?

## Common misunderstandings

- **“There is no selling-cost record, so DB2 equals DB1.”** No. DB2 is unknown until every selling
  category is evidenced, explicitly zero, or not applicable.
- **“The invoice exists, so revenue is enough.”** No. Final DB1 also needs compatible fulfilled
  quantity and reviewed consumed acquisition cost.
- **“Use the latest supplier price.”** No. Reality follows the confirmed consumed inventory layers.
- **“A payment proves revenue for DB1.”** No. Payment and settlement answer cash and receivables
  questions; the supported invoice-line scope supplies commercial revenue.
- **“A location tells us who owns the stock.”** No. Physical custody and economic ownership are
  separate; mixed, consignment and transit ownership require explicit evidence.
- **“A newer event updates the old report.”** No. History remains reproducible; a new basis and
  generation are required.
- **“DB2 is company profit.”** No. It is the result of the named `commercial_v1` cost scope.

## The control principle

Reality separates what a source stated, what an owner decided and what the system derived. That is
why the margin can be repeated, challenged and explained without turning a calculation into a second
financial authority.

Next: [Summary](./07-model-at-a-glance). For exact records and tools, see
[Tool Usage](../../tool-usage/) and the [table map](../../reference/table-map).
