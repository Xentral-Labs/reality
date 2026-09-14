# Feature Specification: Separate Public Site and Product Web App

**Feature Branch**: `022-public-site`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Serve a public landing page at runreality.ai and www.runreality.ai, while the authenticated application is served at app.runreality.ai."

## Context and Intent

### Problem

Reality currently ships its public landing page, authentication screens, onboarding,
and operational product in one browser deployment. This makes the repository and
deployment topology imply that marketing and the tenant application share one origin
and release boundary. Visitors need a canonical public site, while users need a clear,
dedicated application origin.

### Scope

- Provide one independently deployable public site for the canonical company domain.
- Keep login, signup, account verification, onboarding, and the operational product in
  the existing product Web application.
- Ensure every public-site account action opens the product application origin.
- Document canonical production domains and local development equivalents.
- Validate public-site, product-app, API, and MCP boundaries independently.

### Non-Goals

- Adding a content-management system, blog, analytics, or marketing form backend.
- Publishing an exhaustive technical capability or infrastructure catalog on the narrative landing page.
- Changing authentication, tenant behavior, business logic, API, MCP, or database schema.
- Sharing releases or runtime routing between the public site and product application.
- Implementing DNS, certificates, CDN, or provider-specific infrastructure in this repository.

### Existing Contracts

- [Repository architecture](../../docs/ARCHITECTURE.md)
- [Web product contract](../../docs/WEB_SPEC.md)
- [Deployable application layout](../021-deployable-app-layout/spec.md)
- [Frontend and storage boundary decision](../../docs/decisions/0005-frontend-backend-object-storage.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visit the canonical public site (Priority: P1)

A new visitor opens the root company domain and sees the Reality landing page without
loading authentication state or tenant application behavior.

**Why this priority**: The company domain must have one clear public purpose and remain
independent from availability or releases of the authenticated product.

**Independent Test**: Build and serve only the public-site artifact, open its root URL,
and verify the complete landing page works while no application API request is made.

**Acceptance Scenarios**:

1. **Given** a visitor opens `https://runreality.ai/`, **When** the page loads, **Then** the public Reality landing page is shown from the public-site deployment.
2. **Given** a visitor opens `https://www.runreality.ai/`, **When** canonical host routing is applied, **Then** the visitor receives one permanent redirect to the equivalent `https://runreality.ai/` URL.
3. **Given** API or product application runtime is unavailable, **When** the already deployed public site is requested, **Then** its static landing page remains independently deliverable.

### User Story 2 - Enter the dedicated product application (Priority: P1)

A prospective or returning user follows an account action and lands on the matching
authentication route at the dedicated application origin. An authenticated user opens
the same origin and uses the operational product.

**Why this priority**: Domain ownership must be obvious and authentication cookies and
application routes must remain confined to the product origin.

**Independent Test**: Open all public-site sign-in/signup actions and verify their
absolute destinations; then serve the product app alone and verify root, authentication,
onboarding, and `/app` behavior without a landing-page route.

**Acceptance Scenarios**:

1. **Given** a visitor selects Sign in on the public site, **When** navigation occurs, **Then** the destination is `https://app.runreality.ai/login` with any selected language preserved.
2. **Given** a visitor selects Create account, **When** navigation occurs, **Then** the destination is `https://app.runreality.ai/signup` with any selected language preserved.
3. **Given** a user opens `https://app.runreality.ai/`, **When** no authenticated session exists, **Then** the product app presents its existing authentication entry flow and never renders the marketing landing page.
4. **Given** an active authenticated user opens an `/app` route, **When** the product loads, **Then** existing tenant-scoped cockpit and inspector behavior is unchanged.

### User Story 3 - Develop and deploy each browser boundary coherently (Priority: P2)

A developer can run, test, build, and package the public site and product Web app
independently and can understand the production-domain mapping from repository docs.

**Why this priority**: A directory split is only useful if CI, containers, documentation,
and local commands enforce the same ownership boundary.

**Independent Test**: Follow documented commands from a clean checkout, build both
browser applications, render Compose configuration, and inspect their independent images.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** the documented site and Web commands run, **Then** both locked dependency sets, tests, audits, and production builds pass independently.
2. **Given** Compose configuration, **When** services are inspected, **Then** `site` and `web` use separate build definitions and ports while only `web` depends on API.
3. **Given** current CI and repository policy, **When** a change touches either browser app, **Then** both ownership paths are validated without retired combined-site assumptions.
4. **Given** the full development stack is running, **When** Site, Product Web, API, or MCP source changes, **Then** the owning process reloads without rebuilding the production-like stack.
5. **Given** a human or coding agent starts development in detached mode, **When** it follows the documented log command, **Then** combined service logs remain available on stdout with stable service prefixes.

### User Story 4 - Understand Reality as the shared agentic core (Priority: P1)

A prospective customer understands that Reality can be added beneath existing or new
business agents as their shared, explainable basis for decisions and controlled actions.

**Why this priority**: The public site must communicate the product category clearly;
Reality is infrastructure for agentic business operations, not merely one bundled agent.

**Independent Test**: Read the public landing page in English and German and verify that
the hero and operating model explicitly connect multiple agents to one shared Business
Reality, shared application tools, evidence, permissions, and confirmation boundaries.

**Acceptance Scenarios**:

1. **Given** a visitor sees the first viewport, **When** they read the primary proposition, **Then** Reality is identified as the agentic core for business-agent decisions.
2. **Given** a company already uses or plans multiple agents, **When** it reviews the operating model, **Then** the page explains that those agents can use one shared Business Reality instead of maintaining separate interpretations of the business.
3. **Given** a visitor evaluates control and trust, **When** it reviews the agent connection model, **Then** the page states that all agents use scoped tools and retain evidence, permissions, and human confirmation for mutations.
4. **Given** a visitor already has ERP and MCP infrastructure, **When** it reviews the public explanation, **Then** the page distinguishes transaction storage and tool access from Reality's immutable, structured and decision-traceable business context.

### User Story 5 - Choose an operating level (Priority: P1)

A prospective customer understands that Reality provides one invariant operational core
through three adoption packages: Starter, Business, and Enterprise.

**Why this priority**: The offer needs a clear adoption path without implying that data
integrity or traceability depends on purchasing a premium tier.

**Independent Test**: Open the landing page and `/platform` in English and German, verify
that the shared navigation reaches the package route and that the route presents the three
packages, their shared guarantees, source and history allowances, individual Enterprise
scope, and account actions.

**Acceptance Scenarios**:

1. **Given** a visitor is reading the landing narrative, **When** it wants to evaluate the offer, **Then** the shared Packages navigation opens `/platform` without interrupting the landing explanation with a duplicate package comparison.
2. **Given** a visitor opens `/platform`, **When** it compares packages, **Then** one compact three-column view shows the intended operating fit, sources, companies, and retained history without weakening Source → Evidence → Reality, tenant isolation, or traceability.
3. **Given** a buyer has complex individual requirements, **When** it reviews Enterprise, **Then** it sees an individually scoped offer with a personal contact, joint architecture, custom integrations, agent tools, and governance without a fixed consulting-hour promise.

### User Story 6 - Understand the Reality category (Priority: P1)

A business leader can open a dedicated education page and understand why mutable current-state
records are insufficient for trustworthy agents, how Source → Evidence → Fact creates durable
business context, and why the model remains useful as systems and agents change.

**Why this priority**: Reality introduces a category that buyers cannot evaluate through a feature
list alone. The public site must make the conceptual difference visible before asking visitors to
evaluate packages.

**Independent Test**: Open `/why-reality` in English and German and verify the old-world versus
Reality comparison, one conflicting multi-system order example, the Source → Evidence → Fact →
Context → Decision sequence, the long-term durability explanation, and links back to the landing
page and packages.

**Acceptance Scenarios**:

1. **Given** a visitor knows ERP status fields and human process notes, **When** it opens `/why-reality`, **Then** it sees that the old model overwrites state and separates reasons while Reality preserves an ordered, traceable history.
2. **Given** Operations, Procurement, and Finance systems report incomplete or conflicting states, **When** the visitor reviews the concrete examples, **Then** it sees how immutable source assertions become evidence and typed facts without inventing a second source truth.
3. **Given** a visitor evaluates long-term value, **When** it reaches the durability explanation, **Then** it sees that source systems remain authoritative, corrections preserve history, and multiple agents reuse one shared context.

### Edge Cases

- A language query parameter on the public site must survive navigation to login/signup.
- Public-site internal section anchors remain on the public origin.
- Unknown paths on the product origin fall back to its authentication/application router,
  not the public landing page.
- Unknown paths on the public origin may render the public-site shell, but must never
  proxy API or product routes.
- Local development uses distinct ports and origins without production-domain DNS.
- `www` redirect preserves path and query and must not form a redirect loop.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an independently buildable and deployable public site containing the current landing-page experience.
- **FR-002**: The canonical public production origin MUST be `https://runreality.ai`.
- **FR-003**: `https://www.runreality.ai` MUST permanently redirect to the equivalent canonical public URL while preserving path and query.
- **FR-004**: The product Web application MUST be independently deployable at `https://app.runreality.ai`.
- **FR-005**: Login, signup, verification, access review, onboarding, profile, and operational product routes MUST remain owned by the product Web application.
- **FR-006**: The product Web application root MUST enter the existing authentication/application flow and MUST NOT render the public landing page.
- **FR-007**: Public-site login and account-creation links MUST target the configured product-app origin and preserve supported language selection.
- **FR-008**: The public site MUST contain no API proxy, tenant-state dependency, authentication-state request, or business rule.
- **FR-009**: Public site and product Web app MUST have separate locked dependencies, build definitions, local commands, CI validation, and container images; the repository root MUST expose memorable `make site`, `make app`, `make api`, and `make mcp` service-start targets plus a full `make dev` workflow.
- **FR-010**: Local development MUST provide distinct documented origins and independently configurable host ports for public site, product Web, API, and MCP without requiring production DNS.
- **FR-011**: Compose MUST expose explicit `site` and `web` services; only the product Web service may proxy or depend on API.
- **FR-012**: Current architecture, deployment, environment, and repository-layout documentation MUST describe the split and canonical domains consistently using the public configuration names `SITE_URL`, `APP_URL`, `API_URL`, and `MCP_URL`; framework-specific variables MUST remain internal implementation details.
- **FR-013**: Development mode MUST provide source-mounted automatic reload for Site, Product Web, API, and MCP while keeping the production-like `make stack` path unchanged.
- **FR-014**: Development mode MUST provide foreground combined logs plus explicit detached start, log-follow, status, and teardown commands that are readable and operable by humans and coding agents.
- **FR-015**: The public site MUST present Reality in every advertised language (English, German, Dutch, and Spanish; see [`specs/034-public-site-localization/spec.md`](../034-public-site-localization/spec.md)) as an addable shared agentic core for existing or new business agents, and MUST explain the shared Reality, tool, evidence, permission, and confirmation model without claiming unbounded autonomy.
- **FR-016**: The public site MUST provide a shared landing-page navigation link and a bilingual `/platform` route presenting one Reality Core early-access offer rather than speculative Starter, Business, or Enterprise tiers. The same Core MUST be available as Reality Cloud with a configurable monthly EUR price and trial message or as a free self-hosted release with an official download destination. The route MUST state shared capabilities once, distinguish who operates and updates each deployment, and preserve account actions. It MUST present the configured automatic-admission limit as the total early-access capacity, explain that verified accounts within that capacity can start immediately and later applications join a waitlist, and MUST NOT imply that the displayed number is a live remaining-seat count. The price and admission capacity MUST be supplied to the static Site at build time from public environment configuration, with documented local defaults. The route MUST also explain that Reality supplies shared business context to the customer's chosen agent system through MCP, using OpenClaw, Hermes Agent, Claude Code, Codex, and custom agents as non-exclusive compatibility examples without claiming endorsement or partnership. Shopify MUST remain an example source integration rather than define the offer.
- **FR-017**: The public site MUST provide a bilingual `/why-reality` education route that visually contrasts mutable last-known-state workflows with Reality's ordered and traceable Source → Evidence → Fact → Context → Decision model. It MUST use no more than two concrete business scenarios: one detailed fulfillment context case and one concise Finance transfer example. It MUST explain that Reality preserves assertions and lineage rather than replacing source-system authority; explain long-term reuse across systems and agents; link the shared public navigation directly to the examples; and link to the package route without introducing tenant or API dependencies.
- **FR-018**: The landing, education, and package routes MUST use one shared public header with identical navigation, account actions, and language control. On desktop, the navigation MUST remain geometrically centered between equal flexible outer columns regardless of the width of the logo or account actions.
- **FR-019**: The `/why-reality` route MUST explain the category as an enjoyable visual narrative rather than only a technical model. It MUST use the detailed fulfillment context case to demonstrate how individually valid source assertions combine, compare raw-system reconstruction with Reality-informed agent behavior, introduce a plain-language memory or flight-recorder analogy, and use only one additional concise Finance example to demonstrate transferability.
- **FR-020**: The `/why-reality` route MUST also work as a self-contained introductory chapter. It MUST define source assertion, evidence, fact, commitment, reservation, movement, context, and decision in plain language; distinguish an assertion from operational truth; walk through the recurring order as a worked reasoning example; explain how corrections change current context without erasing history; and answer common category questions without implying that Reality replaces source systems or guarantees infallible decisions.
- **FR-021**: The `/why-reality` route MUST show why typed and pre-linked Reality records materially improve agent context loading. It MUST use one realistic fulfillment question involving customer and supplier commitments, inventory reservations, inbound and outbound movements, constraints, missing evidence, and source lineage; contrast repeated raw-system reconstruction with a bounded context packet; and explain that the advantage comes from relevance, explicit relationships, temporal validity, and preserved uncertainty rather than an unsupported universal speed or correctness guarantee.
- **FR-022**: The detailed fulfillment case MUST visualize the Business Reality history as a chronological record graph rather than disconnected summary cards. It MUST pair human-readable event meaning with restrained technical record types and opaque identifiers, show the shortest true links from customer Commitment to Reservation and from supplier Commitment to the expected or missing Movement, mark the agent context-load time, and visibly select the relevant records into the bounded context packet without implying that a missing record exists.
- **FR-023**: The detailed fulfillment case MUST present the growing Business Reality as a temporal plan-versus-actual subgraph. It MUST branch one order into line, payment, and delivery concerns; distinguish evidenced Commitments and Reservations from observed Movements and Facts; preserve an original ten-unit promise alongside a later evidenced reduction to eight; visibly mark which nodes the agent loads for the delivery question; and translate the selected subgraph into simultaneous historical, current, operational, open, and change-reason statements. The explanation MUST distinguish Reality's typed, linked business model from a source system's technical change log without claiming that the storage technology itself is a graph database.
- **FR-024**: The single concise Finance transfer example MUST show the financial plan-versus-actual relationship rather than only three prose summaries. It MUST trace a refund Source assertion through credit-note Evidence to a monetary Commitment and Ledger Entry/open item, distinguish the expected Settlement from the missing outbound Payment, and derive the agent's safe instruction not to close the open item until cash movement is evidenced. The example MUST remain subordinate to the detailed fulfillment case and MUST NOT imply that a shop status or Ledger Entry proves cash settlement.
- **FR-025**: The shared public navigation MUST name the education destination "How it works" in English and "So funktioniert es" in German, MUST name it in every other advertised language through the public-site catalog, and MUST link to the explanatory beginning of `/why-reality`, not directly to the secondary Finance example. The education route MUST include an early section, available in every advertised language, explaining that Reality is not a copied source-system schema: source systems retain their complete operational data; Reality receives only selected assertions; every accepted source payload is retained losslessly and immutably as a SourceRecord; and a deliberately small, stable vocabulary of Evidence, Fact, Commitment, Reservation, Movement, and Ledger Entry records stores the shortest true business relationships. The section MUST serve business and technical readers, MUST avoid a fixed table-count claim, and MUST NOT imply live federation, deletion from source systems, or a graph-database storage requirement.
- **FR-026**: Every unauthenticated Product Web account surface MUST provide a clear same-tab return path to the canonical public Site using the configured `SITE_URL`; the auth surface MUST NOT assume that its own `/` route owns public marketing content.
- **FR-027**: The homepage hero MUST offer exactly one action, Create account, linking in the same tab to the configured product signup route with the selected language preserved. It MUST NOT ask visitors to choose Playground, observation mode, or an operating model before registration. Keep ordinary site navigation and the existing system-safety note; remove the separate Playground hero explanation. Playground discovery remains available through Docs and the application. This presentation change MUST NOT change authentication, admission, or onboarding logic.

- **FR-028**: After source connections and before the agent-context comparison, the landing page MUST introduce "ERP Lite. Built for agents." through six concise capability summaries: inventory/reservations, orders/fulfillment, purchasing/receiving, operational finance, journal/traceability, and business context/exceptions. Explain lossless versioned source payloads, selective operational mapping, typed Reality records and read-time derived state; shared tools, confirmed actions, custom views, MIT open source and self-hosting. Dashboard publishing MUST be labeled coming next. Avoid fixed table counts, statutory-accounting scope, universal tool coverage and unverified speed/setup promises. All four advertised languages and narrow screens MUST retain the complete message.

### Approved ERP Lite increment (2026-09-12, US4)

Owner visual refinement: present the five existing platform attributes as one
balanced, responsive strip with decorative icons, consistent spacing and readable
labels. Retain their wording and list semantics; do not imply clickable controls.

Final owner copy refinement: shorten the introduction and both foundation paragraphs
while retaining optional ERP adoption, the five Context Graph record types, lossless
versioning, derived state and shared-core extension. No new capability or layout.

Owner-approved narrative refinement: move the complete Context Graph/agent-core
section before Observe, numbering them 04 and 05. Keep their anchor IDs. Make the
graph readable with a light diagram surface in light appearance, larger labels and
clear text contrast in both appearances. Explicitly introduce Facts, Commitments,
Reservations, Movements and Ledger Entries as one connected context, without
misclassifying the existing payment posting as a Fact. All four languages retain
the explanation. Acceptance: graph precedes Observe; record labels and event text
remain legible on narrow screens; current-context/time labels do not overlap.

Context Graph clarification approved by the owner: name the Context Graph in the
ERP introduction as the shared operational foundation for inventory, orders,
purchasing and finance. Name Facts, Commitments, Reservations, Movements and Ledger
Entries as its linked records. Acceptance: readers see that this is the core itself,
not a separate feature; all four languages retain the explanation and evidence link.

Latest owner refinement supersedes the dashboard-label requirement below: omit the
dashboard publishing teaser entirely, including its translations. Do not replace
it with an availability claim. Acceptance: the ERP section contains no dashboard
roadmap sentence and retains the approved custom-application explanation.

Owner-approved extension: the introduction explicitly states "An existing ERP is
optional" and explains use alongside current systems or as the foundation for own
business applications. Replace the custom-interface block with "Your business.
Your software. Built on Reality." and explain extension with preferred AI coding
tools while business rules, permissions and traceability stay in the shared core.
Add "Built to extend" beside the existing open-source/self-hosting attributes.
Acceptance: all four languages convey both adoption paths, shared-core boundaries,
and extensibility; preserve the six capabilities and future-dashboard label. This
is positioning of existing capabilities, not a new workflow builder or scale claim.

Owner refinement: remove the Connections readiness paragraph and its "Check current
readiness" link without replacement. Acceptance: neither the paragraph nor its link
appears on the landing page in any language; retain the provenance caption. This
supersedes the inline landing placement in spec083 FR-003, not integration readiness.

The owner accepted the proposed section and placement with "ja mach". This extends
the existing Business Reality Layer positioning; it does not replace the hero or
implement dashboards, integrations, business tools, or deployment changes.

Acceptance scenarios for FR-028:

1. Given an ERP-familiar visitor, reading after Connections reveals the six operational
   areas before the existing agent-context comparison, with sequential section numbers.
2. Given incoming orders or master data, the explanation distinguishes preserved source
   versions from selected typed values and derived state; it makes no blanket no-mapping
   or no-duplication claim.
3. Given an agent or custom-interface builder, the section describes shared tools and
   confirmed actions, and distinguishes custom views from forthcoming dashboard publishing.
4. Given any advertised language at desktop or mobile width, all section content remains
   translated and readable without horizontal page overflow.

### Approved account-first entry (2026-09-06)

The owner requested a single registration CTA instead of the three competing hero
actions. Acceptance: in each supported language, the hero contains one signup link,
no Playground or section-anchor action, and no preselected usage-mode query. The
existing header and footer navigation remain available. Application onboarding is
outside this increment; choosing how to use Reality belongs after this public entry.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality is unaffected because this feature changes only static presentation and deployment ownership.
- **DR-002**: No business entity, relationship, operational state, or schema field may be introduced or duplicated.
- **DR-003**: Product Web continues to use tenant-scoped shared API services; the public site has no tenant or application-service access.

## Success Criteria *(mandatory)*

- **SC-001**: A reviewer can map all five public deployables—site, Web app, API, MCP, and their shared core—from the root README in under two minutes.
- **SC-002**: All public-site account links resolve to the configured application origin with the correct route and language in automated tests.
- **SC-003**: Both browser applications install and build independently from clean locked dependencies with zero cross-directory runtime imports.
- **SC-004**: Site remains serveable when API and product Web are absent; product Web remains serveable when site is absent.
- **SC-005**: Every FR and DR has an acceptance scenario, implementation task, and executable proof or explicit non-code validation.
- **SC-006**: A developer or coding agent can start, observe, inspect, and stop the complete reload-enabled environment using only documented root Make targets.
- **SC-007**: A first-time visitor can identify from the first viewport that Reality provides the shared business-decision foundation for multiple agents, while a dedicated section explains how external or bundled agents connect safely.
- **SC-008**: A prospective customer can identify the appropriate operating level and reach its next action from the landing overview or `/platform` without interpreting higher levels as more truthful or auditable.

## Assumptions and Dependencies

- The hosting edge or DNS provider owns host-to-deployment mapping, TLS, and the `www`
  redirect; repository contracts and examples define the required behavior.
- `https://runreality.ai` is canonical and `www` is redirect-only.
- `https://app.runreality.ai`, `https://api.runreality.ai`, and
  `https://mcp.runreality.ai` remain the production application origins.
- Public-site and product-app visual primitives may initially be independently owned;
  a shared UI package is introduced only after repeated cross-application reuse proves it.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 scenarios 1–3 | Public-site route/link tests, independent image smoke test, domain contract review |
| FR-004–FR-007 | US2 scenarios 1–4 | Product root/auth routing tests and cross-origin account-link tests |
| FR-008 | US1 scenarios 1 and 3 | Static-source and Nginx contract assertions |
| FR-009–FR-011 | US3 scenarios 1–3 | CI, Compose, locked install, build, and image inspection |
| FR-012 | US3 scenario 3 | Current-document path/domain scan |
| FR-013–FR-014 | US3 scenarios 4–5 | Merged development-Compose rendering, reload-process inspection, lifecycle and combined-log smoke test |
| DR-001–DR-003 | All scenarios | No schema diff; backend regression suite; browser boundary review |
| FR-015 | US4 scenarios 1–3 | Landing-copy contract, four-language catalog audit (`034`), and independent Site build |
| FR-016 | US5 scenarios 1–3 | Public route, product-level content contract, and independent Site build |
| FR-026 | US2 scenarios 3–4 | Product Web auth-link configuration contract and independent Web build |
