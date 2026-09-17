# Filling the Model, and Asking It Things

Companion to [data-model.md](data-model.md). Status: planned; nothing here executes yet.

## Part 1: The model is declared, not filled

The most common misunderstanding about this design is that objects are inserted into a
graph. They are not. **Nothing is ever written into the reporting graph.** It is a
declaration that says how to read the tables that already exist, and it holds no rows.

Three things are easy to confuse, so they are separated here.

| | What it is | Who writes it | When |
|---|---|---|---|
| **The declaration** | Nodes, edges, measures in `config/reporting_graph.yaml` | A developer, reviewed | Once per business concept, then rarely |
| **The data** | `document`, `document_line`, `party`, `ledger_entry`, … | The existing ingestion path, unchanged | Continuously, as business happens |
| **The extension** | `fact` rows for concepts the schema does not model | Interpretation rules, unchanged | Continuously |

The data path does not change at all in this feature. A source system sends a payload,
`source_record` retains it losslessly and versioned, interpretation writes the typed
rows, and Facts record what was concluded. Declaring a node adds a way to *read* that;
it adds no write, no copy, no job and no table.

This is why the question "when is the model filled" has a slightly surprising answer:
**the day the table gets its first row, because the model was already pointing at it.**

### The life of a declaration

1. **Propose.** A node, edge or measure is written as configuration. A node names its
   table, grain, key, tenant column and any discriminating predicate. An edge names its
   direction, multiplicity, carrying column and whether it recurses. A measure names its
   node, source, unit and additivity.
2. **Validate against the live schema.** Loading checks that every table, column and
   foreign key exists and that multiplicity matches reality — a `n:1` edge declared over a
   column with no unique constraint on the target is rejected. Schema drift fails a test,
   not a query at runtime.
3. **Review.** Multiplicity and additivity are business statements, not technical ones.
   They are the two places a mistake produces confident wrong numbers, so they are read by
   a person, once, instead of being re-derived per question forever.
4. **Version and publish.** The model version goes into every saved report, so a stored
   report always says which meaning produced it.

The cost model is the point: a new business concept costs one review. A new *question*
costs nothing.

### What each node must declare

Beyond grain, key and tenant column, every node declares two things that are easy to
forget and expensive to omit:

- **Temporal coverage** — whether it can answer current state, business-dated activity, or
  neither, and what is missing before it could answer an as-of question.
- **Update semantics** — how this node changes when the world corrects itself. This is not
  cosmetic; see [scale-and-updates.md](scale-and-updates.md), where it turns out the
  answer differs by node and changes what an aggregate means.

## Part 2: Questions

Written in the Cypher-near surface because it reads well. Chat and the API author the
same thing as a typed object. Examples marked **needs declaration** work only after the
named node, edge or measure is added as configuration — they are included deliberately,
because seeing what a new question costs is the point of the model.

### Sales

**Revenue by month and currency**

    MATCH (o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN month(o.ordered_at), o.currency, sum(stated_order_amount)

**One customer, this period against last year**

    MATCH (c:party {id: $customer})<-[:ordered_by]-(o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN month(o.ordered_at), o.currency, sum(stated_order_amount), count(o)

Run twice with shifted bounds and compare, or declare the comparison in one query with
two period parameters. Customers present in only one period still appear, with zero.

**Top ten customers**

    MATCH (c:party)<-[:ordered_by]-(o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN c.name, o.currency, sum(stated_order_amount)
    ORDER BY sum(stated_order_amount) DESC
    LIMIT 10

**Top three products per month** — note `line_amount`, not `stated_order_amount`,
because the path reaches line grain

    MATCH (o:order)-[:contains]->(l:order_line)-[:of_item]->(i:item)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN month(o.ordered_at), o.currency, i.name, sum(line_amount)
    ORDER BY month(o.ordered_at), sum(line_amount) DESC
    LIMIT 3 PER month(o.ordered_at)

**Quantity sold per article** — `quantity` is additive per single item only, so grouping
by item is required and grouping across items is refused

    MATCH (l:order_line)-[:of_item]->(i:item)
    WHERE l.requested_at >= $from AND l.requested_at < $until
    RETURN i.name, l.unit, sum(quantity)

**Average order value** — a ratio of two measures at the same grain

    MATCH (o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN o.currency, sum(stated_order_amount) / count(o)

**Orders by sales channel**

    MATCH (o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN o.sales_channel, o.currency, sum(stated_order_amount), count(o)

**Customers who ordered last year but not this year**

    MATCH (c:party)<-[:ordered_by]-(o:order)
    WHERE o.ordered_at >= $prior_from AND o.ordered_at < $prior_until
    AND NOT EXISTS {
      MATCH (c)<-[:ordered_by]-(r:order)
      WHERE r.ordered_at >= $from AND r.ordered_at < $until
    }
    RETURN c.name, sum(stated_order_amount)

**Delivery address different from the invoice party** — the reason edges are named

    MATCH (o:order)-[:ordered_by]->(c:party), (o)-[:ships_to]->(s:party)
    WHERE s.id <> c.id
    RETURN c.name, s.name, count(o)

### Finance

**Open items by customer**

    MATCH (c:party)
    RETURN c.name, c.currency, open_balance

Grouping `open_balance` over months is refused: it is a state, not a flow.

**Ordered against invoiced against settled** — three branches, joined on the grouping
keys, never chained

    MATCH (c:party)
    BRANCH orders:      (c)<-[:ordered_by]-(o:order)   WHERE o.ordered_at IN $period
    BRANCH invoices:    (c)<-[:invoiced_to]-(v:invoice) WHERE v.document_date IN $period
    BRANCH settlements: (c)<-[:invoiced_to]-(v2:invoice)-[:posted_as]->(p:posting)
                        <-[:settles]-(a:allocation)
    RETURN c.name, c.currency,
           sum(stated_order_amount), sum(invoiced_amount), sum(allocated_amount)

Each branch keeps its own date basis. A single chain would multiply all three against
each other, which is exactly the E03 question from the withdrawn engine comparison.

**Invoices with no settlement**

    MATCH (v:invoice)-[:posted_as]->(p:posting)
    WHERE NOT EXISTS { MATCH (p)<-[:settles]-(:allocation) }
    RETURN v.number, v.document_date, invoiced_amount

**Payments and what they settled**

    MATCH (a:allocation)-[:paid_by]->(pay:posting), (a)-[:settles]->(inv:posting)
    WHERE a.allocated_at >= $from AND a.allocated_at < $until
    RETURN a.allocated_at, a.currency, allocated_amount

**Aging** — *needs declaration*: a `days_overdue` property on `invoice`, derived from the
payment term, plus its bucket definition. One declaration, then every aging question.

### Inventory and fulfilment

**Stock by location, including all sub-locations** — the recursive case

    MATCH (l:location {id: $warehouse})<-[:within*1..6]-(sub)<-[:stored_in]-(m:movement)
    RETURN m.item, sum(quantity)

**Movements per article in a period**

    MATCH (m:movement)
    WHERE m.occurred_at >= $from AND m.occurred_at < $until
    RETURN m.item, m.direction, sum(quantity)

**Order lines with no movement yet**

    MATCH (o:order)-[:contains]->(l:order_line)
    WHERE NOT EXISTS { MATCH (l)-[:fulfilled_by]->(:movement) }
    AND l.promised_at < $today
    RETURN o.number, l.sku, l.quantity, l.promised_at

**Promised against actual delivery** — *needs declaration*: a `delivered_at` measure on
`shipment` and the edge from `order_line` to `shipment`.

**Bill of materials explosion** — *needs declaration*: a `consists_of` recursive edge on
`item`. The query language needs no change; today the schema has no such table.

    MATCH (i:item {id: $article})-[:consists_of*1..8]->(part:item)
    RETURN part.name, sum(quantity)

### Deliberately refused

These are worth keeping in the catalog as teaching examples, because each refusal
explains a business rule that is otherwise learned by shipping a wrong number.

| Question | Refusal |
|---|---|
| `MATCH (o:order)-[:contains]->(l) RETURN sum(stated_order_amount)` | `contains` is 1:n. Order value is order grain. Use `line_amount`, or drop the hop. |
| `RETURN sum(stated_order_amount)` across EUR and USD without grouping by currency | Two units cannot be added. Group by currency, or declare a conversion. |
| `MATCH (c:party) RETURN month(...), open_balance` | `open_balance` is a state, not a flow; it is not additive over time. |
| `MATCH (i:item) RETURN sum(quantity)` across articles with different units | Pieces and kilograms cannot be added. Group by item and unit. |
| `MATCH (a)-[:within*]->(b)` with no depth bound | Unbounded traversal is refused. Name a depth. |
| A path through an undeclared edge | The edge does not exist in the model. Declare it, with its multiplicity, and it works everywhere. |

## Part 3: What a new question actually costs

| Situation | Cost |
|---|---|
| New combination of declared nodes and measures | Nothing. Ask it. |
| New grouping, period, filter or ranking | Nothing. |
| New property of an existing table | One line in the declaration. |
| New measure on an existing node | One declaration with unit and additivity, reviewed. |
| New relationship between existing tables | One edge with multiplicity, reviewed. |
| New business concept with a new table | The table and its migration, as always, then one node. |
| A relationship that recurses | One edge with `recursive`, a depth bound and a cycle policy. No compiler change. |

The design succeeds if the first two rows stay empty and the rest stay small. That is the
measurable claim, and T015 is where it is tested.
