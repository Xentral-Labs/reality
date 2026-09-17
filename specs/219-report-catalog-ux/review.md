# Review and verification

## Specification analysis
Five requirements, four tasks, all requirements covered. No unresolved clarifications,
critical findings, conflicting requirements or unmapped tasks. Constitution passes;
requirements checklist 3/3. Approved presentation-only scope, no external interface or
business-model changes. No extension hooks configured.

## Verification
- Test-first catalog tests failed before implementation and now pass: exact-target
  grouping, separate live/stored readers, unknown entries, price input requirements,
  localized search combined with workspace filtering.
- `gmake spec-check web-build`: passed, including 219 frontend tests, four-language
  audit, TypeScript and production build. Existing large-bundle advisory remains.
- `REPORTS_ONLY=1` inspector browser: English/German/Dutch/Spanish, 1440px and 390px;
  visible descriptions, filters/search/empty results, keyboard opening, Escape and
  focus restoration, retained filters, stored and live data, secondary technical
  details, documentation and details-only price resolution all passed. Stored
  pending/failed/uninitialized/ready freshness transitions remain functional.
- No browser errors or writes. German desktop/mobile list and mobile report
  screenshots visually reviewed. No page-level mobile horizontal overflow.
- Full executable projection/workspace catalogs produce 25 distinct targets;
  every target has a translated title and summary in German, Dutch and Spanish.
- Final diff reviewed: existing tenant-scoped reads, preview bounds, traceability,
  technical identifiers, source authority and confirmation remain unchanged.

## Notes
The former `PROJECTION_ONLY` browser entry now runs the report scenario, retaining
freshness coverage. No migrations, new services, dependencies or navigation moves.

## Report context refinement (2026-09-17)

- Pre-implementation analysis: six requirements mapped to six tasks; FR-006 maps to
  T005/T006. No unresolved clarifications, critical findings, unmapped requirements,
  schema changes or Constitution exceptions. The existing report specification was
  reviewed directly; the checkout's prerequisite helper selected feature 220.
- The new 100-row browser regression failed against the old collapsed footer details
  before implementation. It now passes in English, German, Dutch and Spanish at
  1440px and 390px, covering explanation placement, stable header, disclosure,
  Escape/focus restoration, live/stored reads and details-only reports.
- German desktop/mobile screenshots visually reviewed. Mobile details start collapsed
  because an expanded explanation displaced the visible table rows; the summary stays
  visible and the explanation can be opened immediately above the table.
- Existing uncommitted freshness handling was preserved. No data calculations, service
  calls, preview limits, localization catalogs or source authority were changed by
  this refinement. Full report-specific formatting/filtering remains separate work.
- Final gates: `gmake spec-check web-build` passed (format, 219 tests, four-language
  audit, TypeScript and production build). Existing bundle-size advisory remains.
  `git diff --check` passed; final diff reviewed against FR-006 and existing changes.

## Sidebar simplification (2026-09-17)

The user requested removal of repeated code/documentation controls. Pre-implementation
review mapped the FR-004/FR-006 refinement to T007; no unresolved clarification,
critical inconsistency or Constitution exception. One canonical catalog explanation
is visible; every original catalog component remains under one collapsed technical
disclosure. No catalogs, source values, readers or business behavior changed.

The test-first browser assertion failed with two visible code buttons; after the
change, all four languages pass on desktop/mobile. Tests verify code/documentation
are initially hidden and accessible after expansion, alongside the existing report
readers, scrolling, focus restoration and mobile disclosure checks. The German
desktop screenshot was visually reviewed with the technical disclosure closed.

`gmake spec-check web-build` passed, including formatting, 219 tests, localization
audit, TypeScript and production build. Final diff reviewed; only the existing
bundle-size advisory remains.

## Designer-reviewed report screen (2026-09-17)

The user explicitly requested delegated design review. The designer identified
repeated projection/view compositions, raw API column order and inappropriate
button emphasis. FR-007/008, plan and T008–T010 cover the resulting presentation-only
scope. Preimplementation analysis found no critical inconsistency, unresolved
clarification, uncovered requirement or Constitution exception. No backend/schema
work is required.

ReportExplanation now renders canonical metadata once; workspace aliases are
unique navigation links. ReportDataTable renders business-first dispatch columns,
localized timestamps/booleans and nested-data disclosures, preserving every original
field in row details and raw JSON. RegisterTable defaults remain unchanged; reports
explicitly omit its filter icon and supply a real final action column.

Test-first presentation tests failed before the module existed and now cover field
order, sparse/unknown/identity-only fallbacks, exact input preservation and scoped
party labels. The designer's implementation review found two issues, both fixed:
Customer was restricted to dispatch, and recursive object details now span the grid
rather than shrinking into nested columns.

The report browser passes all four languages at desktop/mobile sizes, including
one code action, one documentation link, no alias cards, dispatch field order,
original row identity, collapse/keyboard/focus and stored/live/price readers. German
dispatch screenshots with closed/open technical information and dark theme were
visually reviewed by the implementer and designer; no visual blockers remained.
`gmake spec-check web-build` passed with 223 tests, localization, TypeScript and
production build. The existing bundle-size advisory remains. Final action-column
spacing was subsequently rechecked in the four-language browser run.
Final production rebuild after the spacing adjustment and `git diff --check` also passed.

## Shared report directory (2026-09-17)
The user selected the existing Actions directory-tree pattern. Specification review updated FR-001/002/003 and mapped tests/implementation to T011; Constitution checks pass with no critical findings. The new unique-membership grouping test failed before implementation, then passed. DirectoryBranch now owns the shared folder icons, hierarchy, toggle semantics and spacing; ActionDirectory delegates its existing branches to it without changing business behavior.

Report browser checks pass in four languages at desktop/mobile sizes: collapsed folders, expand/collapse all, search-driven expansion and restoration of manual groups, report disclosures, dialog focus restoration, unknown/stored/live/price readers. The German directory screenshot was visually inspected. `gmake spec-check web-build` passed with 225 tests, localization, TypeScript and production build; existing bundle-size advisory only.

The existing Actions directory checks also pass via the new DIRECTORY_ONLY mode in action-discovery-browser.mjs: keyboard folder opening, action disclosure, search expansion, manual-state restoration and collapse all. The initial broader run passed those checks but failed later at its unrelated warehouse-header expectation, which omits the existing Dispatch package/Receive package actions. That broader context-fixture mismatch was not changed or reported green. All required checks for the shared tree are green. Final diff review and `git diff --check` passed.
