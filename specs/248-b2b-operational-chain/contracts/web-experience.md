# Contract: B2B Operational Web Experience

## Invoice

The confirmation review shows the invoice header and every line before recording. The result opens
the recorded invoice with line-level links to the billed order/delivery. Contribution shows revenue,
consumed cost, DB1, selling costs and DB2 or one explicit unavailable reason with a next action.

## Purchasing and sales coverage

A supplier commitment offers **Assign supply**. The user chooses customer demand or stock
replenishment, sees remaining quantities before confirmation and receives a reconciled result.
Customer order detail shows protecting supply without calling it reserved or received.

## Return

An arrived unresolved return presents four plain choices: return to sellable stock, quarantine for
inspection/repair, record as scrap/loss, or send to supplier. Partial quantities remain visible. The
screen keeps the physical goods result and customer credit in separate sections.

## Movement explanation

Movement rows expose **Why did this happen?**. The explanation names the primary business event and
offers links to the commitment/return/correction and original source. An otherwise unexplained
adjustment warns during preview and remains visible as an exception if deliberately confirmed.

## Feedback and freshness

Every mutation uses preview → explicit confirmation → progress → durable result. Projection-backed
results retain the last completed value with updated/running/failed freshness; a first-time setup
does not require a manual Refresh to obtain its initial result. Business rules and calculations do
not run in React.
