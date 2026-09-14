# Verification and review

2026-09-10, isolated branch based on main c8a9682:
- Frontend contract suite: 85 passed, zero failures, including the new page-action
  contract. The new test was proved non-vacuous against an export of origin/main's
  `apps/web/src` with only `PageActionBar.tsx` added: it fails on
  "CompanySettings.tsx writes into the header slot directly".
- Browser suites passed on the feature branch: opening-stock, facts, page-introduction,
  holds, corrections, receipt-release, register-footer, daily-work. The action-discovery
  suite passes its rewritten warehouse and finance section (primary, beside, More actions
  for three or more; the outgoing receivable payment view shows one primary button and no
  menu) and then stops at the same mobile launcher step as origin/main.
- Direct runtime check with the discovery fixture at 1440px: Stock shows Record opening
  stock beside the primary Reserve stock; Movements shows More actions (Receive goods,
  Record shipment, Correct movement) beside Record opening stock; Open items receivable
  shows More actions beside New customer invoice; Integrations shows More actions beside Add
  integration; Master data, Companies and Exceptions show one primary button each; all
  buttons share the header height.
- TypeScript/Vite production build passed; existing chunk-size warning remains.
- Localization audit passed in English, German, Dutch and Spanish (1224/1224 covered; two
  new keys, New customer and New supplier).
- Prettier on the changed files and spec policy passed.

Browser scripts updated for the bar: order-entry, invoice-entry, business-journey,
opening-stock, item-import and source-configuration open More actions only when the page
has one; workspaces checks the menu keyboard contract on Warehouse movements and the
family-named Master data button; receipt-release starts Release reservation from the
register row, which the header now also offers; action-discovery reads the bar.

Pre-existing failures on this base, reproduced against a detached origin/main worktree on
a second port and therefore not regressions: unified-app and unified-delivery (heading
"Your business, in focus."), unified-workspaces (Analytics heading), unified-tables,
unified-sources, unified-settings and sales-purchasing (tabs and `.register-heading`
expected inside the global header), unified-finance and unified-inspector (strict-mode
"No matching records"), unified-operations ("Needs attention"), unified-source-configuration
("Documents"), unified-payment-entry, unified-financial-reversal, unified-refund-entry and
unified-credit-entry (global "Actions" launcher), unified-customer-holds ("Place customer
delivery hold"), unified-company-access ("Company name"), integrations-catalog (German
"Integration hinzufügen" step), unified-orders (delivery case "Reserve stock").
unified-item-import and unified-business-journey require the live API and were not run.

Cross-artifact review: FR-001–006 covered by T001–T003 and by US1–US4; no unresolved
clarification, critical finding or Constitution exception. The final diff contains the
shared bar and hook, the toolbar without its action slot, the twelve page migrations, the
style scope, two labels, one contract test, the script updates and documentation. Reads,
discovery eligibility, confirmation flows and tenant scope are unchanged.
