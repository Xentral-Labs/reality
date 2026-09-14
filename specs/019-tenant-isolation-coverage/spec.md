# Feature Specification: Complete Tenant Isolation Coverage

**Feature Branch**: `[019-tenant-isolation-coverage]`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Create deterministic isolation coverage for every public business service, query, and aggregate family so that 003/FR-012 can move from Documented gap to Verified as-is."

## Context and Intent

### Problem

Tenant isolation is a non-negotiable product and security boundary. Existing business
stories prove isolation for several important records and workflows, but the repository
does not provide one deterministic map showing that every public business service,
query, and aggregate family has explicit cross-tenant proof. A new public operation can
therefore be added without making missing tenant-isolation evidence immediately visible.

This leaves `003/FR-012` as a documented gap even though many individual services are
already tenant-scoped. The gap is not a request for new tenant behavior; it is a request
for complete, durable, reviewable proof of the behavior the product already promises.

### Scope

- Establish one authoritative inventory of public business service, query, aggregate,
  and tenant-owned relationship families.
- Classify each family by its tenant-isolation behavior and required proof.
- Provide a named executable cross-tenant scenario for every tenant-scoped family.
- Prove that foreign-tenant reads do not disclose records, lists and aggregates do not
  mix tenants, and writes or relationships cannot target foreign records.
- Make newly introduced or newly exposed public business families fail the coverage gate
  until their tenant behavior and evidence are classified.
- Record narrow, explicit reasons for public operations that are genuinely global or
  administrative rather than tenant-scoped.
- Correct any discovered implementation defect only where necessary to restore the
  already-approved tenant contract.
- Update the Tenant and Access baseline evidence for `003/FR-012` only after the complete
  inventory and all required isolation scenarios pass.

### Non-Goals

- Adding tenant roles, invitations, ownership transfer, single sign-on, or new access
  policy.
- Changing authentication, membership, session, or platform-administrator semantics.
- Adding database fields, tenant identifiers, tables, or migrations.
- Replacing existing business-story tests or duplicating every test at every adapter.
- Treating internal helpers, migrations, fixtures, or private implementation details as
  public business families.
- Changing Source, Evidence, Reality, financial, inventory, or fulfillment behavior
  except to repair a proven tenant-isolation violation.
- Claiming that an adapter is safe merely because it hides a service defect.

### Existing Contracts

- [`specs/003-tenant-access/spec.md`](../003-tenant-access/spec.md), especially FR-010,
  FR-012, DR-003, DR-005, and SC-006.
- [`docs/features/tenancy.md`](../../docs/features/tenancy.md).
- [`docs/TEST_STRATEGY.md`](../../docs/TEST_STRATEGY.md), especially required tenant
  assertions and the tenancy test map.
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) and
  [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md) for shared service/adapter boundaries.
- [`docs/SPEC_COVERAGE_MATRIX.md`](../../docs/SPEC_COVERAGE_MATRIX.md), documented gap
  `003/FR-012`.
- [`AGENTS.md`](../../AGENTS.md) and the project Constitution.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep One Company's Data Isolated (Priority: P1)

As an operator working in one company, I can query business records and summaries
without seeing or being influenced by another company's records.

**Why this priority**: Cross-company disclosure or aggregate contamination would break
the product's foundational trust and security boundary.

**Independent Test**: Create two tenants with overlapping human-readable values and
distinct business data, exercise every inventoried public read/query/aggregate family
for the first tenant, and verify that only first-tenant records and totals are returned.

**Acceptance Scenarios**:

1. **Given** two tenants contain records with identical names, numbers, codes, or
   external references, **When** a public list or search is run for one tenant, **Then**
   only records owned by that tenant are returned.
2. **Given** both tenants contribute data to the same business family, **When** a public
   total, balance, count, projection, or operational summary is requested for one
   tenant, **Then** the result is calculated exclusively from that tenant's records.
3. **Given** a record belongs to another tenant, **When** its opaque ID is supplied to a
   tenant-scoped read, **Then** the operation behaves as not found without confirming
   that the foreign record exists.

---

### User Story 2 - Reject Cross-Tenant Writes and Links (Priority: P1)

As an operator, I cannot mutate or connect a record from another company by supplying
its opaque ID to an otherwise valid business action.

**Why this priority**: A cross-tenant write can corrupt both authority and traceability
even when no foreign data is displayed first.

**Independent Test**: For every inventoried family that mutates tenant-owned state or
resolves a tenant-owned relationship, attempt the action with a foreign record ID and
verify a non-disclosing failure and zero persisted side effects.

**Acceptance Scenarios**:

1. **Given** a valid tenant-owned source record and a foreign tenant-owned target,
   **When** a public action attempts to create their relationship, **Then** the action
   fails without creating or modifying any business record.
2. **Given** a foreign record ID is supplied to an update, lifecycle, proposal, or
   confirmation action, **When** the action executes under the current tenant, **Then**
   it fails without revealing foreign-record details.
3. **Given** a cross-tenant action fails after validating several inputs, **When** the
   transaction is reviewed, **Then** no partial write, event, allocation, reservation,
   movement, or ledger effect remains.

---

### User Story 3 - Detect Coverage Drift (Priority: P1)

As a reviewer, I can see a deterministic relationship between every public business
family and its tenant-isolation evidence, so new uncovered operations cannot pass
silently.

**Why this priority**: A one-time test campaign does not close the gap unless future
public operations are forced into the same coverage discipline.

**Independent Test**: Run the coverage check against the current inventory and observe
complete classification; introduce a temporary public family without isolation
evidence and observe a failure naming the uncovered family.

**Acceptance Scenarios**:

1. **Given** the current public business surface, **When** the coverage check runs,
   **Then** every family is named, classified, and linked to executable evidence.
2. **Given** a new public tenant-scoped family is introduced without named evidence,
   **When** the coverage check runs, **Then** it fails and identifies that family.
3. **Given** an operation is genuinely global or platform-administrative, **When** it is
   inventoried, **Then** its exemption names the governing contract and reason rather
   than silently treating it as tenant-safe.

---

### User Story 4 - Close the Baseline Gap with Objective Evidence (Priority: P2)

As the product owner, I can verify that the tenant-isolation gap was closed by complete
executable evidence without changing unrelated capability baselines.

**Why this priority**: Baseline status must reflect proven behavior and must not hide
remaining uncertainty elsewhere.

**Independent Test**: Review `003/FR-012` after all inventory, read, aggregate, write,
relationship, and drift checks pass; confirm that only this gap changes status and that
all unrelated documented gaps remain visible.

**Acceptance Scenarios**:

1. **Given** every public business family has passing required evidence, **When** the
   Tenant and Access baseline is reviewed, **Then** `003/FR-012` changes from
   `Documented gap` to `Verified as-is` and cites the new coverage proof.
2. **Given** any tenant-scoped family remains unclassified or lacks required evidence,
   **When** baseline closure is considered, **Then** `003/FR-012` remains a documented
   gap.

### Edge Cases

- A public operation accepts several tenant-owned IDs, only one of which is foreign.
- Two tenants reuse the same human number, external ID, SKU, code, or name.
- A query returns no rows for the current tenant but rows exist for another tenant.
- An aggregate would coincidentally have the same result with or without foreign data.
- A family supports both a single-record lookup and a list or aggregate form.
- A mutation validates data before resolving the foreign relationship.
- A proposal is created in one tenant and confirmed, rejected, or inspected from another.
- A Source or Evidence record is foreign while a related Reality record ID is local, or
  the reverse.
- An archived tenant remains stored but is excluded from normal active-tenant behavior.
- An explicitly global administrative operation is incorrectly treated as a tenant-
  scoped business operation, or vice versa.
- A public adapter calls the correct service but supplies the wrong tenant context.
- A new public family is added under an unexpected module or naming convention.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST maintain a deterministic inventory of every public
  business service, query, aggregate, and tenant-owned relationship family.
- **FR-002**: Every inventoried family MUST be classified as tenant-scoped read,
  collection/search, aggregate, mutation/relationship, or explicitly global/
  administrative, with a reason for its classification.
- **FR-003**: Every tenant-scoped family MUST have named executable isolation evidence;
  broad claims or incidental coverage in an unrelated test MUST NOT count unless the
  exercised boundary and expected isolation behavior are explicit.
- **FR-004**: Single-record reads using a foreign opaque ID MUST behave as not found and
  MUST NOT reveal whether the foreign record exists.
- **FR-005**: Collections, searches, registers, projections, counts, balances, and other
  aggregates MUST exclude all foreign-tenant records, including when human-readable
  values overlap across tenants.
- **FR-006**: Mutations and tenant-owned relationships MUST reject every foreign input
  without creating partial state or changing either tenant.
- **FR-007**: Tenant isolation MUST be enforced at the shared business boundary used by
  CLI, Web, API, Chat, agent, and other adapters; adapter filtering alone MUST NOT count
  as service-family isolation evidence.
- **FR-008**: The coverage gate MUST fail when a public business family is missing from
  the inventory, lacks a valid classification, or lacks the evidence required by its
  classification.
- **FR-009**: Every global or platform-administrative exemption MUST be narrow, named,
  and linked to an approved authority; ordinary business operations MUST NOT be exempt.
- **FR-010**: Coverage results MUST be deterministic and identify uncovered or invalid
  families precisely enough for a reviewer to locate the missing proof.
- **FR-011**: Any tenant-isolation defect discovered by this feature MUST be corrected at
  the existing shared boundary and receive a regression scenario; the correction MUST
  NOT introduce an alternate adapter-specific business rule.
- **FR-012**: `003/FR-012` MUST remain a documented gap until FR-001 through FR-011 and
  their acceptance evidence pass; only then may its evidence status become
  `Verified as-is`.

### Domain and Traceability Requirements

- **DR-001**: Tenant isolation MUST preserve Source → Evidence → Reality traceability;
  a tenant may traverse only relationships whose records all belong to that tenant.
- **DR-002**: Opaque IDs and shortest true relationships MUST remain authoritative;
  duplicated human-readable values MUST neither identify nor connect records across
  tenants.
- **DR-003**: Every tenant-owned business table and public business operation MUST
  enforce tenant scope through the shared service/query boundary.
- **DR-004**: Documents MUST remain Evidence rather than the owner of operational state;
  isolation corrections MUST NOT add delivery, reservation, fulfillment, inventory, or
  payment state to documents.
- **DR-005**: Source payloads and SourceRecords MUST remain immutable and lossless;
  isolation testing or correction MUST NOT rewrite external payloads.
- **DR-006**: This feature MUST NOT add schema, duplicate tenant relationships, or direct
  adapter-to-persistence writes.

### Key Entities *(when data is involved)*

- **Public Business Family**: A stable group of externally reachable business
  operations that share a tenant-isolation contract, such as record lookup, register,
  aggregate, mutation, or relationship management.
- **Isolation Classification**: The required cross-tenant behavior for one public
  business family and the reason that behavior applies.
- **Isolation Evidence**: A named executable scenario proving the classified behavior
  with at least two tenants and controlled local/foreign records.
- **Coverage Entry**: The durable mapping from one public business family to its
  classification, governing requirement, and executable evidence.
- **Approved Exemption**: A narrow public operation that is global or platform-
  administrative by contract and therefore does not use tenant-scoped business
  semantics.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of inventoried public business families have a valid classification
  and named executable evidence or an approved global/administrative exemption.
- **SC-002**: Every tested foreign-ID read returns the same non-disclosing outcome as an
  unknown ID.
- **SC-003**: Every tested collection and aggregate contains 0 records or contribution
  from the foreign tenant.
- **SC-004**: Every tested cross-tenant mutation or relationship attempt produces 0
  persisted side effects in both tenants.
- **SC-005**: Introducing one uncovered public business family causes the coverage gate
  to fail and name that family.
- **SC-006**: Duplicate human-readable values across tenants cause 0 collisions or
  cross-tenant matches in the complete coverage suite.
- **SC-007**: This feature introduces no schema, new business state, Source payload
  mutation, or adapter-specific business rule; any proven isolation defect is corrected
  only at the existing shared service, query, or application-tool boundary.
- **SC-008**: `003/FR-012` cites the completed inventory and passing evidence and is no
  longer listed as an accepted documented gap, while all unrelated gaps remain visible.
- **SC-009**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The public business surface can be identified deterministically from existing shared
  service, query, tool, and adapter authorities without treating every private helper as
  a separate family.
- Multiple operations may share one evidence scenario only when the scenario explicitly
  exercises each operation and its required isolation behavior.
- Platform-wide authentication, admission, and explicitly authorized administration
  remain governed by the Tenant and Access baseline and must be recorded as exemptions
  where they appear in the public inventory.
- Existing isolated PostgreSQL business-story fixtures can represent two tenants with
  overlapping human-readable values and distinct opaque IDs.
- Corrections that merely restore FR-010/FR-012 behavior are within scope; any new
  authorization policy or schema requirement needs a separate approved specification.

## Open Questions

No unresolved product questions remain. The default scope follows `003/FR-012`: every
public business query and aggregate plus every public mutation or relationship that
resolves tenant-owned records at the same shared boundary.

The product owner approved this specification on 2026-08-31.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US3 scenarios 1–3 | deterministic public-family inventory and evidence map |
| FR-004 | US1 scenario 3 | foreign-ID versus unknown-ID read scenarios |
| FR-005 | US1 scenarios 1–2 | two-tenant collection/search/aggregate scenarios |
| FR-006 | US2 scenarios 1–3 | cross-tenant mutation, relationship, and atomicity scenarios |
| FR-007 | US1–US3 | shared-boundary evidence and representative adapter equivalence |
| FR-008–FR-010 | US3 scenarios 1–3 | complete, missing, invalid, and exempt inventory cases |
| FR-011 | US1–US2 | regression for each implementation defect discovered during coverage work |
| FR-012 | US4 scenarios 1–2 | baseline and coverage-matrix closure gate |
| DR-001–DR-006 | US1–US4 | Constitution, lineage, tenant, schema, and service-boundary review |
| SC-001–SC-009 | All stories | final quantitative coverage and independent acceptance review |
