# Plan: Work counts on workspace tabs

Generalize spec 253's `usePendingDecisions` into `useWorkCount(key, read, enabled)` in `apps/web/src/unified/workCounts.ts` (same rhythm: company change, visibility, 60 s while visible, `reality:records-changed`; disabled while the tab's own register is open). Add `withWorkCount(tab, {count, active, description, tone})` in `apps/web/src/unified/TabWorkCount.tsx`: it returns the tab and, when inactive and non-zero, a header count chip described on the tab. Use it in the Inbox tabs (`Shell.tsx`), Sales/Purchasing (`OrdersPage.tsx`), Warehouse (`WarehousePage.tsx`, warning tone) and Finance (`FinancePage.tsx`). Each count calls the register's existing client read with page size one and the register's default filters. Warning tone tokens in `tailwind.css` for light and dark.

## Constitution Check
PASS: no schema, service, tool, API or MCP change; counts reuse the shared register reads (Web UI invariant), so no alternative business rule exists. Tenant scope is enforced by the existing endpoints. Hard rule 2 respected: no document status is introduced for "open orders"; the order tabs stay quiet. Rule 11: nothing is stored.

## Verification and rollback
Fixture browser script `workspace-tab-counts-browser.mjs` (en light, de dark) asserts every work tab count, its description, the warning tone, the absence on stock tabs and on the active tab, and that each count read uses the register's filters with size one. Re-run spec 253's browser script, `npm run format:check`, `npm run test:i18n`, i18n audit, build, spec policy, and check live on the local stack. Revert the commit to roll back; no migration.
