# Feature Specification: Tool interface clarity

**Created**: 2026-10-02
**Status**: Approved scope
**Language**: English
**Input**: Implement the session's accepted plan to distinguish commands, agent tools and Web actions, show their relationships, and reduce demonstrated duplicate definitions.

## Context and Intent

### Problem

Readers mistake three access layers for independent features. The technical label Actions does not explain its Web workspace scope. Independently maintained terminology can drift between the interactive reference and generated manual pages.

### Scope

Explain the three categories in both documentation languages, show a real reservation example and command relationships, audit reservation/order/payment definitions, and consolidate proven presentation duplication.

### Non-Goals

No new business operations, database fields, MCP contract changes, automatic command execution, universal form generator, or speculative input-validation refactor.

### Existing Contracts

- `AGENTS.md`, `.specify/memory/constitution.md`, `docs/SPEC_DRIVEN_WORKFLOW.md`
- `docs/WEB_SPEC.md`; `specs/226-unified-tool-catalog/spec.md`

## User Scenarios & Testing

### User Story 1 - Understand the categories (Priority: P1)

A reader opens the technical Tool Usage overview and understands the shared operation and its agent and Web entrypoints.

**Independent Test**: Both languages explain all three categories, overlapping counts and registered Web action scope.

**Acceptance Scenarios**:

1. **Given** the technical overview, **When** a reader views its category guide, **Then** commands include reads, agent tools describe callable interfaces, and Web actions describe registered workspace interactions.
2. **Given** the category counts, **When** reading their explanation, **Then** the reader learns they are overlapping definitions and Web actions do not count every button.
3. **Given** either documentation language, **When** reading the manual pages or overview, **Then** the same category terminology is used.

### User Story 2 - Follow the shared operation (Priority: P1)

A reader follows the reservation example or a technical entry to its actual command.

**Independent Test**: Existing catalog identities drive navigable relationships and the reservation example.

**Acceptance Scenarios**:

1. **Given** the reservation example, **When** following its links, **Then** `reserve_stock`, `reservation_propose`, and `reserve` open their respective entries and proposal approval is explained.
2. **Given** a mapped tool or Web action, **When** opening its details, **Then** its command relationship is explicitly labeled.
3. **Given** a tool without a mapped business command, **When** reading its details, **Then** its registered description remains visible and the guide explains that reads and governance need not map to one command.

### User Story 3 - Maintain one definition where appropriate (Priority: P2)

A maintainer can change category terminology once and regenerate both presentations while preserving business interfaces.

**Independent Test**: Shared category metadata feeds the manual renderer and overview; audit evidence distinguishes real duplication from deliberate adapter differences.

**Acceptance Scenarios**:

1. **Given** the category metadata, **When** documentation is generated, **Then** the interactive model and manuals share labels, explanations and reservation identities.
2. **Given** reservation, manual order and customer payment, **When** reviewing their paths, **Then** the audit records schemas, service authority, confirmation and justified adapter differences without introducing another business rule.

### Edge Cases

- Commands can be reads; a command can have several tools or none.
- Unmapped tools retain their descriptions; mapping absence does not imply unsupported functionality.
- Reservation quantity is optional; the proposal tool alone does not allocate stock.
- Technical identifiers and existing anchors remain stable; business-resource Actions labels remain general.

## Requirements

### Functional Requirements

- **FR-001**: Use Web actions/Web-Aktionen for technical workspace actions, preserving general business Actions terminology.
- **FR-002**: Explain the categories, overlapping counts, extra read/governance tools, and registered-action count scope in both languages.
- **FR-003**: Show a reservation example linked to real entries and explain proposal followed by explicit confirmation before execution.
- **FR-004**: Explicitly label existing command/agent/Web relationships in entry details and retain explanations for unmapped tools.
- **FR-005**: Reuse one category definition and catalog-derived example across interactive and generated documentation.
- **FR-006**: Record the three-operation duplication audit and consolidate only demonstrated duplication without changing business validation or public interfaces.

### Domain and Traceability Requirements

- **DR-001**: Preserve existing shared services, tenant boundaries, confirmation, source/evidence/reality relationships and all MCP identities, schemas and handlers. This feature reads catalog metadata only.

## Success Criteria

- **SC-001**: Both documentation languages explain all three categories and offer three valid reservation links.
- **SC-002**: Every existing mapped technical entry retains its relationship; all existing entries and identifiers remain present.
- **SC-003**: One category definition supplies both presentations; audit evidence covers all three selected operations.

## Assumptions and Dependencies

The user's “ja mach” approves the session's proposed product scope. Existing catalog mappings and registry schemas are authoritative. Additional runtime consolidation is warranted only by demonstrated duplication. No unresolved clarifications remain.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001, FR-002 | US1.1–3 | Documentation contract tests and build |
| FR-003, FR-004 | US2.1–3 | Catalog relationship/example tests and build |
| FR-005 | US3.1 | Generator/renderer shared-definition tests |
| FR-006 | US3.2 | `research.md` audit and final diff review |
| DR-001 | US2, US3 | Registry schema preservation tests and scoped diff review |

## Business-object overview revision (2026-10-03)

The user withdrew the grouped-offering design and requested separate Views and Projections again. No PR or push is authorized at this stage.

### User Story 4 — Distinguish read surfaces and data models (P1)

Given Order, readers see Views and Projections separately with typed badges, including both Fulfillment blockers definitions. Counts and search retain those individual entries. Details explain and link their relationship. Existing Commands, Agent tools, Web actions, deep links and business services remain unchanged.

- **FR-007**: Preserve separate View and Projection rows in business-object lists, including distinct Views using a shared Projection and standalone Projections.
- **FR-008**: Counts and search reflect individual catalog entries. Order retains eight lists.
- **FR-009**: Show typed badges in read-list rows and explain View/Projection relationships through navigable links in details. Preserve all technical definitions and existing operation relationships.

Acceptance: Order shows both Fulfillment blockers entries, eight lists, and separate View/Projection badges. Searching fulfillment_queue retains the Projection entry. Both documentation languages show relationship details. No unresolved clarifications.

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-007, FR-008 | US4 overview, counts, search | T012–T014; Vue rendering tests |
| FR-009, DR-001 | US4 detail and Technology | T012–T014; Vue rendering tests and scoped review |

## Canonical technical category vocabulary (2026-10-03)

The user explicitly approved retaining View, Projection, Command, Agent Tool and Web Action in English in every language, including plurals. This extends spec208's model vocabulary without changing its localized Exceptions/Decisions exception.

### User Story 5 — Recognize technical categories across languages (P1)

Given either documentation edition or any supported application language, category labels use the same five English names. Business titles, descriptions and general action/control wording remain localized. Views and Projections remain separately listed.

- **FR-010**: Technical category labels use View/Views, Projection/Projections, Command/Commands, Agent Tool/Agent Tools and Web Action/Web Actions unchanged in English, German, Dutch and Spanish wherever supported. General business Actions and control verbs remain localized.
- **FR-011**: Generated manuals, interactive reference and application translation catalogs follow the same vocabulary. Record the policy in WEB_SPEC and the invariant-term registry; preserve identities, schemas, source content and separate entries.

Acceptance: German reference badges show View instead of Sicht, Agent Tool instead of Agenten-Tool and Web Action instead of Web-Aktion; the English edition uses identical capitalization. Effective application catalogs in de/nl/es retain all ten singular/plural labels. Save, business objects and Actions remain localized. No unresolved clarifications.

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-010, FR-011, DR-001 | US5 vocabulary/preservation | T015–T017; rendered reference, generator and effective-language tests |

## Complete business-object entry navigation (2026-10-03)

### User Story 6 — Recognize every interface (P1)
The user requests a type badge on business-object Actions and all related read/action interfaces in the object overview.

- **FR-012**: Every business-object entry row shows its technical kind badge, including Command rows under Actions and lookups.
- **FR-013**: Business-object navigation lists all catalog-related Agent Tools and Web Actions separately alongside Views, Projections, Commands and exceptions. Derive membership from authoritative entry resource relationships, including command-mapped tools; do not limit tools to the legacy unmapped-only resource.tools collection. Preserve search, deep links and existing separate categories. Event placement is optional and defaults to existing technical details unless the user selects separate navigation.

Acceptance: Order shows reserve as a Command, reserve_stock as a Web Action and reservation_propose as an Agent Tool; every tool whose resource membership includes order can be opened from the left list. All three access entries remain distinct and their existing detail relationships explain the shared operation.

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-012, FR-013 | US6 object navigation/badges | T018–T020; rendered membership and search tests |

## Shared five-category explanation

**FR-014**: Technology starts with a compact, initially expanded explanation of all five technical categories, using shared definitions also rendered before the manual catalog entries. Include registered examples for reading Fulfillment blockers (View/Projection/Agent Tool) and reserving stock (Command/Web Action/Agent Tool), noting Commands can read and Projections are optional data bases for Views. Business-object navigation offers a What do the types mean? link to that guide. No additional documentation page. User explicitly approved this placement.

**FR-015**: Rename development navigation to Extending Reality/Reality erweitern, with overview, customization, ERP/data sources, Commands, Views/Projections, exceptions and entrypoints. Nest ERP example and connector contract under ERP/data sources. Split exception development into a dedicated existing-section page; explain five-category development choices in overview and entrypoints. Preserve old routes and exception anchors with onward links. No application behavior changes. User-approved scope.

**FR-016**: Review both-language customization, connector/example/contract and development guides for self-service extension. Correct Command reads and shortest-link provenance guidance; provide concrete registered examples, ordered steps and verification for Commands, Views/Projections, exceptions, Agent Tools and Web Actions. Expose dedicated Agent Tool and Web Action tutorials beneath entrypoints; keep shared API/CLI guidance. Clearly mark excerpts rather than implying incomplete snippets are runnable. No invented schemas or runtime changes. User explicitly requests review and usable templates.

## Approved systematic extension handbook

The user approved the proposed systematic handbook redesign in plan.md. This supersedes the combined View/Projection navigation from FR-015 while preserving existing content contracts and routes.

### US7 — Learn, follow and adapt an extension (P1)

- **FR-017**: Overview starts with learning outcome/prerequisites, a relationship diagram and a compact table ordered Building block, Purpose, Example, Guide, with separate Agent Tool and Web Action rows. Repository map/common engineering rules move to a shared reference.
- **FR-018**: Provide a learning sequence: overview, customization decision, first bounded extension walkthrough, separate Views and Projections chapters, Commands, exceptions, entrypoints (Agent Tools/Web Actions/API+CLI), data sources (ERP example/contract), shared reference. Preserve legacy derived-views route and its actual heading anchors as onward links.
- **FR-019**: Each implementation chapter consistently contains learning outcome, definition/use, prerequisites, real worked example, ordered changes, expected verification, bounded adaptation exercise, common mistakes and next/reference links. Use the existing stock/reservation/fulfillment story across chapters; explain optional layers and avoid repeating the full engineering contract.
- **FR-020**: The first walkthrough adds a training-only read Agent Tool using the existing inventory read service and exact registry schema; provide complete insertion/testing instructions, explain it must not ship as a redundant production feature, and use no database/schema changes. Clearly distinguish registry/source validation from executing business reads in a PostgreSQL test environment.
- **FR-021**: Both language editions share the learning structure and canonical category terms. Examples and paths are source-backed; required tests/builds are green and pending visual or reader trial limitations are disclosed.

Acceptance: table leads with named building blocks; distinct View/Projection links open focused chapters; all chapter steps have prerequisites and expected results; the training registry is valid against actual module helpers; old anchors remain reachable; all original code-grounded references are retained or explicitly moved. Documentation changes only; no new runtime operation is registered.

| Requirement | Tasks | Proof |
|---|---|---|
| FR-017/018 | T024–T028 | Bilingual navigation/table/legacy-anchor tests and build |
| FR-019/020 | T024–T028 | Consistent chapter tests, source-backed examples and training registry proof |
| FR-021, DR-001 | T027/T028 | Docs suite, formatting, spec/build, final review and reported limitations |


## Approved vendor integration walkthroughs

- **FR-022**: Keep the Connector Contract as the shared foundation and add bilingual Xentral, Shopify and Odoo integration guides under data-source navigation. Each guide defines scoped completeness, access prerequisites, current executable versus advertised support, a source-object/Reality/implementation-gap matrix, ordered capture/interpret/update/reconcile steps, a complete illustrative business acceptance story and concrete repository/vendor references. Cover sales, purchasing, stock, reservation/fulfillment, invoices, payments/refunds, returns and relevant module-specific domains; additional sources and excluded areas must be explicit. Do not imply unsupported transports/interpreters or all vendor fields are implemented.
- **FR-023**: Add a shared coverage and completion checklist to the Connector Contract: one authority per business fact across sources, opaque identity/version boundaries, cutover opening balances versus historical movements, amounts recorded as stated, snapshot versus movement/reservation distinctions, deletion/change/retry/tenant/error/reconciliation evidence and separate outbound scope. Link all three guides from the connector guide and pilot. Correct source-proven stale Shopify order-update/refund status. No live credentials, vendor calls, schema or runtime capability changes.

Acceptance: readers can identify required source objects, implementation gaps and how to prove an agreed integration scope complete for each vendor. Proposed end-to-end examples are labelled acceptance scenarios rather than already-executed integrations. Source-backed status is tested against SOURCE_INTERPRETERS and connector_catalog.yaml. User approved the concrete proposal with “mach”.

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-022/023, DR-001 | T029–T032 | Bilingual guide/navigation/matrix/status tests, source checks, Docs build and review |


## Approved readable documentation layout

- **FR-024**: Widen normal Docs articles to approximately 960px where viewport space permits. Keep left navigation. Show the right outline only at widths of at least 1920px; preserve the existing accessible/localized VitePress outline dropdown above content below that threshold. Tables with up to five columns fit the article on desktop with wrapping, including long inline identifiers; wider tables and small screens keep horizontal scrolling within the table, never the whole page. Preserve code-block formatting, special full-width explorers, dark mode, keyboard controls and heading anchors. Both locales share the responsive layout.

Acceptance: the Xentral four-column coverage matrix fits a 1705px desktop article without concealing the final column; outline remains accessible through the dropdown at intermediate widths and right aside on wide desktops. Mobile tables retain all content and local scrolling. User approved the concrete layout proposal with “ok”.

## Integration acquisition guidance refinement

- **FR-025**: Shopify and Xentral guides in both locales explain initial bulk/paginated capture, named verified change triggers, fallback/reconciliation intervals and source limitations. Intervals are recommended starting values, not vendor guarantees or implemented runtime. Preserve raw payloads, replay/checkpoints and stock/physical-shipment semantics. No connector runtime change.

## Integration operating modes refinement

- **FR-026**: Explain Shopify observation, Xentral observation and Reality decides / Xentral executes as the third mode in bilingual vendor chapters, with responsibilities, data boundaries, an order example and actual implementation limits. Do not equate read-only upstream access with absence of local Evidence/Reality records. The user explicitly clarified that Reality decides and Xentral executes, as in the supplied draft. No runtime/outbound implementation.

## Mode-scoped coverage refinement

- **FR-027**: Shopify/Xentral coverage matrices in both locales identify baseline observation data, goal-dependent additional data and decision-dependent requirements for Reality-controlled mode C. Observation does not require every listed source or outbound writes. A basic order-observation scope includes identity/context, orders and relevant revisions; claims about delivery/payment/stock require their own evidence. C requires only sources supporting transferred decisions plus confirmed outbound execution and feedback. Completeness and acquisition/acceptance guidance apply to the agreed scope.

FR-027 scope extension approved by the user: Odoo also explains read-only observation and Reality-directed execution, with the same goal-dependent matrix and reviewed outbound/feedback boundary. Odoo methods/rights depend on the actual installed version/modules; no runtime implemented.

## Progressive example ERP learning chapter

- **FR-028**: Add a bilingual fictitious ERP chapter linked first under ERP/data sources. Teach staged read-only capture: identities/orders/revisions, actual shipment, stock baseline/subsequent receipts, supplier promises, allocation, finance, then optional confirmed outbound execution. Each stage names upstream records and references, resulting Reality answer, unknowns and an acceptance check. Explain pre-cutover delivery history/open-scope completeness, no snapshot-derived fabricated movements, and no upstream decision logic required for observation. Use consistent labelled illustrative values, distinguish proposed adapters from implemented capabilities.

## Agent-centered learning refinement

- **FR-029**: Frame the example ERP learning chapter in both locales around the owner’s agent: which captured facts it can read, which conclusions it can explain and which operations it can propose/direct under explicit execution contracts. Separate user setup responsibilities from agent capabilities; preserve unknowns, shared tools/services and mutation confirmation boundaries. No new autonomous runtime capability is claimed.

## Source concept chapter and navigation refinement

- **FR-030**: Rename the bilingual Connector Contract chapter to From source data to Reality / Von Quelldaten zu Reality. Lead with the Source -> Evidence -> Reality concept and a concrete agent-oriented order/shipment example, then retain identity/version/retry/error rules and existing heading anchors. Nest its sidebar link under shared development reference. Remove technical order example from integration sidebar; rename its title as technical implementation and retain contextual links. Update public link labels consistently, preserve URLs and regenerate derived Product Advisor knowledge. No runtime change.

FR-030 navigation correction approved by user: place the concept page first directly under ERP/data sources, followed by the staged example and vendors. Shared development reference remains a simple sibling link. Stable concept URL and contextual links unchanged.

## Source stream and revision explanation

- **FR-031**: Explain original payload capture, SourceStream identity, immutable SourceRecord versions, duplicate detection, stale/conflicting source timestamps and interpreter-specific semantic changes in both source-concept chapters. Clarify Source versus UI Surface, source events versus full-object snapshots, shortest provenance links and no generic automatic business diff. No runtime change.
