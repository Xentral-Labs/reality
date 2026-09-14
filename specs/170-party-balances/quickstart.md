# Quickstart and evidence: Party balances (170)

## Run it

- Service: `party_balances(session, tenant_id, side="customer" | "supplier", credit_only=False, query="", page=1, size=50, sort="balance", sort_direction="desc", as_of=None)` in `services/finance/balances.py`.
- API: `GET /api/tenants/{tenant}/finance/open-items?flow=customer-balances` (or `supplier-balances`), optional `credit_only=true`, `q`, `sort`, `sort_direction`, `page`, `size`. The open items and credit flows accept `party_id` for the drill-down.
- App: Finance → Balances; side selector, "Credit only", sortable columns, per row "Open items" and "Available credit" open the party's documents.
- Agent: `finance_party_balances(side, credit_only?, query?, limit?)` over MCP, `finance.party_balances.list` in the application tool set.

## Proof (2026-09-11)

- `tests/finance/test_party_balances.py`: 4 passed (sums per party and currency, overdue against the aging register's due date and the as-of instant, credit-only lists each party once and drops used credit, tool equals view and is tenant-scoped).
- Existing credit register tests unchanged and green after the split into rows and paging wrapper.
- Catalog, guidance and MCP contract suites: 92 passed with the new tool (operations 447).
- Full backend suite in a clean detached worktree of the branch: the five failures seen in the shared worktree (spec policy, scheduler deployment) came from another session's uncommitted files there and do not occur on the branch itself; `make spec-check` passes on the branch.
- Web: `tsc -b` clean, 123 node tests including the new routing test, i18n audit green in de, nl, es, prettier clean.
- Finance browser suite (`apps/web/scripts/unified-finance-browser.mjs`) passes with the Balances section: request shape, side switch, credit-only switch, drill-down into a party's open items with `party_id`, back to all parties. The suite's company-switch step had to pick the visible option; it failed the same way on main before this branch.
- Live on the local stack, company `ten_de87f2e90b` (582 sales invoices, 550 payments, 546 allocations): the Balances view shows 22 customer rows across EUR and USD, totals per currency, credit-only three customers.

## Finding: the open items derivation was quadratic

The first live read took 42–50 seconds, exactly as long as the existing Open items page on the same
company. Profiling `financial_open_items` inside the API container showed 23 seconds, 18 of them in
`open_invoice_amount` reloading the tenant's settlement allocations for each of 578 invoices. The fix
is its own pull request from main, #204 (allocations read once per derivation; 22.9 s → 1.8 s for
`financial_open_items`, 1.7 s for `aging_register`). With that fix applied in the running container
(and the API process restarted so it loads the patched module) the balances flow answers in 4.4 s
and the open items flow in 5.5 s on this company. Feature 170
does not depend on #204 for correctness, only for a usable demo.

## Feature number

Verified before opening the pull request: `origin/main` holds specs up to 169; 170 is free. Other
sessions' local spec folders (171, 172) do not exist on main.
