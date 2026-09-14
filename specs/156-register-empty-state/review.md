# Verification and review

2026-09-09, isolated branch based on main 06eeb61:
- Frontend contract suite: 44 passed, zero failures, including the new register
  empty-state contract. The new test was proved non-vacuous: with `RegisterTable.tsx`
  restored from HEAD it fails on the missing shared empty row.
- Register browser suites passed: facts, orders, finance, sources, tables, inspector and
  customer-holds. Each of them waits for the empty wording of the pages this change
  touches. `unified-orders-browser` crashed once on a navigation timeout and passed on
  re-run without a source change.
- TypeScript/Vite production build passed; existing chunk-size warning remains.
- Localization audit passed in English, German, Dutch and Spanish (1184/1184 covered,
  no new keys).
- Prettier on `apps/web/src` and `apps/web/scripts`, and spec policy, passed.
- Direct runtime check on the empty Facts and Orders registers: title and hint appear once
  inside the table frame, header, selection and pagination keep their place, and the text
  stays at the visible left edge after scrolling the register 400px horizontally.

Pre-existing failures on this base, reproduced with the change stashed and therefore not
regressions: `unified-app-browser` (mobile `Navigation` click intercepted by the company
switcher), `unified-workspaces-browser` (`de/light/390/analytics overflow`),
`unified-operations-browser` (`Needs attention`), `unified-source-configuration-browser`
(`Documents`) and `unified-opening-stock-browser` (`Record opening stock`).

Cross-artifact review: FR-001–003 covered by T001–T003 and by US1–US2; no unresolved
clarification, critical finding or Constitution exception. The final diff contains only the
shared empty row, its styles, the removal of eight page-level empty states, one contract
test and documentation. Reads, filters, pagination and tenant scope are unchanged.
