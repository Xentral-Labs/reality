# Plan: One register empty state

Move the empty state into the shared `RegisterTable`: when the body has no rows, render one
body row spanning the visible columns with a title and hint, defaulting to the existing
"No matching records" wording and accepting a per-page `empty={{ title, hint }}`. Remove the
eight page-level empty blocks (Orders & deliveries, Warehouse, Finance, Facts, Master data,
Data sources, Reality Inspector records, Rules) and pass their wording instead. Style it in
`tailwind.css` next to the existing table rules, sticky at the left edge for horizontally
scrolling registers. Update `docs/WEB_SPEC.md`. Implementation touches only web adapters;
no domain, service, tool, API or persistence change.

## Constitution Check
All principles PASS. No schema, authority, mutation, confirmation or business calculation
changes; reads, tenant scope and Source → Evidence → Reality links are untouched. Owner
approved the scope; every requirement maps to a task and an acceptance scenario.

## Verification and rollback
Extend `apps/web/scripts/unified-app-contract.test.mjs` with a register empty-state contract
that fails without the shared row. Run the frontend contract suite, the register browser
suites that already assert the empty wording (facts, orders, finance, sources, tables,
inspector, workspaces), TypeScript/Vite build, the four-language localization audit, Prettier
and the spec gate. Rollback reverts this UI commit; no migration or data operation.
