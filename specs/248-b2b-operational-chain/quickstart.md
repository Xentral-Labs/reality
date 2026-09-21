# Quickstart: Validate the Explainable B2B Operational Chain

## Prerequisites

- PostgreSQL-backed local stack with scheduler and worker roles running.
- Current migrations applied.
- A verified user allowed to create a company.

## Automated gates

Run the focused backend tests for invoice actions, contribution, supply assignment, returns,
movement explanations, projections and the B2B story. Then run the complete backend suite, migration
tests, frontend tests/build, i18n audit, generated docs check and `make spec-check` using the
repository's documented commands.

## Visible acceptance run

1. Create an empty company and record sellable opening/received stock with non-zero retained cost.
2. Record one immediately fulfilable customer order and another order with a shortage.
3. Deliver the first order, create its dated line-level sales invoice and record a partial payment.
4. Create two supplier orders for the shortage item: assign one quantity to customer demand and the
   other explicitly to stock replenishment. Partially receive both and verify the three operational
   views reconcile.
5. Complete delivery and invoicing. Confirm each supported invoice line shows non-zero DB1 and the
   reviewed case also shows DB2 without pressing an initial Refresh.
6. Create and cancel a separate order before shipment; verify no delivery or revenue is implied.
7. Announce and receive five returned units. Restock two, quarantine one, scrap one and return one to
   the supplier. Verify zero unresolved quantity and no duplicated stock.
8. Record the customer credit separately. Verify goods and money explanations remain distinct.
9. Open every movement through **Why did this happen?**. Each reaches its reason/evidence within two
   navigation steps and the story has no unexplained-movement exception.
10. Replay selected confirmations with the same request identity. Verify no duplicate line,
    assignment, movement, posting or number.

## Expected reconciliations

- Invoice quantities never exceed delivered/eligible quantities; remaining quantities stay visible.
- Revenue minus consumed retained acquisition cost equals DB1; DB1 minus reviewed selling costs
  equals DB2.
- Customer-assigned + stock-replenishment + unassigned supply reconciles to the effective supplier
  quantity without overlap; receipts remain a separate dimension.
- Restocked + quarantined + scrapped + supplier-returned + unresolved equals arrived return quantity.
- Every document has a date, all commercial item prices/costs are plausible and non-zero, and each
  human-facing number follows its type's configured sequence.

The generated story manifest supplies exact references and UI search paths; validation must not use
database access to find business objects.
