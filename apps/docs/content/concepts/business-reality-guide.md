# Reality for ERP professionals

## From familiar ERP work to the new model

You know order headers and lines, reservations, warehouse journals and open items. You may have
configured or extended an ERP with several hundred tables. That experience carries over to Reality.
The main change is which record owns each business statement and how those records answer questions
about the current situation.

This handbook teaches you to place a business case in the model, explain the records behind a
quantity or receivable, and assess an agent's proposed action. You do not need to read JSON or
memorise the database schema first.

## One case throughout

Acme Bikes sells bicycle parts. Huber Handel orders **30 bicycle lamps**. Eight are in the Augsburg
warehouse; Acme orders another 22 from LightWorks. Goods arrive in two parts and ship to Huber in
two parts. The invoice for this order states **EUR 1,470**. Huber pays EUR 500; a later EUR 100
credit is applied to that invoice.

We use the same relationships throughout: sales order `SO-1001`, purchase order `PO-2001` and
invoice `INV-1001`. These are readable example numbers, not technical identities. Variants such as a
return sit outside the base sequence. This is an explanatory case, not a preinstalled demo or a
template for tax invoicing.

## Where Reality works

Information can arrive through a connected system or a supported manual entry operation. Reality
preserves that input and records the business statements the particular importer understands.
Supported operations can then record a reservation, shipment or posting in Reality.

The data a particular ERP or shop supplies depends on its connection. A change in Reality does not
automatically update the source system. Recording a shipment does not move goods either: warehouse
work and its recording must agree. The [parallel pilot guide](../integrations/parallel-test)
explains how to begin alongside an existing ERP.

## Chapters

1. [From ERP Documents to Business Reality](./business-reality-guide/01-from-erp-documents-to-business-reality):
   Which questions belong to the order, promise, reservation and movement?
2. [Orders, Stock and Deliveries](./business-reality-guide/02-orders-stock-and-deliveries): Follow
   Huber's 30 lamps and work out stock, allocation and outstanding delivery.
3. [Invoices and Payments](./business-reality-guide/03-invoices-and-payments): Why are invoice
   entry, posting and payment allocation separate steps?
4. [Working as a Process Owner](./business-reality-guide/04-working-as-process-owner): What do you
   check when an agent explains an order or proposes a change?
5. [One Order End to End](./business-reality-guide/05-one-order-end-to-end): Decide whether Huber's
   order is complete, then compare your answer.
6. [Facts and Open Questions](./business-reality-guide/06-facts-and-open-questions): Where does
   information belong if you would previously have added a custom ERP field?
7. [Inventory Cost, DB1 and DB2](./business-reality-guide/08-inventory-cost-and-contribution): How
   does received cost evidence become a reviewed, explainable contribution margin?
8. [Summary](./business-reality-guide/07-model-at-a-glance): The shared business journal for people,
   agents and workflows.

Read in order the first time. Collapsible technical sections are optional. Afterwards,
[Tool Usage](../tool-usage/) and the [table map](../reference/table-map) provide reference material.

## Authority and open reference core

This handbook explains the existing product. The authoritative references remain
[Architecture](https://github.com/Xentral-Labs/reality/blob/main/docs/ARCHITECTURE.md),
[Data Model](https://github.com/Xentral-Labs/reality/blob/main/docs/DATA_MODEL.md),
[feature contracts](https://github.com/Xentral-Labs/reality/tree/main/docs/features) and the
specifications under `specs/`.

The reference core uses the [MIT License](/reference/license). You can inspect, use and modify its
implementation under that licence. Copyright, licence and liability notices must remain with copies
or substantial portions.

## Explore fields and data structures

Which fields does a Commitment have? Where do later date changes, reservations and shipments belong?
The [Data Model in Tool Usage](/tool-usage/#model:commitment) shows the central records with
examples, every stored field and relevant actions. It distinguishes operational fields, additional
Facts, original sources and derived observations.

Go directly to the ERP records: [Business partner (Party)](/tool-usage/#model:party),
[Item](/tool-usage/#model:item), [Shipment](/tool-usage/#model:shipment),
[Price list](/tool-usage/#model:price_list) and
[Settlement allocation](/tool-usage/#model:settlement_allocation).
