# Verification and review

Verified on 2026-09-12 in the isolated `175-docs-data-model` worktree.

## Pre-implementation analysis
Six functional requirements, nine tasks, 100% requirement coverage. No unresolved clarification, constitutional conflict, unmapped implementation task or critical finding. Requirements checklist passed before implementation. The approved scope remains documentation only with no business model or service change.

## Evidence
- Initial Python contract failed because the new generator did not exist; it passed after implementation.
- Python schema parity: 3 tests pass, covering 9 objects and 119 actual columns, types, nullability, defaults, references and illustrative field names.
- `make docs-build`: generation, schema parity, full documentation formatting, 51 Node contracts and production VitePress build pass.
- `make lint`, scoped Ruff checks, `make spec-check` and `git diff --check` pass.
- `apps/docs/scripts/model-browser-check.mjs`: DE and EN at 375px and 1280px pass against both the built local site and the Docker container on port 8083. Checks cover object fields, field search, expanded field details, revision links, action manuals, browser Back, reload, unknown hashes and returning to Resources. No page errors or horizontal page overflow.
- Desktop and mobile screenshots inspected: object heading, example, derived guidance and field cards remain readable without ellipsis.
- Docker image rebuilt from `/private/tmp/reality-data-model` using an isolated Compose override. Existing handbook changes are included. No backend container or tenant data changes.

## Review findings resolved
- Existing YAML was not a complete schema authority; ORM metadata supplies the field inventory.
- Original promise quantity/date remain distinct from effective revised values and open quantity.
- Fact string values are canonical text, not necessarily JSON strings; example preserves source wording.
- Source payload hash reflects canonicalized content rather than exact incoming bytes.
- DocumentLine payload can be empty; SourceRecord keeps the complete source.
- LedgerEntry's tenant/account composite relationship is explicitly explained.
- Narrow tab wrapping and code-block margins prevent the observed mobile page overflow.

## Scope of verification
No business implementation changed, so database integration, migration and unrelated web/site test suites were not rerun. Existing bundle-size advisory remains non-failing. No production deployment, push or merge was performed.

## ERP expansion verification

- Approved follow-up expands the original 9 records to 35 records and 331 actual stored fields in five groups.
- Initial schema-parity test failed with 9 rather than 35 records; after implementation all 3 Python tests pass for every column/type/nullability/default/reference and example field.
- `make docs-build` passes: generated metadata, schema tests, formatting, 52 Node contracts and production build. Scoped Ruff, `make lint`, spec policy and diff checks pass.
- Browser acceptance passes DE/EN at 375/1280px against both the built site and the final container on port 8083. Added direct Party/Item/Shipment checks, automatic group selection, all-record discovery, tracking_number search across groups and ShipmentPackage → Shipment → Back.
- Screenshots reviewed for group cards and selected object detail on mobile and desktop. No horizontal page overflow or runtime errors.
- A browser attempt during container recreation received connection refused; all four acceptance cases passed after the container finished starting.
- Source review covered core model declarations and creation/hold/pricing/shipment service contracts. Shipment reports remain distinct from physical Movements; accounts and Item have no copied balances. Generated relationships retain actual links, including composite account scope.
- No domain/schema/service changes, new dependencies, production deployment or merge.

## Field table verification

- The owner requested a table in place of field cards. FR-009 was reviewed and planned before implementation.
- The semantic table contract failed before the change and passes afterward. Full docs build, formatting, 53 Node contracts and the existing 3 schema tests pass; spec policy and diff checks pass.
- Six columns show field name, meaning, storage requiredness, type, default and references without per-field disclosure controls. Metadata remains unchanged.
- Existing browser acceptance passes DE/EN at 375/1280px for fields, filtering, links, Back, reload and ERP grouping. Final container checks on port 8083 confirm all 17 Commitment rows and six headers, no page overflow, and actual ArrowRight keyboard scrolling of the mobile table region.
- Final desktop/mobile screenshots inspected. The table wraps long text and keeps horizontal scrolling inside its labeled region. Docker preview rebuilt with the final short column labels and 820px minimum table width.
- No business code, schema, generated field metadata or dependencies changed.

## Unified explorer presentation verification

- FR-010 was reviewed and planned before implementation. The shared visual contract failed before implementation and passes afterward.
- All four tabs share intro hierarchy, card, filter, list surface and detail panel primitives. Large model guidance cards became a keyboard-operable disclosure; the field table and generated metadata are unchanged.
- `make docs-build` passes: 3 schema tests, formatting, 54 Node contracts and production build. Spec policy and diff checks pass.
- `explorer-browser-check.mjs` passes all 32 tab/locale/viewport/theme combinations: DE/EN, 375/1280px, light/dark. Computed card/filter styling agrees across tabs, guidance supports the keyboard, and no page overflow or runtime errors were found. Desktop and mobile screenshots were visually reviewed.
- Final Docker preview rebuilt from this worktree on port 8083. Existing browser acceptance passes all four locale/viewport cases for field counts, table scrolling, search, links, actions, Back, reload, unknown hashes and ERP groups. One earlier static-server run timed out loading the English model; all final container cases passed.
- Review: shared styles remain scoped to Tool Usage; no business logic, metadata, dependencies, production deployment or merge changed.

## Documentation navigation labels

Spec impact: none. This owner-approved documentation-only change renames and reorders existing documentation links and adds a direct link to the existing Tool Usage page. No product behavior or route changes. The order is Understand Reality, Get started, Tools & data model, Reference, Blog, with equivalent German labels.

- Formatting and all 54 documentation tests pass; production Docker build passes. Preview on port 8083 uses this worktree.
- Browser checks pass for DE/EN at 375, 1024, 1280, 1600 and 1920px: approved labels/order, visible links and navigation to the handbook. Screenshots reviewed for full desktop navigation and the expanded menu.
- The original desktop menu overflowed at 1024/1280px with the longer labels. Below 1600px the existing expandable navigation keeps every destination reachable.

## Navigation wording follow-up

Spec impact: none. The owner requested shortening the navigation labels in all
supported locales: Understand Reality to Understand and Tools & data model to Tools
in English; Reality verstehen to Verstehen and Tools & Datenmodell to Tools in German.
This changes documentation wording only; destinations and behavior are unchanged.

Spec impact: none. Documentation-only navigation cleanup requested by the owner: remove Reference from the top menu and replace Commercial offering with Website in both locales (including the shared footer label). The reference sidebar and existing routes remain available.

- Updated the existing commercial-link contract to the new Website wording; all 54 docs tests and formatting pass. Docker production build passes.
- Final port-8083 browser checks pass DE/EN at mobile and desktop widths: Website is present, Reference is absent from the top menu, order and navigation work.

## Compact header and search verification

FR-011: short Search/Suchen header labels preserve descriptive accessible names. Tablet navigation exposes the first three links alongside the full menu; full navigation starts at 1280px. The local search input uses its existing parent focus border without a duplicate global outline. Other controls retain visible keyboard focus.

- All documentation gates pass: deterministic generation (no generated diff), 4 schema tests, full formatting, 57 Node tests and production build. Spec policy and diff checks pass.
- `apps/docs/scripts/header-browser-check.mjs` passes 24 English/German home/article layouts at 375, 768, 1024, 1194, 1280 and 1600px, including non-overlap, page overflow and all six menu destinations. Eight mobile/tablet search checks cover light/dark input focus, typing, Tab focus and Escape.
- Browser checks wait for the LanguageBridge mount signal; preliminary checks could click before hydration. Final checks pass. Screenshots of the German tablet article and English/light and German/dark search were visually inspected.
- Chromium viewport emulation was used; no physical iPad or Safari verification. No business, schema, route or generated catalog changes.
