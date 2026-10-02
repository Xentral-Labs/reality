# Feature Specification: Consolidate Census Membership

**Feature Branch**: Existing shared workspace; no branch switch.
**Created**: 2026-10-02
**Status**: Foreign-currency main integration revalidation pending
**Language**: English
**Input**: The owner selected the next specification step with "ok weiter" after the
four-to-one census assessment and the proposed history/link/lifecycle acceptance scope.

## Context and Intent

### Problem

Four retained census member families describe the same captured-observation grain,
but use separate physical storage. The owner wants a smaller coherent system while
preserving the exact evidence needed to explain an earlier company observation.
These captures are historical observations, not financial approvals. Reading current
Reality records cannot replace what was captured previously.

### Scope

- Share physical storage for `cost_company_census_movement`,
  `cost_company_census_document`, `cost_company_census_line` and
  `cost_company_census_source`; retain four original logical interfaces.
- Preserve original member identities, observations, hashes, family membership,
  subject references, capture context, request replay, bounded inspection and counts.
- Preserve immutable membership, same-tenant building-parent admission and sealing.
- Preserve the captured line-to-document and downstream company-input-to-line links.
- Deliver a populated lossless upgrade, rollback and re-upgrade, including the original
  schema/link/index/protection contracts and transactional failure handling.

### Non-Goals

- Consolidating or removing the census header, captured-basis members, company inputs,
  received basis, confirmed revisions, source records or any other cost family.
- Reconstructing retained observations from current source/evidence/Reality, deriving
  new authoritative values, recalculating source amounts or changing capture eligibility.
- New financial approval, publishing behavior, public writes, background work, generic
  Facts/Settings storage, universal identity registry or new retention/cleanup policy.
- Commit, merge, deployment or live migration. Acceptance applies to repository artifacts
  and isolated verification; the potential saving is not counted before acceptance.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md) and
  [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- [Retained current input observations](../../docs/features/receipt-costing.md),
  [data model](../../docs/DATA_MODEL.md) and [architecture](../../docs/ARCHITECTURE.md).
- [Census assessment](../../docs/ideas/census-storage-consolidation.md) and
  [exact metadata inventory](../../docs/ideas/census-storage-inventory.json).
- Existing census/captured/company feature contracts in specs 242 and subsequent
  storage specifications; consolidations 331, 332, 324 and 330 (renumbered for current-main integration).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explain the Original Captured Observation (Priority: P1)

An inspector opens an earlier census after newer intake or a manual correction.
The original observations and their trace links must remain the same.

**Why this priority**: A smaller store must not change the explanation of history.

**Independent Test**: Compare all four member families, hashes, counts, pages and
context before/after transition, then change current knowledge and replay the old capture.

**Acceptance Scenarios**:

1. **Given** a retained census with all four families, **When** storage is consolidated,
   **Then** every original member field/value, identity, context, hash and family count
   is unchanged, with the original inspection fields and capture-bound cursors.
2. **Given** a retained census followed by revised source/current evidence, **When**
   it is read or the same capture request is replayed, **Then** its observations remain
   the original ones, while a new capture may observe the newer values.
3. **Given** a source observation without an interpretation outcome or financial
   support, **When** read after consolidation, **Then** absence remains absence,
   and the capture remains ineligible for financial publication.
4. **Given** corrupted or missing membership, **When** full verification or downstream
   resolution uses it, **Then** existing integrity refusal remains effective.

### User Story 2 - Keep Protected, Correctly Typed Membership (Priority: P1)

An internal capture writer records a consistent observation, while an inspector or
company-input builder relies on links that cannot cross tenants, captures or member types.

**Why this priority**: Storage savings must not weaken identity or historical protection.

**Independent Test**: Exercise valid all-family capture admission, invalid references,
mutation refusal and simultaneous insertion/sealing through every supported write path.

**Acceptance Scenarios**:

1. **Given** a same-tenant building census and valid subjects, **When** all four families
   are inserted and the capture is sealed, **Then** existing batch inserts, returned
   identities and final verified capture work through the original interfaces.
2. **Given** existing members, **When** an update/delete is attempted or a new member
   is inserted after sealing, **Then** the existing protection refuses it; a sealed
   header also remains immutable.
3. **Given** different tenants/censuses/types and equal opaque IDs, **When** a line
   selects its captured document or a company input selects its census line, **Then**
   only the original required type and tenant are accepted; the document must also
   belong to the same census. Valid equal IDs across types/tenants stay independent.
4. **Given** a missing subject, duplicate selected subject or invalid family shape,
   **When** inserted, **Then** it is refused without partial capture retention.
5. **Given** competing member insertion and header sealing, **When** they overlap,
   **Then** the existing parent admission serialization is retained: no member is
   admitted after sealing, and an admitted member is within the building transition.

### User Story 3 - Reversibly Reduce Storage (Priority: P2)

A maintainer transitions populated storage and can restore the predecessor without
losing retained history or changing downstream company input identities.

**Why this priority**: The reduction is acceptable only with a credible reversible transition.

**Independent Test**: Upgrade a populated predecessor, perform supported new captures,
rollback and re-upgrade; compare full values and original storage/protection contracts.

**Acceptance Scenarios**:

1. **Given** all four families, two tenants, equal IDs, empty captures/families and
   downstream company inputs, **When** upgraded, **Then** all original values and links
   survive and physical storage is reduced by exactly three tables.
2. **Given** supported captures after upgrade, **When** rolled back and re-upgraded,
   **Then** all old/new values survive and rollback restores the exact predecessor
   columns, keys, references, indexes and mutation/admission protections.
3. **Given** a copy/parity failure during transition, **When** the transaction aborts,
   **Then** original populated storage and its protections remain intact.
4. **Given** counts and an existing authorized tenant purge, **When** run after
   consolidation, **Then** members are counted once and purge retains the predecessor result: eligible
   records are removed once, while protected retained history remains refused with
   rollback. Another tenant's capture and downstream history remain unchanged.

### Edge Cases

- Equal member IDs across all four families and multiple tenants; equal subject IDs.
- Empty census/family, NULL source outcome, exact observation precision and sizes.
- Wrong-tenant subject/header/outcome, document membership in another census,
  company input naming a document/movement/source member, missing targets and duplicates.
- Existing building member UPDATE/DELETE refusal as well as sealed-member refusal.
- Chunk boundaries, clean-session admission, request replay with changed arguments,
  capture-bound paging, cutoff/context identity, missing/corrupt hashes and counts.
- Concurrent sealing/admission, savepoint rollback, migration parity failure,
  populated rollback with downstream references and partial/repeated schema lifecycle.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The four named member families MUST use one physical store, saving exactly
  three tables while retaining the census header and original four logical resources.
- **FR-002**: Original opaque IDs, tenant/type namespaces, family-specific selected-subject
  uniqueness and every observation/context/hash value MUST remain unchanged.
- **FR-003**: Original tenant-qualified subject, source-outcome and parent references
  MUST remain enforced. Line-to-document membership MUST select a document member
  in the same tenant/census; company-input-to-line membership MUST select a line
  member in the same tenant. Enforcement MUST not rely solely on application reads.
- **FR-004**: Every family MUST require its original subject and family-specific mandatory
  fields, permit its original optional fields, and reject other-family subject/extra
  fields. Equal IDs across families MUST not weaken typed link enforcement.
- **FR-005**: The original logical column sets and supported insertion/returned-identity,
  detail, paging and verification contracts MUST remain unchanged, including batched
  inserts. New private storage fields MUST not appear in public rows or hash inputs.
- **FR-006**: Members MUST remain immutable on update/delete. Inserts MUST retain the
  same-tenant building-parent check and admission serialization; sealed header/member
  protection MUST survive every supported interface and physical write path.
- **FR-007**: Existing member/header digests, byte-size checks, retained replay/context,
  historical resolution and corruption/missing-member refusal MUST remain unchanged.
  Later knowledge MUST not change an earlier capture or its publication eligibility.
- **FR-008**: Capture admission MUST retain its consistent snapshot, clean-session,
  savepoint, request-replay and changed-argument refusal behavior and original limits:
  100,000 combined records, 1 MiB per canonical member and 64 MiB per capture.
- **FR-009**: Populated upgrade/rollback/re-upgrade MUST preserve exact original and
  supported post-upgrade values, including downstream references. Rollback MUST restore
  predecessor column/key/reference/index/protection contracts. Interrupted or failed
  parity MUST not leave partial storage retirement or missing protection.
- **FR-010**: Schema lifecycle, index coverage, migration discovery/exclusion, original
  record inspection and physical counts MUST work without duplicate counting. Existing
  authorized purge MUST preserve eligible removal and protected-history refusal, with
  no duplicate removal or partial committed deletion; another tenant stays unchanged.
- **FR-011**: All unrelated source, evidence, decision, review, output and ledger values,
  authorities and lifecycles MUST remain unchanged; no new received/derived authority
  or incidental capture/lifecycle behavior MAY be introduced by the consolidation.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality through the exact retained subjects
  and observations. Never substitute current records, recompute stated values, turn
  missing evidence into zero or admit the census as a financial approval.
- **DR-002**: Preserve the shortest original typed links, opaque identity and captured
  document/line relationship. Do not duplicate business authority or weaken real links
  to untyped IDs to obtain a smaller storage count.
- **DR-003**: Tenant isolation and shared application services remain mandatory. Existing
  confirmation and authorized purge boundaries remain unchanged; this adds no public
  mutation surface, transport rule, scheduler or bypass.

### Key Entities *(when data is involved)*

- **Retained census**: A tenant/request-bound consistent observation with exact context,
  counts, content integrity and a building-to-sealed lifecycle; not financial authority.
- **Census member**: A retained typed subject and its exact observation/hash. Line members
  select an original captured document; source members optionally select an outcome.
- **Company contribution input**: An existing retained financial input whose census-line
  reference must retain its original identity and line type across the transition.

## Success Criteria *(mandatory)*

- **SC-001**: Four member storage tables become one with four original logical resources;
  measured net reduction is exactly three, with zero unrelated storage retirements.
- **SC-002**: 100% of original and supported post-upgrade captured values/identities and
  downstream references match through upgrade, rollback and re-upgrade, with exact
  predecessor structural/protection restoration and transactional abort evidence.
- **SC-003**: Every defined invalid-tenant/type/census/shape and forbidden-mutation case
  is refused; every supported capture/history/replay/inspection case retains its
  original result, including simultaneous admission/sealing and absent outcomes.
- **SC-004**: Every FR/DR has a planned executable proof and final passing evidence;
  all required backend, migration, benchmark, documentation and Web gates pass before
  the storage saving is marked accepted.

## Assumptions and Dependencies

- The owner selected the bounded four-to-one proposal and specification continuation.
  Technical mechanics remain planning decisions; the assessment's identity aliases
  are a candidate, not prescribed implementation or accepted schema expansion.
- No unanswered product-scope question remains. Existing valid/invalid capture behavior
  is the baseline; do not add a stronger live line/document business constraint.
- Actual populated predecessor DDL, FK/trigger/function dependencies and index names
  must be captured on isolated PostgreSQL before implementation; metadata alone is
  insufficient. Recheck migration head/number and shared source before planning.
- Previous accepted storage consolidations must remain intact. Current inventory is
  147 physical tables/21 views; total accepted saving is 15 until this slice passes.
- No branch switch, staging, commit or live migration is requested. Use the explicit
  feature-directory override so concurrent spec 325 retains its shared active pointer.

## Open Questions

None for requirements. Planning review clarified FR-010/US3.4 against the predecessor:
existing guards refuse deletion of retained census history even in authorized purge.
Preserve that refusal and rollback rather than introduce an incidental bypass.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
| --- | --- | --- |
| FR-001 | US3.1 | Physical/logical inventory and populated transition |
| FR-002 | US1.1/2, US2.3/4, US3.1/2 | Exact row/hash/context and ID/uniqueness cases |
| FR-003 | US2.3/4, US3.1/2 | All subject/parent/outcome and incoming typed link cases |
| FR-004 | US1.3, US2.3/4 | Closed family shape, NULL outcome, equal-ID tests |
| FR-005 | US1.1/4, US2.1 | Original column/insert/RETURNING/batch/inspection tests |
| FR-006 | US2.1/2/5, US3.2/3 | Physical/interface immutability, admission/sealing and rollback guards |
| FR-007 | US1.1/2/3/4 | Historical, replay, digest, size and corrupt/missing-member tests |
| FR-008 | US1.2, US2.1/4/5 | Existing capture limit/replay/savepoint and concurrency regressions |
| FR-009 | US3.1/2/3 | Populated exact-schema roundtrip and injected parity failure |
| FR-010 | US1.1, US3.1/4 | Lifecycle/index/record/count/purge and migration tests |
| FR-011 | US1.2/3, US3.1/2/4 | All unrelated authority snapshots and retained downstream results |
| DR-001 | US1.1/2/3/4 | Original received observations, hashes and trace links |
| DR-002 | US2.3/4, US3.1/2 | Family-safe incoming links and identity parity |
| DR-003 | US2.3/4, US3.4 | Tenant isolation, shared entrypoint and authorized purge review |

Exact test paths and ordered tasks will be assigned during planning, before implementation.
