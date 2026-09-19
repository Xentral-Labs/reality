# Analytics on your business reality

Reality connects operational records into a business graph you can query. Explore orders, stock and
payments, follow their relationships, and build reports over the data already held in Reality. Your
agents use the same model and checks as the analysis editor.

**No separate analytics database to keep in sync.** The graph describes existing records in
PostgreSQL; it does not require exporting them into a second graph database. External sources still
need to be brought into Reality and interpreted before they can be analyzed.

## Why the shared foundation matters

Suppose one order states a value of EUR 1,000 and contains four lines. A naive join can repeat that
order value four times and report EUR 4,000. Reality's model knows that the amount belongs to the
order and that the relationship to lines reaches many records. It refuses an unsafe sum instead of
presenting a plausible but wrong total.

The same principle applies to currencies, units and time: euros are not added to dollars, pieces are
not added to kilograms, and current stock is not summed across months.

| Business question                                    | What the model contributes                                                      |
| ---------------------------------------------------- | ------------------------------------------------------------------------------- |
| Which customers account for the largest order value? | Customer identity, received order amounts and separate currencies               |
| What is still to deliver?                            | Commitments linked to movements, with declared remaining-quantity measures      |
| What do customers owe us?                            | The same canonical financial-position calculations used by Finance              |
| Which articles have a shortage?                      | Current physical and reserved quantities from the operational inventory service |

An order value is **not recognized revenue**, a reservation is **not a shipment**, and available
stock is **not permission to ship**. Those distinctions stay visible in the model.

## Architecture: a graph over existing records

There are two connected paths: how business data enters Reality, and how an analysis reads it.

```text
SourceRecord → Document / DocumentLine → operational Reality records
                                            ↑
Question → declared business graph → checked query → PostgreSQL / shared services
                                            ↓
                              result + query explanation
```

The foundation includes **Facts, Commitments, Reservations, Movements and Ledger Entries**, as well
as source evidence, documents, partners and articles. This is not a graph built only from the `Fact`
table. “Business Facts” is the product area for inspecting records; `Fact` is one specific record
type.

A declaration describes the meaning of the data:

| Part     | Plain-language meaning                  | Example                                                            |
| -------- | --------------------------------------- | ------------------------------------------------------------------ |
| Node     | What one record represents              | One sales order or one article                                     |
| Edge     | Which records are actually related      | An order contains lines; a line refers to an article               |
| Grain    | What one row counts as                  | One order, not one order repeated for each line                    |
| Measure  | Which number can be aggregated, and how | Received order amount, separated by currency                       |
| Coverage | Which kind of observation is supported  | Current state, activity in a period, or a supported dated snapshot |

The graph layer validates paths and measures, then compiles ordinary questions into a SQL aggregate
over the existing PostgreSQL tables. Each node is scoped to the selected company. For stock and
financial positions, registered adapters call the **existing canonical services** and aggregate
their temporary results. Those paths can perform several bounded reads; they do not maintain a
second persistent copy or a competing balance calculation.

This is a semantic graph query layer on PostgreSQL, with **Cypher-like syntax**, rather than a
separate graph database or a fully compatible Cypher implementation. New declared paths over
existing data do not require copying that data into another storage engine.

For implementation details, see the
[graph declaration](https://github.com/Xentral-Labs/reality/blob/main/packages/reality-core/config/reporting_graph.yaml),
[query checks](https://github.com/Xentral-Labs/reality/blob/main/packages/reality-core/src/reality/services/analytics/traversal.py)
and
[SQL compiler](https://github.com/Xentral-Labs/reality/blob/main/packages/reality-core/src/reality/services/analytics/compile_sql.py).

## Explore the graph and build a report

You can start in three ways — no query language is required:

- **Use a template:** open **Analytics → Analysis** and choose a starting point such as **Order
  value by month**, **Order intake by customer**, **Stock shortages** or **Customer overdue**. A
  template opens an editable, unsaved analysis. Adapt its period, filters or grouping, run it, and
  save the question to **My reports** when useful.
- **Start with chat:** use **Create with chat** and describe the question, for example “Show order
  value by customer for this month, in EUR.” The action prepares a draft in the existing chat; you
  review and send it. Open a supported analysis proposal with **Open in analysis** to inspect and
  adjust it before saving.
- **Explore the data:** the **Data Explorer**, under **Explore data**, lets you discover available
  business objects, search their fields, inspect relationships and preview records. Use a field or
  path as the starting point for an unsaved analysis when you want to see what can be asked before
  choosing a report.

In the analysis editor, the editable sentence lets you choose records, conditions, measures,
grouping and sorting. All three starting points use the same checked model.

Three tabs explain the same question:

- **Result** shows the returned values and available table/chart presentation.
- **Connections** shows the records and relationships used by the question. It is a view of the
  query's connections, not a separate database containing a copy of your business.
- **Cypher** exposes an editable, parameterized path for readers who prefer query text.

Execute after editing the question. Unsupported paths or measures can still be refused; controls
guide construction but cannot guarantee that every combination is answerable. A changed or failed
question must not be read as if an earlier result answered it.

Use the stock, shortage, outstanding-payment or overdue-payment templates for operational positions.
Historical balance and physical-stock templates ask for an explicit snapshot date. Historical
reservations, historical availability and historical aging are not supported.

Explore the complete [Analytics model](../tool-usage/#analytics:): searchable objects, fields,
relationships, measures and starting templates.

## Example queries

Paste these paths into the **Cypher** tab and supply the parameters separately. The examples use
declared record and measure names, not arbitrary SQL columns. Date bounds include the start and
exclude the end. Results depend on the interpreted records held in your company.

### Order value by month and currency

```cypher
MATCH (o:order)
WHERE o.ordered_at >= $from AND o.ordered_at < $until
RETURN month(o.ordered_at), o.currency, sum(stated_order_amount), count(order_count)
```

```json
{ "from": "2026-01-01T00:00:00Z", "until": "2027-01-01T00:00:00Z" }
```

This sums the order amounts received from the source. It does not calculate revenue or reconstruct
amounts from quantity multiplied by price.

### Top ten customers by order value

```cypher
MATCH (o:order)-[:ordered_by]->(customer:party)
WHERE o.ordered_at >= $from AND o.ordered_at < $until
RETURN customer.id, customer.name, o.currency, sum(stated_order_amount)
ORDER BY sum(stated_order_amount) DESC
LIMIT 10
```

Use the same date parameters. Keeping the customer ID separates customers with identical names. The
limit selects ten customer/currency groups; it is not a currency conversion or a comparable
cross-currency ranking. Filter to one currency when you need that comparison.

### Order-line value for an article

```cypher
MATCH (o:order)-[:contains]->(line:order_line)-[:of_item]->(item:item)
WHERE item.sku = $sku AND o.ordered_at >= $from AND o.ordered_at < $until
RETURN item.id, item.sku, o.currency, sum(line_amount)
```

```json
{ "sku": "LAMP-001", "from": "2026-01-01T00:00:00Z", "until": "2027-01-01T00:00:00Z" }
```

Use your own article number. This counts received **line values**, not the parent order amount once
per line. It measures ordered value, not delivered quantity or paid revenue.

### An intentionally refused question

```cypher
MATCH (o:order)-[:contains]->(line:order_line)
RETURN line.sku, o.currency, sum(stated_order_amount)
```

The line grouping would repeat the order amount across its lines. The `fan_out` refusal asks you to
change the question rather than silently inflate the answer. Use `line_amount` for a line-grain
total. Similarly, `sum(o.gross_amount)` is not an escape hatch: this language requires declared
measures in aggregates.

## Performance: execution shape, limits and evidence

Avoiding another database removes the need to synchronize an analytics copy. It does not make
queries free: they still consume PostgreSQL and, for service-backed measures, application resources.
Selective filters, data volume, indexes, relationships and concurrent operational work all affect
latency.

The current execution contract includes:

| Property                      | Current behavior                                                                          |
| ----------------------------- | ----------------------------------------------------------------------------------------- |
| Ordinary graph question       | One aggregate SQL statement, rather than one query per returned record                    |
| Stock / finance service paths | Bounded canonical reads plus aggregation; actual reads are reported                       |
| Traversal limits              | At most 8 path steps; recursive depth at most 6                                           |
| Result budget                 | At most 10,000 result rows; default page size 200                                         |
| Statement timeout             | 30 seconds; a safety boundary, not a response-time promise                                |
| Large service inputs          | Explicit refusal when the adapter's input budget is exceeded; no silently truncated total |

Input budgets differ by service. For example, current article stock bounds articles and open
supplier commitments at 20,000 each, and movements and commitment revisions at 100,000 each. A small
result limit does not bypass the work needed to calculate a correct aggregate.

### Recorded measurements

A recorded comparison on a company with 10,233 documents and 13,590 ledger entries measured monthly
invoiced amounts at 3 ms, order intake by customer at 6 ms and whole-company balances at 753 ms
after the query improvements. Seventeen questions returned identical results before and after the
change. These are the best of three interleaved runs on a non-idle machine, not p95 measurements or
production guarantees. See the
[measurement conditions and complete results](https://github.com/Xentral-Labs/reality/blob/main/specs/234-analysis-derivation-cost/verification.md).

The difference explains why query shape matters: filtering before a canonical derivation can reduce
its input, while an unfiltered company-wide balance still requires the broader calculation. The
compiler also enforces a separate statement budget for derivations to catch accidental per-record
query loops.

### A useful load-test plan

Measure three workloads separately: monthly order totals, the multi-hop article query above, and a
current stock or financial-position template. For each, compare expected results first, then test
increasing record counts and concurrency (for example 1, 5 and 10 readers).

Record PostgreSQL version, machine resources, dataset size and distribution, query parameters, index
state, SQL-read count, warm/cold conditions, p50/p95 end-to-end latency, failures and impact on
operational writes. Separate time spent interpreting chat from query execution. Run only against
dedicated benchmark data.

There is **no published Analytics-specific scale or p95 guarantee here**. The
[engine comparison](https://github.com/Xentral-Labs/reality/blob/main/specs/224-native-reporting-platform/engine-comparison.md)
remains deferred; timings from other operational subsystems are not evidence for this engine.

## Agent access and saved reports

Agents call `graph_catalog` to discover the model and `graph_ask` to submit either a typed question
or a Cypher-like path with parameters. They submit no SQL. Company scope and execution checks come
from the application, not from an instruction the agent has to remember.

Save a question to **My reports** to reuse it. The saved artifact is the **question**, not a frozen
answer; reopening executes it again. Chat-driven saving uses `graph_report_change_propose` and
explicit confirmation. Trusted user identity comes from the application; tenant-only credentials
cannot own private reports. Reads need no confirmation.

See [tool schemas](../tool-usage/commands) and [agent playbooks](../agent-playbooks/).

## What an answer covers

An answer describes interpreted records held in the selected company, within the chosen filters and
supported history. An empty answer does not prove that an external source never received an order.
Missing amounts stay unknown. Source amounts remain recorded values; derived stock and balances
remain observations. Inspect the query explanation, connections and underlying records when you need
to understand a number.
