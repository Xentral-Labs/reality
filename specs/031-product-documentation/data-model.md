# Content Model: Product Documentation Surface

This feature adds no business-domain or persistence entities. These static content concepts define authoring and test boundaries only.

## Documentation Area

- **Meaning**: One of the eight top-level reader goals.
- **Attributes**: stable path, navigation label, purpose, ordered child pages.
- **Rules**: every area has a landing page; every page belongs to exactly one area except Home; labels are English and unique at their level.

## Documentation Page

- **Meaning**: A version-controlled unit of reader guidance.
- **Attributes**: title, description, headings, body, relative path, references, claim classification.
- **Relationships**: belongs to one area; may link other pages or canonical contracts.
- **Rules**: meaningful heading hierarchy; descriptive links; no secrets or tenant data; current behavior, future direction, examples, and normative rules are distinguishable.

## Navigation Entry

- **Meaning**: A discoverable route to an area or page.
- **Attributes**: label, target path, order, parent group.
- **Relationships**: targets exactly one existing page.
- **Rules**: all eight areas are present; hierarchy and current route are perceivable; mobile and keyboard access use the same topology.

## Search Document

- **Meaning**: Build-generated searchable representation of shipped public content.
- **Attributes**: page path, title, headings, text excerpts.
- **Relationships**: derived only from Documentation Pages.
- **Lifecycle**: generated at build time and replaced with each deployment.
- **Rules**: no query leaves the browser; no private repository files enter the index.

## Surface URL Contract

- **Meaning**: Configured origins used for cross-surface links.
- **Attributes**: `SITE_URL`, `APP_URL`, `API_URL`, `MCP_URL`, and additive `DOCS_URL`.
- **Rules**: existing names/meanings are unchanged; `DOCS_URL` is the Docs origin; trailing slashes are normalized; local fallbacks are explicit.

## Runtime Artifact

- **Meaning**: Immutable static files served by the Docs container.
- **Attributes**: HTML, styles, scripts, search index, assets, health routing.
- **Lifecycle**: Markdown/configuration → validated build → container image → deployment → replaceable rollback.
- **Rules**: no database, authentication, tenant, API, or writable runtime volume.
