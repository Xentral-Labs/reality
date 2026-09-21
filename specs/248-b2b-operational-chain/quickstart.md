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

## Recorded implementation evidence

### Movement explanations

- `pytest -q packages/reality-core/tests/test_movement_explanations.py packages/reality-core/tests/operational_exceptions/test_derivation.py -k movement`: 8 passed.
- The read-time explanation selects correction, return, commitment, shipment, source or explicit
  adjustment evidence without persisting a second authority. Foreign-tenant movement IDs return
  `NotFound`.
- An unlinked receipt preview contains the `unexplained_movement` warning; recording the same
  movement still produces the canonical operational exception.
- `npm run build` in `apps/web`: production TypeScript/Vite build passed. Warehouse movement detail
  renders the shared explanation and the unexplained warning.
- Shared exposure is covered by `test_b2b_operational_chain_contracts.py`: application tool, MCP,
  API route and CLI `movement explain` use the same service.

### Integrated B2B reference story

- Profile version 11 adds `SO-040`/`PO-010`: ten ordered units reconcile to six assigned to
  customer demand, two assigned to stock and two unassigned; four received and six open remain a
  separate fulfilment dimension.
- `SO-041` returns five units and resolves them as two restocked, one quarantined, one scrapped and
  one returned to the supplier, leaving zero unresolved.
- The retained contribution reference remains exact: DB1 EUR 570 and DB2 EUR 456 with no missing
  basis. Every document in the story has a business date and each human number matches its type.
- `pytest -q packages/reality-core/tests/scenarios/test_b2b_operational_chain.py packages/reality-core/tests/scenarios/test_b2b_operational_chain_catalog.py`: 4 passed in 32.30 seconds.

### Supply assignment

- `pytest -q tests/test_supply_assignments.py tests/test_supply_coverage.py tests/test_unified_delivery_reads.py`: 13 passed.
- The concurrency proof starts two seven-unit assignments against twelve units of supplier supply;
  exactly one succeeds and the retained assigned total is seven.
- The three-view proof records four units received, six assigned to customer demand, two assigned to
  stock and four unassigned. No Reservation is created and physical stock remains a separate four.

### Returned goods and commercial credit

- `pytest -q tests/test_returns.py`: 20 passed.
- `pytest -q tests/test_return_announcement_adapters.py tests/test_b2b_operational_chain_contracts.py`: 10 passed.
- `pytest -q tests/test_commercial_matching_services.py`: 11 passed.
- The independent five-unit story resolves two units to stock, one to quarantine, one to scrap and
  one to the supplier, leaving zero unresolved. A corrected disposition restores its quantity to
  unresolved without deleting history.
- The commercial lifecycle first reports three returned-but-uncredited units, then two after a
  partial credit, then one credited-but-not-returned unit after an over-credit, and finally clears
  both exceptions when the remaining goods arrive. Each exception retains document-line,
  document and commitment trace links.
- The combined return, adapter, catalog, CLI and operational-exception regression run completed with
  267 passing tests. The production frontend build also completed successfully.
