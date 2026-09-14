# Feature Specification: Web UX Matrix Completion

**Feature Directory**: `030-web-ux-matrix-completion`

**Created**: 2026-09-02

**Status**: Approved

**Language**: English

**Input**: "Close `016/FR-006` by proving that every in-scope Product Web surface fulfils its approved job, hierarchy, and interaction pattern from the Web UX matrix."

## Context and Intent

### Problem

Reality exposes the required business areas, but route existence alone does not prove a
coherent daily operations product. Some surfaces still present flat registers, technical
identifiers, weak empty states, or page-specific interaction arrangements where the
approved UX matrix calls for attention-first control, business context, guided actions,
and explanation. This leaves `016/FR-006` as an accepted documented gap.

The product owner needs a bounded completion pass that treats the UX matrix as an
executable product contract. Each surface must help its intended operator complete the
declared job, preserve a consistent hierarchy on desktop and mobile, and expose the
shortest path from an operational answer to Reality, Evidence, and Source.

### Scope

- Inventory the actual Product Web routes and map every applicable route to exactly one
  approved UX-matrix surface and user job.
- Complete shared shell and page-state behavior needed by all in-scope surfaces.
- Complete the attention-first operational surfaces: Home, Exceptions, Commitments,
  Inventory, Reservations, and Movements.
- Complete finance and Evidence surfaces: Open Items, Payments, Journal, Documents, and
  document explanation.
- Complete reference and configuration surfaces: Parties, Items, Locations, Commercial
  Terms/Pricing, Sources & Imports, and company settings.
- Complete support surfaces: Ask Reality, Explorer, Help & Documentation, and direct
  explanation paths.
- Prove the required hierarchy, primary actions, empty/loading/error states, responsive
  behavior, and trace entry points with a versioned coverage matrix and representative
  executable journeys.
- Close only `016/FR-006` after executable evidence, visual review, and product-owner
  final approval.

### Non-Goals

- The repeatable 10,000-orders/day benchmark owned by `016/FR-015`.
- New domain entities, business workflows, stored presentation status, or alternate
  calculations in the browser.
- Replacing the established visual identity or introducing a second component system.
- Reworking the public marketing site, authentication, localization completeness, demo
  equivalence, master-data adapter parity, or global Activity drawer already owned by
  approved or separately numbered specifications.
- Adding fields, filters, totals, or actions when no authoritative service/read model can
  support them truthfully.
- Pixel-identical layouts across desktop and mobile; the required job and hierarchy must
  remain equivalent while layout adapts to available space.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start With the Required Decision (Priority: P1)

As a Head of Operations, I can open any daily-work surface and immediately understand
what requires attention, the current position, and the next available action before
neutral history or technical detail.

**Why this priority**: The primary product promise is fast operational control, not a
collection of database registers.

**Independent Test**: Populate representative healthy, attention, and empty states;
open Home, Exceptions, Commitments, Inventory, Reservations, and Movements on desktop
and mobile; verify the declared page job, hierarchy, state, and next action.

**Acceptance Scenarios**:

1. **Given** material exceptions and current operational position, **When** Home opens,
   **Then** attention and control totals precede neutral activity, followed by inventory
   position and recent changes.
2. **Given** derived exceptions, **When** Exceptions opens, **Then** severity, impact,
   cause, recommendation, and trace form a prioritized review journey rather than a flat
   generic register.
3. **Given** at-risk and healthy commitments, **When** Commitments opens, **Then** risk
   totals and promise control precede filters and the complete register.
4. **Given** shortage, fully allocated, and available stock, **When** Inventory opens,
   **Then** the three states are distinguishable, location can be considered, and the
   explanation shows movements, reservations, inbound supply, and the inventory equation.
5. **Given** no applicable records, **When** an operational page opens, **Then** its empty
   state explains what belongs there and identifies the truthful next setup or intake step.

---

### User Story 2 - Control Financial Position and Evidence (Priority: P1)

As a financially literate operator, I can assess receivables, payables, cash allocation,
postings, and document interpretation without starting from technical posting IDs.

**Why this priority**: Financial control is part of operational reality and must remain
scannable, balanced, and traceable to evidence.

**Independent Test**: Open representative receivable, payable, overdue, unmatched,
balanced, corrected, and empty states across Open Items, Payments, Journal, Documents,
and document explanation; verify totals, prioritization, business labels, and trace.

**Acceptance Scenarios**:

1. **Given** receivables and payables with mixed due states, **When** Open Items opens,
   **Then** receivable, payable, overdue, and open totals precede aging/status controls
   and the worklist.
2. **Given** allocated and unallocated payments, **When** Payments opens, **Then** cash
   direction and control totals are visible and unmatched payments receive priority.
3. **Given** posting groups, **When** Journal opens, **Then** debit and credit control
   totals, date/account context, and balance state are visible before technical identity.
4. **Given** normalized documents, **When** Documents opens, **Then** type, date, party,
   amount, interpretation, and linked Reality can be scanned using business labels.
5. **Given** one document, **When** its explanation opens, **Then** summary, execution,
   lines, Reality consequences, financial postings, source metadata, and collapsed raw
   payload appear in that order where applicable.

---

### User Story 3 - Maintain Minimal Operational Configuration (Priority: P2)

As an operator responsible for setup, I can maintain the minimal reference, commercial,
source, and company configuration Reality actually uses without encountering a shadow
ERP or many competing forms.

**Why this priority**: Safe configuration enables daily work but must not dominate it or
invent domain authority.

**Independent Test**: Complete find, create, inspect, edit, lifecycle, and empty-state
journeys for Parties, Items, Locations, Commercial Terms/Pricing, Sources & Imports, and
company settings using authorized representative records.

**Acceptance Scenarios**:

1. **Given** reference records, **When** a register opens, **Then** business identity,
   type, state, useful filters, and one clear create action precede opaque trace identity.
2. **Given** a selected reference record, **When** detail opens, **Then** it is read-first,
   connected operational context precedes trace detail, editing is explicit, and lifecycle
   controls are visually separated.
3. **Given** commercial setup, **When** Commercial Terms opens, **Then** price lists,
   tiers, assignments, and groups are separated into focused tasks with contextual empty
   guidance and at most one focused create/edit workflow at a time.
4. **Given** source definitions and recent intake, **When** Sources & Imports opens,
   **Then** configured sources precede discovery, capabilities and readiness are clear,
   and test intake does not compete with normal inspection.
5. **Given** company configuration, **When** settings opens, **Then** company, Data, and
   Agents remain one coherent settings hierarchy rather than a second dashboard.

---

### User Story 4 - Ask, Learn, and Trace Without Losing Context (Priority: P2)

As an operator or support user, I can ask a business question, learn the product, or
inspect technical records while staying connected to the same operational truth.

**Why this priority**: Explanation is the bridge between the simple cockpit and the full
Business Reality model.

**Independent Test**: Follow representative paths from an operational value through its
Inspector to Reality, Evidence, and Source; exercise Ask Reality, Explorer, and Help in
populated and empty states on desktop and mobile.

**Acceptance Scenarios**:

1. **Given** an important number, state, or row, **When** the user requests explanation,
   **Then** a focused detail preserves page context and exposes shortest true links to
   authoritative Reality, Evidence, and Source where applicable.
2. **Given** an empty Ask Reality history, **When** the surface opens, **Then** it offers a
   focused first-question state; once active, conversation context, evidence, proposals,
   and confirmations remain part of one task flow.
3. **Given** a support investigation, **When** Explorer opens, **Then** collection search,
   Source/Evidence/Reality landmarks, bounded records, fields, and relationships support
   exact inspection without becoming the normal operational interface.
4. **Given** a user seeking guidance, **When** Help opens, **Then** task-oriented entry
   points and search precede generated concepts, commands, model, and catalog reference.

---

### User Story 5 - Trust a Consistent Responsive Product (Priority: P2)

As an operator, I can use every in-scope surface at desktop and representative mobile
sizes with consistent controls, readable business data, and no hidden critical action.

**Why this priority**: A complete hierarchy is only useful when it survives real viewport
and state changes.

**Independent Test**: Execute a versioned route/state audit for every matrix row at
desktop and mobile widths, covering populated, empty, loading, error, confirmation, and
destructive states where applicable.

**Acceptance Scenarios**:

1. **Given** any in-scope route, **When** audited at desktop and mobile sizes, **Then** its
   page job, hierarchy, primary action, business data, and trace entry remain usable with
   zero browser errors.
2. **Given** a form, table, dialog, drawer, or status state, **When** compared across
   surfaces, **Then** shared interaction language and accessible semantic controls are used.
3. **Given** genuinely tabular detail on a narrow screen, **When** horizontal scrolling is
   necessary, **Then** it is bounded to the table and does not hide navigation or actions.
4. **Given** a changed or newly added route, **When** the coverage audit runs, **Then** an
   unmapped route, missing state proof, or stale matrix entry fails with a named category.

### Edge Cases

- A surface has no authoritative data for a desired total, filter, or relationship.
- The same route behaves differently because the selected workspace changes navigation.
- A record is corrected, reversed, deactivated, archived, or changes after a list loads.
- A register contains long names, multiple currencies, negative quantities, large values,
  missing optional dates, or original non-English source content.
- A user has no tenant, an empty tenant, partial setup, no permissions for an action, or a
  stale/foreign record link.
- Loading is slow, a request fails, validation conflicts, or a mutation needs confirmation.
- A mobile viewport cannot display all genuinely tabular columns simultaneously.
- A matrix surface is represented by a focused drawer or settings destination rather than
  a standalone route.
- Work owned by another numbered specification changes a shared shell or route during this
  feature; ownership and acceptance evidence must remain explicit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST maintain a versioned, exhaustive mapping from every actual
  in-scope Product Web route or destination to its UX-matrix surface, user job, required
  hierarchy, primary action, required states, and explanation entry point.
- **FR-002**: The mapping MUST identify deliberate non-applicability, shared-shell
  destinations, and separately owned features explicitly; silent omissions MUST fail review.
- **FR-003**: Home MUST present attention/control state before neutral activity and MUST
  preserve the approved exception, briefing, inventory-position, and recent-change hierarchy.
- **FR-004**: Exceptions, Commitments, Inventory, Reservations, and Movements MUST support
  their approved operational jobs with business-first state, useful controls, an appropriate
  next action, and focused explanation.
- **FR-005**: Inventory MUST distinguish shortage, fully allocated, and available states and
  MUST explain derived position through authoritative movements, reservations, inbound
  commitments, and the inventory equation where applicable.
- **FR-006**: Open Items, Payments, and Journal MUST expose the applicable financial control
  totals, direction, due/allocation/balance state, useful work controls, and Evidence links
  before opaque identifiers.
- **FR-007**: Documents and document explanation MUST prioritize business context and MUST
  order interpretation, operational consequences, financial consequences, source metadata,
  and raw payload according to the approved matrix where each section applies.
- **FR-008**: Parties, Items, and Locations MUST provide business-first registers and
  read-first detail with explicit editing, connected context, progressive trace disclosure,
  and separated lifecycle controls.
- **FR-009**: Commercial Terms/Pricing MUST separate lists, tiers, assignments, and groups
  into focused tasks with contextual empty guidance and one primary workflow at a time.
- **FR-010**: Sources & Imports MUST prioritize configured sources and their readiness,
  separate discovery/configuration from test intake, and preserve direct access to recent
  immutable source records.
- **FR-011**: Company, Data, and Agents configuration MUST remain one coherent settings
  hierarchy with one canonical title and no competing setup dashboard. Company lifecycle
  actions MUST reflect their consequence: New company remains a header action, while Archive
  belongs in the General tab's Danger zone and MUST NOT compete with creation in the header.
- **FR-012**: Ask Reality, Explorer, and Help MUST fulfil their distinct conversation,
  technical investigation, and task-guidance jobs without creating alternate business truth.
- **FR-013**: Every important operational or financial answer MUST offer a context-preserving
  path to its authoritative Reality record and onward to Evidence and Source where applicable.
- **FR-014**: Every in-scope surface MUST provide truthful empty, loading, and error states;
  applicable mutations MUST provide clear confirmation and outcome states.
- **FR-015**: Desktop and representative mobile layouts MUST preserve the same user job,
  information priority, critical actions, navigation, and readable business data.
- **FR-016**: Shared page, control, table, form, dialog, drawer, state, and responsive patterns
  MUST be used consistently; a surface MUST NOT introduce a competing interaction language.
- **FR-017**: Desired presentation that lacks authoritative service/read-model support MUST
  remain absent or be described as unavailable; the browser MUST NOT infer or persist it.
- **FR-018**: Executable coverage MUST detect unmapped routes, missing required state proof,
  stale matrix entries, browser errors, and loss of explanation entry points by named category.
- **FR-019**: The feature MUST close only `016/FR-006` after all in-scope matrix rows have
  evidence, affected desktop/mobile states pass visual review, and the product owner approves
  the final review; `016/FR-015` MUST remain a documented gap.

### Domain and Traceability Requirements

- **DR-001**: Page arrangements MUST preserve Source → Evidence → Reality and MUST NOT add
  presentation status as domain authority.
- **DR-002**: Values, totals, classifications, and filters MUST come from shared tenant-scoped
  services/read models; the browser MUST NOT own alternative business calculations.
- **DR-003**: UI relationships and actions MUST use opaque identity and the shortest true
  relationship while presenting human-readable business labels first.
- **DR-004**: Explanation MUST traverse authoritative relationships and MUST preserve access
  control, tenant non-disclosure, and immutable source payloads.
- **DR-005**: No schema expansion is permitted unless a separately approved, repeatedly used
  business calculation, constraint, filter, join, prediction, or action proves it necessary.
- **DR-006**: The UX coverage inventory is verification metadata only; it MUST NOT become a
  second route authority, business catalog, permission model, or source of operational truth.

### Key Concepts

- **UX Matrix Row**: The approved user job, hierarchy, and preferred interaction pattern for
  one product surface.
- **Product Destination**: An actual route, settings destination, drawer, or detail state that
  fulfils a matrix row.
- **Coverage Evidence**: The mapped populated/state/responsive/explanation proof for one
  destination, including explicit non-applicability or separate ownership where appropriate.
- **Operational Answer**: A displayed fact, risk, position, amount, state, or recommended
  action that must remain traceable to authoritative records.
- **Page State**: Populated, empty, loading, error, confirmation, destructive, or restricted
  presentation applicable to a destination.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of actual in-scope Product Web destinations map to exactly one approved
  UX-matrix job, with zero silent omissions and zero duplicate ownership.
- **SC-002**: 100% of applicable UX-matrix rows pass their required hierarchy and primary-job
  acceptance checks using representative business data.
- **SC-003**: All applicable operational and financial surfaces expose their declared control
  state and likely next action within the first viewport at desktop size.
- **SC-004**: 100% of sampled important answers across operational, financial, Evidence, and
  reference surfaces open a valid authoritative explanation path without a second calculation.
- **SC-005**: Every in-scope destination has passing evidence for each applicable empty,
  loading, error, confirmation, and destructive state; non-applicable states are recorded.
- **SC-006**: Every affected destination passes desktop and representative mobile review with
  zero browser errors and no hidden critical navigation or action.
- **SC-007**: Deliberately removing one route mapping, required hierarchy marker, state proof,
  or explanation entry point produces a deterministic failure naming the drift category.
- **SC-008**: Existing tenant-isolation, domain-story, correction/reversal, adapter-parity,
  localization, demo, and Product Web regression suites remain green.
- **SC-009**: `016/FR-006` moves from `Documented gap` to `Verified as-is`, while
  `016/FR-015` remains documented and no domain schema change is introduced.

## Assumptions and Dependencies

- `docs/WEB_UX_MATRIX.md` is the authoritative matrix; this feature may clarify it when the
  actual route topology has evolved, but may not silently weaken an approved user job.
- `docs/WEB_SPEC.md`, the Constitution, and owning domain specifications remain authoritative
  for calculations, actions, tenant scope, and traceability.
- Current supported Product Web languages and their complete audit are already owned by Spec
  017; this feature must preserve, not redefine, that coverage.
- Spec 029 owns the global Activity drawer. Its destination may be mapped and regression-tested
  here after merge, but its implementation is not duplicated.
- The existing shared product visual system remains the design foundation.
- Representative visual proof may use deterministic fixtures; it must clearly separate empty,
  demo, and ordinary business states.
- If an approved hierarchy requires missing authoritative data, the plan must either reuse an
  existing shared read model, narrow the presentation truthfully, or raise a separate product/
  domain decision before implementation.

## Requirement Traceability

| Requirement | User story/scenario | Planned evidence |
|---|---|---|
| FR-001–FR-002 | US5 scenarios 1 and 4 | Exhaustive route/destination-to-matrix inventory and drift proof |
| FR-003–FR-005 | US1 scenarios 1–5 | Operational hierarchy, state, action, and explanation journeys |
| FR-006–FR-007 | US2 scenarios 1–5 | Finance/Evidence control and document-explanation journeys |
| FR-008–FR-011 | US3 scenarios 1–5 | Reference/configuration focused-task journeys |
| FR-012–FR-013 | US4 scenarios 1–4 | Conversation, Help, Explorer, and explanation traversal journeys |
| FR-014–FR-016 | US1–US5 | Shared-state, control-language, desktop, and mobile review |
| FR-017 | All stories and edge cases | Browser-boundary and authoritative-data review |
| FR-018 | US5 scenario 4 | Categorized coverage-drift regression |
| FR-019 | Final review | Baseline closure and unrelated-gap preservation regression |
| DR-001–DR-006 | All stories | Constitution, tenant, shared-boundary, shortest-link, schema, and inventory review |
| SC-001–SC-009 | All stories | Acceptance matrix, visual evidence, complete regression, and policy gates |
