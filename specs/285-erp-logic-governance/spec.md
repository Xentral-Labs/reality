# Feature Specification: Governed ERP Logic Ownership

**Feature Branch**: `285-erp-logic-governance`
**Created**: 2026-09-27
**Status**: Approved scope (owner: the initial semantic audit covers the four named critical ERP calculations; all other capabilities receive structural governance only)
**Language**: English
**Input**: Make the existing ERP capability package safer to inspect, maintain and extend over time, especially by preventing duplicate business logic across services, tools and adapters. Specify only; do not implement yet.

## Context and Intent

### Problem

Reality already has the correct architectural direction: business meaning belongs to the shared
domain and application services, while Web, API, CLI, Chat, MCP, workers and demo flows are entry
points to that same core. Executable catalogs describe commands, tools, resources, processes,
events, projections and exceptions. This gives maintainers a strong index, but it does not yet give
them one complete proof that every ERP capability has one authoritative owner and that every
adapter reaches that owner without restating its rules.

As the catalog grows, a maintainer or external reviewer must currently correlate several catalogs,
registries, services, tests and generated pages. Existing checks catch many missing or stale
references, but they do not comprehensively refuse a second calculation, a direct adapter write, a
transport-specific eligibility rule or an unclassified ERP mutation path. Large central registries
also make unrelated capability areas harder to review independently and increase merge and
maintenance risk.

Without stronger executable governance, two implementations can gradually answer the same
business question differently. Stock availability, open commitment quantity, fulfilment,
settlement, contribution and operational exceptions are particularly sensitive: a small duplicate
calculation can create contradictory answers while every individual component still appears valid.

### Scope

- Give maintainers and external reviewers one generated trace from every governed ERP capability
  to its business resource and process, authoritative application owner, public entry points,
  business events, verification reads and executable evidence.
- Enforce that every governed mutation and material business calculation has one authoritative
  business owner and that adapters delegate to it rather than implementing an alternative rule or
  direct business write.
- Make capability registration independently reviewable by business area while preserving one
  complete runtime catalog and rejecting missing or duplicate registrations.
- Detect and resolve materially duplicated implementations of the selected critical ERP
  calculations: inventory availability, commitment fulfilment/open quantity, financial open
  balances and contribution results.
- Preserve existing observable business behavior, public tool identities, confirmation rules,
  tenant isolation, traceability and generated documentation throughout the work.

### Non-Goals

- Do not add a new ERP capability, business process, business status or user workflow.
- Do not change the meaning or arithmetic of an existing business rule. A disagreement discovered
  during consolidation is reported for separate product clarification rather than silently chosen.
- Do not create a universal rules engine, configuration language or single monolithic ERP-logic
  module.
- Do not move business calculations into catalogs. Catalogs remain executable descriptions and
  validation authorities, not business-state or calculation engines.
- Do not add or change business schema, migrate business records or alter retained source payloads.
- Do not rename or remove public commands, tools, events, views, projections or exceptions.
- Do not redesign user interfaces or replace existing specialized proposal reviews.
- Do not claim that textual similarity alone proves duplicated business meaning; suspected
  duplication requires a named authoritative rule and behavioral evidence.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Architecture](../../docs/ARCHITECTURE.md)
- [Spec-Driven Development Workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Tool Usage](../../apps/docs/content/tool-usage/index.md)
- [Web product contract](../../docs/WEB_SPEC.md)
- [Company setup and demo production-tool boundary](../../docs/features/company-setup-demo.md)

## Clarifications

### Session 2026-09-27

- Q: Should the initial semantic duplication audit cover inventory availability, commitment
  fulfilment/open quantity, open financial balances and contribution results, while other ERP
  capabilities receive structural ownership and adapter-boundary checks only? → A: Yes; the four
  named critical calculations are the approved initial semantic audit scope.

## User Scenarios & Testing

### User Story 1 - Trace an ERP capability to one authority (Priority: P1)

As a maintainer or independent reviewer, I can start with any governed ERP capability and see one
complete, current trace to its business classification, authoritative owner, entry points, effects,
verification reads and executable evidence, so I can judge what the system does without assembling
an undocumented map by hand.

**Why this priority**: Safe review and extension begins with knowing which operation owns the
meaning and how its result is proven. Without that trace, later duplication controls cannot be
interpreted or audited reliably.

**Independent Test**: Generate the capability trace from a known repository state and select one
representative read and mutation from orders, inventory, logistics, finance and contribution. Each
selection resolves to exactly one authoritative owner and all of its registered entry points,
effects, verification reads and executable evidence without an unresolved reference.

**Acceptance Scenarios**:

1. **Given** a catalogued ERP command, **When** a reviewer follows its trace, **Then** the reviewer
   sees its resource, applicable process steps, authoritative application owner, public tools,
   emitted events, verification reads and requirement/test evidence in one result.
2. **Given** a public ERP read that is not itself a business command, **When** it is traced, **Then**
   its authoritative read owner, data basis, limitations and executable evidence are visible
   without inventing a command relationship.
3. **Given** a catalogued entry with a missing, duplicate or stale ownership relationship, **When**
   the trace is validated, **Then** validation fails and identifies the exact capability and broken
   relationship.
4. **Given** a deliberately excluded transport or operational helper, **When** the trace is
   validated, **Then** it carries an explicit reason rather than appearing as an unexplained gap.

---

### User Story 2 - Prevent a second business implementation (Priority: P1)

As a maintainer extending Web, API, CLI, Chat, MCP, workers, integrations or demo flows, I am
stopped before merge if the change directly writes business state or restates a governed ERP rule
outside its authoritative business owner.

**Why this priority**: This is the central safety outcome. Documentation can make duplication
visible, but an executable boundary prevents a divergent rule from becoming part of the product.

**Independent Test**: Plant representative forbidden changes in test fixtures—an adapter business
write, a transport-local availability calculation, an independently registered mutation and a
service-to-adapter dependency—and verify that each is refused with the owning capability and
permitted boundary identified. Existing legitimate paths remain accepted.

**Acceptance Scenarios**:

1. **Given** an adapter that attempts to create or change a business record without the registered
   application boundary, **When** architecture validation runs, **Then** it fails before the change
   can be accepted.
2. **Given** an adapter or operational runtime that restates a governed calculation used to decide
   or present a business outcome, **When** validation runs, **Then** it fails and points to the
   authoritative owner that must be reused.
3. **Given** a new public mutation, **When** it lacks one registered command/owner path or has more
   than one, **Then** catalog validation fails.
4. **Given** a legitimate adapter that validates transport shape, formats an authoritative result
   or handles presentation-only state, **When** validation runs, **Then** it remains allowed and is
   not misclassified as business logic.
5. **Given** an intentional exceptional path that cannot use the normal boundary, **When** it is
   proposed, **Then** it remains failing until a narrow, documented and reviewed exception names
   its scope, rationale and proof that no competing business authority is created.

---

### User Story 3 - Verify critical ERP calculations have one meaning (Priority: P1)

As a business-domain reviewer, I can verify that every consumer of a critical ERP result receives
the result from the same authoritative rule, so different interfaces and operational views cannot
silently disagree.

**Why this priority**: Inventory, fulfilment, balances and contribution are central operational and
financial claims. Divergence in any one of them undermines the trustworthiness of the complete
system.

**Independent Test**: For each selected critical result, run a shared set of boundary business
stories through its direct business read and every registered consumer. All consumers identify the
same evidence cutoff and return the same value or the same explicit unknown/refusal state.

**Acceptance Scenarios**:

1. **Given** physical movements, reservations and open supply/demand, **When** inventory is read by
   its registered consumers, **Then** physical, reserved, available, incoming and projected values
   agree and trace to the same authoritative rule.
2. **Given** commitment revisions, fulfilment movements, cancellation and holds, **When** open and
   fulfilled quantities are read by registered consumers, **Then** they agree and preserve the
   distinction between promise, allocation and movement.
3. **Given** postings, allocations, credits and reversals, **When** open financial balances are read
   by registered consumers, **Then** they agree per party and currency and do not infer external
   settlement.
4. **Given** received revenue, reviewed acquisition cost and stated selling-cost evidence, **When**
   contribution is read by registered consumers, **Then** they agree or return the same explicit
   unknown state without manufacturing missing authority.
5. **Given** two existing implementations that disagree, **When** the audit reaches that case,
   **Then** the feature records a blocking discrepancy for product/domain review and does not
   silently select either result.

---

### User Story 4 - Extend one business area without destabilizing others (Priority: P2)

As a maintainer, I can review and change the registration of one business area without navigating
or editing an undifferentiated central list, while the assembled product still exposes one complete
and deterministic capability catalog.

**Why this priority**: Independent ownership reduces review scope and merge risk, but it follows
the higher-priority proof that the resulting registrations remain complete and singular.

**Independent Test**: Add a test-only capability to one business-area fixture. It appears exactly
once in the assembled trace and catalog; duplicate naming, missing classification or cross-area
ownership fails deterministically. Unrelated business areas produce unchanged output.

**Acceptance Scenarios**:

1. **Given** a maintainer reviewing one business area, **When** its registered capabilities are
   inspected, **Then** that area's definitions can be understood without scanning unrelated
   registrations.
2. **Given** all business areas, **When** the runtime catalog is assembled, **Then** every current
   command and public tool appears with unchanged identity and deterministic ordering.
3. **Given** two areas registering the same public identity or authoritative mutation, **When** the
   catalog is assembled, **Then** assembly fails with both conflicting owners named.
4. **Given** only internal organization changes, **When** existing callers and generated references
   are compared, **Then** their observable command, tool, schema, authorization and documentation
   contracts remain unchanged.

### Edge Cases

- One public tool may legitimately contribute to more than one discovery grouping, but a mutation
  still has one authoritative execution owner; grouping is not ownership.
- One command may use supporting services, but only one service owns its application operation;
  helper reuse must not become a second entry point.
- Read-only composition may combine several authoritative reads. It must preserve each component's
  data basis, cutoff and unknown state instead of recomputing their business meaning.
- Technical validation, authorization, tenant selection, serialization, formatting and user-interface
  state are not automatically business logic. The governance rules must distinguish these from
  decisions about business eligibility, amounts, quantities, state or effects.
- Historical or compatibility adapters may remain only with an explicit classification and must
  still reach the authoritative operation for business effects.
- Generated, migration, test-fixture and external-payload code must not create false ownership
  findings merely because it contains business field names or representative arithmetic.
- An authoritative rule may intentionally return unknown when evidence is incomplete. Consumers
  must preserve unknown rather than replace it with a local default.
- Catalog initialization failure must remain deterministic and must not expose a partially assembled
  capability surface.
- Existing public aliases, if any, may share one owner but must not be counted as separate business
  implementations.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST produce a complete, deterministic governance trace for every
  catalogued ERP command and every public ERP read.
- **FR-002**: Each governed trace MUST identify the capability's business resource, applicable
  process steps, authoritative owner, public entry points, business effects or data basis,
  verification reads and executable evidence.
- **FR-003**: Every governed mutation MUST resolve to exactly one authoritative application owner;
  missing and duplicate ownership MUST fail validation.
- **FR-004**: Every public adapter and operational runtime MUST execute governed mutations through
  their authoritative application boundary and MUST NOT directly create, update or delete business
  records.
- **FR-005**: Public adapters and operational runtimes MUST NOT independently decide business
  eligibility, calculate governed business results or derive substitute business status.
- **FR-006**: Governance validation MUST distinguish prohibited business logic from permitted
  transport validation, authorization, tenant selection, serialization, formatting and
  presentation-only behavior.
- **FR-007**: Intentional boundary exceptions MUST be explicit, narrow, reviewable and fail closed
  when their declaration is missing, stale or broader than their verified need.
- **FR-008**: Capability registration MUST be reviewable by business area and MUST assemble into one
  complete catalog that refuses duplicate public identities, conflicting owners, missing
  classifications and nondeterministic output.
- **FR-009**: Existing public command names, tool names, input and output contracts, access classes,
  confirmation requirements, events and verification semantics MUST remain unchanged.
- **FR-010**: The generated business-resource, process, command, view, projection, exception and
  event references MUST remain complete and MUST be regenerated from the assembled executable
  catalogs without a separately maintained inventory.
- **FR-011**: The feature MUST audit inventory availability, commitment fulfilment/open quantity,
  open financial balances and contribution results for competing implementations and registered
  consumers.
- **FR-012**: Each critical calculation in FR-011 MUST have one named authoritative rule and
  shared behavioral evidence covering its material boundary and unknown states.
- **FR-013**: When existing implementations of a governed rule disagree, completion MUST be blocked
  for that rule until the discrepancy has an approved domain decision; consolidation MUST NOT
  silently change business meaning.
- **FR-014**: Every new or changed governed capability MUST declare its owner, classification,
  effects or data basis, verification path and executable evidence before it is accepted.
- **FR-015**: Validation failures MUST identify the affected capability, the violated ownership or
  boundary rule and the authoritative path or missing declaration needed to correct it.
- **FR-016**: The governance trace MUST explicitly classify justified exclusions so that transport
  helpers, operational mechanics and retired compatibility paths do not appear as silent gaps.
- **FR-017**: Existing tenant isolation, idempotency, authorization, human confirmation and
  Source → Evidence → Reality behavior MUST remain intact.
- **FR-018**: The completed work MUST include an externally readable review record stating the
  inspected capability scope, discovered duplication or discrepancies, resolved ownership and any
  deferred product decisions.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality remains the only business-authority chain. Governance
  metadata, generated traces and architecture findings MUST NOT become business state or evidence.
- **DR-002**: Documents remain evidence rather than operational authority. The feature MUST NOT add
  delivery, reservation, fulfilment, inventory or payment status to a document to simplify
  ownership tracing.
- **DR-003**: Values stated by a source remain received values. Shared calculations MAY derive
  observations from retained Reality at read time but MUST NOT recompute a source-owned value or
  persist a derivation as new authority.
- **DR-004**: Every adapter and consumer MUST preserve tenant scope and opaque identities while
  calling the same governed application owner.
- **DR-005**: The shortest true relationship remains authoritative. Governance traces MUST describe
  existing links and MUST NOT require duplicate foreign keys or denormalized business authority.
- **DR-006**: Events, projections and operational exceptions MUST consume the same authoritative
  business meaning as direct reads; a materialized or derived view MUST NOT become an alternate
  permission or calculation authority.
- **DR-007**: Demo profiles, scheduled work, integrations and workers MUST use the same production
  owners as ordinary company operations and MUST NOT receive governance exemptions merely because
  their caller is automated.

### Key Entities

- **Governed capability**: A catalogued business command or public business read whose meaning,
  owner, entry points, effects or data basis, verification and evidence can be traced.
- **Authoritative owner**: The single application-level operation responsible for a governed
  mutation or material business calculation. Supporting services and adapters do not become
  additional owners.
- **Capability trace**: Generated review information connecting a governed capability to its
  business classification, authority, consumers, effects and executable evidence. It is metadata,
  not business state.
- **Boundary exception**: A narrow, reviewed declaration for an otherwise prohibited dependency or
  path, carrying rationale, scope and proof that it creates no competing business authority.
- **Critical ERP calculation**: One of the initially audited operational or financial results:
  inventory availability, commitment fulfilment/open quantity, open financial balances or
  contribution results.
- **Consumer**: A view, projection, exception, adapter or composed read that presents or acts on an
  authoritative business result without owning its meaning.

## Success Criteria

- **SC-001**: 100% of catalogued ERP commands and public ERP reads appear in the generated
  governance trace with no unexplained missing owner, classification or evidence relationship.
- **SC-002**: Planted examples of direct adapter writes, transport-local ERP calculations,
  duplicate mutation ownership and reversed layer dependencies are rejected before acceptance,
  while all existing legitimate paths pass.
- **SC-003**: For each of the four critical ERP calculations, 100% of registered consumers pass the
  same boundary stories with equal results, evidence cutoff and unknown/refusal semantics.
- **SC-004**: Every discrepancy discovered among existing implementations is either resolved by an
  approved domain decision or remains explicitly blocking; zero discrepancies are silently
  normalized.
- **SC-005**: A reviewer can select a representative capability in each current business resource
  and identify its authoritative owner and verification evidence in no more than five minutes per
  capability without source-wide search.
- **SC-006**: Adding a test capability to one business area changes only that area's ownership input
  and the assembled generated output; duplicate or incomplete registration fails automatically.
- **SC-007**: Existing business-story, adapter-parity, tenant-isolation, catalog and generated-
  documentation checks remain green with no public contract or business-data migration.
- **SC-008**: Every FR and DR maps to an acceptance scenario and planned executable proof before
  implementation begins.

## Assumptions and Dependencies

- Existing domain behavior is the baseline, but two existing paths that disagree are not assumed
  equivalent; they require explicit product/domain review under FR-013.
- The current command, resource, event, projection, workspace, exception, fact and MCP catalogs
  remain the starting executable vocabulary rather than being replaced.
- Existing production application services remain the required boundary for CLI, Web, API, Chat,
  MCP, demo and scheduled callers.
- The initial duplicate-calculation audit is deliberately bounded to the four critical areas named
  in FR-011. Other areas receive ownership and boundary coverage but not a complete semantic
  consolidation audit in this feature.
- An implementation plan will choose the smallest enforcement mechanisms that produce executable,
  low-noise evidence. This specification does not mandate a particular module layout, static
  analysis technique or testing framework.
- Product/domain owner approval is required before planning if the specification review changes the
  critical calculation set or permits any exception to the Constitution.
- The product/domain owner approved the four critical calculations named in FR-011 on 2026-09-27;
  extending the semantic audit beyond them requires a separate scope decision.
- No implementation starts until this draft has been reviewed, all clarifications are resolved, a
  plan passes the Constitution Check, tasks provide requirement/test traceability and analysis has
  no critical finding.

## Open Questions

None. The scope uses the discussed package, limits semantic duplication audit to four critical ERP
calculations, treats all other capabilities with structural ownership checks, and requires separate
approval for any discovered behavioral disagreement.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 scenarios 1–3 | Catalog ownership and generated trace coverage proof |
| FR-004–FR-007 | US2 scenarios 1–5 | Planted-drift architecture and boundary tests, exception review |
| FR-008–FR-010 | US4 scenarios 1–4 | Business-area registration, assembly parity and generated-reference checks |
| FR-011–FR-013 | US3 scenarios 1–5 | Cross-consumer business stories and discrepancy report |
| FR-014–FR-016 | US1 scenarios 3–4; US2 scenario 5 | New-capability drift fixtures and exclusion coverage |
| FR-017 | All stories | Existing tenant, confirmation, idempotency and provenance suites |
| FR-018 | US1 and US3 | Externally readable final audit/review record |
| DR-001–DR-003 | US3 scenarios 1–5 | Provenance and received-versus-derived review |
| DR-004–DR-007 | US2 and US4 | Tenant/layer parity tests and automated-caller coverage |
