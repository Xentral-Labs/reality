# Verification
- `npm run test:tables-browser`: pass; current-page checkboxes, actual CSV download content/row count, formula neutralization, selection reset on page-size change, 44/36px rows, preferences, sort/size, keyboard/row detail and sticky geometry; 24 localized layouts.
- `npm run test:workspace-browser`: pass; master-data family/action/recovery and 64 localized screenshots.
- `npm run test:orders-browser`: pass; customer/supplier drilldown, filters/pagination/tenant isolation and 48 screenshots.
- `npm run test:finance-browser`: pass; currency totals, history, Inspector/tenant/error checks and 48 screenshots.
- `npm run test:facts-browser`: pass; subject/source navigation, original values and 16 screenshots.
- 131 frontend contracts, production build, 1893-key four-language localization audit, changed-file Prettier, spec policy and diff checks: pass.
- German desktop master-data/finance and narrow table layouts visually reviewed. Existing fixtures now provide the global chat response; alignment assertions exclude the new checkbox column.
No backend code or shared business data changed. Existing full backend baseline applies. Export is limited to selected rows on the current page and visible data columns. No bulk business command is offered.

FR-005 reference-style refinement: five registers now use a compact sticky title/tab strip, search/action row, filter/table-control row and result count. Table controls remain owned by RegisterTable and are portalled into a scoped toolbar slot. Existing page actions are grouped in an accessible Actions disclosure; Escape restores trigger focus, outside interaction dismisses it, and existing dialogs retain their review boundaries. Facts retain explicit search submission; the large empty master-data panel is expandable guidance.

Verification: 133 frontend contracts, production build, 1941-key four-language audit, changed-file formatting and spec/diff checks passed. Table browser (24 layouts and search/filter control geometry), workspace browser (64 layouts plus action-menu Escape/focus and four-family form/recovery flow), orders (48 layouts), finance (48 layouts) and facts (16 layouts) passed. Final German master-data register and open-menu screenshots were visually reviewed. Action-entry fixtures were adjusted to open the new menu; no backend code or live business data changed.

FR-006 verification: title/tabs are portalled into the actual shell header; the table browser asserts header ancestry and absence of a duplicate workbench heading. Native chip selects retain filtering and persisted Normal/Compact density. Production build, 133 frontend contracts, 1943-key four-language audit, changed-file formatting, spec policy and diff checks passed. Table (24 layouts), shell (48), orders (48) and workspace (64) browser suites passed with isolated HTTP fixtures. German 1440px desktop and 390px mobile screenshots were visually reviewed; preview also checks page overflow at 1920px. No backend or live business data changed.

FR-007 verified: Inspector and Company titles/tabs render once in the shell header, including embedded Facts. Settings browser (48 layouts), sources browser (48 layouts) and Inspector browser (16 layouts and rule workflows) passed. German Settings desktop and Inspector screenshots visually reviewed. Build, 133 frontend contracts, localization audit, formatting and spec policy passed.

FR-008: final accepted tab name is Commitments, with delivery-promise and reservation/movement guidance. Production build, 136 frontend contracts, 1997-key locale audit, formatting and spec checks PASS. Route values and handlers are unchanged; no backend changes or new behavior tests.
