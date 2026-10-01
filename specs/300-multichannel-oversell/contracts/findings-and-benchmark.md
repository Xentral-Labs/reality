# Contract: Oversold Items, Deadlines at Risk and the Peak-Intake Benchmark

## Finding `item_oversold`

- **Reported** while an item's open customer demand exceeds its stock on hand plus open supplier supply.
- **Values and trace**: see `data-model.md`; the channels are grouped by the order's stated `sales_channel`.
- **Clears through**: receiving or ordering more, reserving and shipping less, or cancelling demand. The finding is derived at read time, so it clears when the numbers stop exceeding.
- **Surfaces**: the existing exception tools (MCP `exceptions_list` / `exception_explain`, Web Attention page, CLI), with the German label "Artikel überverkauft".

## Finding `outgoing_commitment_due_soon`

- **Reported** while an open customer promise with quantity remaining has a date in force less than one day ahead, whether or not it is reserved.
- **Precedence**:
  - overdue first, then due soon, then at risk;
  - a short reservation rides along as the cause `insufficient_reservation`.
- **Clears through**: shipping the quantity, cancelling the promise, or a later agreed date.
- **German label**: "Liefertermin gefährdet".

## Benchmark `benchmarks/peak_intake`

- **Run**:

  ```
  REALITY_DATABASE_URL=… python -m benchmarks.peak_intake.runner \
    --orders 10000 --processes 4 --confirm-disposable --output result.json
  ```

- **Refusal**: the runner refuses without `--confirm-disposable` and on a database that holds a company not created by it.
- **Result**: JSON plus a printed summary.
- **Exit code**: non-zero if an invariant fails. Missing the time target does not change the exit code; the target is recorded.
