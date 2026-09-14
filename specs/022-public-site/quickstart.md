# Quickstart: Validate Public Site and Product Web Split

## Account-first hero verification (2026-09-06, FR-027)

The replacement contract failed first with three hero links instead of one. After
simplification, all 53 Site tests, four locale audits (431/431 each), formatting,
TypeScript/Vite build and Spec policy passed. No CSS, API, schema or onboarding
behavior changed. Browser-tool discovery found no connected browser; isolated
Chromium verified all four languages at 1440px and 390px in light and dark mode:
exactly one visible hero signup link, correct locale, same-tab behavior, no usage-mode
query, no Playground hero text, no horizontal overflow or page errors. German
desktop/dark and mobile/light screenshots were inspected. No account was created.
The existing header and closing account actions retain the same signup destination;
the hero no longer offers competing onboarding choices.

## 1. Prove the old combined behavior

Run the new site, product-boundary, and repository-layout tests before extraction.

Expected: tests fail because `provider-site` is absent, account links are relative, product
root renders the landing page, and Compose/CI document only one browser app.

## 2. Validate public site

Install locked dependencies in `provider-site`; run its contract tests and production build.
Serve the result alone and request `/`.

Expected: landing page loads without API, auth, or tenant calls. Login/signup targets
use the configured application origin and preserve the language query.

## 3. Validate product Web

Install locked dependencies in `apps/web`; run localization and product-boundary tests,
the translation audit, and the production build.

Expected: root enters authentication/application flow; no landing-page source or style
remains; existing `/app` and auth routes remain available.

## 4. Validate deployment ownership

Render Compose configuration and build `site` and `web` images independently. Start
them on distinct ports. Stop API and Web while Site remains serveable; restart Web/API
without Site and verify the product static shell remains serveable.

Expected: independent lifecycle and explicit service dependencies match the contracts.

## 5. Validate repository gates

Run Spec Policy, repository-layout tests, Ruff, the full PostgreSQL suite, both browser
application gates, Docker builds, and a current-document domain/path scan.

Expected: all gates pass, Alembic revisions have no content changes, and the README
maps the canonical production and local origins consistently.

## Recorded verification — 2026-08-31

- Red proof: the initial five browser extraction assertions failed because `provider-site`
  did not exist and Product Web still owned the landing page. Four of six focused
  repository-layout assertions also failed because Site had no Compose, CI, command,
  or documentation ownership.
- Site proof: 3/3 contract tests passed; the production Vite build completed with
  `APP_URL=https://app.runreality.ai` translated to an internal compile-time constant.
- Product proof: 11/11 localization and boundary tests passed; the strict translation
  audit covered 670/670 Product Web strings in each of `en`, `de`, `nl`, and `es` with
  zero missing or invalid entries; the production Vite build completed.
- Container proof: Compose rendered successfully; independent Site and Web images
  built; both static roots returned HTTP 200; Site remained available after the Web
  and API placeholder were stopped. Temporary containers and network were removed.
- Repository proof: Spec Policy passed, exact shared-core Ruff passed, diff formatting
  passed, and the PostgreSQL suite passed with 196 tests and 7 intentional skips.
- Schema proof: no migration, domain model, application service, or database schema
  changed; shared-core edits are limited to Web transport URL configuration.

### Follow-up command and configuration proof

- Root dry-run proof maps `make site`, `make app`, `make api`, and `make mcp` to their
  corresponding Compose services.
- Compose rendering with host-port overrides verified `SITE_PORT`, `APP_PORT`,
  `API_PORT`, and `MCP_PORT` independently.
- Public configuration now uses only `SITE_URL`, `APP_URL`, `API_URL`, and `MCP_URL`;
  the Site production build embeds the configured `APP_URL` through an internal build
  constant.
- Focused affected tests passed 15/15 and the full PostgreSQL suite remained at
  196 passed with 7 intentional skips.

### Reload-enabled development proof

- The merged `compose.yml` plus `compose.dev.yml` configuration rendered successfully;
  all Site, Product Web, API, MCP, PostgreSQL, migration, and object-storage services
  started in an isolated project on temporary host ports.
- Site, Product Web, the Product Web `/healthz` proxy, API health, and MCP readiness all
  returned HTTP 200.
- Touching Site and Product Web source produced service-prefixed Vite HMR entries;
  touching shared-core Python source restarted both Uvicorn API and MCP processes.
- Combined logs exposed startup, health, HMR, and reload evidence on stdout. Status and
  teardown commands completed successfully; isolated smoke containers, network, and
  volumes were removed.
- Both browser scripts explicitly select `vite.config.ts`, preventing ignored stale
  TypeScript compiler output from overriding current development configuration.

### ERP Lite section verification (2026-09-12, FR-028)

Attribute strip: five balanced desktop cells with decorative icons, dividers and
an outlined surface replace the loose text row. Safari desktop review confirms
alignment and spacing below the foundation panel. CSS collapses to two/one columns.
Complete Site gate, all 59 tests, four language audits, build, spec policy and
whitespace checks pass. No copy, interaction or business behavior changed.

Final copy trim and PR verification: shortened the three ERP paragraphs while
retaining their core meaning in all languages. Updated contract failed first,
then passed with all 59 tests, 470/470 strings per locale, format and production
build in an isolated checkout based on current origin/main. Spec policy and
whitespace checks also pass. Unrelated documentation changes remain excluded.

Graph emphasis/reordering: updated contract failed before implementation. Complete
Site gate passes (59 tests, all locale audits at 470/470, format and build), as do
spec policy and diff whitespace checks. Safari desktop visual review after full
reload confirms 04 Agent core before 05 Observe, translated explanation, light
diagram with readable labels and no overlapping current-context label. Reviewed
mobile CSS: stacked diagram/card below 1100px, wrapping event rows below 600px,
10px record labels and 13px events rather than the former 6px/8px mobile text.
Normal appearance tokens adapt the diagram in dark mode; no new business assertion.

Context Graph foundation clarification: observed the new assertion fail before
implementation. All 59 Site tests, all four locale audits (468/468), formatting,
production build, spec policy and diff whitespace check pass. Reviewed copy names
the five linked Reality record types as the shared core, with evidence and confirmed
actions retained. This changes wording only and does not reintroduce the dashboard teaser.

Dashboard teaser removal: updated contract failed before deletion, then all Site
gates passed (59 tests, 468/468 strings per language, format and production build).
Spec policy and diff whitespace checks pass. Removed the sentence, translations
and unused style without adding an availability claim.

ERP-optional / Build on Reality follow-up: observed the updated contract fail on
the missing ERP-optional sentence, then implemented both approved copy blocks and
the extensibility attribute in all four languages. `make site-build` passes all
59 tests, 469/469 strings per language, formatting and production build.
`make spec-check` and `git diff --check` pass. Reviewed the scoped changes against
FR-028: no readiness, workflow-builder or scalability claim added; existing layout
and future-dashboard label retained. No deployment performed.

Owner follow-up: removed the Connections readiness paragraph and link. Updated
the superseded assertions after observing the removal contract fail. Full Site gate
passes: 59 tests, 467/467 strings in each language, formatting and production build;
spec policy and diff whitespace check pass. The provenance caption remains intact.

- Owner approved the section and placement before planning. Increment analysis:
  one requirement, three mapped tasks, four scenarios, full coverage, no unresolved
  clarification, critical finding or Constitution conflict. Historical scope is unchanged.
- Observed three relevant contracts fail before implementation: missing ERP section,
  obsolete mapping copy, and obsolete section numbering.
- `make site-build`: PASS, including formatting, 59 tests, all four language audits
  (469/469 strings each), TypeScript and Vite production build.
- `make spec-check` and `git diff --check`: PASS.
- Safari at `http://127.0.0.1:5174/?lang=de#erp-lite`: visually reviewed the desktop
  three-column grid and the single-column narrow-breakpoint layout using page zoom.
  Capability rows and stacked explanatory blocks remain readable within the viewport;
  dashboard publishing is visibly future scope. Restored normal zoom afterwards.
  This checks responsive reflow, not a physical mobile device or mobile browser engine.
- Final diff review: static presentation only; source versioning, selective mapping,
  confirmed actions and operational finance scope remain accurate. No backend, schema,
  hosting or deployment change. Existing unrelated working-tree changes are preserved.
