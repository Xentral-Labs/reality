# Page introductions review

## Scope and analysis
Product owner approved the shared-header/one-line proposal on 2026-09-09.
FR-009 maps to T009A (route/subview tests), T009B (implementation and translation),
and T009C (verification). Zero critical findings, ambiguities or unmapped new tasks.
All eight Constitution principles pass: presentation only, with unchanged services,
authority, authorization, tenant scope and persistence. No schema or migration.

## Verification
- Route/subview contract initially failed because the new module did not exist.
- 59 frontend contract tests pass, including all destinations, subview distinctions,
  legacy records aliases and both customer/supplier commitment descriptions.
- Production TypeScript/Vite build passes; existing chunk-size warning remains.
- English/German/Dutch/Spanish localization audit passes.
- 30 browser page/layout combinations pass (1440px and 390px) with unavailable
  business reads: one visible h1, one unboxed introduction, no horizontal overflow,
  and description below the global header. German/Dutch/Spanish translation smoke
  checks pass. Desktop/mobile screenshots visually reviewed.
- Changed frontend files pass Prettier; spec policy and diff whitespace pass.
- Backend tests are not rerun: no backend file or contract changes.

## Review and local integration
The PR is based on the still-open navigation PR #167 so its review diff contains only
this presentation change. Public/auth flows and modals are outside scope. Existing
specific help (currency separation, correction history and original-content semantics)
is preserved. Local port 8080 uses the intentional integration worktree: patch only
matching files and keep the newer daily-work lists. Their shared WorkHeader retains
counts/actions while the title is supplied by the new global fallback. No service or
database restart/migration is required; rebuild only web.

## Approved information-box refinement
The owner replaced the unboxed treatment with a compact muted information strip.
Simple registers attach directly below it in one shared outer frame; pages with
multiple independent sections keep a separate introductory box. Headers/tabs do
not move. The updated browser assertion first failed on the old zero-border
presentation. Final checks: 59 frontend contracts, isolated and integrated builds,
Prettier, spec policy and diff whitespace pass. The expanded browser matrix covers
32 desktop/mobile layouts, border/radius/padding, zero gap for joined registers,
and the existing three localization smoke checks. No translations or business
behavior changed.

## Final approved two-line header (FR-010)
The owner's final direction supersedes both information-box variants and the
unshipped content-heading prototype. The description now lives in the global
header below title/tabs/actions. There is no duplicate content heading or box.
Generic extra descriptions identified in Finance, Facts, Orders, Warehouse,
received-data and all-record registers are removed. Local operational guidance stays.
Page actions use a shared portal; search submits remain local. Save preferences uses
its existing form via a native form attribute. ResizeObserver tracks header height
for sticky sidebar/chat offsets, including wrapping and translated content.

Verification: 59 frontend contracts; both production builds; localization and spec
policy pass. 32 desktop/mobile header states and three translated descriptions pass.
22 populated layout combinations cover finance's three views, master data, reports,
Home and Inspector catalogs/rules. Screenshots reviewed at 1440px and 390px. Profile
Save submitted the existing request exactly once; creation actions retain dialogs.
No backend changes; no migration or data modification. Existing bundle-size warning.

Final integrated verification on port 8080: all 32 desktop/mobile route checks and
three translation checks passed, including sidebar alignment to the measured header.
The web container is running. PR 168 updated; remote CI/merge review remains separate.

## Final placement: first middle-content element
The owner moved the shared introduction back into the middle content area. The
compact global header keeps its title/tabs. A white rounded first element contains
view icon/title/subtitle and the same action portal. Generic duplicate explanations
remain removed. Verification: 59 contracts, both builds, localization/spec checks,
32 desktop/mobile layout checks, three translation checks and six populated Finance
layouts pass. Profile Save still submits once. Finance desktop/mobile screenshots
reviewed. No business or persistence change.

FR-011: header tabs now have transparent backgrounds, zero corner radius and a 2px
active underline. All 32 desktop/mobile checks (including computed selected styles),
59 frontend contracts, build, formatting and spec policy pass. Desktop screenshot
reviewed. Existing click handlers and tab state remain unchanged. Local web updated.

FR-012 verification: 59 frontend contracts passed; TypeScript/Vite build and spec policy passed. Browser matrix passed 32 desktop/mobile routes plus 3 translations, asserting 12px outer/11px painted-child corners and visible overflow. Embedded company label is hidden. Populated Inspector screenshots (8 views/sizes) reviewed, including Fact rules. Active local frontend rebuilt and restarted on port 8080. No business or database changes.

Final PR extraction (2026-09-09): restored daily-work PR #161 because it was merged into the naming branch, not main. Reconciled the shared introduction with the current list headers and added all later UI refinements from this conversation. Final extracted build, 61 frontend contracts, four-language audit, spec policy and isolated PostgreSQL queue regression passed. Browser results: 32 page layouts plus 3 translations; 16 delayed-Home combinations; all three daily-work lists in eight language/theme/viewport combinations; six Finance footer cases including chat toggle edge alignment and 50-row scrolling. Broader graph hover limitation remains documented in spec 149; it was not part of the loading-only acceptance.
