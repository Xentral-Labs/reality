# Plan
## Constitution Check
PASS all principles: presentation on existing read models; no alternative business rules, ORM writes or schema. CSV is explicitly a displayed-data snapshot, not authority.
## Design
Scope workbench classes to five register pages. Move existing action nodes into table toolbars; turn large navigation cards into compact horizontal tabs. Keep summary and explanation text compact. RegisterTable accepts pagination content in its footer and owns current-page selection and CSV download; extend TableContext with tenant/query selection scope. Use shared CSS for geometry and sticky footer, preserving sticky first data column. Export neutralizes leading formula characters.
## Tests
Extend existing table browser before implementation for footer, selection, export and reset; adapt column indexes for checkbox column. Run table, workspace/orders/finance/facts browser checks with existing chat fixture, contracts/build/i18n/format/spec. No service changes; previous backend baseline applies. Review representative desktop and mobile screenshots.
## Rollback
Revert workbench markup/CSS and selection/export UI. No data migration.

FR-005 Constitution PASS: authorized presentation refinement only. Add shared RegisterWorkbench/Header/Toolbar/Actions components and context slot for RegisterTable controls. Convert the five page headers/toolbars, retain event handlers and table state, and keep compact expandable explanatory text. Verify shared table/workspace/order/finance/facts browser fixtures, frontend contracts/build/i18n/format/spec. Update action-menu entry fixtures before verification; no domain changes.

FR-006 Constitution PASS: user clarified actual global header placement. Shell provides a scoped header portal; RegisterHeader retains tab handlers in that portal. Company/utility controls remain available. FilterChip wraps existing controlled selects and exposes visible label/value/icon with the native select as the interactive surface. Shared row density uses a controlled select. Verify header ancestry, filter geometry/accessibility and persistence in existing table/register/shell browser fixtures; build/contracts/i18n/format/spec.

FR-007: Reuse RegisterHeader portals for Inspector, Settings and Data & sources. Preserve native Settings links and extend shared tab styles to anchors. Suppress the nested Facts header in Inspector. No schema, service, authorization or mutation changes; Constitution PASS. Verify existing Inspector/settings/sources browser journeys plus header ancestry and one-heading assertions, frontend contracts/build/localization and spec checks.

FR-008: Presentation-only label/hint change in OrdersPage with four-language translations. Constitution PASS; no service, route or data changes. Verify existing frontend contracts, formatting, localization and production build; no new behavior tests required for wording alone.

FR-009 Constitution Check: PASS all eight principles. Presentation only; no schema, backend or business-rule change. Add pure route/subview copy selection in apps/web/src/unified/pageIntroduction.ts and a single Shell description before page content. Reuse the header slot and provide a fallback title for pages without a portal. Remove duplicate introductory markup in page components; preserve local section headings and specific help. Translate through localization.tsx. Verify route/subview coverage first, then frontend contracts, build, localization, formatting, spec policy and desktop/mobile browser layout. Rollback reverts frontend files without data changes. Base this separate PR on the open navigation PR to preserve Facts/Calculated views.

FR-009 visual refinement approved: change only the shared page-description CSS to a muted information box (1px border, 8px radius, 12px/16px padding). Existing headers, tabs and inner page layouts are unchanged. Constitution PASS. Update the existing browser assertion before CSS and verify desktop/mobile and the production build.

Latest approved refinement: Shell groups simple registers with the intro strip in one shared surface; scoped CSS removes their duplicate outer register border and gap. Multi-section pages retain independent surfaces. No content or interaction changes. Browser tests cover both variants. Analysis: FR-009 and T009D cover the refinement; no critical findings.

FR-010 final approved design: Constitution PASS. Shell renders the existing title/tabs
and action portal in the global header with the description on a second row.
ResizeObserver publishes measured header height to scoped CSS for chat/sidebar offsets.
PageActions moves existing page controls; search submits stay local and profile Save
retains its explicit form target. Remove the intermediate content frame entirely.
No business/schema changes. Verify populated registers/catalogs/profile, action targets,
responsive header geometry, existing contracts/build/i18n/spec and visual screenshots.
Analysis: T010A-C cover heading, actions, responsive offsets and no duplicate intro;
no unresolved findings. Rollback reverts frontend changes only.

Placement correction: reuse the same action portal and description in a first-child
main header surface. Restore compact shell CSS, retaining measured sticky offsets.
Map the title/icon to the current view. Constitution PASS; no service or form changes.
Update existing browser ancestry/geometry assertions, then run build/contracts/i18n,
responsive browser verification and visual review. No new component hierarchy needed.
Analysis: covered by FR-010 and T010D; no unresolved requirements or critical findings.

FR-011 Constitution PASS: scoped global-header tab CSS only. Retain native button/link
semantics and selection state. Add computed-style assertions to the existing browser
matrix; check build, localization, desktop/mobile appearance and switching. No schema,
service, routing or action changes. Analysis: T011 covers the sole requirement; no
unresolved clarification or critical finding. Rollback reverts the scoped CSS.

FR-012 Constitution PASS: shared surface CSS and embedded activity presentation only. Round painted edge children without overflow clipping; preserve standalone drawer context. Verify frontend build/contracts and responsive browser surfaces. Analysis: T012 covers the requirement; no critical findings or open clarifications.

FR-013 Constitution PASS: shared RegisterTable viewport sizing only, no services or pagination changes. Observe main/footer geometry and viewport scrolling/resizing; reserve actual footer height. Scope to page tables outside dialogs. Verify populated Finance desktop/mobile footer placement, row scrolling and unchanged controls, plus build/contracts. Analysis: requirements covered; no critical findings.

FR-013 clarification review: reuse the shared geometry observer to anchor footer left/width to main; fixed bottom zero and square full-width outer edges. Reserve footer height in row viewport. No data changes; Constitution PASS. Verify both chat states, resize and internal scrolling.

FR-014: Owner-reviewed copy cleanup, Constitution PASS. Remove five general explanatory paragraphs and only the sentence following the Reports timestamp. No service, schema, translations or interaction changes. Analysis: six locations mapped to the requirement; no unresolved findings. Verify focused diff, frontend build/contracts, formatting and spec policy.

FR-015 Constitution PASS: derive workspace from existing order view/delivery direction; reuse existing services and URLs. Shared helper drives menu, title and two-tab selection. Remove cross-workspace direction selector. Verify both sides, tab switching, URL reload, stale record clearing and existing contracts/build/i18n. Analysis: requirements resolved, no critical findings; no schema changes.

FR-016 Constitution PASS: replace datalist input with native select; derive labels from canonical identifiers and preserve saved aliases. No timezone conversion or persistence changes. Verify selection/save/rejection via existing profile browser fixture, build/contracts and i18n audit. Requirements clear; no critical analysis findings.
