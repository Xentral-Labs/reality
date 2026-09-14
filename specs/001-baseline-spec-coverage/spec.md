# Feature Specification: Existing-System Specification Baseline

**Feature Branch**: `spec/specification-baseline`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Create consistent, reviewable Spec Kit specifications for every existing Business Reality capability, with user clarification where current intent is unclear."

## Context and Intent

### Problem

Business Reality already contains substantial domain documentation, implementation,
tests, and UI behavior, but those sources do not use one consistent specification
format. It is therefore difficult for an owner or coding agent to determine which
behavior is intentional, which is merely implemented, which acceptance evidence proves
it, and what must be updated before future development starts.

The owner needs a trustworthy baseline that makes the current system reviewable without
pretending that historical behavior was previously approved through Spec Kit.

### Scope

- Inventory all existing product capabilities across durable documentation, executable
  tests, public application behavior, and persisted business concepts.
- Divide the system into bounded feature specifications that are independently
  understandable and reviewable.
- Classify every requirement as `Verified as-is`, `Documented gap`, `Implemented gap`,
  or `Intended`, with evidence links and unresolved decisions made explicit.
- Preserve the authority of the Constitution, ADRs, architecture, data model, test
  strategy, and Web product contracts.
- Produce a coverage matrix that identifies the canonical specification for every
  existing capability and any uncovered behavior.
- Ask the owner only about material business choices that cannot be resolved from
  current evidence.

### Non-Goals

- Retrospectively claiming that existing behavior received prior product approval.
- Changing application behavior, schema, business rules, or UI while documenting it.
- Treating every table, endpoint, page, or test file as a separate feature.
- Copying implementation details into business requirements.
- Marking intended but unimplemented behavior as current reality.
- Repairing every discovered product gap during baseline creation.

### Existing Contracts

- [`AGENTS.md`](../../AGENTS.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Architecture](../../docs/ARCHITECTURE.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Test strategy](../../docs/TEST_STRATEGY.md)
- [Web product specification](../../docs/WEB_SPEC.md)
- [V0 checklist](../../docs/V0_CHECKLIST.md)
- [`docs/features/`](../../docs/features/)
- [`backend/tests/`](../../backend/tests/)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the Authority for Existing Behavior (Priority: P1)

As the product owner, I can start from any existing capability and find one bounded
baseline specification that explains its business purpose, scope, rules, edge cases,
and evidence without having to infer intent from code.

**Why this priority**: Future spec-first development is unsafe until every meaningful
existing capability has an identifiable authority.

**Independent Test**: Select each durable feature document, public capability family,
and business-story test; verify that the coverage matrix links it to exactly one primary
baseline spec or explicitly classifies it as a cross-cutting contract.

**Acceptance Scenarios**:

1. **Given** an existing capability documented under `docs/features/`, **When** the
   owner consults the coverage matrix, **Then** exactly one primary baseline spec is
   identified and related cross-cutting contracts are linked.
2. **Given** observable implemented behavior with no matching feature document,
   **When** the baseline audit processes it, **Then** it is recorded as an
   `Implemented gap` rather than silently treated as approved intent.
3. **Given** documented behavior with no executable proof, **When** evidence is
   classified, **Then** it is recorded as a `Documented gap` and remains incomplete.

### User Story 2 - Review Current Reality Without Losing Uncertainty (Priority: P1)

As the product owner, I can review concise requirements and answer only the decisions
where documentation, tests, and implementation do not establish one clear business
intent.

**Why this priority**: A baseline is trustworthy only if facts and assumptions are
visibly separated.

**Independent Test**: Review a sample containing verified, documented-only,
implemented-only, intended, and ambiguous behavior; verify that each carries the
correct status, evidence, and owner-decision marker.

**Acceptance Scenarios**:

1. **Given** matching documentation, implementation, and green acceptance evidence,
   **When** a requirement is baselined, **Then** it is labeled `Verified as-is` and
   links all three sources.
2. **Given** multiple reasonable business interpretations with different outcomes,
   **When** no authoritative evidence resolves them, **Then** the requirement remains
   Draft and the owner receives one focused question with implications.
3. **Given** a reasonable non-material default, **When** evidence is incomplete,
   **Then** the default is recorded as an assumption rather than interrupting review.

### User Story 3 - Start the Next Change Spec-First (Priority: P2)

As a contributor or coding agent, I can locate the applicable baseline, create a new
change specification, and trace its requirements to existing invariants before touching
code.

**Why this priority**: The baseline creates value when it guides subsequent work rather
than becoming a static documentation archive.

**Independent Test**: Choose one representative future behavior change and demonstrate
that its new spec can link the affected baseline requirements and cross-cutting
contracts without re-discovering the system from implementation.

**Acceptance Scenarios**:

1. **Given** a proposed change to an existing capability, **When** a contributor starts
   Spec Kit, **Then** the coverage matrix identifies the baseline spec and required
   cross-cutting reviews.
2. **Given** a proposed new schema field, **When** the contributor prepares the plan,
   **Then** the baseline exposes the business scenario and derived-state constraints
   against which the field must be justified.

### Edge Cases

- One behavior spans multiple feature documents but must still have one primary owner.
- A test proves current behavior that contradicts a durable domain invariant.
- A feature document mixes implemented V0 behavior with future intent.
- The same UI action and CLI/agent action call different service paths.
- A database concept exists only to support infrastructure and is not a user feature.
- Generated assets or incidental implementation details appear in repository scans.
- Existing tests are skipped conditionally and cannot be counted as current proof.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The baseline MUST provide one coverage matrix containing every durable
  feature document, business-story test family, public capability family, and persisted
  business concept.
- **FR-002**: The baseline MUST assign every covered capability to exactly one primary
  feature specification or explicitly classify it as a cross-cutting contract.
- **FR-003**: Each baseline feature specification MUST contain context, scope,
  non-goals, prioritized user scenarios, edge cases, testable `FR-*` requirements,
  domain `DR-*` requirements, measurable outcomes, assumptions, and traceability.
- **FR-004**: Each requirement MUST use exactly one evidence status: `Verified as-is`,
  `Documented gap`, `Implemented gap`, or `Intended`.
- **FR-005**: A `Verified as-is` requirement MUST link a durable contract, observable
  implementation location, and green executable proof.
- **FR-006**: The baseline MUST NOT describe a missing or skipped proof as verified.
- **FR-007**: Contradictions between sources MUST be recorded explicitly and MUST NOT be
  resolved by silently choosing implementation over domain contracts.
- **FR-008**: Material unresolved product decisions MUST be presented to the owner in
  bounded review batches of no more than three questions.
- **FR-009**: Baseline specs MUST distinguish current behavior from future intent and
  MUST remain Draft until the owner accepts their scope and unresolved decisions.
- **FR-010**: Cross-cutting architecture and governance rules MUST be linked rather than
  duplicated inconsistently in every feature spec.
- **FR-011**: The baseline MUST cover, at minimum, the capability groups listed below.
- **FR-012**: Creating the baseline MUST NOT change product behavior or schema.
- **FR-013**: Every baseline specification, plan, task, checklist, coverage entry, and
  recorded owner decision MUST be written in English.

### Baseline Capability Groups

1. Tenant lifecycle, identity, access, membership, and isolation.
2. Party, item, location, payment-term, pricing, and operational master data.
3. Source systems, immutable ingestion, artifacts, mappings, import jobs, and Shopify.
4. Documents, document lines, corrections, and evidence interpretation.
5. Commitments plus commitment- and party-level execution holds.
6. Inventory, reservations, movements, lots, serial units, and handling units.
7. Order-to-cash business story.
8. Procure-to-pay business story.
9. Ledger, postings, payments, open items, and financial derivations.
10. Explain, timeline, operational exceptions, and materialized projections.
11. Chat sessions, AI providers, MCP, application tools, and confirmed proposals.
12. Guided demo and deterministic business scenarios.
13. Web Operations Cockpit, Inspector, Explorer, and shared-service equivalence.

### Domain and Traceability Requirements

- **DR-001**: Every baseline spec MUST state how Source → Evidence → Reality applies or
  give a bounded reason why one or more stages do not apply.
- **DR-002**: Every baseline spec MUST identify stored versus derived state and flag any
  document-owned operational state as a constitutional contradiction.
- **DR-003**: Every baseline spec MUST identify its tenant boundary and the shared
  application-service path used by adapters.
- **DR-004**: Relationships MUST be described through opaque identities and shortest
  true links; human numbers remain display/search values.
- **DR-005**: Important Web outcomes MUST identify their explanation path to Reality,
  Evidence, and Source where applicable.

### Key Entities

- **Coverage entry**: One existing capability or cross-cutting contract, its primary
  baseline owner, source links, evidence status, and unresolved gaps.
- **Baseline feature specification**: The reviewed as-is business contract for a bounded
  capability group; it is not a change request and does not authorize implementation.
- **Evidence reference**: A durable document, observable implementation location, or
  executable test that supports a requirement status.
- **Owner decision**: A material ambiguity with options, implications, answer, and date.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of current `docs/features/*.md` files appear in the coverage matrix
  with one primary baseline specification.
- **SC-002**: 100% of backend business-story and public adapter test families appear as
  evidence or as an explicit uncovered/insufficient-proof entry.
- **SC-003**: Every persisted business concept in the machine-readable data model is
  owned by a baseline feature or a named cross-cutting contract.
- **SC-004**: Every baseline requirement has one evidence status and at least one source
  link; all `Verified as-is` requirements have all three required evidence types.
- **SC-005**: No baseline spec contains unresolved ambiguity after its owner-review gate.
- **SC-006**: A contributor can identify the governing baseline and cross-cutting
  contracts for a representative new change in under five minutes.
- **SC-007**: Baseline generation produces zero product-code or schema changes.

## Assumptions and Dependencies

- The thirteen capability groups are the smallest useful business-oriented baseline;
  individual endpoints, pages, and tables remain evidence within those groups.
- Existing long-lived documents remain authoritative unless they contradict the
  Constitution or the owner explicitly changes intent.
- Green tests prove observed behavior, not by themselves desired business intent.
- Skipped integration tests are evidence references but not verified proof.
- Infrastructure/deployment choices remain governed by Architecture and ADRs unless
  they expose independent user-visible behavior.
- The owner will review specs in small batches rather than approving the entire system
  in one step.

## Open Questions

No blocking clarification is required to define the baseline process. Individual
feature audits may surface up to three material owner questions per review batch.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-002 | US1 scenarios 1–3 | Automated coverage audit plus owner review |
| FR-003–FR-007 | US1, US2 | Spec-policy validation and source comparison |
| FR-008–FR-010 | US2 scenarios 2–3 | Review log and bounded clarification batches |
| FR-011–FR-013 | All stories | Thirteen English baseline specs; product-code diff audit |
| DR-001–DR-005 | US3 | Constitution checklist for every baseline spec |
| SC-001–SC-007 | All stories | Final coverage report and representative change drill |
