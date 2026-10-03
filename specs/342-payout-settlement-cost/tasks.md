# Tasks: Payout Settlement Cost

- [x] T001 Measure statements per line for N = 10, 50, 200 and attribute them by call site (research.md).
- [x] T002 `core._batch_reads` scope; locks, stable records, held records, company currency, accounts, opening scopes, control entries and reversal roles kept within it.
- [x] T003 `allocate_settlement` reads only the payment's allocations.
- [x] T004 `core.store_source_records` for payout line sources.
- [x] T005 `payouts._warm` and memo-aware reference resolution; review and settlement run in the scope.
- [x] T006 Tests: cost per line, batched equals line-by-line; R04 budget 20.
- [x] T007 Finance, payment, payout and scenario suites; spec, research, plan, coverage matrix.
