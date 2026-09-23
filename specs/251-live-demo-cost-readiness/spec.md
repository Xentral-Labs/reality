# Feature Specification: Live Demo Cost Readiness

**Feature Branch**: `251-live-demo-cost-readiness`
**Created**: 2026-09-22
**Status**: Approved
**Approved**: 2026-09-22
**Language**: English
**Input**: "A newly created live-demo company must be immediately usable for demonstrations: every stocked demo item must have an explainable non-zero acquisition basis and every applicable sales invoice line must expose current contribution values. Initial setup and later synthetic intake must not leave the user at an uninitialized or permanently stale cost result."

## Context and Intent

### Problem

A freshly created company can report `ready` and start synthetic intake while stocked items remain unreviewed or a cost review becomes stale immediately. The inventory and Finance screens then show unavailable carrying values or contribution margins even though the canonical demo profile is intended to be a complete, presentation-ready business. A sales user cannot reliably explain the demo and may mistake unavailable values for zero acquisition cost.

### Scope

- Make the canonical demo profile cost-complete before company setup reports it ready.
- Keep inventory valuation and contribution observations current while Demo Data continues synthetic intake.
- Give users an explicit, understandable progress and freshness state without requiring a manual first refresh.
- Preserve the same costing authority, review, explanation, and scheduling boundaries used outside demo companies.

### Non-Goals

- Automatically invent, infer, or default an acquisition cost when evidence is absent.
- Treat zero as a substitute for unavailable cost evidence.
- Add demo-only costing rules, browser timers, direct persistence shortcuts, or a second job queue.
- Guarantee contribution values for documents that are intentionally outside the demo profile or lack the required commercial evidence.
- Change accounting authority, valuation algorithms, or contribution formulas.

### Existing Contracts

- [Company setup and demo profiles](../../docs/features/company-setup-demo.md)
- [Scheduled jobs](../../docs/features/scheduled-jobs.md)
- [Web product](../../docs/WEB_SPEC.md)
- [Inventory costing](../242-inventory-cost-contribution/spec.md)
- [Demo business journeys](../246-demo-business-journeys/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open a calculation-ready demo company (Priority: P1)

A sales user creates a company with Demo Data and live simulation. When the setup flow says the company is ready, the user can immediately open Warehouse and Finance and see explainable inventory values and contribution margins for the provided demo cases.

**Why this priority**: The ready state is a product promise. A company that opens with unavailable core demo values is not ready for a customer demonstration.

**Independent Test**: Create a fresh canonical demo company, wait for its normal ready state, then inspect every stocked demo item and every contribution-eligible demo invoice line without triggering a manual refresh.

**Acceptance Scenarios**:

1. **Given** a confirmed canonical demo-company request, **When** setup reports `ready`, **Then** every demo item with positive physical stock has a reviewed acquisition basis and an explainable current inventory result.
2. **Given** the canonical sales and invoice cases created by the profile, **When** setup reports `ready`, **Then** every contribution-eligible invoice line has current DB1 and DB2 values with explanation links to revenue, consumed acquisition cost, and selling costs.
3. **Given** a stocked demo item, **When** its evidence cannot support a positive acquisition basis, **Then** setup does not silently publish a zero value and the incomplete scope is named before the company is declared calculation-ready.
4. **Given** the setup progress dialog, **When** costing is still being prepared, **Then** the user sees a distinct calculation step and the dialog does not close until that step reaches a terminal outcome visible to the user.

### User Story 2 - Preserve truthful freshness during live intake (Priority: P1)

A sales user leaves live simulation running and continues exploring the company. Newly generated orders, invoices, credits, and payments do not invalidate unrelated retained acquisition or contribution reviews. A genuinely authority-changing movement or selling-cost revision is instead shown as stale until an owner explicitly reviews the new evidence.

**Why this priority**: The live-demo promise is continuous activity. Immediate staleness makes the initial readiness calculation misleading and recreates the manual-refresh confusion.

**Independent Test**: Start from a calculation-ready demo company, allow one normal synthetic order/settlement cycle to complete, and verify that its unrelated events do not stale retained inventory or contribution observations; then add one relevant movement or cost withdrawal and verify a truthful stale result without an invented replacement review.

**Acceptance Scenarios**:

1. **Given** a current valued item, **When** normal synthetic orders, invoices, credits, or payments are admitted without changing that item's physical or reviewed cost evidence, **Then** the inventory observation remains current without a manual refresh.
2. **Given** a current contribution-eligible invoice line, **When** unrelated synthetic business events are admitted, **Then** DB1 and DB2 remain current and retain their exact reviewed cutoff and explanation.
3. **Given** a new movement changes a reviewed item's physical evidence, **When** the value is read, **Then** the current observation is stale and no background job creates a replacement financial review.
4. **Given** an attributed selling cost is withdrawn, **When** the affected contribution is read, **Then** DB2 is unavailable at the current cutoff while the historical reviewed result remains addressable.

### User Story 3 - Trust the same result across interfaces (Priority: P2)

An operator or agent checks the same demo value through Web, MCP, Chat, CLI, or API and receives the same current result and explanation state.

**Why this priority**: Demo automation and autonomous operators use MCP while people use Web. Divergent readiness or costing paths would make the demonstration unreliable.

**Independent Test**: Read three stocked items and three contribution-eligible invoice lines through Web-backed reads and MCP after initial setup and after one live cycle; compare identities, freshness, values, and missing-basis reasons.

**Acceptance Scenarios**:

1. **Given** a current demo value, **When** it is read through any supported interface, **Then** all interfaces report the same scope identity, value, currency/unit, cutoff, and explanation state.
2. **Given** an unavailable demo value, **When** it is read through any supported interface, **Then** all interfaces report the same explicit missing or failed basis rather than substituting zero.

### Edge Cases

- An item has zero physical stock but retained receipt history; zero carrying value remains valid while unit acquisition evidence stays explainable.
- A stocked item uses a non-piece unit, foreign currency evidence, a lot, serial identity, or handling unit.
- A return, correction, credit, cancellation, or backdated event changes a previously current scope.
- Live intake advances through unrelated finance events after a review cutoff.
- Setup is replayed with the same request key after calculation completed or failed.
- The scheduler or worker restarts after work was materialized but before completion.
- One tenant's freshness read must not inspect or reveal another tenant's scope.
- Historical companies with incomplete demo evidence remain visible and are not silently repaired by rollout.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define the calculation-ready coverage of the canonical demo profile as every item with positive physical stock plus an explicit immutable manifest of opaque invoice-line identities for which the profile claims contribution demonstration coverage.
- **FR-002**: The canonical demo profile MUST provide explicit positive acquisition evidence for every item that it leaves with positive physical stock; unavailable evidence MUST never be represented as a zero acquisition price.
- **FR-003**: Before setup reports `ready`, the system MUST complete and verify inventory-cost coverage for every in-scope stocked item.
- **FR-004**: Before setup reports `ready`, the system MUST complete and verify DB1 and DB2 coverage for every in-scope contribution invoice line.
- **FR-005**: The setup progress presented to users MUST include a distinct calculation step with pending, running, succeeded, and failed outcomes and MUST keep the final ready state visible for at least 1.5 seconds before automatic company entry.
- **FR-006**: Starting live simulation as part of setup MUST NOT race ahead of the initial calculation-ready cutoff; the durable setup completion state MUST identify the admitted cutoff and verified coverage.
- **FR-007**: Freshness MUST be based on scope-relevant physical and reviewed-cost events; unrelated company, finance, order, invoice, credit, or payment events MUST NOT invalidate retained inventory or contribution observations.
- **FR-008**: A relevant movement or cost-attribution revision MUST make the affected current observation stale without automatically creating a replacement authoritative review; historical reviewed results remain addressable.
- **FR-009**: A normal synthetic order/settlement cycle that changes no reviewed cost authority MUST leave the canonical demo's retained inventory and contribution observations current without user action.
- **FR-010**: Reads MUST distinguish current, updating, failed, stale, and evidence-missing outcomes and MUST never render unavailable cost or contribution as a trusted zero.
- **FR-011**: Web, MCP, Chat, CLI, and API MUST use the same application services and expose equivalent scope identity, freshness, value, cutoff, and explanation information.
- **FR-012**: Retry and request replay MUST preserve completed setup and MUST not restart live-source controls or overwrite later operator choices.
- **FR-013**: Existing historical demo companies MUST not be automatically rewritten; any repair is explicit, tenant-scoped, previewable, and separately confirmed.
- **FR-014**: The company and affected pages MUST expose a concise diagnostic when calculation readiness fails, including the bounded scopes and evidence reasons that prevented completion.

### Domain and Traceability Requirements

- **DR-001**: Acquisition and selling values MUST remain grounded in retained SourceRecord, Document/DocumentLine, Movement, allocation, and reviewed cost evidence; setup and scheduling state are not financial authority.
- **DR-002**: Inventory and contribution values MUST remain derived observations at read time or disposable projections; recalculation MUST NOT create a new authority for a value already stated by a source.
- **DR-003**: Scope correlation MUST use opaque tenant-scoped item, document-line, review, generation, event, and job identities rather than SKU, document number, or display label.
- **DR-004**: Live intake, setup orchestration, Web, MCP, Chat, CLI, and API MUST call shared services; no adapter may implement an alternative costing or freshness rule.
- **DR-005**: Recalculation MUST preserve the exact admitted event cutoff and explanation links so a user can distinguish the last completed result from newer not-yet-included events.
- **DR-006**: Every repository query and queued work item introduced or extended by this feature MUST enforce tenant scope and cross-tenant identities MUST behave as not found or be refused without disclosure.
- **DR-007**: The feature MUST reuse existing business tables and costing authorities unless planning proves a repeated core need that cannot be represented by existing setup, job, review, generation, and event records.

### Key Entities *(when data is involved)*

- **Demo profile coverage**: Every positively stocked item discovered at the admitted cutoff plus the immutable list of opaque contribution invoice-line identities declared by the canonical profile manifest.
- **Calculation-ready cutoff**: The latest admitted business-event sequence whose required demo scopes have verified current observations before setup opens the company.
- **Cost observation**: The explainable inventory or contribution result for one opaque scope at a specific effective, knowledge, and event cutoff.
- **Recalculation request**: Idempotent tenant-scoped background work that brings affected observations forward without changing source authority.
- **Readiness diagnostic**: The bounded list of scopes and evidence reasons that prevents or delays a calculation-ready outcome.

## Success Criteria *(mandatory)*

- **SC-001**: In ten consecutive fresh canonical demo-company creations, 100% reach `ready` with current inventory results for every positively stocked item and current DB1/DB2 results for every declared contribution-demo line.
- **SC-002**: For at least three stocked items and three contribution invoice lines sampled in each run, Web and MCP report identical identities, values, cutoffs, freshness, and explanation outcomes.
- **SC-003**: After one normal synthetic order/settlement cycle, 100% of previously current retained demo observations whose evidence did not change remain current; a planted relevant movement and selling-cost withdrawal both produce stale current reads while preserving historical results.
- **SC-004**: No acceptance run displays an unavailable acquisition cost or contribution as a trusted zero; every unavailable result carries a specific updating, failed, stale, or evidence-missing explanation.
- **SC-005**: Replaying setup and intake requests produces no duplicate authoritative review, Movement, financial posting, or source-control transition.
- **SC-006**: A planted cross-tenant scope or work request is refused without revealing whether the foreign identity exists.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The canonical `international_demo` profile is the only profile whose setup `ready` state promises complete demonstration costing in this feature.
- Existing costing policies, review semantics, generation services, Demo Data intake, and the shared scheduler/worker are authoritative dependencies and remain reusable.
- Synthetic demo evidence may be deterministic, but it is still recorded through normal source interpretation and reviewed-cost services rather than inserted as unexplained values.
- A stale state is required when later evidence invalidates a review; returning to current then requires the existing explicit owner-confirmed review path.
- Product approval was granted on 2026-09-22 before planning because calculation readiness changes when setup may declare a company ready.

## Open Questions

No unresolved product questions. The default is complete canonical-profile coverage, scope-relevant freshness, no automatic financial review or historical repair, and no invented fallback values.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-006 | US1 scenarios 1–4 | Fresh-company coverage story, setup progress browser proof, request replay proof |
| FR-007–FR-010 | US2 scenarios 1–4 | Relevant-event freshness, batch invalidation, selling-cost withdrawal and unavailable-state proofs |
| FR-011–FR-012 | US3 scenarios 1–2; US2 scenario 3 | Web/MCP/Chat/CLI/API parity matrix and idempotency tests |
| FR-013–FR-014 | US2 scenario 4; edge cases | Historical no-repair test and readiness diagnostic proof |
| DR-001–DR-005 | US1–US3 | Source-to-observation explanation assertions and exact cutoff checks |
| DR-006–DR-007 | US2–US3; edge cases | Tenant-isolation family and schema-stability check |
