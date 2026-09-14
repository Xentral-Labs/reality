# Implementation Plan: Auditable Movement Corrections

**Branch**: `[023-auditable-movement-corrections]` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)
**Status**: Approved by the product owner on 2026-08-31; analysis remediation approved on 2026-08-31
**Language**: English for all repository artifacts and review evidence.

## Summary

Close `009/FR-009` with one tenant-scoped correction service that row-locks an immutable
original Movement, appends an exact inverse, optionally appends a normally validated
replacement, records one explicit correction relation and one `movement.corrected`
event, and commits once. A small `MovementCorrection` table provides durable chain,
reason, actor, and canonical retry identity without adding mutable status to Movement.
Stock continues to derive from Movement locations; fulfilment, identity location,
exceptions, registers, and Inspector become correction-aware. API/Web provide server-
calculated preview and confirmation; CLI and agent tools reuse the same service and
their existing confirmation boundaries.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL with existing Movement/BusinessEvent records plus one tenant-scoped correction relation
**Testing**: pytest service/story/API/CLI/tool/PostgreSQL isolation tests; Ruff; migration checks; Web build/i18n/manual acceptance
**Project Type**: shared Python application core with CLI/API/MCP/Chat adapters and React Web product
**Constraints**: Positive Decimal quantities; UTC; opaque IDs; immutable Movements and SourceRecords; strict tenant scope; one transaction
**Scale/Scope**: One original plus exact compensation and at most one replacement per correction; no bulk or benchmark scope

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Original direct SourceRecord stays immutable; correction and replacement carry only their own direct evidence while explicit Movement links preserve the chain. | PASS |
| Reality owns operational state | New Movements remain physical authority; stock, fulfilment, correction role, and identity location are derived without Document status or mutable Movement flags. | PASS |
| Proven schema only | One relation is required because validation, uniqueness, retry, derivation, filtering, and explanation all repeatedly act on chain, reason, and fingerprint. | PASS |
| Tenant + shared service boundaries | One tenant-explicit service owns preview, validation, append, relation, event, and commit; API/Web/CLI/tool/MCP delegate. | PASS |
| Spec/test traceability | Every FR/DR maps to focused executable proof below; tests precede implementation. | PASS |
| Explainable web behavior | Register badges and Inspector traverse every chain member, event, reason, effect, actor, and direct SourceRecord. | PASS |
| Smallest coherent design | Existing Movement shape, validators, event system, proposal confirmation, and projections are reused; only one table and one event type are added. | PASS |

Post-design re-evaluation: PASS. The design introduces no Constitution exception.

## Repository Structure and Layer Changes

```text
packages/reality-core/
├── migrations/versions/0028_movement_corrections.py
├── config/
│   ├── business_event_catalog.yaml
│   ├── command_catalog.yaml
│   └── tenant_isolation_catalog.yaml
├── src/reality/
│   ├── db/core.py
│   ├── services/{core,exceptions,projections}.py
│   ├── tools/application.py
│   ├── mcp/catalog.py
│   ├── cli/app.py
│   └── web/{api,read_models}.py
└── tests/
    ├── test_movement_corrections.py
    ├── test_inventory_and_fulfillment.py
    ├── test_inventory_tracking_reservations.py
    ├── test_master_data_api.py
    ├── test_application_tools.py
    ├── test_ai_mcp.py
    ├── test_business_events.py
    ├── test_application_catalog.py
    ├── test_migrations.py
    └── tenant_isolation/
apps/web/src/{App.tsx,api.ts,localization.tsx}
docs/{ARCHITECTURE.md,DATA_MODEL.md,WEB_SPEC.md,CLI_SPEC.md,SPEC_COVERAGE_MATRIX.md}
docs/features/movements.md
specs/009-inventory-execution/spec.md
```

**Files/layers affected**: Persistence and migration define the correction relation;
shared services own all business behavior; adapters translate only; read models and Web
explain the result; catalogs, tests, and durable contracts close the baseline gap.

## Design

### Reality flow

```text
optional immutable SourceRecord evidence
  → original immutable Movement Reality
  → MovementCorrection (reason, actor, retry identity)
      ├── exact compensating Movement
      └── optional normally validated replacement Movement
  → derived stock / fulfilment / identity / exceptions / projections
  → movement.corrected BusinessEvent
```

`MovementCorrection` holds direct opaque FKs to its three Movement roles and no
Document/DocumentLine/Commitment/SourceRecord link. The compensation uses explicit type
`correction`, swaps the original locations, and copies only item, positive quantity, and
tracking dimensions needed to reverse the physical effect. Its fulfilment contribution
derives through the relation to the original Commitment rather than a duplicated
`commitment_id`. It does not copy the original SourceRecord because that record is not
direct evidence for the correction. Replacement accepts its own normal type, optional
Commitment/direct SourceRecord, and may later be corrected as a new original.

### Service and adapter flow

Refactor normal Movement validation/insertion into non-committing internal helpers while
preserving `record_movement(...)` as the public committing behavior. Introduce:

- `movement_correction_snapshot(...)`: tenant-safe chain/status, canonical revision,
  eligibility, and dependent-history guidance.
- `preview_movement_correction(...)`: uses the same normalized builder/validators to
  return exact compensation, optional replacement, and net physical/fulfilment effects
  without writes.
- `correct_movement(...)`: locks the original, compares revision/fingerprint, validates
  the complete atomic outcome, appends both Movement rows as applicable, creates the
  correction relation/event, reconciles affected Commitment statuses, and commits once.

The canonical fingerprint covers tenant, original opaque ID, trimmed reason, and
canonical replacement fields including Decimal/UTC normalization. Actor context is
audit metadata rather than correction intent and is deliberately excluded, so the same
semantic request can replay safely through another authenticated surface.
After locking, an existing equal fingerprint returns the existing result; an existing
different fingerprint raises conflict. A database uniqueness constraint is the race
backstop.

FastAPI exposes snapshot, preview, and execute under
`/api/tenants/{tenant_id}/movements/{movement_id}/correction`. Web renders the server
preview and requires a distinct confirmation. CLI prints the same preview and asks for
confirmation (`--yes` remains explicit automation). The mutating application tool uses
the existing ChangeProposal → human approval → execution lifecycle; MCP/Chat can propose
but cannot bypass approval.

### Data and migration impact

Migration `0028_movement_corrections` adds one `movement_correction` business table:
opaque `id`, indexed `tenant_id`, unique `original_movement_id`, unique
`compensating_movement_id`, nullable unique `replacement_movement_id`, required trimmed
`reason`, `corrected_at` UTC, serialized bounded `actor_context`, and unique canonical
`request_fingerprint` within the tenant. Checks require distinct role IDs. Tenant-aware
service queries validate every FK owner; no existing Movement is backfilled and all
existing rows derive role `normal`.

Correction role/status are derived from the relation. Compensation uses type
`correction`, retains positive quantity, swaps endpoints, and follows inverse-specific
validation rather than normal type/location-shape rules. Shared fulfilment expressions
subtract the linked original's applicable contribution through the correction relation;
normal/replacement Movements contribute positively. Directional stock already cancels
naturally. Identity current-location logic is changed from newest-row inference to net
physical legs so historical replacement timestamps cannot become false authority.
Compensation rows are excluded from `unexplained_movement`; their explanation is the
correction relation.

### Failure, security, and tenant behavior

- Original selection and every chain/reference traversal use tenant predicates; foreign
  IDs behave as not found.
- A compensation cannot be corrected; an already-corrected original accepts only an
  identical retry; a replacement may start its own later chain.
- Inverse outbound legs require currently available stock/identity at the affected
  location. Later dependent history blocks correction with newest-to-oldest guidance.
- Compensation applies exact-inverse tenant, item, positive quantity, eligible-location,
  stock-feasibility, and tracking rules without pretending to be a normal Movement type.
- Replacement applies normal location, stock, hold, Commitment, lot, serial, handling-
  unit, quantity, and source validation against the post-compensation state.
- Validation completes before durable effects; Movement rows, relation, Commitment
  reconciliation, and exactly one `movement.corrected` event share one transaction.
- No historical Reservation is recreated, deleted, released, or reactivated.
- Event payload contains opaque role IDs, reason, actor context when supplied, and net
  effects. It invalidates the same seven consumers as `movement.recorded`.
- Stale preview revision and divergent/concurrent attempts map to conflict with refresh
  guidance. Event or relation failure rolls back everything.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003 | PostgreSQL service/story | every Movement type voided/replaced; original immutable; exact inverse and intended net result | No correction service or relation exists. |
| FR-004–FR-005 | model/service/Inspector | unique opaque chain, required reason, UTC time, actor context, role traversal | No durable correction context exists. |
| FR-006 | PostgreSQL failure injection | compensation/replacement/relation/event rollback together | Current `record_movement` commits each call. |
| FR-007–FR-008 | service/concurrency/API | compensation rejection, replacement chain, identical retry, divergent/stale/concurrent rejection | No lock, fingerprint, or uniqueness boundary exists. |
| FR-009–FR-010 | business story | normal replacement invariants and later-dependent stock/identity rejection | General adjustment does not validate an atomic correction. |
| FR-011–FR-012 | derived-state/story | net stock, fulfilment/status, identity, projections, exceptions; Reservation history unchanged | Fulfilment and identity derivations are not correction-aware. |
| FR-013–FR-014 | source/isolation/PostgreSQL | immutable original source, optional replacement source, two-tenant non-disclosure for every FK | No correction path is classified. |
| FR-015 | API/CLI/tool/MCP/Web | shared preview; CLI/Web confirmation; proposal-before-effect for Chat/MCP | Only direct Movement recording exists. |
| FR-016 | read model/UI/Inspector | status badges and full chain/effect/source/event explanation from every member | Correction metadata is absent. |
| FR-017 | event/catalog/projection | exactly one corrected event, payload, invalidations, retry and rollback counts | Event type is absent. |
| DR-001–DR-005 | schema/policy/isolation | append-only authority, shortest links, schema justification, shared tenant boundary | `009/FR-009` remains a documented gap. |

Write the focused failing service/model tests first, followed by derived-state,
isolation, event, adapter, and UI-contract tests. Run migration upgrade/downgrade/upgrade,
Ruff, focused PostgreSQL stories, full backend suite, Spec policy, Web build, EN/DE/NL/ES
audit/tests, and recorded manual preview/confirmation/Inspector parity before closure.

## Rollout and Rollback

Deploy the additive migration before application code. Existing Movements remain normal
and all prior recording APIs remain compatible. Monitor correction conflicts, blocked
dependent-history attempts, and correction-event projection failures.

Code rollback is safe before any correction is accepted. After production corrections
exist, do not drop the relation: roll back application behavior while retaining the table
or export/retain correction context, because removing it would make valid compensating
Movements indistinguishable from ordinary execution. Alembic downgrade is therefore for
empty/non-production correction data only and must refuse or be operationally guarded
when correction rows exist.

## Review Risks

- Fulfilment queries currently sum positive Movement types; every duplicated read-model
  expression must move to one correction-aware semantic.
- Copying the original Commitment or SourceRecord onto compensation would duplicate or
  falsely claim direct provenance; both derive through the original correction link.
- Later execution can make an inverse outbound leg physically impossible; validation
  must not permit negative stock or identity ambiguity.
- Commitment status is stored while quantity is derived; all affected old/new
  Commitments must be reconciled without reopening cancelled Commitments.
- Replacement `occurred_at` may be historical; identity current state cannot rely on
  newest business timestamp alone.
- Tool proposal approval and Web/CLI confirmation must not drift from the preview that
  is revalidated under the execution lock.
- Migration downgrade after accepted corrections would erase indispensable semantics.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
