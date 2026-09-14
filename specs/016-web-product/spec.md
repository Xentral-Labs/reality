# Feature Specification: Web Product Baseline

**Baseline ID**: `016-web-product`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline the React Operations Cockpit and Business Reality Inspector over shared tenant-scoped services."

## Context and Intent

### Problem

A Head of Operations needs one fast daily product for exceptions, commitments,
inventory, finance, evidence, sources, and controlled actions, while support users need
full explanation underneath. This baseline defines the Web product boundary and
separates currently proven behavior from the broader product/UX target.

### Scope

- Public React product page, authentication flow, and independently deployed React app.
- Authenticated tenant shell, company switching/lifecycle, profile preferences, and
  task-oriented workspace views.
- Home, Facts, Exceptions, Commitments, Inventory, Documents, Open Items, Payments,
  Reservations, Movements, Activity, reference data, Sources, Chat, and settings.
- Shared operational register patterns, detail/Inspector drill-down, Explorer, and Help.
- Source intake, Evidence entry/correction, Reality actions, finance views, and agent
  controls through shared APIs/services.
- English-first localization with German, Dutch, and Spanish presentation preferences.
- Bounded tenant-scoped reads, server-side filtering/pagination, frontend build,
  translation audit, and desktop/mobile visual review expectations.

### Non-Goals

- Browser-owned business calculations or direct persistence.
- A second domain model, alternate workflow state, or Document-owned operational status.
- Customer-facing ecommerce/storefront, generic ERP replacement, or dashboard builder.
- Fine-grained RBAC beyond platform access and tenant membership.
- Bulk data export through register/Explorer HTML responses.

### Existing Contracts

- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/WEB_UX_MATRIX.md`](../../docs/WEB_UX_MATRIX.md)
- [`docs/TAILADMIN_UI_AUDIT.md`](../../docs/TAILADMIN_UI_AUDIT.md)
- [`docs/features/web.md`](../../docs/features/web.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

The React/TypeScript frontend is the only browser presentation layer. It owns `/` and
application routes; FastAPI owns API, MCP, health, and generated API documentation and
redirects retired browser routes. The frontend calls tenant-scoped APIs that delegate
to the same application services used by CLI, tools, Chat, and MCP.

The current app provides the principal cockpit, registers, company/settings surfaces,
Chat, Explorer, and Inspect paths. The shared visual foundation and desktop/mobile
visual audit are established, but deeper page arrangements in the UX matrix remain
product backlog rather than fully proven behavior. German coverage has an executable
audit; Dutch and Spanish catalogs are partial and fall back to English. Spec 033 adds a
repeatable 10,000-orders/day dataset and proves the bounded core-register read contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enter the Correct Company Workspace (Priority: P1)

As an approved operator, I can sign in, select only an authorized company, and retain
my language, locale, timezone, and workspace presentation preferences.

**Why this priority**: Tenant authority and presentation context precede all operations.

**Independent Test**: Sign in with memberships, switch companies and views, save profile
preferences, archive one company, and attempt unauthorized routes.

**Acceptance Scenarios**:

1. **Given** an active membership, **When** the operator opens the app, **Then** an
   authorized tenant is selected and its state is loaded.
2. **Given** no membership, **When** a tenant API is requested, **Then** access is denied.
3. **Given** language/locale/timezone preferences, **When** saved, **Then** labels and
   values use them while stored timestamps remain UTC.
4. **Given** workspace view changes, **When** selected, **Then** navigation/task context
   changes without changing tenant, records, calculations, or permissions.

### User Story 2 - Control Daily Operations (Priority: P1)

As Head of Operations, I can start with exceptions and position, scan operational
registers, apply server-side filters, and execute available actions through shared rules.

**Why this priority**: This is the Web product's primary daily job.

**Independent Test**: Load Home/Exceptions/Commitments/Inventory and finance registers,
filter them, open a record, execute a confirmed action, and compare domain state with
the corresponding service/CLI result.

**Acceptance Scenarios**:

1. **Given** current Reality, **When** Home opens, **Then** material risks precede neutral
   activity and important totals link to explaining records.
2. **Given** an operational register, **When** query/classification/range filters apply,
   **Then** filtering/counting/pagination occur tenant-scoped before the bounded result.
3. **Given** an action, **When** submitted, **Then** the API calls the owning service and
   confirmation is required where the interaction contract mandates it.
4. **Given** another interface performs the same command, **When** outcomes compare,
   **Then** authoritative domain state is equivalent.

### User Story 3 - Trace an Answer to Source (Priority: P1)

As an operator or support user, I can move from an operational answer through Reality
and Evidence to original Source without direct SQL.

**Why this priority**: Simple surface and complete explanation are one product promise.

**Independent Test**: Open Commitment, Inventory, Document, finance, and exception
details and follow Inspect/Explorer links across sourced and manual records.

**Acceptance Scenarios**:

1. **Given** an important number or exception, **When** Inspect opens, **Then** its
   derivation and authoritative Reality records are visible.
2. **Given** sourced Evidence, **When** traced, **Then** normalized fields and original
   payload are visibly distinct and reachable.
3. **Given** manual Evidence or Commitment, **When** traced, **Then** missing external
   Source is explicit rather than fabricated.
4. **Given** Explorer, **When** a collection is selected, **Then** a bounded searchable
   list and one selected record are shown with relationships/raw fields.

### User Story 4 - Configure Data and Agents Safely (Priority: P2)

As a tenant administrator, I can maintain minimal references, source definitions,
intake, commercial configuration, Copilot, and MCP access without bypassing services.

**Why this priority**: Occasional setup enables daily operations but must remain bounded.

**Independent Test**: Create/update/deactivate reference data, configure source
capabilities, ingest a file, manage AI secret/token, and verify confirmation/tenant scope.

**Acceptance Scenarios**:

1. **Given** reference data, **When** created or edited, **Then** shared services validate
   it and lifecycle history remains traceable.
2. **Given** a file/source, **When** intake is confirmed, **Then** the immutable shared
   ingestion path runs and unknown input is not guessed.
3. **Given** an AI secret or MCP token, **When** configured, **Then** clear credentials
   are not rendered again and tenant/tool authority is enforced.
4. **Given** Chat mutation, **When** proposed, **Then** Reality changes only after confirmation.

### User Story 5 - Use a Consistent Responsive Product (Priority: P2)

As an operator, I can work on desktop and mobile with consistent hierarchy, loading,
empty, error, confirmation, form, table, and navigation behavior.

**Why this priority**: Operational correctness must remain usable all day.

**Independent Test**: Build the frontend, run translation audit, and visually inspect
all captured routes/states at desktop and representative mobile sizes with no browser errors.

**Acceptance Scenarios**:

1. **Given** any changed page, **When** built and visually audited, **Then** shared
   Tailwind/TailAdmin primitives render without browser errors at both sizes.
2. **Given** loading/empty/error/action states, **When** displayed, **Then** shared
   interaction language and accessible semantic controls are used.
3. **Given** a supported language, **When** selected, **Then** formatting follows its
   locale/timezone and missing text safely falls back to English.

### Edge Cases

- Session expires or membership changes while the app is open.
- Archived/current tenant appears in a stale route or browser session.
- API is unavailable, slow, or returns validation/conflict errors.
- Register filter yields no rows, exceeds page bounds, or includes foreign-tenant values.
- Record is changed between register load and action confirmation.
- Raw payload is large, malformed for display, or contains original non-English data.
- Mobile table has genuinely tabular detail requiring bounded horizontal scrolling.
- Translation is missing in German, Dutch, or Spanish.
- Tenant volume exceeds ordinary fixtures and exposes unbounded read behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: React MUST be the only browser presentation layer; backend MUST remain
  API/MCP/health/docs only and redirect retired UI routes.
- **FR-002**: Protected Web use MUST enforce authentication, active account, tenant
  membership, and tenant scope at API plus application-service boundaries.
- **FR-003**: Workspace views MUST change presentation/navigation only and MUST NOT
  alter tenant authority, records, calculations, or permissions.
- **FR-004**: Operational pages MUST call shared services/read models and MUST NOT
  implement alternative business rules or direct persistence.
- **FR-005**: Home and Exceptions MUST prioritize derived risks and every important
  operational/financial value MUST link to its explanation.
- **FR-006**: Core operational, warehouse, finance, Evidence, source, reference, Chat,
  settings, Help, and Explorer surfaces MUST provide the jobs defined in the UX matrix.
- **FR-007**: Registers MUST use tenant-scoped server-side search/filter/sort/count and
  stable pagination with at most 100 rows, preserving filters in navigation.
- **FR-008**: Derived values MUST be filtered and counted before pagination in SQL or
  materialized projections, not calculated from the visible browser page.
- **FR-009**: Inspect MUST expose authoritative Reality, Evidence, Source/raw payload,
  and shortest true links while Explorer remains a bounded technical secondary view.
- **FR-010**: Web mutations MUST delegate to owning services; Chat/agent mutations and
  other specified high-impact interactions MUST require explicit confirmation.
- **FR-011**: Reference, source intake, commercial, company lifecycle, AI, and MCP
  configuration MUST preserve their owning domain/security contracts.
- **FR-012**: Shared page-header, form, control, table, dialog/drawer, empty, loading,
  error, and responsive patterns MUST be used for new or changed product UI.
- **FR-013**: UI language (`en`, `de`, `nl`, `es`), locale, and IANA timezone MUST be
  independent preferences; English MUST be default/fallback and all user-facing text in
  each advertised language MUST have audited coverage.
- **FR-014**: The frontend MUST build cleanly, pass translation audit, and pass
  desktop/mobile visual review with zero browser errors for affected states.
- **FR-015**: The 10,000-orders/day read contract MUST have repeatable proof that core
  register requests remain bounded and perform filtering/counting before pagination.
- **FR-016**: Help/reference MUST derive CLI, data model, Command, Event, Fact, and
  Projection reference from validated machine-readable/runtime authorities.

### Domain and Traceability Requirements

- **DR-001**: Web MUST preserve Source → Evidence → Reality and never add presentation
  status as domain authority.
- **DR-002**: UI relationships/actions MUST submit opaque IDs; human values are labels/search only.
- **DR-003**: Derived views and projections MUST link to authoritative records and remain rebuildable.
- **DR-004**: Browser/API adapters MUST remain thin over shared tenant-scoped services/tools.
- **DR-005**: Operational answer → Reality → Evidence → Source MUST be the repeated inspect pattern.

### Key Entities

- **Authenticated user/session/membership**: Platform and tenant access context.
- **Workspace preference**: Presentation choice, not authority.
- **Operational register/read model**: Bounded tenant-scoped authoritative/derived view.
- **Inspector/Explorer result**: Explanation and bounded technical record view.
- **ChangeProposal**: Confirmation boundary for interactive agent mutation.

## Reality Applicability

- **Source**: Intake and Inspect retain/show immutable payloads without translation/mapping loss.
- **Evidence**: Documents/lines appear as normalized evidence, not operational authority.
- **Reality**: Operational/financial registers display owning Reality records and derived states.
- **Shortest links**: UI navigation follows opaque relationships and does not change storage provenance.
- **Stored/derived**: Preferences/session/configuration stored; operational numbers/status derive from Reality.
- **Shared boundary**: React calls API adapters that call the same services/tools as CLI/Chat/MCP.
- **Web explanation**: Clean cockpit surfaces open focused Inspect; Explorer provides deeper bounded support detail.

## Success Criteria *(mandatory)*

- **SC-001**: Unauthorized/foreign-tenant Web requests expose zero protected records.
- **SC-002**: Equivalent Web and service/CLI actions produce equivalent authoritative domain state.
- **SC-003**: Every important tested number/action reaches authoritative Reality and applicable Evidence/Source.
- **SC-004**: No core register response exceeds 100 rows and filtering/counting precedes pagination.
- **SC-005**: Frontend build, German translation audit, and captured desktop/mobile visual audit pass.
- **SC-006**: English, German, Dutch, and Spanish surfaces have complete audited user-facing text
  coverage or retain an explicit language-specific gap.
- **SC-007**: A repeatable 10,000-orders/day dataset proves bounded core register behavior.
- **SC-008**: Generated Help/reference catalogs match runtime/schema authorities with no drift.

## Assumptions and Dependencies

- Domain baselines `003–015` remain authoritative for business/security behavior.
- Horizontal scrolling is acceptable only for genuinely tabular mobile detail.
- English fallback is safe but does not count as complete Dutch/Spanish translation.
- Deep UX workflow refinement may be staged without changing business semantics.

## Open Questions

The product owner approved this baseline on 2026-08-31. Spec 030 subsequently
verified full UX-matrix completion for FR-006 on 2026-09-02. Spec 033 provides the
repeatable large-tenant read proof for FR-015 with 10,000 same-day orders, 19,999
lines/commitments, all nine core register families, and a control tenant. Spec 017
verified complete English, German, Dutch, and Spanish localization coverage for FR-013.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001 | Verified as-is | Web Spec Start | React entry; API-only backend | `tests/test_http_boundary.py`; frontend build | — |
| FR-002–FR-004 | Verified as-is | Web/Architecture/Constitution | auth API, React API client, shared services | user-access, API, tenancy, CLI/tool tests | — |
| FR-005 | Verified as-is | Web Spec Home/Exceptions | Home/Exceptions/read models | API, application-tool, projection, visual audit | — |
| FR-006 | Verified as-is | Web UX Matrix; Web Spec; Spec 030 | Complete routed UX matrix, tenant-scoped Journal, shared responsive/state primitives, and shortest-link Inspect paths | `ux-matrix-v1`; 33 Product Web contracts; 245-test PostgreSQL suite; four-language audit/build; owner-approved visual and final review | Spec 030 evidence accepted 2026-09-02 |
| FR-007–FR-008 | Verified as-is | Web large-tenant contract | paged/filtering read models and APIs | bounded Explorer/API/read-model tests | — |
| FR-009–FR-011 | Verified as-is | Web Inspect/configuration contracts | Inspector, Explorer, settings/intake APIs | master-data API, source, agent, lifecycle tests | — |
| FR-012, FR-014 | Verified as-is | TailAdmin audit; Web shared UI rules | shared React/CSS primitives | frontend build, i18n audit, 22-state visual audit record | — |
| FR-013 | Verified as-is | Web Accounts/access; Spec 017 | complete four-language catalog, localized public/auth boundary, safe English fallback, and protected original content | strict audit: 775/775 for `en`, `de`, `nl`, and `es`; 9/9 focused tests; production build; owner-reviewed desktop/mobile representative states | Spec 017 evidence accepted 2026-08-31 |
| FR-015 | Verified as-is | Web large-tenant contract; Spec 033 | deterministic reduced/full dataset, shared register cases, bounded Payment enrichment, Pydantic result contract | Full PostgreSQL result: 10,000 orders, 19,999 lines/commitments, nine register families, two semantically identical runs, zero over-limit/unstable/cross-tenant results | Spec 033 evidence accepted by product-owner final review on 2026-09-02 |
| FR-016 | Verified as-is | Web Help/reference contract | generated/validated catalogs | catalog, schema, HTTP boundary, CLI documentation tests | — |
| DR-001–DR-005 | Verified as-is | Constitution; Architecture; Web Spec | API/read-model/Inspector boundaries | API, domain story, explain, tenancy tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-004 | US1–US2 | HTTP boundary, access, tenancy, API/service equivalence tests |
| FR-005–FR-008 | US2 | Home/register/projection tests and UX-matrix gap |
| FR-009–FR-011 | US3–US4 | Inspector, Explorer, lifecycle, intake, agent tests |
| FR-012–FR-015 | US5 | Build/i18n/visual gates and language/load gaps |
| FR-016 | US3–US5 | Catalog/schema/CLI drift tests |
| DR-001–DR-005 | All stories | Constitution and cross-layer Web review |
