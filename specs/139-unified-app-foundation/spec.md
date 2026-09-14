# Feature Specification: Unified App Foundation

**Feature Branch**: Not created; the existing checkout is preserved for specification review.
**Feature directory**: `specs/139-unified-app-foundation`
**Created**: 2026-09-07
**Status**: Scope approved by owner on 2026-09-07; technical planning authorized
**Language**: English
**Input**: Build from the new HTML design, selectively reuse valuable legacy capabilities, and ultimately deliver one product instead of separate old-App and Playground interfaces. Start with the new application shell, Home, company Chat, a complete delivery case and one shared action card reached from case, Chat and global action discovery.

## Context and Intent

### Problem

The current Product App exposes the operational core but its navigation and forms grew through experimentation. The separate Playground makes business activity easier to understand, yet separates learning from the main product. Operators need a coherent application in which overview, conversation, business cases and precise actions stay connected.

The owner prefers the new design as the product starting point. Legacy feature parity is not a goal: existing screens must earn a place through an actual user task. Proven business services, security, records and recovery behavior remain authoritative.

### Scope

This is the first independently usable increment of the [unified-product roadmap](../../docs/ideas/unified-product-migration.md). It delivers:

- A new application shell for authorized ordinary-company contexts, following the accepted sidebar and page design, with company selection, responsive navigation and global action discovery.
- Home with authoritative current position, attention items and pending decisions, plus real company Chat and its existing saved conversations.
- A delivery worklist and selected case showing business context, quantities, history, relevant actions and an explanation inspector.
- One reusable action-card experience for **reserve stock** and **record shipment**, reached from the delivery case, company Chat and the global launcher.
- A complete delivery journey against an existing customer commitment, including partial and final shipment. Opening stock and order creation provide the acceptance fixture through existing business services; new creation interfaces are outside this increment.
- A focused Decisions destination for the two action families, retaining recovery access to existing proposals through their established paths where necessary.
- Real loading, empty, unavailable, stale, failure, confirmation and recovery states. The HTML's in-memory behavior and scripted answers are never production behavior.

The final product architecture includes Analytics, master data, specialist workspaces, data/source tools and integrated practice companies. Those later scopes do not become acceptance requirements for this first increment. The new shell must leave a coherent place for them without presenting unfinished destinations as working features.

### Non-Goals

- Rebuilding every old screen, experimental control, command or specialized projection.
- Full Analytics, historical time series, automation percentages or a new KPI engine.
- New master-data, order-entry, finance, returns or correction interfaces beyond the selected delivery actions. Existing control/recovery paths remain accessible during transition.
- A universal form/workflow builder, arbitrary command/code execution, autonomous shipping, outbound warehouse execution or automatic approval of multiple steps.
- Converting practice accounts into production accounts, broadening sandbox Chat permissions, migrating practice history or removing the standalone Playground in this increment.
- Removing legacy business records, saved conversations, proposals, receipts or access policies.
- A permanent Old/New product choice, wholesale legacy-screen transplantation, or redesigning the domain around a stored case/workflow status.
- Deployment, final cutover or legacy retirement approval as part of specification creation.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md) and [spec-driven workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- [Web product](../../docs/WEB_SPEC.md), [UX matrix](../../docs/WEB_UX_MATRIX.md), [data model](../../docs/DATA_MODEL.md), [test strategy](../../docs/TEST_STRATEGY.md).
- [Workspace actions](../046-workspace-views-actions/spec.md), [command-owned guidance](../051-command-action-guidance/spec.md), [Chat command coverage](../042-chat-mcp-command-parity/spec.md).
- [Learning Playground](../096-learning-playground/spec.md), [practice companies](../104-playground-practice-companies/spec.md), [read-only Playground companion](../106-playground-companion/spec.md).
- [Frozen visual reference and interpretation](design/README.md).

The proposal supersedes old navigation/layout expectations only for the new foundation surfaces. Existing domain, command, company Chat and practice security contracts continue to apply. Accepted changes to durable web/UX contracts must accompany implementation; this draft does not claim that the current application already follows the new layout.

## User Scenarios & Testing

### User Story 1 - Enter a coherent application (Priority: P1)

An authorized company member enters the new application, recognizes the active company, moves between Home, Ask Reality, Your work and Decisions, and returns to the same selected business context.

**Why this priority**: Every subsequent workflow depends on trustworthy navigation and context.
**Independent Test**: Use two authorized companies, an unauthorized company and an empty company to navigate, reload and follow a saved case link on desktop and mobile.

**Acceptance Scenarios**:

1. **Given** access to two companies, **When** switching company, **Then** the company identity is visible and the new company has its own records, conversations and proposals; no previous-company detail flashes into view.
2. **Given** a selected case, **When** using history navigation or reopening its link in the same authorized company, **Then** the same case is selected or an honest no-longer-accessible state is shown.
3. **Given** revoked membership or a foreign record link, **When** reading or confirming, **Then** no foreign details or action effects are exposed.
4. **Given** an empty company, **When** Home opens, **Then** it explains the absence of operational data and links to the existing authorized setup/source path. No synthetic tenant position appears.
5. **Given** a verified account with only practice admission, **When** it enters the application, **Then** existing authorized practice access remains available without granting company access or loading unauthorized company data.
6. **Given** an unfinished later module, **When** navigating the new shell, **Then** it is not presented as an operational destination. Necessary existing support/configuration paths remain identifiable and reachable during transition.

### User Story 2 - Start from an explainable Home (Priority: P1)

The operator sees current work and can open the case or records that explain an important number.

**Why this priority**: The dashboard must connect company oversight to actionable work.
**Independent Test**: Compare Home with the existing authoritative current-position and exception reads for the same company and filters.

**Acceptance Scenarios**:

1. **Given** open customer commitments and pending decisions, **When** Home loads, **Then** it presents current position, attention items and pending decisions with direct access to the corresponding cases or review.
2. **Given** a displayed quantity, **When** opening its explanation, **Then** contributors preserve its company, filters, item/unit scope and read-time interpretation.
3. **Given** a failed or incomplete read, **When** Home displays its state, **Then** unavailable information is distinguished from zero and an empty attention queue.
4. **Given** no AI provider or an unavailable provider, **When** Home opens, **Then** authoritative position and deterministic actions remain usable; no fabricated briefing is shown.
5. **Given** a confirmed reservation, **When** returning to Home, **Then** the current position and decision state reflect the authoritative result, or explicitly indicate that refresh is unavailable.

### User Story 3 - Understand a delivery without knowing the data model (Priority: P1)

The operator selects an open delivery and sees what was promised, what shipped, what is reserved and what remains, alongside contextual assistance and record explanations.

**Why this priority**: This is the core business-oriented interaction that the new product must prove.
**Independent Test**: Open a seeded delivery and follow quantity, history and source links without needing the technical Explorer as a separate starting point.

**Acceptance Scenarios**:

1. **Given** stock 20, customer commitment 12 and active reservation 12, **When** shipment of 5 has been recorded, **Then** the case shows physical 15, active reservation 7, available 8, fulfilled 5 and open 7 through authoritative reads.
2. **Given** a multi-line order or several reservations, **When** choosing a line or action target, **Then** the selected commitment and applicable reservations are explicit; a human order number does not identify the action target.
3. **Given** a quantity such as reserved 7, **When** inspecting it, **Then** the actual records, relevant history and shortest path to evidence/source are accessible without discarding the selected case.
4. **Given** unreserved demand, a hold, insufficient stock or missing evidence, **When** viewing the case, **Then** each condition is described according to the held evidence. Unreserved alone is not a shortage and missing dates do not establish lateness.
5. **Given** a case with incomplete references or history, **When** showing its explanation, **Then** missing information is explicit rather than supplied by a guessed narrative.
6. **Given** the final shipment closes the commitment, **When** refreshing open work, **Then** it no longer appears as open work, but its case/history remains accessible through its link and the execution result.

### User Story 4 - Use the same action card from any entry (Priority: P1)

The operator requests a reservation or shipment from the case, company Chat or a searchable global action launcher, completes the same fields and reviews the same business effect.

**Why this priority**: This unifies natural-language intent and precise form-based operation.
**Independent Test**: Prepare equivalent intents through each entry using identical fixtures, then compare the resolved references, validation, review and recorded effects.

**Acceptance Scenarios**:

1. **Given** a selected delivery, **When** opening Reserve, **Then** known references are prefilled visibly; opening or editing the form has no business effect.
2. **Given** no selected case, **When** searching the global launcher for reservation or shipment, **Then** business labels and prerequisites identify the action and the form asks for missing context.
3. **Given** a company Chat request with ambiguous names or missing quantities, **When** preparing an action, **Then** actual candidate choices or missing fields are presented rather than silently guessed.
4. **Given** a prepared review, **When** changing quantity, location or target, **Then** the old review cannot authorize the changed intent; a fresh review is required.
5. **Given** the same valid reservation/shipment intent through the three entry points, **When** reviewing and confirming in equivalent independent fixtures, **Then** the same business validation, records and effect apply.
6. **Given** a request to reserve and ship, **When** the first action is confirmed, **Then** the second is not implicitly executed or approved; it requires its own current review and confirmation.
7. **Given** an unsupported or unauthorized command, **When** searching or asking for it, **Then** the new card never supplies a bypass. Existing supported capabilities outside this increment remain at their established access paths.

### User Story 5 - Confirm once and recover a reliable outcome (Priority: P1)

The operator can review, reject or confirm a proposal and distinguish completion, failure and unknown execution even after navigation or connectivity loss.

**Why this priority**: A coherent UI must not create duplicate business actions or hide uncertainty.
**Independent Test**: Exercise stale state, simultaneous confirmations, lost responses and observation failure around real reservation/shipment proposals.

**Acceptance Scenarios**:

1. **Given** a draft or pending review, **When** cancelling before preparation or rejecting a prepared proposal, **Then** no inventory, fulfillment or financial effect occurs and other views agree on the decision state.
2. **Given** a pending proposal, **When** navigating from Chat to Decisions and the case or reloading, **Then** the same proposal is recovered, not silently duplicated or lost.
3. **Given** an already applied confirmation, **When** repeating it from another entry or tab, **Then** no second reservation or shipment is recorded.
4. **Given** changed stock, a hold, revised intent, revoked access or an invalid target, **When** confirming, **Then** the current rules reject stale/unauthorized execution and the user gets an actionable review state.
5. **Given** a response lost after execution, **When** reopening, **Then** the user sees the existing receipt or explicit unresolved execution; dependent actions cannot assume success and no blind retry occurs.
6. **Given** successful execution but failed observation refresh, **When** reviewing the outcome, **Then** recorded execution and unavailable observation are distinct, and refresh does not reexecute.
7. **Given** a verified result, **When** inspecting technical detail, **Then** command, reviewed arguments, proposal/execution identifiers and resulting record links are available.

### User Story 6 - Ask globally or within a case (Priority: P1)

The operator uses existing company conversations and asks about a selected delivery without repeatedly describing its identity.

**Why this priority**: Chat must participate in the same work, not behave as a disconnected helper.
**Independent Test**: Use a deterministic provider to answer and propose from global and case context; additionally exercise real provider-unavailable behavior.

**Acceptance Scenarios**:

1. **Given** an existing saved company conversation, **When** opening Ask Reality or reloading, **Then** its authorized history remains available without rewriting old messages.
2. **Given** a selected case, **When** asking a contextual question, **Then** the current case is visibly identified, answers use its authorized records and supporting links reopen that context.
3. **Given** an edited or switched case, **When** asking again, **Then** the current question's context is explicit; past answers remain identifiable as past responses rather than current facts.
4. **Given** a timeout or provider failure, **When** sending a question, **Then** the question is retained with a retryable error and forms remain usable. No scripted business answer replaces provider output.
5. **Given** a prompt containing another company's identifiers, **When** tools are called, **Then** the prompt cannot override the authenticated company/context boundary.
6. **Given** an accepted action draft, **When** continuing through its form or the shared Decisions view, **Then** the same proposal and result are used.

### User Story 7 - Use the new design with confidence (Priority: P1)

An operator recognizes the design from the approved reference and can work with a keyboard, a phone, or another supported language without losing context or controls.

**Why this priority**: The user selected the new design for its coherence; a visual reskin of old screens does not meet the goal.
**Independent Test**: Review Home, global Chat, selected case, action review and outcome at 390 px and 1440 px in light/dark appearance and en/de/nl/es.

**Acceptance Scenarios**:

1. **Given** a wide display, **When** working a delivery, **Then** application navigation is distinct from the worklist and case detail/contextual assistance remain together.
2. **Given** a narrow display, **When** moving between worklist, case, assistance and inspection, **Then** the selected case and pending proposal remain intact, with no page-wide horizontal overflow; genuinely tabular detail may scroll within its own region.
3. **Given** keyboard-only operation, **When** opening/closing a card or inspector and resolving validation, **Then** labels, focus and the next relevant control are available without hover.
4. **Given** any supported language/theme, **When** viewing key states and long labels, **Then** quantities, dates, controls and confirmation are readable and localized; source payloads and intentional business names retain their original content.
5. **Given** the visual reference, **When** reviewing the implementation, **Then** it preserves the sidebar grouping, content hierarchy, whitespace, card treatment and connected case interaction using real product behavior.

### Edge Cases

- Duplicate display names, foreign identities, multi-line orders, multiple reservations, decimal quantities and incompatible units.
- Several pages of open work; an empty page after final fulfillment; direct links to a closed or no-longer-accessible case.
- Zero denominators, partial data, provider failure and quantities from incomplete result pages.
- Case/company switches with drafts, pending proposals, delayed read responses or uncertain execution.
- Stale stock, holds, overfulfillment, two tabs confirming and a response lost after commit.
- Confirmed execution with an unavailable refreshed observation; changing arguments after review.
- Empty company, pending production admission, archived practice run and membership revoked during review.
- Unsafe assistant markup and attempts to override context or approvals through source content or prompts.

## Requirements

### Functional Requirements

- **FR-001**: Present a coherent new shell for authorized ordinary-company contexts with Home, Ask Reality, Your work, Decisions, company selection and global action discovery. Later destinations must not imply unavailable capability.
- **FR-002**: Preserve company-bound selection, deep links and navigation recovery; clear or safely isolate prior-company requests, drafts, caches and visible records on context changes.
- **FR-003**: Keep existing authenticated setup/support and practice admission reachable during transition without granting new permissions or broadening sandbox capabilities.
- **FR-004**: Home must display authoritative current position, attention and pending decisions, with preserved-scope contributor/case links and no fabricated AI briefing.
- **FR-005**: Distinguish loading, empty, incomplete, unavailable, failure and stale states on every new read surface; missing reads must not display success or zero.
- **FR-006**: Provide a bounded, searchable open-delivery worklist with counterparty/item, promised, fulfilled, open and reserved quantities, preserving item/unit meaning.
- **FR-007**: Present selected commitment/line context, related reservations, actual changes, applicable blockers and links to business references without inventing a linear document-owned status.
- **FR-008**: Expose business explanation followed by underlying records, evidence and original source where applicable; optional technical detail must retain selected case context.
- **FR-009**: Use one action-card experience for reservation and shipment from case, company Chat and global launcher, with visible targets, required fields, business effect and existing prerequisites.
- **FR-010**: Use actual bounded reference choices and opaque identities; missing/ambiguous targets require user resolution before a proposal can be confirmed.
- **FR-011**: Opening/editing a form creates no business effect. A prepared proposal must identify its exact intended change; edits invalidate the previous review authority.
- **FR-012**: Require explicit confirmation of each current mutation proposal. Confirmation of a preceding action does not authorize dependent actions.
- **FR-013**: Make pending proposals and their review/rejection/execution outcomes consistent across Chat, case and Decisions and recoverable after navigation/reload.
- **FR-014**: Recheck current authorization, relevant stock/holds, target validity and reviewed intent at confirmation; repeated confirmation must not duplicate a business effect.
- **FR-015**: Distinguish rejected, failed, executing, unresolved, verified and observation-unavailable outcomes according to existing execution semantics; recover results without blind reexecution.
- **FR-016**: After confirmation, refresh dependent case/worklist/Home/Decisions reads or clearly expose refresh failure. A fulfilled case remains inspectable after leaving open work.
- **FR-017**: Preserve existing company conversations and show selected case context for contextual assistance. Historical replies must not silently become current observations.
- **FR-018**: Company Chat uses existing authorized tools/provider behavior and renders the shared card for in-scope actions. Provider failure retains questions and leaves deterministic controls available.
- **FR-019**: The launcher is searchable by business action name/effect and offers the supported action card only when its context policy permits it; no arbitrary execution escape is added.
- **FR-020**: Record command, reviewed intent, proposal/execution identity and authoritative result links in accessible technical detail for in-scope mutations.
- **FR-021**: Deliver en/de/nl/es, light/dark, desktop/mobile and keyboard-accessible states for the entire increment, with readable numbers, errors, focus and confirmation.
- **FR-022**: Follow the frozen design's hierarchy and shared product controls rather than transplant whole legacy screens or ship prototype fixtures as company truth.
- **FR-023**: Preserve existing data, saved conversations, proposals, receipts and continuity-critical access paths while introducing the new foundation. Legacy UI retirement and unsupported capability removal are outside this increment.

### Domain and Traceability Requirements

- **DR-001**: Preserve SourceRecord → Document/DocumentLine → Reality where applicable. Explanations follow actual shortest true links; absent evidence is explicit.
- **DR-002**: Delivery fulfillment, reservations, stock and available quantity remain derived from existing Reality authorities, not document status or a new stored case/workflow state.
- **DR-003**: All reads, references and actions enforce the active tenant and actor through the shared application tools/services. UI and agent transports must not introduce their own domain calculations or writes.
- **DR-004**: Received quantities/amounts are preserved as stated; this increment does not recalculate source totals, taxes or implied commercial values. Operational observations remain read-time derivations.
- **DR-005**: Reservation links to its Commitment; user-facing human references never replace opaque identity or justify duplicated source/evidence relationships.
- **DR-006**: Preserve existing idempotency, immutable-source/version history, fulfillment/consumption and authorization semantics across every supported entry and recovery path.

### Key Entities

- **Company context:** Authorized scope for records, conversations, proposals and navigation; practice admission remains separately governed.
- **Delivery case:** A user-facing selection of an existing commitment and its relevant evidence/Reality relationships, not a new operational authority.
- **Commitment, Reservation and Movement:** Existing promises, assigned stock and physical changes used to explain fulfillment and availability.
- **Action intent, proposal and receipt:** Editable requested change, reviewed authorization subject and recorded outcome under the existing business lifecycle.
- **Conversation and message:** Existing company-scoped history with explicit context and references to proposed/recorded actions.

## Success Criteria

- **SC-001**: In the canonical delivery story, reservation of 12 followed by shipment of 5 yields physical 15, reserved 7, available 8 and open 7; the separate final shipment of 7 yields physical 8, reserved 0, available 8 and open 0.
- **SC-002**: Reservation and shipment each pass equivalent-intent acceptance through all three entry points; six entry/action combinations are demonstrated without duplicate effects.
- **SC-003**: Every FR and DR maps to named acceptance scenarios and an executable proof category before technical planning; plan/tasks must subsequently bind those categories to concrete tests.
- **SC-004**: All important delivery quantities and confirmed action results expose the actual supporting records and applicable evidence/source without requiring a separate technical starting point.
- **SC-005**: Required rejection, stale-review, cross-company, duplicate-confirmation, lost-response and unavailable-observation scenarios produce no unauthorized or duplicate effects.
- **SC-006**: Home, Chat, case, action review and result pass the specified four-language, two-theme, two-viewport and keyboard review without missing controls or unintended page overflow.
- **SC-007**: Saved company conversations and pending in-scope proposals survive reload; final-fulfillment cases retain an inspectable result even after leaving open work.
- **SC-008**: No later-module placeholder, prototype fixture or synthetic historical value is presented as a working live-company capability in this increment.

## Assumptions and Dependencies

- The owner has selected the new design and the first-increment direction. The owner explicitly approved this concrete scope on 2026-09-07. Technical planning is authorized; later scope expansion still needs review.
- The existing authorization, company Chat, command catalogs, reference lookup, inspector, proposal and fulfillment capabilities are the starting contracts. Their availability and gaps must be verified during planning.
- A first delivery fixture can be created through existing tools with explicit supplied business values. This increment does not need new stock/order/master-data creation interfaces to prove its selected reservation and shipment workflows.
- Current Home summaries use existing authoritative reads only. Full Analytics and historical metric definitions belong to a separate reviewed increment.
- The final integrated-practice policy remains a later decision. This increment preserves the current practice entry, saved history and read-only companion policy, so that decision does not block ordinary-company foundation work.
- This is an additive transition; the existing access paths remain until the selected replacement and continuity contract passes its own cutover review. There is no requirement for full legacy feature parity.
- The HTML demonstrates additional later features. Its mocked automation, sample histories and placeholder commercial registers do not enlarge this increment's scope.
- No new domain entity or expanded business schema is justified by this specification. Any proven persistence gap must be surfaced during planning rather than inferred from UI convenience.

## Open Questions

None requiring clarification for this bounded first increment. The ordinary-company scope, reservation/shipment action families, existing-data fixture and deferred practice migration are explicit. Owner review of this concrete scope was completed on 2026-09-07.

## Requirement Traceability

Scenario references use USn-m for User Story n, acceptance scenario m.

| Requirement | Scenario(s) | Planned test/evidence |
| --- | --- | --- |
| FR-001, FR-022 | US1-1, US1-6, US7-5 | Shell navigation and owner visual acceptance |
| FR-002 | US1-1 to US1-3, US6-3, US6-5 | Tenant/context isolation, history and delayed-response browser journeys |
| FR-003, FR-023 | US1-3 to US1-6, US5-2, US6-1 | Admission, compatibility and saved-record continuity regressions |
| FR-004 | US2-1, US2-2, US2-4, US2-5 | Home/current-position service comparison and drill-down journey |
| FR-005 | US1-4, US2-3, US3-5, US5-6 | Failure/empty/incomplete state browser and adapter scenarios |
| FR-006, FR-007 | US3-1, US3-2, US3-4, US3-6 | Bounded delivery reads and partial/multi-line fulfillment story |
| FR-008 | US3-3, US3-5, US7-2 | Shortest-link inspector and missing-evidence journeys |
| FR-009, FR-019 | US4-1, US4-2, US4-5, US4-7 | Command discovery and six action-entry parity scenarios |
| FR-010 | US3-2, US4-3 | Ambiguous/missing/foreign reference resolution |
| FR-011 | US4-1, US4-4, US5-1 | Form/proposal effect separation and intent-revision tests |
| FR-012 | US4-6, US5-1 | Explicit per-step confirmation and rejection story |
| FR-013 | US5-1, US5-2, US6-6 | Shared proposal persistence and navigation/reload journey |
| FR-014 | US5-3, US5-4 | Concurrent confirmation, stale inventory/holds and revoked membership |
| FR-015 | US5-5, US5-6 | Interrupted execution and observation recovery integration tests |
| FR-016 | US2-5, US3-6, US5-6 | Post-action read refresh and closed-case access |
| FR-017 | US6-1 to US6-3 | Persistent conversation and visible-context browser proof |
| FR-018 | US2-4, US6-4 to US6-6 | Deterministic provider/tool adapter tests and unavailable-provider UI |
| FR-020 | US5-7 | Exact reviewed intent and execution-receipt inspection |
| FR-021 | US7-1 to US7-4 | Localization audit, keyboard and responsive/theme acceptance |
| DR-001, DR-005 | US3-2, US3-3, US5-7 | Source/evidence/Reality relationship and opaque identity proofs |
| DR-002 | US3-1, US3-4, US3-6 | Canonical stock/reservation/partial/final shipment service story |
| DR-003 | US1-3, US4-5, US6-5 | Tenant-scoped service/tool/adapter parity and boundary tests |
| DR-004 | US2-2, US3-1, US3-5 | Supplied-value preservation and authoritative read-model checks |
| DR-006 | US5-3 to US5-7 | Idempotency, recovery, source history and fulfillment regressions |
