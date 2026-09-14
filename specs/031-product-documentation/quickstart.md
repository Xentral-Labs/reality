# Quickstart: Validate the Product Documentation Surface

## Prerequisites

- Node.js 22 and npm
- Docker with Compose for container validation
- Repository checkout on the feature branch

## 1. Install and run locally

```bash
cd apps/docs
npm ci
npm run dev
```

Open the printed local address. Expected: Docs loads without API, authentication, tenant, or database services.

## 2. Validate reader journeys

1. Reach Getting Started and the first traceable-result guide.
2. Reach Core Concepts and locate SourceRecord, Document/DocumentLine, Commitment, Reservation, Movement, and LedgerEntry.
3. Search locally for `shortest true link` and open the matching concept page.
4. Open one Product Guide and follow its traceability section.
5. Open Deployment & Operations and locate `DOCS_URL`.

Expected: destinations take no more than three choices, search needs no external request, and claims distinguish current behavior from examples or future direction.

## 3. Run quality gates

```bash
make docs-build
python3 scripts/check_spec_policy.py
```

Expected: formatting, Docs contracts, links, production build, and Spec Kit policy pass.

## 4. Validate the independent container

```bash
docker compose build docs
docker compose up -d docs
curl --fail http://localhost:8083/healthz
curl --fail http://localhost:8083/
docker compose stop docs
```

Expected: health and root succeed without API, Web, MCP, PostgreSQL, or object storage.

## 5. Validate cross-surface links

```bash
DOCS_URL=https://docs.example.test docker compose config
```

Expected: Docs, Site, and Web use `DOCS_URL`; existing surface variables remain named and scoped as before.

## 6. Responsive and keyboard review

- Inspect at 320 CSS pixels.
- Open and close navigation by keyboard.
- Traverse header, search, outline, body links, and previous/next links.

Expected: no page-level horizontal scroll, trapped focus, or invisible focus; headings and landmarks remain understandable.

## Validation evidence — 2026-09-02

- Docs formatting, 9 content/deployment contracts, internal links, local-search configuration, and production build: PASS.
- npm dependency audit: PASS, 0 known vulnerabilities.
- Site formatting, 16 contracts, and production build with `DOCS_URL`: PASS.
- Product Web formatting, 19 contracts, 702/702 translation coverage in English, German, Dutch, and Spanish, and production build: PASS.
- Compose configuration, independent Docs image build, `/healthz`, and root response without business services: PASS.
- Backend Ruff and PostgreSQL-backed suite: PASS, 248 tests passed and 7 skipped.
- Spec policy and whitespace/diff validation: PASS.
- Interactive 320px and keyboard browser review: not executed because no in-app browser was connected; release reviewer should perform this manual check before merge. Static responsive/focus contracts pass.

## Home link regression verification (2026-09-13)

FR-001/FR-018 follow-up: restore the overview's canonical path, point the model
button at the existing summary chapter and prioritize reading before one final
Product Web action in both languages. No business behavior or schema change.

- `home-links.test.mjs` failed on both broken destinations and product-first ordering
  before the content repair, then passed all four cases. It also checks feature links.
- `make docs-build`: four Python reference tests, 61 Node tests, formatting and
  production build passed. Spec policy and final diff checks passed.
- `home-browser-check.mjs`: all three internal hero actions were clicked in both
  languages at 375/1280 px; destination headings and generated HTML responses passed.
  Product URL, new-tab safety and horizontal overflow checks passed. Mobile and
  desktop screenshots were visually reviewed. The configured production Product Web
  endpoint responded HTTP 200.
- The browser check verifies generated HTML explicitly, matching the production
  nginx configuration's `$uri.html`-first resolution.
