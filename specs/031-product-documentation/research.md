# Research: Product Documentation Surface

## Decision 1: Static documentation framework

**Decision**: Use VitePress with Markdown content and its built-in local search provider.

**Rationale**: The repository already uses Node.js, TypeScript, Vite, static frontend builds, and Nginx containers. VitePress adds documentation navigation, outlines, previous/next links, accessible theme behavior, and a build-generated local search index without a runtime service.

**Alternatives considered**:

- Docusaurus: capable but introduces a larger documentation stack and more configuration than the initial surface needs.
- A custom React/Vite app: reimplements navigation, Markdown rendering, search indexing, and accessibility without product benefit.
- Hosted documentation/search: adds external runtime and privacy dependencies.

## Decision 2: Public, independent runtime

**Decision**: Serve generated documentation from its own Nginx container and public origin.

**Rationale**: Documentation remains available independently of tenant, auth, API, and database state and matches the existing static-runtime pattern.

**Alternatives considered**:

- API mount: couples static help to backend availability and violates the API-only boundary.
- Product Web mount: makes public docs dependent on product deployment.
- Site mount: prevents independent release and domain ownership.

## Decision 3: URL configuration

**Decision**: Add exactly `DOCS_URL`, with `https://docs.runreality.ai` as the documented production value and a local default. Do not rename existing variables.

**Rationale**: This follows the established surface-origin model and the owner's explicit decision.

**Alternatives considered**:

- `DOCS_PUBLIC_URL`, `PRODUCT_URL`, or `MARKETING_URL`: rejected because equivalent variables already exist.
- A generalized origins map: an unnecessary migration with wider deployment risk.

## Decision 4: Canonical content and API reference

**Decision**: Summarize product contracts for readers and link authoritative repository documents. Point API readers to canonical OpenAPI output; do not maintain a second complete endpoint catalog.

**Rationale**: Reader guidance is valuable, but normative domain/API truth must remain single-sourced.

**Alternatives considered**:

- Copy all internal contracts: creates silent forks and may expose inappropriate details.
- Fetch OpenAPI at runtime: couples docs availability to API health.
- Commit a generated schema copy: unnecessary until release-version pinning is required.

## Decision 5: Quality gates

**Decision**: Add a dedicated Docs CI job for deterministic install, formatting, content/deployment contracts, internal links, and production build.

**Rationale**: Docs is observable product behavior and must fail before merge when its topology, URL contract, or deployability breaks.

**Alternatives considered**:

- Fold into Site CI: obscures independent ownership and diagnostics.
- Build-only checks: miss absent content areas and broken source links.

## Decision 6: Content granularity

**Decision**: Create concise area landing pages plus focused pages for the canonical model, first trace, product surfaces, connector contract, application interfaces, production operations, contributor workflow, environment variables, and glossary.

**Rationale**: This answers initial journeys without shallow page proliferation or unsupported claims.

**Alternatives considered**:

- One long manual: hard to search, link, and maintain.
- Exhaustive endpoint/screen documentation: high drift risk and outside the initial proof.
