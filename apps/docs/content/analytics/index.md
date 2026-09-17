# Analytics: from a question to its answer

Ask "Which customers ordered Product X this year?" in the existing chat, or open **Analytics →
Business graph** and build the same question as a stack of steps. Both go through the same declared
model and the same company scope.

## Build your first question

The page reads top to bottom like a sentence. Each step offers only what is valid where it stands,
which is why you cannot assemble a question the system then has to refuse.

1. **Data** — start at the records you want to look at. Sales orders, invoices, stock movements.
2. **Only** — narrow them. A date offers named periods (this year, last month, the last 30 days) or
   a range you pick; text and numbers offer comparisons; a flag offers yes or no.
3. **Then** — reach further along a declared connection. Each one says whether it reaches **one**
   record or **many**, before you take the step.
4. **Count** — choose the numbers. Only numbers that this path actually reaches are offered.
5. **Split by** — choose the axes. A timestamp is split by month, because one row per instant is a
   list rather than an answer.
6. **Sort** and **At most** — biggest first, smallest first, or unsorted; ten rows or your own
   number.

Remove any step and everything that pointed at the records it reached goes with it.

## Three useful starting points

- **Revenue by currency and month:** start at sales orders, count the order value, split by currency
  and order date. Amounts in different currencies are never added together.
- **Your largest customers:** start at sales orders, reach the business partner that ordered them,
  split by name and currency, sort by order value, keep ten.
- **What a product sold:** start at sales orders, reach the order lines, filter on the article
  number, count the line value.

## When it says no

Some questions cannot be answered correctly, and the page says so instead of showing a number that
is wrong:

- **"Summing this here would multiply the total."** One order has many lines. Once the path reaches
  the lines, the order value would be counted once per line. Count a line number instead, or take
  the step away.
- **"These values are not measured in the same unit."** Euros and dollars, pieces and kilograms.
- **"This number is a state, not a flow."** A stock level on hand cannot be added up over months.
- **"This field is not kept as a date."** Some document dates are stored as text; they can still be
  filtered and listed, just not folded into months.

Reaching further without using what you reach does not multiply anything: the step becomes a test
that the records exist, not a join. That is why you can ask for orders _that contain_ a product
without the order total changing.

## Saving

Save a question to **My reports**. Reopen, rename, duplicate or delete it; it is private to you.

What is saved is the **question**, never its answer. Reopening runs it again against the records as
they are now, so a named period resolves again and the numbers can differ. Saving does not freeze a
result, because a frozen number stops being true the moment somebody corrects a record.

## How an agent operates it

1. Call `graph_catalog` to discover the records this company declares, how they connect, and what
   each number means — in the reader's language.
2. Call `graph_ask` with a traversal, or with a path string in the Cypher-near syntax.
3. Read the refusal if one comes back. It names the connection that fans out or the unit that cannot
   be added. Asking again will not change it.

The agent submits no SQL, and the company predicate is added by the compiler rather than by whoever
asked. Reading needs no confirmation. Saving a private report uses `graph_report_change_propose` and
explicit confirmation; the trusted user identity is supplied by the application, never invented in
tool arguments. Tenant-only credentials cannot own private reports.

See the [exact tool schemas](../tool-usage/commands) and [agent playbooks](../agent-playbooks/).

## What the answer covers

Results describe interpreted records held in the selected company. An empty result means no matching
retained records; it does not prove that the source system never received such an order. Missing
amounts stay unknown, and units and currencies are never silently combined. Every answer can show
the statement it became and the path it took.
