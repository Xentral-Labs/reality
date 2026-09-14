# Implementation Plan: Complete Operational Exception Coverage

**Branch**: `[020-exception-class-coverage]` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Status**: Approved by the owner on 2026-08-31.

**Language**: English for all repository artifacts and review evidence.

## Summary

Close `013/FR-005` with one source-controlled exception taxonomy containing five
visible classes and the `insufficient_reservation` cause, one typed tenant-scoped
derivation/explanation service, and focused PostgreSQL stories for every condition.
Replace the currently divergent Core and Web rules with that shared service, preserve
the existing list payload fields for UI compatibility, and add class, cause, identity,
causal values, and trace information. Rebuild the existing exception projection from
the same service. Add no table, migration, Document state, or mutable exception record.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML, FastAPI, existing application
tools and MCP boundaries; no new dependency
**Storage**: Existing PostgreSQL records plus one source-controlled YAML taxonomy;
exceptions remain derived and projection rows remain disposable
**Testing**: Focused PostgreSQL business stories, taxonomy/registry drift tests,
projection parity, tool/API/MCP boundary tests, complete backend suite and Ruff
**Project Type**: Backend application services with Web/API, Chat, tool, and MCP
adapters; existing frontend consumes a backward-compatible list/Inspector contract
**Constraints**: Decimal amounts/quantities, UTC comparison, opaque IDs, immutable
SourceRecords, strict tenant scope, no schema, no adapter rules, no exception lifecycle
**Scale/Scope**: Five visible initial classes, one nested cause, one shared list and
explain path, one existing materialized projection, representative adapters

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Each exception starts from its authoritative Commitment, ImportJob/SourceRecord, Movement, or LedgerEntry and follows existing shortest links; raw Source remains immutable. | PASS |
| Reality owns operational state | Exceptions remain derived observations; Documents and projection rows receive no operational status or correction state. | PASS |
| Proven schema only | Existing fields are sufficient; the taxonomy is trusted metadata and no table, field, FK, or migration is added. | PASS |
| Tenant + shared service boundaries | One tenant-explicit service owns list/explain behavior; projection, Web, tools, Chat, and MCP consume it without alternative rules. | PASS |
| Spec/test traceability | Every visible class and cause has positive, negative, tenant, explain, and clearing-or-explicit-no-remediation proof before baseline closure. | PASS |
| Explainable web behavior | The shared explain result provides causal values and Source/Evidence/Reality trail while preserving current UI-compatible fields. | PASS |
| Smallest coherent design | Existing records, remediation services, projection machinery, and adapters are reused; persisted tickets and a new rule framework are rejected. | PASS |

Post-design re-evaluation: PASS. The taxonomy, typed derived value, shared service, and
test fixtures introduce no Constitution exception.

## Repository Structure and Layer Changes

```text
packages/reality-core/
├── config/operational_exception_catalog.yaml       # five classes + one cause authority
├── src/reality/
│   ├── catalogs.py                                 # taxonomy/registry/evidence validation
│   ├── services/
│   │   ├── exceptions.py                           # typed derivation + explanation authority
│   │   ├── core.py                                 # compatibility wrapper + fallback Chat caller
│   │   └── projections.py                          # materialize shared exception rows
│   ├── tools/application.py                        # shared list/explain service use
│   └── web/
│       ├── read_models.py                          # paginate canonical derived rows
│       └── api.py                                  # generic shared exception Inspector
└── tests/
    ├── operational_exceptions/
    │   ├── conftest.py                             # deterministic multi-class/two-tenant story
    │   ├── test_coverage.py                        # taxonomy/registry/evidence drift
    │   ├── test_derivation.py                      # class/cause appearance and clearing
    │   └── test_explanation.py                     # trace, stale, and foreign behavior
    ├── test_materialized_projections.py            # projection parity/rebuild
    ├── test_application_tools.py                   # list/explain boundary
    ├── test_master_data_api.py                     # Web/API parity and Inspector
    ├── test_ai_mcp.py                              # MCP parity/non-disclosure
    └── test_spec_policy.py                         # single baseline-gap closure

docs/features/operational_exceptions.md             # canonical taxonomy semantics
specs/013-explain-projections/spec.md               # close FR-005 last
docs/SPEC_COVERAGE_MATRIX.md                        # remove only 013/FR-005 last
specs/020-exception-class-coverage/                  # design and evidence
```

**Files/layers affected**: Derived metadata, service/query behavior, projection payload,
transport mapping, tests, and baseline evidence. The frontend remains unchanged because
`severity`, `title`, `id`, and `impact` stay present. No model, migration, ingestion
payload, or new mutation path is planned.

## Design

### Reality flow

```text
Customer Commitment + Reservation/Shipment
  → outgoing_commitment_at_risk(cause=insufficient_reservation)

Supplier Commitment + Receipt
  → overdue_incoming_supplier_commitment

ImportJob → immutable SourceRecord
  → source_interpretation_failure

Movement → optional Commitment or SourceRecord
  → unexplained_movement

Payment control LedgerEntry → SettlementAllocation → invoice LedgerEntry/Document
  → unmatched_financial_event
```

The derived identity is `exc__{class_id}__{authoritative_record_id}`. Human numbers and
external IDs are display context only. Explanation re-derives the current queue and
finds this identity; resolved, stale, unknown, and foreign identities therefore share
one non-disclosing not-found outcome.

### Taxonomy and derivation registry

`packages/reality-core/config/operational_exception_catalog.yaml` is evidence metadata, not runtime
business state. It declares stable order, five visible class IDs, the nested
`insufficient_reservation` cause, labels, default severity, authoritative record type,
derivation key, governing requirements, and named evidence. A validator cross-checks
the catalog against the explicit derivation registry and test symbols. Missing, stale,
duplicate, unproven, or invalid class/cause entries fail in stable taxonomy order.

The derivation registry is deliberately closed and explicit. Adding a derivator without
updating the taxonomy, documentation, and evidence is a test failure rather than an
implicit new product condition.

### Class semantics

| Visible class | Exact derived predicate | Authority and clearing |
|---|---|---|
| `outgoing_commitment_at_risk` | Open customer-delivery Commitment with active Reservation quantity below remaining unfulfilled quantity | Commitment; cause=`insufficient_reservation`; clear through reserve, shipment fulfillment, or cancellation |
| `overdue_incoming_supplier_commitment` | Open supplier-delivery Commitment with non-null `due_at < as_of` and remaining receipt quantity greater than zero | Commitment; clear through receipt fulfillment or cancellation; missing/equal due time excluded |
| `source_interpretation_failure` | Tenant ImportJob currently has `status=failed` | ImportJob with direct SourceRecord; clear when existing retry/process succeeds; empty error gets safe fallback text |
| `unexplained_movement` | Shipment, receipt, or return has neither Commitment nor SourceRecord | Movement; opening stock and transfer are intrinsically contextual; adjustment is excluded because the owning service requires an audited reason; no retroactive mutation is introduced |
| `unmatched_financial_event` | Payment-side AR/AP control LedgerEntry has positive amount remaining after tenant-scoped SettlementAllocations | Control LedgerEntry; partial allocation reports exact remainder; clear through existing allocation service |

`operational_exceptions(session, tenant_id, *, as_of=None)` uses a supplied UTC instant
for deterministic overdue proof and current UTC by default. It returns immutable typed
derived values while adapters receive JSON-compatible dictionaries.

### Shared list and explanation contract

Every list row retains `severity`, `title`, `id`, and `impact`, and adds `class_id`,
`cause_ids`, `record_type`, `record_id`, `causal_values`, and compact `trace`. The shared
explain service hydrates the same current identity with exact authoritative values,
explicit missing Evidence/Source stages, events where available, and raw Source payload
only when a Source link exists.

`web/read_models.py` stops deriving SQL exception rules and only paginates the shared
ordered result. `services/projections.py` materializes the same result. Application
tools call the shared service for list and explain; MCP remains a thin tool adapter.
The Web Inspector delegates exception explanation to the shared service rather than
inferring record kind from an encoded commitment/import ID. Fallback Chat renders the
same rows without adding classification logic.

### Data and migration impact

No business data or schema change. Existing ImportJob status/error, Commitment due/status,
Reservation and Movement quantities/links, payment control entries, and allocations are
sufficient. The YAML taxonomy is versioned trusted configuration. Existing projection
rows are rebuilt from the new payload and may be safely discarded on rollback.

### Failure, security, and tenant behavior

- Every derivator starts with tenant-scoped queries; linked records are joined/scoped by
  the same tenant.
- Explanation first re-derives current tenant rows; it never accepts record type or ID
  from the caller as proof of authority.
- No exception is acknowledged, closed, edited, or deleted. Clearing changes only the
  authoritative cause through existing services.
- `unexplained_movement` intentionally has no retroactive clearing action in this scope:
  Movement is append-only and the feature will not invent a weak link or schema field.
- Clock comparison is UTC and strict (`due_at < as_of`), making equality non-overdue.
- Fully allocated payments, non-payment cash postings, missing supplier due times,
  ordinary stock openings, transfers, and reason-validated adjustments are excluded.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-002 | catalog/unit | `test_coverage.py` validates five classes, cause, metadata, evidence, and order | No taxonomy or validator exists. |
| FR-003–FR-004 | PostgreSQL story | outgoing risk positive/negative/partial/clear story with cause and no duplicate | Current tuple has no stable class/cause contract. |
| FR-005 | PostgreSQL story | overdue supplier before/equal/after/missing due time and partial/full receipt | No supplier exception is derived. |
| FR-006 | PostgreSQL story | failed import, Source trace, safe empty error, retry clearing | Core exception service omits ImportJob failures. |
| FR-007 | PostgreSQL story | unlinked shipment/receipt/return versus linked, opening, transfer, adjustment | No Movement exception is derived. |
| FR-008 | PostgreSQL story | unmatched, partial, and fully allocated customer/supplier payments | No finance exception is derived. |
| FR-009–FR-012 | service/story | `test_explanation.py` asserts identity, causal values, trace, stale/foreign NotFound, and clearing | Current explain returns only a projection row. |
| FR-010 | adapter/integration | projection, tool, API/Inspector, MCP, and fallback routing parity | Web currently duplicates exception rules. |
| FR-013 | catalog/unit | controlled missing/stale/duplicate/unproven registry fixtures | No drift gate exists. |
| FR-014 | policy/review | baseline and matrix regression preserves every unrelated gap | `013/FR-005` remains documented. |
| DR-001–DR-006 | story/review | Source/Evidence/Reality trace, tenant isolation, service boundary, no-schema diff | No single cross-class proof joins these invariants. |

The multi-class fixture uses two populated tenants with overlapping human identifiers,
different opaque IDs, asymmetric quantities/amounts, and controlled UTC time. Tests are
written before the shared service and observed failing by class where practical.

## Rollout and Rollback

Ship as one derived-service and evidence change. No deployment ordering or backfill is
required. Existing API/UI list fields remain compatible; projection refresh replaces
disposable rows. Close `013/FR-005` only after focused, adapter, policy, and full-suite
gates pass. A revert restores the previous derivation and gap without data reversal.

## Review Risks

- The umbrella risk entry must not also emit an insufficient-reservation row.
- Adapter compatibility can hide divergence unless Web SQL rules are removed entirely.
- Clock-dependent supplier tests can flake unless `as_of` is controlled.
- Import failures must not be limited to one error string such as `Unknown SKU`.
- Movement classification must not flag ordinary openings, transfers, or audited
  adjustments, and must not pretend an append-only Movement can be retroactively fixed.
- Payment matching must use the control LedgerEntry and exact unallocated remainder,
  not payment number, Document status, or cash amount alone.
- Projection JSON must preserve Decimal and UTC serialization deterministically.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
