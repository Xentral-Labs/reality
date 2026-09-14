# Reality Inspector
**Language**: English
## Context and Intent
A dedicated technical workspace exposes Reality records, provenance, interpretation rules, command/action catalogs, projections and execution history within the unified app.
### Non-Goals
No invented graph links, generic arbitrary command executor, new business rules, schema or automatic mutation. Catalogued commands without an existing Web form remain inspectable definitions with their supported adapters.
## User Scenarios & Testing
US1: Search Facts and Reality records, open their details and explore an object-centered graph through actual Inspector links.
US2: Review existing rule versions and create new rules through documented question/context, Fact decision, draft, simulation and explicit activation. Owner-only operations preserve server controls.
US3: Search commands/actions, open definitions or launch existing reviewed action forms; inspect all projection definitions and available view results.
US4: Inspect sources and execution history from the same workspace.
## Requirements
- **FR-001**: Reality Inspector is a dedicated sidebar group between Analytics and Company with four localized destinations: Understand context; Facts & origins; Rules & insights; Actions & history. Remove Technology & system from Company. Group existing tabs beneath those destinations; preserve existing tab URLs and tenant isolation.
- **FR-002**: Facts remain searchable/pageable; explorer searches existing scoped records. A bounded one-hop graph draws only links supplied by Inspector reads, supports node navigation and detail access, and indicates truncation. No fabricated relationship or complete-graph claim.
- **FR-003**: Show current-page rule case/version records with pagination and state. Provide new documented case creation, context/evidence entry, Fact decision, JSON draft preparation, simulation and activation/disable using existing APIs. Mutations require an explicit review and are single-flight. Ambiguous results block resubmission until a fresh state is obtained. Respect server prerequisites and owner authorization.
- **FR-004**: List all commands and distinct workspace actions from the current catalog. Existing supported Web actions open shared forms; other commands expose their definition/adapters without pretending to execute. No arbitrary service-to-tool name guessing.
- **FR-005**: List all projection/view definitions with calculation, outputs, consumers and invalidation metadata; open supported existing results through current APIs. Catalog definitions are distinguished from company data.
- **FR-006**: Link sources and show scoped execution history. Errors/retry, empty states, keyboard access, four languages, light/dark and mobile bounds apply.
## Assumptions and Dependencies
The owner approved the Inspector proposal. Existing tenant-scoped APIs, interpretation lifecycle and shared action forms remain authoritative. Rule authoring is technical JSON backed by the existing validated draft format; no new visual rule language. Rule discovery is paginated by documented question, with versions shown for each returned case. Raw projection reads reuse current endpoints; rendered output is bounded and labelled.
## Requirement Traceability
FR-001/002/004/005/006: isolated inspector browser read/navigation/catalog/graph/tenant tests. FR-003: rule lifecycle browser tests with owner/member/review/rejection/ambiguity boundaries. Shared frontend contract/build/localization gates plus existing shell and action baselines.
## Success Criteria
Technical users can navigate real records and origins, review/test/activate a rule through existing services, inspect catalogs and launch supported actions without leaving the common shell. Required checks pass.

## Context-first navigation
- **FR-007**: The context landing replaces catalog counters with a scoped record picker (orders/documents, parties, items and other returned Reality records), a conceptual five-stage explanation, actual Inspector metrics/meaning and a linked-record graph. The explanation distinguishes received source values, evidence, operational records/Facts, derived insights and reviewed actions; it must not imply every record has every stage. Actual edges come only from existing Inspector links. Selecting a linked node changes the visible detail/perspective; source payload is available when returned. Empty/loading/error states remain explicit. Global chat remains available; do not claim arbitrary selected records are automatically sent to chat.
- **FR-008**: Context includes overview and graph; Facts & origins includes facts and records; Rules & insights includes rules, exceptions and views; Actions & history includes commands and history. Counts remain in relevant technical catalog views. Existing actions and rule lifecycle remain unchanged.

- **FR-009**: Rule controls recognize platform administrators as well as company owners, matching existing server authorization. Ordinary members remain read-only. Render each rule version with a translated status and explanation, visible actions and collapsible technical JSON. Distinguish active application from an inactive draft; editing creates a new version and does not overwrite history. Hide Previous/Next for a single page, retain paging for more than 25 questions. Opening an existing rule as a draft expands and focuses its editor. Do not label the question revision as a rule version.

FR-009 editor readability: expanded rule draft and context inputs show at least 16 and 6 text lines respectively, with vertical resizing and internal scrolling. Shared control minimum-height styles must not collapse these editors.

- **FR-010**: Rule status filter All/Active/Draft/Disabled filters questions by the existence of a matching tenant-scoped rule version before pagination and filters displayed versions identically. List badges derive from actual version states, not the question lifecycle. A question can have both active and draft versions. Status change resets page and selected detail; unmatched results are explicit. No state derivation is stored.

- **FR-011**: Exception catalog and execution history display directly in their Inspector tabs. History is a table using the existing tenant-scoped timeline query, filters and cursor pagination; inspection remains available from rows. The catalog lists existing class definitions with cause/owner/clearance details inline. Existing modal entry points remain supported. Catalog/projection/command failures retain Retry; deployment must load matching code and catalogs. No new business mutations or data sources.

- **FR-012**: Fact rules use a full-width register table with question, intended use, actual version states, updated time and row action. Search, state filter and New rule share the standard toolbar; pagination stays at the footer. New rule opens a modal, and row open/edit opens the existing version/draft/review workbench in a modal. No default creation form or permanent master-detail sidebar. Preserve owner/admin/member restrictions, confirmed writes, uncertainty lock, tenant reset and Escape/focus behavior; closing never executes a pending review.

FR-012 table defaults: 50 rows per page with 25/50/100 choices; changing size resets the page and applies to the existing server query.

### FR-013 — Consistent Inspector presentation patterns
The owner requested uniform Inspector patterns across exception classes, projections/views,
commands/actions and record collections. Fixed definitions use one compact disclosure-row
pattern with shared search toolbar, matching count, section labels and empty feedback.
Editable rules use the FR-012 register and dialog. Facts and event history retain their
shared tables; contextual graph exploration retains its specialized visualization.
Catalog details and supported action/view entry points remain available without fabricated
create/edit controls. Avoid fetching application-reference metadata on tabs that do not
use it. Exception catalog validation must read/parse each evidence file at most once per
request, preserving fresh validation and all missing-evidence errors.
Acceptance: search and clearing search preserve disclosure actions; all fixed catalog rows
share styling; empty matches are explicit; narrow layouts do not overflow the document;
repeated evidence references do not repeat parsing and invalid evidence is still rejected.

### FR-014 — Graph record autocomplete
The graph's Record ID input offers tenant-scoped, bounded suggestions for the selected
record type, searched by ID or the record's available descriptive fields. Each suggestion
shows a label and its opaque ID. Choosing it opens the graph. Keyboard arrows, Enter and
Escape work; typing a known ID and using Open remains supported. Changing type clears the
old selection; late search responses cannot replace newer suggestions. Loading, no matches
and failures are visible, with retry. This adds no writes or cross-tenant lookup.

FR-013 refinement: The owner requested removal of the embedded Facts 'About this view'
disclosure and the separate Fact-predicate catalog count above the rule register. Inspector
Facts/rules start directly with their register toolbar. The standalone Facts explanation
remains available; rule rows and their count still describe actual company rule cases.

### FR-015 — A real graph starting point
Opening Record graph without an explicit record automatically selects a recent, linked
record in the current company. Prefer customer deliveries, then sales orders, items,
customers and Facts when earlier categories are empty. Provide compact Delivery / Order /
Item / Customer / Fact starting buttons and label the chosen starting record. Within the
first available category, compare at most three returned recent records using their actual
Inspector links and prefer the one with the most distinct links. This is a bounded entry
sample, not a most-connected-company-record claim. Node navigation uses the existing graph.
Manual selection and typing must cancel pending automatic selection; explicit graph links
are never replaced. Category and company changes discard stale responses. Show loading,
retry and an honest empty state, without sample data or invented edges.

### FR-016 — Graph-first context overview
The owner requested the same automatic graph as the Overview starting screen. Overview
opens with category starting points and the selected graph beside its existing context
details. Keep record search below and the conceptual model in an expandable explanation.
Reuse FR-015 selection and cancellation; graph navigation continues to update the detail
perspective. The separate Record graph tab remains the larger focused view. Empty/error
states stay honest and support retry or manual search; no separate selection algorithm.

FR-016 responsive graph: the initial graph fits its container horizontally. Narrow
containers stack actual linked nodes below the root; wide containers retain two columns.
Zoom may deliberately overflow inside the graph viewport, never the document. Preserve
node labels, true edges and the existing twenty-link bound.

### FR-017 — Projection data dialog
Every Open view data button opens a labelled modal immediately and loads actual data from
the current tenant's existing projection endpoint inside it. Render returned rows as a
read-only table, bounded to the existing 100-row presentation limit, with technical JSON
available on demand. Loading, error/retry and empty results remain in the modal. Close and
Escape return focus to the triggering button. Reopening reloads data; late results cannot
appear in another projection or after closing. Remove the distant inline result section.

FR-017 clarification: Every catalog view, including authoritative registers with existing application routes, uses the same data modal. No catalog data button navigates away or opens a side drawer. Register previews reuse scoped reads and show only their returned first page, with an explicit bounded-preview notice.

### FR-018 — Projection and view orientation
Show projections in the left column and workspace views in the right column on wide screens, stacked on narrow screens. Each heading includes a keyboard/touch-accessible information disclosure explaining derived read models versus application views using projections or authoritative registers. Shared search and modal actions remain unchanged.

FR-018 extension: Actions on the left and Commands on the right use the same responsive layout and information controls. Explain actions as business-facing operations with prerequisites and confirmation, and commands as callable application operations with inputs and results. Existing action forms remain unchanged.

FR-018 help refinement: Information opens on hover, keyboard focus or touch, with Escape dismissal. All four definitions use plain ERP language and a concrete stock/reservation example.

### FR-019 — Explicit catalog destinations
Each catalog entry links to its existing documentation page using configured DOCS_URL in a new tab. Entries with an explicitly mapped application destination also offer Open in application. This separate navigation action preserves the selected tenant; Open view data continues to open only the data modal. Do not guess destinations for unmapped technical commands.

FR-019 navigation extension: Company navigation includes a Documentation link below Settings, marked with an external-link icon and opening configured DOCS_URL in a new tab. It is available independently of catalog selection and does not change the active application route.

### FR-020 — Explain catalog entries progressively
Opened projections, views, actions and commands present a plain explanation before technical details. How it works shows catalog-backed inputs/reads, calculation or effect, outputs/writes and relationships. Illustrative inventory/reservation examples must be labelled and never mistaken for tenant data. Technical definitions stay collapsed, with service input contracts and safe repository-relative implementation references for interested readers. Source links open repository files in a new tab; no arbitrary filesystem contents, secrets or absolute runtime paths are exposed. Existing data dialogs and action forms remain unchanged.

### FR-021 — Inline Python code dialog
Every catalog entry has a Code button opening a labelled, read-only modal immediately. On demand, load actual Python function source from the running application for its catalog-selected command/projection and related services. Actions resolve to their command; projection-backed views resolve to their projection; direct register views show their explicitly mapped Python read adapter. Clearly state these relationships. Show file/function, readable scrollable code, a service selector, loading/error/retry, and explicit truncation above 600 lines or 64 KiB per function. No arbitrary file paths or callable names are accepted; use the existing tenant-authorized API boundary. Close/Escape restore trigger focus; no code execution or editing.

### FR-022 — Scannable catalog cards
Use one business title and one entry-specific description. Move technical identifiers out of titles into details. Group primary form/data action and documentation/application links into one wrapping row immediately below the explanation. Place code, optional example, How it works and raw definition in a visually separated secondary section. Preserve all handlers and modal behavior; mobile content must wrap without document overflow.

### FR-023 — Consistent Data & sources workspace
Systems, Received records and Documents reuse Master data register chrome: search left, grouped Actions right, direct filters and shared column/density controls, counts and table rows. Systems use a register table rather than cards, retaining configure/record actions and supported server paging only. Registration/configuration and item CSV import open accessible dialogs with Escape/focus restoration, retaining review, uncertainty recovery and busy dismissal guards. Explain each tab with one concise task-oriented hint; remove the large repeated model banner. Preserve provenance links, document/source filters and all existing import/configuration permissions and confirmation behavior.

FR-023 spacing refinement: Table and pagination have a consistent 16px horizontal inset
and bottom spacing within each Data & sources register surface.

### FR-024 — Flight recorder overview
The first Overview tab shows a read-only chronological event band, newest recorded sequence first, with local display dates and lazy loading of older pages on scroll. Reuse tenant-scoped timeline events without a time cutoff. Event nodes expose only explicit source, subject and causation references, never inferred causal edges. Clicking events/records opens the existing Inspector; the focused Record graph remains available. Show recorded versus occurred times, initial/older error retry, empty/end states and manual load fallback. Tenant changes discard stale responses. No historical state reconstruction, fabricated missing movements, schema changes or new business rules.
Acceptance: multiple dated pages append without duplicates; failed older reads preserve earlier events; retry works; changing tenant cannot display stale results; all nodes open their exact reference; narrow screens scroll the band internally.

### FR-025 — Integration navigation terminology
Rename the Company navigation entry and page heading to Integrations. Label tabs Source systems, Received data and Documents (German: Integrationen, Quellsysteme, Empfangene Daten, Dokumente). Preserve route identifiers, reads, actions and the distinction between registered sources and connected systems. User accepted the proposed terminology.

### FR-026 — Layered temporal record graph
Replace the event-list Overview with a left-to-right temporal graph and fixed Reference, Source, Evidence, Reality and Events lanes. Records are deduplicated by kind and opaque ID; every loaded event remains a separate node. Place records at their earliest subject event in the loaded window; records known only through references appear at the left boundary, explicitly labelled as references with unknown creation time. Recording sequence supplies equally spaced time slots with localized recording timestamps (not proportional elapsed time). Show only allowlisted explicit payload/source/subject/causation references, never infer links from names, time proximity or correlation. Relationship lines are hidden until selection. Selecting a node highlights its direct loaded neighbors and draws only incident edges with visible endpoints; counted off-screen hints support stepwise navigation. Reference is always visible and numbered 01 like the other lanes (spec157). Details opens the existing Inspector. Show business labels and received quantities; technical IDs stay in details/tooltips. Older cursor pages prepend on horizontal left scroll while preserving the viewed time anchor, with manual fallback and retry. Initial focus is the newest end. Preserve tenant isolation and empty/error states.
Acceptance: one source node across repeated events; source/document/commitment/reservation references connect their correct identities across lanes; disconnected records stay dimmed on selection; equal timestamps preserve sequence order; prepend preserves viewport; mobile scroll remains inside the band. Loaded history is explicitly bounded and is not a reconstruction of historical operational state.

FR-026 naming refinement: use Understand context as the visible graph heading, matching navigation, with the subtitle How sources, documents and operational records connect over time. Keep Overview and Record graph tab labels. Flight recorder remains only an internal implementation name.

### FR-027 — Unified Inspector record register
The Inspector Facts tab must offer all record families shown in Reality records, plus Facts and document lines, in one searchable paginated read-only table. Default to All records; a direct Record type selector switches families, including the existing detailed Facts table for observations. Keep type identity explicit; no relabelling operational records as source observations. All pages are reachable beyond the explorer ten-record preview. Retain record Inspector and graph actions; URL stores family and page. Existing operational Facts and targeted observation links retain their meaning. No new mutations or schema.
Acceptance: all supported families available; search precedes pagination; full result count/page boundaries stable; foreign records excluded even when search matches their ID; fact selection restores observation columns and existing filters/actions; source/document/reality/event rows open exact record kind and ID.

Spec157 refines FR-026 layout: reference-only records occupy an explicitly untimed left-boundary area with multiple columns and at most two cards per lane/column. Observed records retain their recorded-event columns; no reference is assigned a creation timestamp.

### FR-028 — Inspector numeric presentation
Restore the shared WEB_SPEC account presentation contract in every Inspector entry point. Format typed quantities, amounts and unit prices using the current user locale, independently of UI language. Composite line and historical-price values must retain numeric/currency metadata rather than forcing the browser to guess numbers from text. Preserve received precision for unit prices, retain existing money/quantity formatter conventions, and never invent a currency for an unqualified value. Numeric-looking IDs, SKUs, business names, free text and original payloads remain exact. API raw values, shortest links and tenant reads remain compatible; no schema or business calculations change.

### FR-029 — Content-aligned Inspector navigation
Owner-approved navigation: Context (DE Kontext), Facts (Fakten), Rules (Regeln), Actions (Aktionen). Context tabs: Timeline, Record graph. Facts has one paginated All records entry with the existing type filter; the former grouped raw-record preview remains available as a secondary Technical record overview disclosure, loaded only on request. Legacy `records` URLs open the unified register while preserving tenant/search and record filters. Facts tabs: All records, Calculated views, in that order. Rules tabs: Fact rules, Exception rules. Calculated views retain their explicit explanation as derived results from existing records, not newly stored facts. Actions opens Event history first, followed by Action catalog; the catalog retains application actions and underlying commands. Timeline heading matches its tab. Existing reads, actions, confirmation, raw fields, graph navigation and tenant boundaries remain unchanged. All supported UI languages receive consistent labels.

FR-029 terminology: Facts is the user-facing umbrella for recorded business facts across source, evidence and operational records. The technical `Fact` family is labelled Additional facts (DE Zusätzliche Fakten) in the record-type filter; its identity, authority and behavior remain unchanged. Recorded assertions and commitments are not relabelled as proof of fulfilment.
