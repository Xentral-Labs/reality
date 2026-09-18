# Feature Specification: Global Command Palette

**Feature Branch**: Not created; specification prepared in the existing checkout.
**Feature Directory**: `specs/237-global-command-palette`
**Created**: 2026-09-18
**Status**: Product scope accepted for technical planning on 2026-09-18; implementation pending
**Language**: English
**Input**: Inspect the existing capabilities and specify a strong Command-K experience for finding business records, opening destinations and starting work throughout the ERP.

## Context and Intent

### Problem

The sidebar says Search, but Command-K currently searches only globally discoverable actions. Users who know a customer name, item code, order number or business task must first know which workspace contains it. An empty palette displays a long action inventory. Existing register search, operational forms, reports, tool discovery and chat handoff are not brought together.

The palette should be the fastest predictable route from a known name, number or intention to the correct existing work surface. It must remain simple on the surface and fully explainable underneath.

### Scope

- One company-scoped palette for records, destinations, actions, worklists and reports.
- Direct record search across the coverage matrix below, including closed/historical records where retained and accessible.
- Existing capability discovery with an honest distinction between opening a form, opening a report, showing capability details and preparing a chat draft.
- Keyboard-first interaction, localized vocabulary, deterministic relevance, bounded results, recent destinations and personal favorites.
- Explicit company switching and optional contextual shortcuts without cross-company business search.
- A complete proposed feature, delivered through independently testable stories; P2 stories remain required for feature completion.

### Coverage Matrix

| Category | Required searchable content | Selection outcome |
|---|---|---|
| Business partners | Customers and suppliers by held name, identifier and customer/supplier number where recorded | Existing partner detail; one result with both roles when the same partner is both |
| Items and locations | Item name/SKU, location name/code where recorded, opaque identifier | Existing master-data detail |
| Orders | Customer orders and supplier orders by number, held external reference and partner name | Existing order detail, with direction clearly stated |
| Finance | Customer/supplier invoices and credits, recorded payments by number/reference and partner name | Existing financial detail, or exact record in Inspector when no dedicated detail exists |
| Warehouse and shipping | Shipments by held shipment/tracking reference; reservations and movements by exact identifier | Existing shipment or exact Inspector detail |
| Reality and evidence | Commitments, facts, ledger entries, documents and source records by exact identifier; documents by number; sources by held external identifier | Exact Inspector/evidence/source detail with existing trace links |
| Workspaces and settings | Every permitted primary destination and named register; personal/company settings, members, integrations, eligible demo controls | Exact destination/register, preserving company context |
| Worklists | Outstanding customer/supplier invoices, overdue customer/supplier invoices, blocked outbound commitments, open inbound/outbound commitments, exceptions and pending decisions | Existing list with visible canonical filters |
| Reports and capabilities | Available calculated views, analysis templates, the current user's saved reports and all discoverable Tools capabilities | Existing reader/editor/form, capability detail or explicit chat-draft handoff |
| Help and company | Existing documentation/help entry points; names of accessible companies | Open help, or explicitly switch company |

Only held fields are searched; missing business identifiers are not manufactured. A matching related partner name is supported for the listed operational records, but does not imply a transitive search through every relationship. Deep raw-payload search is outside this scope.

### Result Groups and Search Filters

A **search filter** selects a broad result class: All, Records, Actions, Pages or Reports. A **visible result group** identifies what a hit belongs to and owns the four-hit preview limit and its Show all link. A **search provider** is an internal data source; its request/page boundaries do not define a visible limit. A **record family** is a finer Records refinement, such as customer invoice or supplier invoice.

The visible groups are fixed:

| Visible result group | Search filter | Included results |
|---|---|---|
| Business partners | Records | Customers/suppliers, deduplicated by partner identity |
| Items and locations | Records | Items and warehouse locations |
| Orders | Records | Customer and supplier orders |
| Finance | Records | Invoices, credits and recorded payments |
| Shipping | Records | Shipments |
| Reality and evidence | Records | Remaining evidence/source records and exact Reality identities, including reservations and movements |
| Actions | Actions | Non-report, non-navigation capabilities, including form and capability-details outcomes |
| Pages | Pages | Workspace/register/settings destinations and named worklist shortcuts |
| Reports | Reports | Calculated views, analysis templates and the user's saved reports, merged and deduplicated |
| Help | All only | Existing help/documentation destinations |
| Companies | All only | Explicit accessible-company switch targets |

Each hit has exactly one visible group. A named worklist stays in Pages even when its destination is an existing report reader; equivalent entry points are deduplicated. Report capabilities live in Reports and navigation-only capabilities in Pages. Ask in chat, Switch company, retry, filter and Show all controls are utility controls rather than search hits and do not consume the result budget. A matched named company is a Companies hit and does consume it.

For nonempty search, rank and deduplicate hits before applying a four-hit cap per group and the twelve-hit overall preview cap. Preserve global relevance order across group boundaries; group labels must not move a weaker hit above an exact reference. Groups with matches hidden by either cap retain a labeled Show all link even if none of their hits fits into the twelve-hit preview. There is no reserved quota or fixed priority for a group.

Selecting a broad filter preserves the query and shows the same bounded preview for eligible groups. Show all opens only its named visible group inside the palette, preserving company, query and any compatible record-family refinement, with up to fifty merged hits per page. The four/twelve preview limits no longer apply there. Reports pagination includes all three report sources in one ordering; it is not a separate fifty-hit page per source. Returning from Show all restores the prior broad filter/refinement. Empty-query favorites/recents retain their separate FR-013 limits.

### Non-Goals

- New business commands, financial calculations, booking rules, permissions or document status fields.
- A second chat agent, automatic sending, autonomous execution or unrestricted natural-language query generation.
- Cross-company business search, bulk actions or silent company switching.
- Global search over raw payload contents, attachments, document bodies, chat histories or external help-site contents.
- New background indexing infrastructure, semantic/vector search or a new persisted business authority.
- Arbitrary combinations of filters inferred from prose. Named worklists use explicit existing semantics.
- A preview dashboard inside the palette, or new full business-detail pages solely for search.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md): identity, tenancy, shared services, source authority and confirmation.
- [Spec-driven workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md): scope review before planning and implementation.
- [Web specification](../../docs/WEB_SPEC.md): operational/Inspector split, routing, localization, shell and chat boundaries.
- [Spec 225](../225-refined-workspace-shell/spec.md): existing palette presentation; this feature supersedes its action-only scope when implemented.
- [Spec 226](../226-unified-tool-catalog/spec.md): unified capability discovery.
- [Current capability audit](current-state.md): inspected implementation and limitations; source inspection is not runtime verification.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Navigate and start existing work (Priority: P1)

As an ERP user, I can name a page or task without knowing its menu location.

**Why this priority**: Makes existing functionality reachable immediately without changing its business behavior.

**Independent Test**: Open the palette from several workspaces and launch navigation, one read-only report and one mutation form using only the keyboard.

**Acceptance Scenarios**:

1. **Given** an authorized user, **when** they open Command-K and search for Warehouse, Members or Integrations, **then** permitted exact destinations appear with their type and open the correct register; unauthorized destinations are absent.
2. **Given** a matching mutation capability, **when** the user selects it, **then** the existing form/review flow opens and no business mutation occurs merely from selection; cancellation changes no business data.
3. **Given** several technical representations of one capability, **when** searching its business label or exact technical name, **then** one capability result appears; a capability without a direct Web form offers details or an explicitly labeled chat draft rather than pretending it can execute.
4. **Given** an available report or historical template, **when** selected, **then** the existing reader/editor opens and retains required inputs, ownership restrictions and freshness explanations; a required snapshot date is never silently supplied.

### User Story 2 - Find the exact business record (Priority: P1)

As an operator, I can find a record from its name or reference regardless of its workspace.

**Why this priority**: A global Search entry must actually find business data.

**Independent Test**: Seed every record category in the coverage matrix, duplicate numbers, closed records and a second company; search and open their exact identities.

**Acceptance Scenarios**:

1. **Given** records for every matrix category, **when** searching each supported field, **then** the expected record appears and selection opens that exact record in the current company.
2. **Given** an exact invoice number shared by two records and a loosely matching action, **when** searching the number, **then** both records precede the loose match and show distinguishing type, partner, date and source context where held; neither is silently selected as authoritative.
3. **Given** a customer that is also a supplier, **when** searching their name, **then** one partner result carries both roles; matching orders/invoices appear separately under their own identities.
4. **Given** a completed order, settled invoice or inactive item, **when** its exact reference is searched, **then** it remains discoverable with its applicable state; open-only workspace defaults do not hide it.
5. **Given** a source/evidence/Reality hit, **when** opened, **then** the existing trace path remains available and the search does not invent relationships or business status.
6. **Given** more hits than either preview limit, including a group wholly omitted by the twelve-hit limit, **when** the user selects that visible group's Show all link, **then** only that group opens with the same query/company/refinement, up to fifty merged hits per page and exact-object selection. Reports combines calculated views, templates and saved reports without per-source limits or duplicates; returning restores the prior filter.

### User Story 3 - Search fluently and recover from partial failure (Priority: P1)

As a keyboard or assistive-technology user, I can understand, select and trust results while typing.

**Why this priority**: Speed is useful only when selection and scope are predictable.

**Independent Test**: Exercise ranking fixtures, input changes, keyboard navigation, delayed responses, partial failures and company switches.

**Acceptance Scenarios**:

1. **Given** the palette is open, **when** searching localized labels, English labels, documented business synonyms, case/diacritic variants or a one-character typo in a word of at least five characters, **then** expected matches appear; exact identifier matches precede approximate matches.
2. **Given** the result set, **when** using Up/Down, Enter, Tab and Escape, **then** all controls are reachable, the active result is announced and scrolled into view, Enter performs only its labeled outcome, and Escape restores focus without changing a draft.
3. **Given** a blocking modal or active text composition, **when** the global shortcut/Enter is pressed, **then** it does not steal the modal interaction or submit an incomplete composed query.
4. **Given** query A followed by query B or a company switch, **when** A's delayed results arrive, **then** they never replace B's/current-company results; data, recents and suggestions from the old company disappear immediately.
5. **Given** one failing search provider, **when** other providers succeed, **then** their results remain usable. The affected visible group shows partial/unavailable status with retry, not No results; in Reports, available templates/calculated views remain usable when private-report search fails.
6. **Given** loading inserts higher-ranked results, **when** the user has already moved the active selection, **then** the selected result identity is preserved and Enter cannot launch a different result due to reordering.
7. **Given** a narrow screen or 200% zoom, **when** opening via touch, **then** search, scope, results and dismissal remain reachable without horizontal page scrolling.

### User Story 4 - Reach frequent and contextual work (Priority: P2)

As a returning user, I can reopen recent work, pin destinations and find the next applicable action.

**Why this priority**: Reduces repeated typing without filling the empty palette with the entire catalog.

**Independent Test**: Open records/pages, pin and unpin entries, reload, change users/companies and revoke access.

**Acceptance Scenarios**:

1. **Given** an empty query, **when** opening the palette, **then** at most ten initial entries combine up to four favorites, four recent destinations and two applicable contextual shortcuts, with deduplication; missing slots use permitted common destinations.
2. **Given** a permitted record/page/report, **when** opened or pinned, **then** it is available on a later visit in the same browser, user and company; Clear recent history and Unpin remove it from the relevant collection.
3. **Given** a record detail with an existing applicable action, **when** choosing its contextual shortcut, **then** the target record is named and the normal flow receives its exact identity; applicability and permission are checked again before execution.
4. **Given** a deleted, inaccessible or renamed target, **when** recent/favorite entries are resolved, **then** unavailable targets reveal no stale protected labels and cannot execute; available targets use current labels. Logging out clears local recents/favorites.

### User Story 5 - Open worklists, ask for help and change company explicitly (Priority: P2)

As a user with a business intention, I can enter a known task phrase and reach the appropriate existing surface.

**Why this priority**: Connects discovery to daily work without creating hidden automation.

**Independent Test**: Open every specified worklist, hand a query to chat with an existing draft and switch between authorized companies.

**Acceptance Scenarios**:

1. **Given** each worklist in the matrix, **when** its label or synonym is searched and selected, **then** its visible filters reproduce the canonical list membership and retain the current company; financial sides remain distinct.
2. **Given** a question or a capability requiring chat, **when** the user explicitly selects Ask in chat, **then** the existing chat receives an editable company-bound draft, preserves existing draft content, and sends nothing automatically; record context is visible and removable.
3. **Given** accessible companies with similar names, **when** the user selects a result labeled Switch company, **then** the normal switch flow runs and the palette's business scope resets; ordinary business results never switch company.
4. **Given** a help query or no matches, **when** the user selects Help or Browse all tools, **then** the existing destination opens; Tools receives the search text and no fabricated answer is shown.

### Edge Cases

- Same number in multiple source systems, record types or companies; identity must stay distinct.
- No business records, no favorites, no contextual action, or no authorized result.
- Empty/whitespace input, short exact identifiers, punctuation, Unicode and pasted identifiers.
- Company switch, logout, revoked membership or deleted targets during an in-flight search.
- Repeated Enter, keyboard auto-repeat, IME input and a modal already open.
- Partial failure, stale financial projections, slow search and offline navigation metadata.
- Private reports owned by someone else; reports requiring explicit input.
- A search hit is readable but its related mutation is forbidden or currently inapplicable.
- Unsaved forms and chat drafts retain existing navigation protection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cmd+K/Ctrl+K and the existing sidebar/touch entry open the same palette. Opening resets the query and focuses a localized Search or start an action field; the current company is visible.
- **FR-002**: Provide all permitted destinations/registers in the matrix, using existing navigation behavior and preserving unrelated drafts and navigation protections.
- **FR-003**: Discover capabilities from the shared vocabulary, deduplicate equivalent representations and distinguish Open, Start form, Show details, Open report and Ask in chat outcomes. Existing mutation confirmation and validation remain mandatory.
- **FR-004**: Search every record family and supported field in the coverage matrix across accessible retained records, including closed/inactive records. Search must not be limited to currently loaded rows or a default first page.
- **FR-005**: Each hit displays a business label, result type and sufficient held secondary context to distinguish duplicates. Navigation uses opaque identity, never the human-readable number. Record results open the existing business detail or the exact Inspector fallback.
- **FR-006**: Provide All, Records, Actions, Pages and Reports filters. Help/company results appear in All; an explicit Switch company entry opens an accessible-company chooser. Records additionally allow a family filter. Switching filters preserves query text. Filters, visible result groups and provider boundaries follow the Result Groups and Search Filters section.
- **FR-007**: Rank unique exact identifiers/business references first, exact labels next, then prefix/token matches and approximate word matches. Context and recent use break ties only within the same relevance tier; remaining ties use stable type/label/identity order. Duplicate exact references are all retained.
- **FR-008**: Match supported UI-language labels, English labels, canonical business synonyms, case and diacritic variants. Support a single insertion, deletion, replacement or adjacent transposition in words of at least five characters. Do not fuzzy-correct identifiers or rewrite source values. No minimum length may prevent an exact short identifier match.
- **FR-009**: For nonempty search previews, show at most twelve ranked hits overall and four per visible result group, after identity deduplication. Every group with hidden hits retains Show all, including groups with no hit in the preview. Show all pages one named group with at most fifty merged hits per page and preserves query/company/refinement; provider boundaries never multiply these limits. Controls and empty-query suggestions follow the separately defined rules. Partial hit sets must not be labeled complete totals.
- **FR-010**: Provide accessible active-result navigation, Enter selection, keyboard access to filters and secondary controls, Escape dismissal/focus restoration, visible focus and announced loading/result/error states. Preserve existing modal precedence and IME composition; touch targets are at least 44px.
- **FR-011**: Ignore superseded searches, clear previous-company state on switch, preserve a manually selected result by identity while new results arrive and revalidate access when opening a target. A vanished active result clears selection instead of redirecting Enter.
- **FR-012**: Expose provider loading/failure/retry within its visible result group separately from no matches. Healthy providers and static destinations, including those in the same group, remain usable during unrelated data-search failures. Retain existing freshness/staleness indicators for any displayed derived state.
- **FR-013**: Empty-query suggestions follow US4.1. Maintain at most twenty recent destinations and twenty favorites per user/company in the same browser; recents track successful opens, not typed search text. Provide pin/unpin and clear-history controls. Persistence across devices is not required.
- **FR-014**: Revalidate recent/favorite visibility before rendering protected labels, refresh labels on resolution, suppress unavailable targets and clear local collections on logout. Company/user collections never mix.
- **FR-015**: Contextual shortcuts may preselect only the explicitly identified current record in an existing supported flow. They must state the target and preserve service-owned applicability and confirmation.
- **FR-016**: Offer every named worklist in the coverage matrix through canonical filters, with no new interpretation of overdue, outstanding, blocked or pending. Display its scope at the destination.
- **FR-017**: Discover available calculated views, templates and the user's private saved reports; open their existing readers/editors and preserve ownership, required inputs and freshness semantics.
- **FR-018**: Offer an explicit Ask in chat handoff for nonempty input and supported capabilities. It preserves existing draft text, attaches only visible/removable authorized context, never sends, and uses the existing confirmation workflow later.
- **FR-019**: Offer only accessible companies as explicitly labeled switch targets. Switching uses the existing flow and does not search business records across companies.
- **FR-020**: Offer existing help destinations and Browse all tools, retaining the query in Tools. Do not imply that unavailable direct Web execution exists.
- **FR-021**: Localize all new UI copy in the four supported UI languages; preserve original business names, numbers and technical identifiers. Meet the responsiveness targets in SC-003 without exhaustive client-side record downloads.

### Domain and Traceability Requirements

- **DR-001**: Search is read-only discovery. Source → Evidence → Reality traceability remains through the selected record's existing shortest true links. Search does not create or rewrite source, evidence or Reality records.
- **DR-002**: Displayed operational state and amounts come from canonical shared reads. No document fulfillment/payment status fields, duplicate financial calculations or new stored derived authority are introduced. Missing state is omitted rather than guessed.
- **DR-003**: Every business search and target resolution enforces current tenant and authorization scope through shared application services, as do the existing execution flows. Search results, counts, snippets, recents and favorites must not disclose inaccessible records.
- **DR-004**: Human-readable numbers are search terms, never identities. Deduplication uses actual object/capability identity and does not merge unrelated objects because a number, partner or correlation matches.
- **DR-005**: Source payloads remain lossless and unchanged. Searching held identifiers does not promote arbitrary payload fields into a new typed business schema. Any persistence for user navigation preferences requires explicit justification in the implementation plan.

### Key Entities

- **Search result**: Authorized reference to a record, capability or destination, with its type, display context and explicit selection outcome; not a new business authority.
- **Capability**: Existing business ability with linked read, form, report, details or chat representations.
- **Navigation preference**: A user's favorite or recent target within one company; stores no financial truth or raw search history.
- **Search context**: Current company, optional current record, query and selected result family; confers no execution permission.

## Success Criteria *(mandatory)*

- **SC-001**: Every coverage-matrix row has positive, empty and authorization-negative acceptance fixtures. Every supported exact identifier finds its retained target, including targets beyond the first fifty records and closed/inactive records.
- **SC-002**: Every FR and DR maps to the scenarios below and receives executable proof in plan/tasks before implementation. Duplicate-reference, cross-company, private-report and stale-response scenarios have zero unintended disclosure or mutation.
- **SC-003**: In a declared test environment with 100,000 searchable business records in one company, ten concurrent searching users and 100ms simulated network round-trip latency, 95% of palette openings show an interactive field within 200ms; 95% of destination/action searches show results within 300ms and record searches within 1.5s after the last keystroke. Cold and warm runs are reported separately.
- **SC-004**: All scripted find/open/start tasks complete by keyboard alone. Every exact record task requires one palette invocation, its query and one explicit result activation; ambiguous references require explicit choice.
- **SC-005**: All fixtures for German/English business synonyms, supported-language labels and defined typo/diacritic cases return the expected hit in the first four results of its visible result group before the overall twelve-hit preview cut; exact references precede weaker matches.
- **SC-006**: All required destinations and existing global Web actions are discoverable. No action executes a business mutation on selection and no chat handoff sends a message automatically.

## Assumptions and Dependencies

- The user accepted continuation to technical planning on 2026-09-18 after reviewing the proposed scope. This records scope acceptance; implementation still requires tasks, consistency analysis and the normal technical gates. No application behavior changes in the planning task.
- The baseline is source inspection on 2026-09-18, not a live-system audit. Existing uncommitted work in the checkout remains separate.
- Existing catalog, forms, routes, report readers, source trace views and company switching are reused. Catalog presence describes capability support, not permission.
- Existing register and combobox search cannot be assumed to provide complete, consistently ranked global search. Planning must prove bounded, tenant-scoped coverage without full table downloads or first-page truncation.
- Named worklists are explicit shortcuts. If an existing destination lacks an exact canonical filter, planning must expose that shared filter rather than approximate it in the palette.
- Recent/favorite persistence is intentionally limited to the same browser. No cross-device profile schema is required by this specification.
- Workspaces remain the main place to read and edit. Search results contain only enough context to choose correctly; no live KPI dashboard is required.
- Planning must map every matrix family to its actual reader and exact detail destination, document missing application-service capabilities, and choose the smallest storage-disciplined implementation. PostgreSQL remains the only business database.

## Open Questions

None. Coverage, local preference persistence and inclusion of P2 stories are retained from the accepted planning scope.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-010 | US3.2, US3.3, US3.7 | Keyboard, modal, IME, focus, screen-reader and responsive browser proofs |
| FR-002 | US1.1; edge case unsaved forms | Destination matrix and draft-preservation browser proofs |
| FR-003 | US1.2–3 | Capability identity and no-mutation launch contracts |
| FR-004, FR-005 | US2.1–5 | All-family search/service fixtures, exact deep links and historical records |
| FR-006, FR-009 | US2.6 | Filter/query retention, pagination and partial-total proofs |
| FR-007, FR-008 | US2.2, US3.1 | Deterministic ranking, language, typo and duplicate-reference fixtures |
| FR-011 | US3.4, US3.6; revoked-target edge case | Delayed response, scope switch and active-identity browser proofs |
| FR-012 | US3.5; stale-projection edge case | Independent provider failure/retry, partial visible groups and freshness proofs |
| FR-013, FR-014 | US4.1–4 | Bounded preferences, reload, logout, revoked-access and label-refresh proofs |
| FR-015 | US4.3 | Context target, applicability and cancellation proofs |
| FR-016 | US5.1 | Worklist membership parity with canonical reads |
| FR-017 | US1.4 | Report ownership, template inputs and freshness proofs |
| FR-018 | US5.2 | Chat draft preservation, visible context and no-send proofs |
| FR-019 | US5.3, US3.4 | Accessible-company switching and scope-reset proofs |
| FR-020 | US5.4, US1.3 | Help/catalog navigation and query handoff proofs |
| FR-021 | US3.1, US3.7; SC-003 | Four-language coverage, responsive proofs and declared workload timings |
| DR-001, DR-002, DR-005 | US2.5, US1.2, US1.4 | Trace parity, source immutability and no derived-state persistence review/tests |
| DR-003 | US1.1, US3.4, US4.4, US5.3 | Cross-tenant/non-owner service and browser negative proofs |
| DR-004 | US1.3, US2.2–3 | Identity-based deduplication and duplicate-number fixtures |

## Visual refinement — accepted user feedback, 2026-09-18

FR-010/012/021 refinement: the palette keeps a stable header, bounded scrollable
result area and footer while providers complete. Show one aggregate loading status,
never seven repeated loading rows or transient error controls for pending work.
Failures remain explicit in one compact summary with expandable per-provider retry;
successful results remain visible. Use aligned icon/title/context/outcome columns,
quiet filter tabs, consistent spacing and visible keyboard guidance. No ranking,
authorization, mutation or pagination behavior changes.

Acceptance: loading, partial success, complete success and provider failure retain
the search input position; failures can be inspected and retried independently;
long identifiers wrap or truncate within the viewport, and narrow screens retain
keyboard/pointer access to every control.

### Exact destination presentation repair

FR-005/021: Orders and master records selected outside the loaded register page
must use a contained, responsive preview with the same detail content and actions
as an inline row preview. Register toolbar edge/padding rules must not affect its
close control or content. Compact sections must size to available workspace width
(including an open chat), avoid stretched empty cards and preserve readable links.
Check each destination renderer and enumerate tested record families separately
from families absent in the live fixture. Exact identities and Inspector fallbacks
remain unchanged; no new detail pages or business rules are introduced.

A selected record already present in the register must reveal its inline preview
on opening, including rows below the viewport; navigation must not leave the user
looking at unrelated rows above the selected detail.

### Palette visual consistency

FR-010/021: retain the accepted palette layout and interactions while matching the
app's visual language: unframed 16px outline icons at sidebar stroke weight,
workspace-specific page symbols, neutral active-tab underline, regular list labels
and shared surface/border/radius tokens. Record kinds distinguish items/locations.
No search, ranking, navigation, loading or confirmation behavior changes.
