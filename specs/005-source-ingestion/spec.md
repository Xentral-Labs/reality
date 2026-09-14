# Feature Specification: Source Ingestion Baseline

**Baseline ID**: `005-source-ingestion`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline the existing immutable, lossless, tenant-scoped source ingestion and file-intake behavior."

## Context and Intent

### Problem

Operators need to retain what an external system or uploaded file actually supplied
before the application interprets it. This baseline distinguishes immutable source
truth, retryable interpretation, source configuration, and typed operational outcomes
without guessing at unknown fields.

### Scope

- Tenant-scoped JSON identity, canonical idempotency, and immutable versioning.
- Atomic SourceRecord and ImportJob creation followed by retryable interpretation.
- Explicit interpreters, unmapped retention, version conflicts, and ingestion events.
- Descriptive SourceSystem and SourceCapability registration.
- Streamed SourceArtifact intake, bounded preview, explicit profiles, manual mapping,
  proposal, and confirmation.
- The Shopify order interpreter as the first concrete object interpreter.

### Non-Goals

- Connector credentials, vendor calls, schedules, sync state, or claiming connectivity.
- Fuzzy field inference or automatic promotion of arbitrary payload fields.
- Required AI mapping; external AI suggestions remain future optional help.
- Overwriting inventory or financial balances from an upload.
- Redefining downstream Document, Commitment, Movement, or Ledger rules.

### Existing Contracts

- [`docs/features/source_ingestion.md`](../../docs/features/source_ingestion.md)
- [`docs/features/shopify_ingestion.md`](../../docs/features/shopify_ingestion.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

The shared boundary accepts an external object or confirmed artifact for one tenant. A
SourceStream owns the tenant-scoped external identity; each distinct payload becomes an
immutable SourceRecord version and identical delivery is idempotent. Interpretation is
a separate job. Known formats may create Evidence and Reality; unknown formats remain
retained and explicitly unmapped.

The integration registry describes origins and capabilities but does not configure a
live connector. File intake retains original bytes, returns a bounded preview, and
applies only explicit profiles and mappings confirmed by the user.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve External Source Truth (Priority: P1)

As an operator, I can ingest an external object knowing its complete payload is
retained, repeated delivery is safe, and changed delivery creates history.

**Why this priority**: Lossless source truth is the first link of every externally
sourced business explanation.

**Independent Test**: Ingest identical and changed payloads for one tenant-scoped
identity and compare payloads, IDs, versions, jobs, and events.

**Acceptance Scenarios**:

1. **Given** a new external identity, **When** JSON is accepted, **Then** one immutable
   SourceRecord and one ImportJob are retained atomically.
2. **Given** identical delivery, **When** it repeats, **Then** existing records return
   without duplicate receipt events.
3. **Given** changed delivery, **When** it arrives, **Then** a new version supersedes the
   prior record without changing its payload.
4. **Given** the same external values in another tenant, **When** they arrive, **Then**
   they form an independent stream.

### User Story 2 - Retain Before Interpretation (Priority: P1)

As an operator, I can inspect and retry accepted input even when its format is unknown
or interpretation fails.

**Why this priority**: Incomplete application understanding must never cause source
loss or invented business meaning.

**Independent Test**: Ingest unknown and failing known formats, then verify retained
truth, explicit outcomes, safe retry, and unchanged prior Reality.

**Acceptance Scenarios**:

1. **Given** no interpreter, **When** input is accepted, **Then** its job is unmapped and
   the complete source remains retryable.
2. **Given** interpretation fails, **When** the job ends, **Then** source truth remains
   intact and the failure is explainable.
3. **Given** a stale or conflicting upstream version, **When** it arrives, **Then** it is
   retained but cannot replace a newer current interpretation.
4. **Given** an invalid replacement, **When** retry occurs, **Then** prior current
   Reality remains authoritative.

### User Story 3 - Register Source Capabilities (Priority: P2)

As a tenant operator, I can describe each origin and only its intended capabilities
without implying a live connector exists.

**Why this priority**: Clear source identity supports traceability without premature
connector-management schema.

**Independent Test**: Install two instances of one catalog vendor with selected
capabilities and inspect the tenant-scoped records created.

**Acceptance Scenarios**:

1. **Given** several catalog capabilities, **When** one is installed, **Then** only the
   selected descriptive capability is registered.
2. **Given** two origins provide the same type, **When** both are created, **Then** each
   has an independent opaque identity.
3. **Given** an unregistered origin, **When** input arrives, **Then** open lossless
   ingestion still retains it.

### User Story 4 - Import a File Explicitly (Priority: P2)

As an operator, I can upload a large file, review a bounded sample and deterministic
mapping, and explicitly confirm ingestion.

**Why this priority**: Files must be retained safely while typed outcomes remain
deliberate and reproducible.

**Independent Test**: Stream a file larger than its preview, confirm a valid mapping,
process it, and inspect bytes, digest, source envelope, job context, and typed output.

**Acceptance Scenarios**:

1. **Given** a large file, **When** staged, **Then** original bytes are streamed to
   storage and only a bounded preview returns.
2. **Given** identical tenant-local bytes twice, **When** staged, **Then** both resolve
   to the same content-addressed artifact.
3. **Given** a supported profile and valid mapping, **When** confirmed and processed,
   **Then** job context reproduces the mapping and typed records retain source trace.
4. **Given** unsupported content, **When** confirmed, **Then** it is retained without
   guessed typed records.

### User Story 5 - Interpret a Shopify Order (Priority: P2)

As an operator, I can trace minimal normalized order Evidence and delivery Reality back
to the complete Shopify payload.

**Why this priority**: This proves the generic boundary with a real end-to-end flow.

**Independent Test**: Ingest, repeat, and version the Shopify fixture and inspect its
payload, Document, lines, Commitments, and replacement behavior.

**Acceptance Scenarios**:

1. **Given** a valid Shopify order, **When** interpreted, **Then** only stable fields
   required by current behavior become typed Evidence and Reality.
2. **Given** unknown Shopify fields, **When** interpreted, **Then** they remain in the
   immutable payload without schema promotion.
3. **Given** a valid newer version, **When** interpreted, **Then** replacement Evidence
   becomes current and prior open commitments are cancelled only after validation.

### Edge Cases

- Canonically equivalent JSON arrives with different object-key ordering.
- An upstream timestamp is older than current or equal with a different payload.
- Storage succeeds but interpretation fails or is retried concurrently.
- An artifact has a misleading filename/media type or exceeds bounded JSON size.
- A mapping omits a required target or references a foreign-tenant entity.
- Artifact backing storage is temporarily unavailable after metadata exists.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every accepted external payload MUST be retained losslessly as an
  immutable tenant-scoped SourceRecord before interpretation.
- **FR-002**: Source identity MUST be tenant-scoped by system, type, and external ID;
  each distinct canonical payload MUST create an ordered immutable stream version.
- **FR-003**: Identical delivery MUST NOT duplicate SourceRecords, ImportJobs, or receipt
  events.
- **FR-004**: SourceRecord and ImportJob MUST be created atomically; interpretation MUST
  be independently retryable.
- **FR-005**: Unknown pairs and unsupported files MUST remain explicitly unmapped; the
  system MUST NOT guess typed meaning.
- **FR-006**: Stale or conflicting versions MUST NOT replace current interpretation,
  while their source truth remains retained.
- **FR-007**: Failed replacement interpretation MUST NOT partially supersede previously
  valid Evidence or Reality. Shopify follow-up versions without an existing
  interpretation require review and preserve previous Evidence and Reality under
  `specs/081-shopify-update-guard/spec.md`; automatic replacement is not supported.
- **FR-008**: Ingestion MUST emit tenant-scoped, deduplicated receipt, unmapped, and
  interpreted events.
- **FR-009**: Tenants MUST be able to define multiple opaque SourceSystems and selected
  SourceCapabilities without connector runtime configuration.
- **FR-010**: Lossless ingestion MUST NOT depend on prior source registration.
- **FR-011**: File intake MUST stream original bytes into immutable tenant-scoped,
  content-addressed artifacts and return only a bounded preview.
- **FR-012**: Typed file interpretation MUST use an explicit profile and validated
  mapping stored with the job; unknown columns remain in original evidence.
- **FR-013**: File ingestion MUST require proposal and explicit confirmation before
  creating SourceRecord and ImportJob.
- **FR-014**: Inventory snapshots and bank statements MUST use append-only business
  records and MUST NOT overwrite balances.
- **FR-015**: Valid Shopify interpretation MUST preserve the full payload and create at
  most one order Document per SourceRecord, one line per non-null upstream line ID, and
  one delivery Commitment per interpreted line.

### Domain and Traceability Requirements

- **DR-001**: SourceRecord is immutable; only SourceStream may move its current pointer.
- **DR-002**: Mappings MAY type only fields proven by repeated core use.
- **DR-003**: Source → Evidence → Reality links MUST use opaque identities and shortest
  true relationships; upstream numbers remain references.
- **DR-004**: CLI, Web, API, tools, and workers MUST use shared tenant-scoped services.
- **DR-005**: Inspection MUST distinguish original input from interpreted Evidence and
  Reality.

### Key Entities

- **SourceStream**: Tenant-scoped external identity and current-version pointer.
- **SourceRecord**: Immutable lossless payload version with hash and provenance.
- **ImportJob**: Unique retryable interpretation work and reproducible context.
- **SourceArtifact**: Immutable original bytes plus digest, size, media type, filename,
  storage identity, and lifecycle state.
- **SourceSystem**: Opaque tenant-local description of one external origin.
- **SourceCapability**: Declared source type and intended target for one origin.

## Reality Applicability

- **Source**: SourceStream, SourceRecord, and SourceArtifact say what arrived, not what
  it means operationally.
- **Evidence**: Known interpreters may create Document and DocumentLine.
- **Reality**: Interpreters create only minimal applicable Reality through its owning
  business services.
- **Shortest links**: SourceRecord → prior version; Document → SourceRecord; downstream
  Reality → its closest authoritative Evidence or Reality parent.
- **Stored/derived**: Payloads, versions, artifacts, job outcomes, and explicit mappings
  are stored. Readiness and business projections are derived.
- **Shared boundary**: Every entry point calls tenant-scoped application services;
  mutating tools require confirmation.
- **Web explanation**: Intake and Inspector display original source, interpretation
  state, Evidence, and Reality as distinct stages.

## Success Criteria *(mandatory)*

- **SC-001**: Stored decoded JSON matches every complete accepted fixture with zero
  omitted unknown fields.
- **SC-002**: Repeating identical ingestion 100 times produces exactly one SourceRecord,
  one ImportJob, and one receipt event for that tenant-scoped identity.
- **SC-003**: Every accepted change remains independently inspectable in ordered
  immutable history.
- **SC-004**: Unknown or failed input remains inspectable and retryable without changing
  previously valid Reality.
- **SC-005**: A file larger than the preview can be accepted while returned sample data
  stays bounded and the stored digest matches the original bytes.
- **SC-006**: Every typed profile either rejects missing mappings before confirmation or
  creates records traceable to the artifact.
- **SC-007**: A Shopify order is traceable from complete payload through normalized
  Evidence to every created delivery Commitment.

## Assumptions and Dependencies

- Arrival order is authoritative when no upstream timestamp exists.
- The connector catalog describes mock shells, not connectivity.
- Artifact storage implementations retain one immutable metadata/behavior contract.
- Parsing and interpretation may run after the request that accepted the source.

## Open Questions

The product owner approved this baseline on 2026-08-31. Optional AI mapping, live
connector operation, and richer worker operations remain outside the baseline until
separately specified.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-005 | Verified as-is | `docs/features/source_ingestion.md`; `docs/DATA_MODEL.md` | `services/core.py:enqueue_source`, job processing | `tests/test_source_ingestion.py`; `tests/test_shopify_and_explain.py` | — |
| FR-006–FR-007 | Verified as-is | `docs/features/shopify_ingestion.md` | source ordering and replacement services | `tests/test_shopify_and_explain.py` | — |
| FR-008 | Verified as-is | `docs/features/source_ingestion.md` | ingestion outbox events | `tests/test_source_ingestion.py`; `tests/test_business_events.py` | — |
| FR-009–FR-010 | Verified as-is | Source Ingestion and Web contracts | SourceSystem/Capability services and APIs | `tests/test_integrations.py`; `tests/test_master_data_api.py` | — |
| FR-011–FR-013 | Verified as-is | Source Ingestion and Web contracts | `services/artifacts.py`; source-ingest tool | `tests/test_source_ingestion.py`; `tests/test_integrations.py` | — |
| FR-014 | Verified as-is | `docs/features/source_ingestion.md` | file interpreters and Reality services | `tests/test_import_demo_files.py` | — |
| FR-015 | Verified as-is | `docs/features/shopify_ingestion.md` | Shopify interpreter | `tests/test_shopify_and_explain.py` | — |
| DR-001–DR-005 | Verified as-is | Constitution; Data Model; Web contract | source, tool, interpreter, Inspector boundaries | ingestion, API, and Inspector tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-008 | US1–US2 | Generic ingestion, ordering, retry, and event tests |
| FR-009–FR-010 | US3 | Integration registry and arbitrary-source API tests |
| FR-011–FR-014 | US4 | Artifact, mapping-profile, and import-story tests |
| FR-015 | US5 | Shopify lossless, versioning, and explanation tests |
| DR-001–DR-005 | All stories | Constitution and cross-layer trace review |
