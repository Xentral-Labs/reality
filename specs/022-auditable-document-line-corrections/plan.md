# Implementation Plan: Auditable Manual Document-Line Corrections

**Branch**: `[022-auditable-document-line-corrections]` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)
**Status**: Approved by the owner on 2026-08-31; domain review is encoded in the Constitution Check.
**Language**: English for all repository artifacts and review evidence.

## Summary

Close `006/FR-008` with one tenant-scoped service that accepts the complete intended
line snapshot for a manual Document, reuses manual-entry validation, detects stale edits
from a deterministic snapshot revision, applies additions, updates, and removals in one
transaction, and emits one exact `document.corrected` BusinessEvent. Economically
meaningful changes are rejected when the Document or any line has linked Reality. The
Web/API boundary gains an editable-snapshot read and a `PUT` replacement contract; the
Web register reuses the manual line editor. No migration or new adapter is required.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React for the Web correction surface
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, React/Vite; no new dependency
**Storage**: Existing Document, DocumentLine, Commitment, LedgerEntry, and BusinessEvent tables
**Testing**: pytest service/story/API/isolation tests; Ruff; Web build and localization audit
**Project Type**: Shared Python application core with Web/API and React adapters
**Constraints**: Decimal, UTC, opaque IDs, immutable external Source, strict tenant scope, transactional audit
**Scale/Scope**: One Document per request with the existing API request-size limits; the Spec 016 benchmark remains later

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Manual entry invents no Source; lines remain Evidence; existing Reality links are untouched. | PASS |
| Reality owns operational state | Linked Reality blocks economic changes; no operational Document state is added. | PASS |
| Proven schema only | A digest of existing fields supplies concurrency and retry behavior; no schema change. | PASS |
| Tenant + shared service boundaries | One tenant-explicit service owns normalization, guards, mutation, revision, and audit; API/Web delegate. | PASS |
| Spec/test traceability | Every FR/DR maps to focused executable proof below. | PASS |
| Explainable web behavior | Inspector activity and the correction snapshot expose current Evidence and audit. | PASS |
| Smallest coherent design | Existing models, event type, editor fields, and validation are reused. | PASS |

Post-design re-evaluation: PASS. The snapshot digest is application concurrency
metadata, not stored business truth. No Constitution exception is required.

## Repository Structure and Layer Changes

```text
packages/reality-core/
├── config/command_catalog.yaml
├── src/reality/services/core.py
├── src/reality/web/api.py
└── tests/
    ├── test_document_corrections.py
    ├── test_master_data_api.py
    ├── test_application_catalog.py
    ├── test_operational_fields.py
    └── tenant_isolation/
apps/web/src/
├── api.ts
├── App.tsx
└── localization.tsx
docs/WEB_SPEC.md
docs/features/operational_fields.md
docs/SPEC_COVERAGE_MATRIX.md
specs/006-documents-evidence/spec.md
```

**Files/layers affected**: Evidence service behavior, Web/API transport and UI, catalog
metadata, tests, and baseline documentation. `db/core.py` and Alembic remain unchanged.
CLI, MCP, and chat have no current manual Document correction surface and stay out of
scope; any future surface must reuse the service, with confirmation for chat/agent.

## Design

### Reality flow

```text
Manual input (Source N/A)
  → existing Document + DocumentLine Evidence
  → canonical snapshot + revision
  → validated full replacement
  → unchanged linked Reality, or rejection when economic meaning would diverge
  → document.corrected BusinessEvent
```

External Evidence continues through immutable SourceRecord versioning. `DocumentLine →
Document`, Commitment provenance, and LedgerEntry provenance remain unchanged.

### Correction snapshot and classification

The service returns lines in opaque-ID order and computes a SHA-256 revision from
canonical JSON of every editable stored line field. Decimal strings, nulls, object keys,
and line order are normalized. The digest is neither identity nor business state.

The request carries that revision and every intended line. Existing opaque IDs retain
or update rows; omission removes; absent ID adds a server-identified row. Duplicate,
unknown, foreign, or wrong-Document IDs fail without disclosure. Request order is not
stored. Economic fields are item, quantity, unit, unit price, gross amount,
promised/requested time, and line type; addition/removal is economic. Source-line
reference, SKU, and description are reference/presentation Evidence and may change
after Reality exists. Header values remain governed by the existing header correction;
line correction does not force Document gross to equal the line sum.

### Service and adapter flow

`manual_document_line_snapshot(...)` owns the tenant-safe read, canonical values,
revision, and correctability metadata. `correct_manual_document_lines(...,
expected_revision, lines, actor_context=None)`:

1. Loads and locks the tenant-owned Document and its tenant-owned lines.
2. Normalizes the complete input with a helper shared by manual creation.
3. Returns a no-op when intended and current normalized states, including opaque IDs,
   are identical. A retry that still contains an ID-less addition after its first
   request succeeded is not considered identical and is safely rejected as stale.
4. Otherwise rejects a stale revision.
5. Classifies changes and checks tenant-scoped Commitments linked by Document or line,
   plus Document-linked LedgerEntries; economic changes are rejected when any exist.
6. Applies the full delta, emits one event, commits once, and returns the new snapshot.

The event retains `changed_fields: ["lines"]` and adds exact `line_changes` grouped as
`added`, `removed`, and `changed`, keyed only by opaque line identity. A no-op emits no
event. FastAPI exposes `GET` and `PUT
/api/tenants/{tenant_id}/documents/{document_id}/line-correction`. The Web Documents
register offers “Correct lines” for manual Evidence, loads the snapshot, and displays
stale, external-source, validation, and Reality-boundary outcomes. Business rules remain
server-side.

### Data and migration impact

No schema, migration, or backfill. Retained line IDs remain stable. Existing
BusinessEvent storage holds the audit delta. Revision is derived on demand.

### Failure, security, and tenant behavior

- Every Document, line, item, Commitment, and LedgerEntry query enforces tenant scope.
- Mutation locks the Document/current line set; the revision rejects earlier divergent reads.
- Validation completes before mutation; event and line delta share one transaction.
- Identical current-state retries are no-ops. Stale divergent requests, including a
  lost-response retry with an already-created ID-less addition, fail and instruct reload;
  neither path creates a duplicate effective correction or event.
- External Evidence points to source-version correction.
- Linked Reality blocks economic changes without mutation or disclosure.
- No chat/agent mutation is added, so its confirmation invariant remains unchanged.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-004 | PostgreSQL service/story | add/update/remove snapshot, stable IDs, exact audit including optional actor context, invalid-input rollback, and injected event-emission rollback | No service exists. |
| FR-005 | service/API | external correction rejects with source-version guidance | No endpoint exists. |
| FR-006–FR-007 | PostgreSQL story | Document/line Commitment and Document LedgerEntry block economic changes; reference-only edit succeeds | No line guard exists. |
| FR-008 | service/API | full snapshot semantics and duplicate/foreign/unknown ID rejection | No contract exists. |
| FR-009–FR-010 | service/API | stale divergent and lost-addition retries reject; identical current-state retry creates no second event | No concurrency behavior exists. |
| FR-011–FR-012 | catalog/API/UI | Web/API delegate; catalog updated; Web localization-contract test plus recorded manual parity check; no new chat/agent path | Catalog covers header only. |
| FR-013 | API/UI/Inspector | current lines, revision, correctability, and event visible | Correction metadata is absent. |
| DR-001–DR-002 | service/model | Source remains N/A; Reality FKs and retained IDs unchanged | No correction proof. |
| DR-003–DR-004 | isolation/API | foreign IDs disclose nothing; human references cannot target rows | Operation is absent. |
| DR-005 | schema/policy | no migration/operational field; state remains derived | Gap remains open. |

Write focused tests before behavior, then run API/isolation/catalog tests, Ruff, the
full backend suite, Web build, and EN/DE/NL/ES localization audit. Close `006/FR-008`
and the coverage-matrix gap only after all proof is green.

## Rollout and Rollback

Ship service, API, Web, translations, catalog, and tests in one repository release. The
endpoint is additive; header `PATCH` and source-version correction remain compatible.
A code revert removes the capability without rewriting accepted Evidence or truthful
historical events. No deployment order, feature flag, or data rollback is needed.

## Review Risks

- Mixed Document/line/Reality queries must never omit tenant predicates.
- Only opaque IDs may retain or target lines; SKU and line references are not identity.
- Revision serialization must be stable across Decimal values and query ordering.
- All validation must precede mutation to prevent partial Evidence.
- Both Document- and line-level Commitment links must be checked.
- Document gross must not be silently forced to the line sum.
- Web must refresh on conflict and never infer correctability from displayed counts.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
