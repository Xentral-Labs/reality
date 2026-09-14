# Analytics: from a question to its evidence

Ask “Which customers ordered Product X in week 7?” in the existing chat, or open **Analytics →
Explore** and build the same question visually. Both use the same analytical tools and company
scope.

## Build your first report

1. Select your company and open **Explore**. Choose sales order lines.
2. Resolve Product X using the product selector. Names help you find a product; the selected
   identity determines the filter.
3. Select order date, ISO week **7**, year **2026**, and the business timezone. A week without a
   year is ambiguous.
4. Group by customer and select order count or ordered quantity. Run the analysis.
5. Open the supporting records for a value, then follow the order evidence into the Inspector and
   original source where available.

An empty result means no matching retained records. It does not prove that the source system never
received such an order.

## Three useful starting points

- **Customers for a product and week:** the example above, grouped by customer.
- **Product demand over time:** group sales order lines by week and product. Compare quantities
  within their units; stated values remain separated by currency.
- **Open invoices by due week:** select invoice open items and group by due week and currency. This
  describes current outstanding items, not a cash forecast.

## Explore, save and export

Change filters, measures, grouping or sorting, then run again. Editing a draft does not change the
meaning of the result already displayed. If execution fails or is cancelled, the previous successful
result remains visible with its executed settings.

Use a table, bar chart, line chart or compatible pivot. Supporting records explain a selected
measure; distinct order counts and totals need not equal the sum of visible rows. Choose a
previous-period comparison with explicit dates and inspect both periods. A percentage change from
zero is unknown.

Save the definition to **My reports**. You can reopen, rename, duplicate or delete your private
report. Reopening reads current data; relative dates resolve again. Saving does not freeze the
result. Export CSV for all matching result rows within the declared limit, rather than only the
visible page.

**Discuss analysis** attaches the definition to the existing chat. **Open in Reports** returns an
agent's supported result to an editable Explorer.

## How an agent operates it

1. Call `analytics_catalog` to discover datasets, dimensions, measures and supported relationships.
2. Resolve product/customer references with the existing reference tools.
3. Call `analytics_query` with a structured definition.
4. Read the returned observation time, resolved dates, units, currencies and missing-data
   information.
5. Call `analytics_contributors` with that executed definition, group and measure to explain a
   number. Use `analytics_export` for CSV.

The agent submits no SQL. Reading needs no confirmation. Private changes use
`analytics_report_change_propose` and explicit confirmation; trusted user identity is supplied by
the application, never invented in tool arguments. Tenant-only credentials cannot own private
reports.

See the [exact tool schemas](../tool-usage/commands) and [agent playbooks](../agent-playbooks/).

## What the answer covers

Results describe interpreted records held in the selected company. Missing amounts stay unknown;
units and currencies are not silently combined. Contributors and exports are fresh observations and
can differ when data changes. A broad query may ask you to narrow its filters rather than returning
a hidden sample.

<details>
<summary>30 business questions and their supported meanings</summary>

| Question                               | What you can establish                                                     |
| -------------------------------------- | -------------------------------------------------------------------------- |
| Customers buying X in week 7           | Customers with matching retained orders; specify year and timezone.        |
| Inactive customers                     | Previously observed buyers without orders in a chosen window.              |
| New customers                          | First observed purchase in retained history.                               |
| Customer growth                        | Period changes in stated order values, per currency.                       |
| Buyers of A but not B                  | Presence and absence in a specified retained period.                       |
| Top products                           | Rank by orders, buyers or comparable quantity.                             |
| Weekly product demand                  | Quantities and stated line values, per unit/currency.                      |
| Products bought together               | Distinct product pairs on the same order.                                  |
| Customer prices                        | Recorded agreed prices, not today's price list.                            |
| Cancellations and returns              | Separate cancellation counts and received-return quantities.               |
| Incomplete deliveries                  | Current open customer delivery commitments.                                |
| Late customer promises                 | Current overdue outgoing commitments.                                      |
| Orders ready from stock                | Reservation/hold readiness; no allocation optimization.                    |
| Missing products                       | Reservation gaps or physical stock versus demand, separately.              |
| Delivery duration                      | Dated shipments; no universal receipt/completion metric.                   |
| Stock by location                      | Current physical, reserved and available quantities.                       |
| Stock without outflow                  | Positive stock with no selected effective outbound movement.               |
| Stock below demand                     | Company-wide stock versus open demand, not a supply plan.                  |
| Purchases due next week                | Supplier promises with effective dates, not arrival forecasts.             |
| Customers affected by supplier delay   | Candidate demand for the same product, not proven allocation.              |
| Supplier punctuality                   | Current late promises; no historical reliability rate.                     |
| Purchase price trends                  | Historical stated prices by product, currency and unit.                    |
| Suppliers for X                        | Observed purchase history, with ordered/received quantities distinguished. |
| Single-supplier dependence             | One observed supplier; not proof that alternatives do not exist.           |
| Partially received or billed purchases | Canonical receipt and billing observations.                                |
| Open customer invoices                 | Current open items and aging.                                              |
| Payment lateness                       | Recorded payments and due-date context; no invented average KPI.           |
| Shipped but not fully billed           | Shipment/billing discrepancies with supporting records.                    |
| Unallocated payments                   | Recorded allocated and unallocated amounts.                                |
| Receivables/payables by week           | Current open items by due week and currency.                               |

</details>
