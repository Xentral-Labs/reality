# Your First Product Journey

Want to ask a business question? [Analytics](../analytics/) walks through “Which customers ordered
Product X in week 7?”, from the filtered answer to its supporting orders.

## Open the app

<ProductLink>Open Reality</ProductLink>, sign in and choose a company. For learning, create a
separate company with sample data. Actions in the app change records in the selected company; check
the company before confirming.

This path takes you from an empty company to one traceable business result. If Reality is not
running yet, begin with the [One-line setup](/operations/installation).

If you are learning Reality as an ERP professional, first read
[Foundations](/concepts/business-reality-guide/01-from-erp-documents-to-business-reality) and
[The Process Owner role](/concepts/business-reality-guide/04-working-as-process-owner). This product
journey is the practical second step in the 30-minute learning path.

## Create or select a company

Open Product Web, sign in and create or select a company. The company is the tenant boundary for
every business record, query, agent and configuration. Its name helps people recognise it; an opaque
ID provides identity.

## Choose real intake or the guided demo

For a real source, open Company → **Integrations** → **Source systems**, register the external
system and declare which record types it may provide. For learning, use the guided demo. It creates
one connected business scenario through the same application services without requiring external
credentials.

Reality stores accepted external payloads losslessly. It does not discard unknown fields or create
typed business meaning merely because a source supplied a field.

Registering a source does not connect the external system. For your own data, first plan a
[bounded pilot](/integrations/parallel-test).

## Or play a storyline

A storyline is a guided business flow you play step by step in a sandbox of its own: an order from
creation to the month-end review, or a purchase from the order to the discounted payment. Every step
is an ordinary command; beside it you read every call Reality made and what it recorded. Open
**Storyline** in the navigation, pick one in the library and press Start. The
[storylines page](/storylines/) explains the screen and lists the packages that ship with Reality.

## Read the first result

Open **Home** for the current position. Use **Exceptions** for conditions needing attention, **Event
history** for recorded events and the appropriate workspace View for the authoritative register.
Select one important result and open **Inspect**.

## Business Graph, Business Facts and Tools

Start with the same question you would ask at work: “Why are six lamps still open?”

- **Business Facts** shows the elements of the case: for example Source Records, Documents,
  Commitments, Reservations, Movements and Ledger Entries. Open a record to inspect its details and
  the evidence actually available.
- **Business Graph** shows how those elements connect and what happened over time. Follow the
  delivery commitment to its reservation and shipment, then to the available source data. The graph
  and timeline show retained history.
- **Tools** shows what Reality can do with them. **Actions** contains commands; **Calculated views**
  contains views and projections. A view answers a question, such as which deliveries are open. An
  action changes records through its existing preview and confirmation flow.

**Business Facts is the group name for records.** The **Fact** data type still means one specific
source-supported observation. Grouping a Commitment or Movement here does not turn it into a Fact.
Calculated views belong to Tools; they are not recorded as new source authority. For stored
projections, check when the result was calculated.

The separate **Event history** lists recorded Business Events chronologically. Business Graph
instead explores relationships and the timeline of a business context. Use the
[Tools reference](/tool-usage/) for capabilities and parameters.

## An example to think through

**Illustrative example, not a live feed or a promised demo configuration.** Assume matching order,
shipment, reservation and payment records have been captured. The guided demo may show another case.

| Recorded position  | What it means                                                                  |
| ------------------ | ------------------------------------------------------------------------------ |
| 10 lamps promised  | The outgoing Commitment is for ten lamps.                                      |
| 4 shipped          | Qualifying Movements record four lamps leaving the location.                   |
| 6 still to deliver | Ten promised minus four fulfilled.                                             |
| 2 reserved         | Active Reservations cover two of the six open lamps.                           |
| 4 not yet reserved | The remaining demand is not allocated, not necessarily unavailable.            |
| Invoice settled    | Financial postings and a matched payment allocation leave no unsettled amount. |

Paid does not mean delivered. Unreserved does not automatically mean unavailable. Judging a shortage
or lateness requires stock data and a promised date.

Continue with [Trace your first result](./first-trace) to follow it through Reality, Evidence and
the original SourceRecord. Then use [Business Reality in practice](/concepts/business-reality-guide)
to understand the complete operational model or [Agent Playbooks](/agent-playbooks/) for
task-oriented product instructions.

Before deciding, check that relevant data arrived, was interpreted and is fresh enough. An empty
Exception list does not prove completeness. Mutating chat actions need preview and confirmation; a
Reservation in Reality does not automatically reserve stock in Xentral.
