# Feature Specification: Demo Entrypoint Equivalence

**Feature Branch**: `[027-demo-entrypoint-equivalence]`
**Created**: 2026-09-02
**Status**: Approved
**Language**: English
**Input**: "Close `015/FR-010` with focused proof that interactive CLI, CLI auto mode, and Product Web onboarding create equivalent complete demo domain state through the same application boundary."

## Context and Intent

### Problem

The guided demo is intended to be one coherent introduction to Business Reality, but
there is no focused proof that its interactive CLI, automatic CLI, and Product Web
onboarding entrypoints create the same complete business state. Individual paths may
appear successful while silently omitting records, using a different seed path, or
presenting a normal empty-company setup as the guided demo. This weakens the demo as
executable product documentation.

### Scope

- Define the single guided-demo scenario compared across interactive CLI, CLI auto
  mode, and Product Web onboarding.
- Make the Product Web demo choice explicit and distinct from creating an empty company.
- Run each entrypoint from an equivalent empty starting state in an isolated tenant.
- Compare canonical Source, Evidence, Reality, reference-data, derived operational,
  financial, and traceability outcomes after completion.
- Prove confirmation, cancellation, non-empty-tenant safety, tenant isolation,
  idempotency, and drift detection at the entrypoint boundaries.
- Close only the documented `015/FR-010` gap after executable evidence and final
  product-owner approval.

### Non-Goals

- Redesigning the demo story, adding new business transactions, or changing its
  documented expected outcomes.
- Treating the September 2026 normal-month scenario as the guided demo; it remains a
  separate, already-proven deterministic scenario.
- Requiring identical terminal and browser wording, layout, timing, generated opaque
  identifiers, or transport envelopes.
- Comparing Chat or bootstrap execution in the focused three-entrypoint matrix; their
  existing confirmation and shared-service contracts remain authoritative.
- Resetting, deleting, or overwriting a populated tenant to obtain a clean comparison.
- Adding demo-specific domain tables, copied business rules, or browser-owned state.

### Existing Contracts

- [`specs/015-demo-scenarios/spec.md`](../015-demo-scenarios/spec.md)
- [`docs/features/demo.md`](../../docs/features/demo.md)
- [`docs/DEMO_SPEC.md`](../../docs/DEMO_SPEC.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/TEST_STRATEGY.md`](../../docs/TEST_STRATEGY.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reach the Same Guided Demo Outcome (Priority: P1)

As a product evaluator, I can start the guided demo from the terminal or Product Web
and receive the same explainable business reality regardless of entrypoint.

**Why this priority**: A demo that changes meaning by interface cannot serve as a
trustworthy explanation of the product or its domain model.

**Independent Test**: Start the interactive CLI, CLI auto mode, and Product Web demo in
three equivalent isolated empty tenants, complete each flow, reload authoritative state,
and compare one canonical outcome manifest.

**Acceptance Scenarios**:

1. **Given** three equivalent empty tenants, **When** the guided demo completes through
   interactive CLI, CLI auto mode, and Product Web, **Then** all three produce equivalent
   reference data, Source, Evidence, Reality, derived outcomes, and traceability links.
2. **Given** the same guided-demo definition, **When** any entrypoint starts it, **Then**
   that entrypoint delegates to the same application-owned demo operation without direct
   persistence or alternative business rules.
3. **Given** interface-specific generated IDs or presentation text, **When** outcomes are
   compared, **Then** those differences are normalized without hiding a business-state
   or relationship difference.
4. **Given** the completed state, **When** an evaluator follows representative output
   links, **Then** the order source, document line, commitments, reservations, movements,
   and explanations remain traversable through the shortest true relationships.

### User Story 2 - Choose Demo or Empty Company Deliberately (Priority: P1)

As a new Web user, I can clearly choose between trying the guided demo and creating an
empty company, so onboarding never creates unexpected sample business data.

**Why this priority**: Demo equivalence must not turn normal company creation into an
implicit data mutation.

**Independent Test**: Exercise both Product Web onboarding choices and verify that the
demo choice requires explicit confirmation and creates the canonical demo, while empty
company creation creates no demo records.

**Acceptance Scenarios**:

1. **Given** a user with no company, **When** onboarding is shown, **Then** it presents
   distinct actions for an empty company and the guided demo with clear consequences.
2. **Given** the guided-demo action, **When** it has not been explicitly confirmed,
   **Then** zero demo domain records are created.
3. **Given** the guided-demo action is confirmed, **When** it succeeds, **Then** the new
   tenant opens with the canonical demo state and a clear route to inspect its records.
4. **Given** empty-company creation, **When** it succeeds, **Then** the company remains
   empty of guided-demo business records.

### User Story 3 - Preserve Safety and Detect Drift (Priority: P2)

As a maintainer, I receive a focused failure when one demo entrypoint becomes incomplete,
unsafe, cross-tenant, or behaviorally different.

**Why this priority**: Long-term equivalence requires a durable contract, not a one-time
manual comparison.

**Independent Test**: Verify cancellation, populated-tenant protection, repeated runs,
foreign demo-inspection attempts, and deliberately changed canonical fields or links.

**Acceptance Scenarios**:

1. **Given** a cancelled interactive or Web confirmation, **When** cancellation
   completes, **Then** no demo mutation occurs.
2. **Given** a populated tenant, **When** a demo entrypoint is requested for it, **Then**
   existing records are not reset, overwritten, or silently mixed with the demo.
3. **Given** a completed demo tenant, **When** the supported rerun behavior is exercised,
   **Then** the result is deterministic and does not create duplicate business state.
4. **Given** a tenant identifier the actor cannot use, **When** a demo mutation is
   requested, **Then** no foreign state is disclosed or changed.
5. **Given** one entrypoint omits or changes a canonical record, value, relationship, or
   derived outcome, **When** the focused proof runs, **Then** it fails with the affected
   outcome category identified.

### Edge Cases

- Product Web company creation succeeds but demo population fails, leaving a truthful
  possibly partial tenant that is not advertised as safely retryable.
- A user submits or confirms the Web demo action more than once.
- The interactive CLI is cancelled before confirmation or interrupted after completion.
- A tenant contains only partial prior setup or a name matching the sample company.
- Equivalent records have different opaque IDs, timestamps, or insertion order.
- Optional source payload fields or explanation links are missing on only one path.
- An entrypoint returns success while a derived inventory or commitment outcome differs.
- The comparison accidentally treats the normal-month scenario as the guided demo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST inventory every record family actually produced by the
  guided demo before fixing one explicitly versioned canonical outcome manifest covering
  reference data, Source, Evidence, Reality, derived outcomes, and representative links.
- **FR-002**: Interactive CLI, CLI auto mode, and Product Web guided-demo entrypoints MUST
  invoke the same application-owned demo operation and MUST NOT implement independent
  persistence or business rules.
- **FR-003**: A focused executable proof MUST complete all three entrypoints in equivalent
  isolated tenants and compare their reloaded authoritative state against the canonical
  outcome manifest.
- **FR-004**: Canonical comparison MUST include every record family found by the
  pre-implementation inventory, including Party, Item, Location, SourceRecord, Document,
  DocumentLine, Commitment, Reservation, Movement, Fact, BusinessEvent, and Chat records
  when the real guided execution produces them.
- **FR-005**: Canonical comparison MUST include physical, reserved, available, incoming,
  projected, and fulfilment outcomes plus an explicit zero financial-state expectation
  when the guided demo creates no LedgerEntries or open items.
- **FR-006**: Canonical comparison MUST preserve business values, record multiplicity,
  relationship topology, tenant ownership, complete source provenance, lifecycle state,
  and explanation reachability while ignoring only generated opaque IDs, timestamps,
  ordering, and presentation formatting.
- **FR-007**: Product Web onboarding MUST present explicit, distinguishable actions for
  creating an empty company and creating a company with the guided demo.
- **FR-008**: The Product Web guided-demo mutation MUST require explicit confirmation;
  cancellation or failure before confirmed execution MUST create zero demo domain records.
- **FR-009**: Successful Product Web guided-demo onboarding MUST open the resulting tenant
  and provide a direct path to inspect the created authoritative records.
- **FR-010**: Empty-company onboarding MUST remain available and MUST create no guided-demo
  business records.
- **FR-011**: Demo entrypoints MUST protect populated tenants from reset, overwrite, or
  silent mixing, and rerunning an already completed demo MUST not create duplicates.
  Partial-failure recovery MUST NOT be described as safely retryable unless separately proven.
- **FR-012**: Company-with-demo creation MUST grant access only to the authenticated
  creator, and all resulting demo reads and mutations MUST remain tenant-scoped; attempts
  to inspect another user's demo tenant MUST behave as not found without disclosure.
- **FR-013**: The focused proof MUST report drift by entrypoint and canonical outcome
  category rather than only returning an undifferentiated mismatch.
- **FR-014**: The guided-demo equivalence proof MUST remain distinct from the normal-month,
  Chat, and bootstrap proofs and MUST not weaken their existing contracts.
- **FR-015**: The feature MUST close only `015/FR-010` after equivalence, confirmation,
  safety, tenant, idempotency, and traceability evidence passes and final product-owner
  review is approved.

### Domain and Traceability Requirements

- **DR-001**: The demo MUST preserve SourceRecord → Document/DocumentLine → Reality links
  wherever the guided story uses those stages.
- **DR-002**: Documents MUST remain Evidence; inventory, reservation, fulfilment, and
  financial state MUST be derived from authoritative Reality records.
- **DR-003**: Comparison aliases MUST follow the shortest true links and MUST NOT add or
  require duplicate foreign keys solely to make test comparison easier.
- **DR-004**: Source payloads MUST remain immutable and lossless across all entrypoints;
  demo reruns MUST reuse or version them according to existing source rules.
- **DR-005**: All demo-created business records and queries MUST be tenant-scoped, and all
  interfaces MUST use the shared application boundary.
- **DR-006**: The feature MUST NOT expand the domain schema unless a separately identified,
  product-owner-approved use case proves that existing authoritative state is insufficient.

### Key Entities *(when data is involved)*

- **Guided demo definition**: The versioned business story and expected outcome categories
  shared by every supported entrypoint.
- **Demo execution**: One confirmed attempt to create the guided-demo state for an isolated
  tenant; it is not a new business authority or a replacement for domain records.
- **Canonical outcome manifest**: A comparison view over authoritative demo-created records,
  relationships, provenance, derived values, and explanation reachability.
- **Demo tenant**: The tenant-scoped workspace in which one guided demo is safely created.

## Success Criteria *(mandatory)*

- **SC-001**: All three declared entrypoints complete and match across 100% of canonical
  guided-demo outcome categories.
- **SC-002**: A deliberate change to any compared business value, count, relationship,
  provenance field, lifecycle state, derived result, or explanation link causes the focused
  proof to fail and identify its outcome category.
- **SC-003**: Cancelled or unconfirmed interactive and Product Web demo attempts create
  zero demo business records.
- **SC-004**: Empty-company onboarding creates zero guided-demo business records in 100%
  of acceptance runs.
- **SC-005**: Populated-tenant, repeated-run, and foreign-inspection acceptance scenarios
  lose, overwrite, disclose, or duplicate zero existing business records.
- **SC-006**: Representative Source → Evidence → Reality and explanation paths are traversable
  after every successful entrypoint execution.
- **SC-007**: `015/FR-010` moves from `Documented gap` to `Verified as-is` without schema
  growth, demo-only business rules, normal-month scope expansion, or closure of unrelated gaps.
- **SC-008**: Every FR and DR maps to an acceptance scenario and executable proof or an
  explicit product-owner-approved reason why automation is inappropriate.

## Assumptions and Dependencies

- The guided demo is the compact scenario defined by `docs/DEMO_SPEC.md`; the September
  2026 normal month remains a separate scenario.
- Existing demo services and domain records are expected to be sufficient; this feature
  adds or adjusts entrypoint orchestration and proof only when real drift is found.
- Equivalent executions use separate empty tenants because opaque identities and timestamps
  are expected to differ.
- Product Web can expose a confirmation step using its existing mutation-confirmation
  interaction patterns.
- Chat and configured bootstrap remain covered by their existing focused proofs.

## Open Questions

No unresolved product-scope questions remain for specification review. Planning must
inventory the exact current guided-demo output before defining the canonical manifest.

## Approval

The product owner approved this specification on 2026-09-02. Planning and implementation
must preserve the explicit empty-company choice and may close only `015/FR-010` after
the remaining workflow gates pass.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-004–FR-006 | US1 scenarios 1, 3–4; US3 scenario 5 | Canonical manifest completeness, topology, derived-state, trace, and drift proofs |
| FR-002–FR-003 | US1 scenarios 1–2 | Three-entrypoint execution and shared-boundary proof |
| FR-007–FR-010 | US2 scenarios 1–4 | Product Web choice, confirmation, success-routing, and empty-company proofs |
| FR-011–FR-012 | US3 scenarios 1–4 | Cancellation, populated/rerun, and tenant-isolation proofs |
| FR-013 | US3 scenario 5 | Categorized diagnostic drift proof |
| FR-014 | Edge cases; scope boundary | Normal-month/Chat/bootstrap separation regression |
| FR-015 | Final review | Baseline and coverage-matrix closure gate |
| DR-001–DR-006 | US1–US3 | Constitution, provenance, shortest-link, schema, tenant, and service-boundary review |
| SC-001–SC-008 | All stories | Acceptance matrix, policy regression, and final review gates |
