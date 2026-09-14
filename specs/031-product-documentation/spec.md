# Feature Specification: Product Documentation Surface

**Feature Branch**: `codex/product-documentation`
**Created**: 2026-09-02
**Status**: Approved
**Language**: English
**Input**: "Add an independently deployed product documentation site, configured through DOCS_URL alongside the existing surface URLs, and document how Reality is intended to be understood, used, integrated, developed, deployed, and operated."

## Context and Intent

### Problem

Prospective users, operators, integrators, and contributors currently have no coherent product documentation surface. Repository documents are authoritative for development but do not provide a guided public journey from Reality's product purpose through Source → Evidence → Reality, daily product use, integration, deployment, and reference material.

### Scope

- Provide a public, independently deployable documentation surface with clear navigation and local full-text search.
- Explain the product through a task-oriented information architecture: introduction, core concepts, product guides, integrations, API and tools, deployment and operations, development, and reference.
- Add the documentation surface to local orchestration, deployment guidance, quality gates, and durable Web contracts.
- Configure links to the documentation surface through one new `DOCS_URL` variable while retaining all existing URL variable names and meanings.
- Reuse Reality's visual identity and provide clear routes to the public Site and Product Web.

### Non-Goals

- Replacing repository governance, specifications, or contributor contracts with public documentation.
- Publishing secrets, tenant data, internal incident procedures, investor material, or unfinished product claims.
- Adding documentation authentication, hosted search, analytics, comments, a CMS, or a database.
- Renaming or consolidating existing `APP_URL`, `SITE_URL`, `API_URL`, or `MCP_URL` variables.
- Changing domain behavior, persistence, APIs, or the Source → Evidence → Reality model.
- Translating the documentation in this increment; English is the complete canonical edition.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Spec-Driven Development Workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)
- [Architecture](../../docs/ARCHITECTURE.md)
- [Data Model](../../docs/DATA_MODEL.md)
- [Test Strategy](../../docs/TEST_STRATEGY.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Reality (Priority: P1)

As a prospective or newly onboarded operator, I can understand what Reality does, how Source → Evidence → Reality works, and how the major product surfaces fit together before connecting business data.

**Why this priority**: The documentation has no value unless its first journey communicates the product model accurately and makes the next step obvious.

**Independent Test**: Starting from the documentation home page, a reader can reach an introduction, a visual explanation of Source → Evidence → Reality, a glossary, and the Product Web without repository knowledge.

**Acceptance Scenarios**:

1. **Given** a reader opens the documentation root, **When** they follow the primary getting-started journey, **Then** they see the product purpose, target operator, conceptual flow, and a next action in no more than three navigational choices.
2. **Given** a reader encounters Commitment, Reservation, Movement, Ledger Entry, Document, or SourceRecord, **When** they use navigation or search, **Then** they can reach a canonical definition and its place in the traceability chain.
3. **Given** documentation contains a product capability claim, **When** the reader opens its guide, **Then** demonstrated current behavior is distinguishable from future direction.

---

### User Story 2 - Complete a Product Task (Priority: P2)

As an operator or integrator, I can find and follow a practical guide for product use, source integration, API/tool use, or troubleshooting without reading the repository.

**Why this priority**: Task completion turns conceptual understanding into successful adoption and reduces dependence on direct support.

**Independent Test**: A reader can search for a representative task, follow one guide end to end, identify prerequisites and expected outcomes, and recover from a documented common failure.

**Acceptance Scenarios**:

1. **Given** a reader wants to connect or import a source, **When** they open the integration guide, **Then** they see prerequisites, the lossless payload rule, idempotency/versioning expectations, mapping guidance, failure handling, and traceability outcomes.
2. **Given** a reader wants to use the Operations Cockpit, Business Reality Inspector, Activity feed, Ask Reality, Sources & Imports, or Exceptions, **When** they select the relevant product guide, **Then** the guide explains purpose, primary workflow, states, and the trace path beneath important results.
3. **Given** a reader searches for a documented term or task, **When** matching content exists, **Then** local search returns navigable results without transmitting the query to a third-party service.
4. **Given** no search result exists or a documentation route is unknown, **When** the reader reaches that state, **Then** the site provides a clear recovery route to navigation or the documentation home.

---

### User Story 3 - Deploy and Maintain Reality (Priority: P3)

As a deployer or contributor, I can run the documentation locally, deploy it as an independent service, understand its URL contract, and keep product/API documentation verifiable as the system evolves.

**Why this priority**: The surface must be operable and governed like the existing Site, Web, API, and MCP runtimes.

**Independent Test**: A clean checkout can build and serve the documentation independently, local orchestration exposes it, and automated gates detect broken navigation or a missing required content area.

**Acceptance Scenarios**:

1. **Given** a deployment has existing surface URL variables, **When** the documentation service is configured, **Then** only `DOCS_URL` is added and existing URL variable names retain their current behavior.
2. **Given** a clean checkout with supported tooling, **When** a contributor follows the documented local commands, **Then** the documentation builds and can be served without API, authentication, tenant, or database availability.
3. **Given** a documentation change breaks a required section, internal link, navigation entry, or production build, **When** quality gates run, **Then** the change fails before merge.
4. **Given** the API contract changes, **When** the documentation is updated, **Then** the API reference links to or derives from the canonical OpenAPI contract rather than creating a contradictory endpoint catalog.
5. **Given** a signed-in user opens the company menu, **When** they choose Help & documentation, **Then** the configured documentation origin opens in a new browser tab and the current product session remains open.

### Edge Cases

- `DOCS_URL` is absent during a local build: the documentation uses its documented local default, while other surfaces omit or use their established fallback for documentation links.
- `DOCS_URL` contains a trailing slash: generated links do not produce malformed double slashes.
- The API or Product Web is unavailable: documentation remains readable and clearly treats outbound links as separate surfaces.
- Search is used with an empty query, punctuation, or a term with no match: the interface remains stable and provides an informative empty state.
- JavaScript is unavailable: core documentation content and navigation remain readable; enhanced local search may be unavailable.
- A stale or unknown documentation path is opened: the reader receives a useful not-found page with recovery navigation.
- OpenAPI cannot be reached at browsing time: conceptual and task documentation remains usable and the reference explains where the canonical contract is served.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a publicly readable documentation home that states Reality's purpose, primary audience, Source → Evidence → Reality principle, documentation areas, and clear routes to getting started and the Product Web.
- **FR-002**: The documentation MUST contain navigable areas for Getting Started, Core Concepts, Product Guides, Integrations, API & Tools, Deployment & Operations, Development, and Reference.
- **FR-003**: Getting Started MUST cover prerequisites, local startup, first company, first source/import, the first traceable result, demo data, and next steps.
- **FR-004**: Core Concepts MUST explain SourceRecord, Document and DocumentLine as evidence, Fact, Commitment, Reservation, Movement, LedgerEntry, tenant scope, opaque identity, shortest true links, and why Documents are not the operational center.
- **FR-005**: Product Guides MUST cover the Operations Cockpit, Business Reality Inspector, global Activity feed, Ask Reality, Sources & Imports, Exceptions, traceability, and user/company preferences, while distinguishing current behavior from future direction.
- **FR-006**: Integration guidance MUST cover connector responsibilities, supported import patterns, lossless source payloads, idempotency/versioning, mapping criteria, failure recovery, and resulting traceability.
- **FR-007**: API & Tools guidance MUST explain authentication and tenant context, identify the canonical OpenAPI reference, provide representative request/error/pagination/filter examples only where supported, and explain how CLI, Chat, MCP, and Web share application services.
- **FR-008**: Deployment & Operations guidance MUST cover containers, PostgreSQL, migrations, backups/restore, health checks, logs, Railway deployment, upgrades, rollback, security, and production readiness without exposing secrets.
- **FR-009**: Development guidance MUST cover repository structure, Spec Kit workflow, Constitution rules, test strategy, domain-first implementation order, adding a domain capability, adding a connector, and contributing.
- **FR-010**: Reference guidance MUST provide a glossary, domain/data-flow overview, environment-variable catalog, changelog/versioning policy, and links to canonical repository contracts.
- **FR-011**: Readers MUST be able to navigate the complete documentation by persistent hierarchical navigation, page-level outline, previous/next links, and local full-text search.
- **FR-012**: The documentation MUST provide usable desktop and mobile layouts, keyboard-visible focus, semantic headings and landmarks, descriptive link text, and sufficient color contrast.
- **FR-013**: The documentation MUST remain readable without live API, tenant, authentication, database, hosted-search, analytics, or CMS dependencies.
- **FR-014**: The documentation MUST be independently buildable and deployable as a container and MUST expose an unauthenticated health endpoint suitable for deployment checks.
- **FR-015**: Local orchestration and durable deployment guidance MUST include the documentation service alongside Site, Web, API, and MCP without coupling their runtime availability.
- **FR-016**: Deployment configuration MUST add only `DOCS_URL` for the documentation origin and MUST preserve the names and meanings of existing `APP_URL`, `SITE_URL`, `API_URL`, and `MCP_URL` variables.
- **FR-017**: Existing public and product surfaces MUST use `DOCS_URL` when they expose documentation links and MUST retain a safe documented fallback when it is unset. The public Site MUST present Docs as a secondary footer destination rather than a primary-navigation item. Product Web MUST group Documentation and the configured Reality website under a distinct Resources section in the company menu; both links MUST open in a new browser tab without granting opener access.
- **FR-017a**: Documentation links to the Product App and public Site MUST use the configured build-time `APP_URL` and `SITE_URL` values, including home-page hero actions, navigation, and footer links; production-domain fallbacks MAY be used only when those variables are unset.
- **FR-018**: Automated checks MUST fail on a broken documentation production build, missing required navigation area, invalid internal documentation link, missing container health response, or undocumented `DOCS_URL` contract.
- **FR-019**: Documentation content MUST identify current demonstrated behavior, planned behavior, examples, and normative contracts distinctly so readers are not misled by aspirational claims.
- **FR-020**: Documentation source, navigation labels, metadata, tests, and deployment artifacts MUST be written in English.

### Domain and Traceability Requirements

- **DR-001**: The documentation MUST preserve and consistently teach SourceRecord → Document/DocumentLine → Fact/Commitment/Reservation/Movement/LedgerEntry wherever those stages apply; this feature creates no business records itself.
- **DR-002**: The documentation MUST state that operational and financial state is derived from Reality records through opaque IDs and shortest true links, never duplicated onto Documents; this feature adds no schema or relationship.
- **DR-003**: The documentation surface MUST remain tenant-independent and read no business data; product examples MUST direct readers to the same tenant-scoped application service paths used by CLI, API, Web, MCP, and Chat.

## Success Criteria *(mandatory)*

- **SC-001**: A first-time reader can reach an accurate explanation of Reality, Source → Evidence → Reality, and the first product task from the documentation root in three or fewer navigational choices.
- **SC-002**: Each of the eight required documentation areas has at least one complete landing page and is reachable through both navigation and local search.
- **SC-003**: All internal documentation links resolve, all required navigation areas are detected, and the production artifact builds successfully in automated quality gates.
- **SC-004**: The independently running documentation service returns readable core content at its root and a successful health response without API, tenant, authentication, or database availability.
- **SC-005**: At 320 CSS pixels viewport width, documentation navigation and main content remain usable without horizontal page scrolling; keyboard users can reach every interactive control with a visible focus indicator.
- **SC-006**: Every URL configuration reference adds only `DOCS_URL`; automated contract checks find no renamed existing surface URL variable.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof or an explicitly reviewed documentation-inspection rationale in the plan and tasks.

## Assumptions and Dependencies

- Documentation is public and English-only for this increment.
- Search uses only content shipped with the documentation artifact and sends no reader query to an external provider.
- `docs.runreality.ai` is the intended production value of `DOCS_URL`, but deployment owners may configure another origin.
- Existing surface variables and routing contracts remain authoritative and unchanged.
- The canonical API schema continues to be served by the API runtime; documentation links to or consumes that source without copying an independently maintained endpoint inventory.
- Product screenshots are optional and must not block the initial release; accurate text, diagrams, and executable examples take priority.
- Repository-authored feature and architecture contracts remain authoritative when public documentation summarizes them.

## Open Questions

No unresolved product questions remain. Public access, English-only scope, local search, independent deployment, and URL configuration are explicit owner decisions for this increment.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005, DR-001–DR-002 | US1.1–US1.3 | Documentation content and navigation contract tests |
| FR-006–FR-013, DR-003 | US2.1–US2.4 | Content inventory, search, link, responsive and accessibility checks |
| FR-014–FR-020 | US3.1–US3.4 | Container health, orchestration, environment contract, build and policy checks |
| SC-001–SC-007 | US1–US3 | Quickstart evidence plus automated documentation quality gate |

## Home navigation clarification (2026-09-13)

FR-001 and FR-018: the English and German home hero starts with a highlighted reading
journey, followed by the existing model chapter and ERP pilot guide, and ends with one
configured Product Web link. Internal hero and feature links must resolve to existing
pages using their canonical paths; a directory containing chapters does not turn its
sibling overview Markdown file into a directory index. Product access remains available
without duplicating the action or preceding the learning journey. This owner-approved
editorial clarification and broken-link repair does not change business behavior.
