# Documentation Surface Contract

## Public routes

- `/` serves the documentation home.
- Configured content paths serve HTML through static-host fallback routing.
- `/healthz` returns a successful plain-text response without another service.
- Unknown paths show a useful not-found experience with recovery navigation.

## Required information architecture

Persistent navigation contains these areas in order:

1. Getting Started
2. Core Concepts
3. Product Guides
4. Integrations
5. API & Tools
6. Deployment & Operations
7. Development
8. Reference

Each area has a landing page. Pages expose an outline when multiple sections exist and previous/next navigation in configured order.

## Search contract

- Search indexes only version-controlled public content included in the build.
- Search is local and submits no query text externally.
- Results target existing pages or headings.
- Empty and no-result states preserve navigation.

## Cross-surface URL contract

- `DOCS_URL` is the only new URL variable.
- Intended production value: `https://docs.runreality.ai`.
- Local Compose default: `http://localhost:8083`.
- Existing `SITE_URL`, `APP_URL`, `API_URL`, and `MCP_URL` remain unchanged.
- Site and Web receive `DOCS_URL` at build time only where they expose docs links.
- Link composition removes trailing slashes before appending a path.

## Availability boundary

Generated documentation and `/healthz` remain available when API, Web, MCP, PostgreSQL, object storage, authentication, or tenant services are unavailable.

## Canonical-truth boundary

- The Constitution and durable `docs/` contracts remain normative.
- Public pages summarize and link those contracts where useful.
- API docs identify runtime OpenAPI as canonical and do not claim a separate complete endpoint list.
- Claims identify current behavior, example, planned direction, or normative invariant.

## Automated evidence

- Production build succeeds from a clean install.
- Tests assert required areas and core topics.
- Relative Markdown links resolve to a source page or asset.
- Compose contains independent `docs` with no API/database dependency.
- Nginx serves `/healthz` and static page routing.
- Configuration references `DOCS_URL` and preserves existing surface variables.
