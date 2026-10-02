# Implementation Plan: Consolidate Receipt Manifest Membership

**Branch**: Existing shared workspace; no branch switch | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Language**: English.

## Summary

Replace five receipt-manifest member tables with `cost_manifest_member`, preserving exact original logical columns through five filtered writable views. Use five true typed target columns, family-qualified identity and original family-specific uniqueness. A narrow insert-routing trigger supplies the hidden family discriminator; ordinary updates/deletes remain native view operations. Four fewer physical tables; no change to calculation, admission, history or confirmation.

## Technical Context

Python 3.12+, SQLAlchemy 2, Alembic and PostgreSQL only. Existing schema-view compiler, metadata dependencies, Alembic exclusions and physical-only tenant counting/purge are reused. pytest uses an owned isolated PostgreSQL instance, never SQLite or live user rows. Decimal amounts and UTC timestamps in unrelated authorities remain untouched. Scope: one physical store, five original logical resources, one frozen reversible migration.

## Constitution Check

| Principle | Evidence in this plan | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Inputs and authority rows unchanged; original selected identities retained | PASS |
| Reality owns operational state | No Document or operational state change | PASS |
| Proven schema only | Same five membership grains and targets; discriminator only distinguishes existing row namespaces | PASS |
| Tenant + shared service boundaries | Original services; composite parent/target FKs; tenant predicate preserved | PASS |
| Spec/test traceability | All 10 FR/3 DR mapped below and in tasks; tests before runtime changes | PASS |
| Explainable web behavior | Original record detail and child paging remain; no UI logic | PASS |
| Received values not recomputed | Exact member parity and unrelated authority snapshots; digest format unchanged | PASS |
| Smallest coherent design | One bounded typed union; insert routing needed for exact old SQL column contract; no registry/JSON authority | PASS |

Pre- and post-design checks pass; no constitutional exception or product clarification remains. Actual migration/view tests remain implementation prerequisites, not claims of completed proof.

## Repository Structure and Layer Changes

- Add `packages/reality-core/src/reality/db/cost_manifest_members.py`: typed physical table, original view registration, metadata dependencies and PostgreSQL insert routing DDL.
- Update `packages/reality-core/src/reality/db/core.py`: import after original costing models, before shared FK index registration.
- Add `packages/reality-core/migrations/versions/0120_manifest_members.py`, provisionally parent `0119_finance_references`. Recheck concurrent numbering before creation; never create a second branch/head silently.
- Add `packages/reality-core/tests/test_cost_manifest_members.py` and `test_cost_manifest_member_migration.py`.
- Reuse existing `db/schema_views.py`, migration `env.py`, tenant purge/count and `services/costing.py` / `cost_records.py` unchanged unless a narrowly demonstrated compatibility defect requires adjustment.
- Review explicit reporting graph declarations in `tests/test_reporting_graph_coverage.py`; place the physical store in the same reporting disposition as original members, never weaken generic coverage assertions.
- Update `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/SPEC_COVERAGE_MATRIX.md`, costing assessment and this feature's verification evidence after acceptance.
- Domain → service → tool → adapter order is preserved by leaving all four business layers unchanged and modifying their persistence boundary only. No new command/tool/catalog resource or frontend behavior is planned.

## Design

### Reality flow

The retained manifest points to received/admitted receipt/component/correction basis or retained attribution/replacement decision. Shared membership storage preserves those shortest relationships and original family names. No Fact, source payload or recalculated amount becomes another authority.

### Service and adapter flow

Existing manifest construction, member loading/hash verification, historical receipt joins and retained record inspection use their original mapped classes. Exact-column views preserve SQL and ORM contracts. The routing trigger handles inserts only, supplies family internally, and returns the stored original columns. It must preserve RETURNING, row count and ORM identity semantics; direct UPDATE/DELETE retain original support. Services retain owner checks, stale-confirmation rules and error codes.

### Data and migration impact

See [data-model.md](data-model.md). Snapshot predecessor DDL/keys/indexes and dependency inventory from an isolated PostgreSQL database at revision 0111. Current metadata shows no incoming physical FK to the five members; verify that against database constraints and view/trigger dependencies. Lock old tables, copy exact columns, prove per-family bidirectional EXCEPT equality, replace with views and insert routing in one transaction. Preserve hash input keys and IDs. Downgrade captures current rows, drops only owned routing/views, restores frozen original DDL/indexes, copies/parity-checks every family and drops shared storage. No CASCADE, live model import, silent repair or live execution.

### Failure, security, and tenant behavior

Physical checks admit exactly one matching target column per family; composite FKs prevent cross-tenant parent/target references. Equal IDs in different families/tenants are valid. Filtered views and CHECK OPTION preserve logical family. Trigger must use invoker rights, schema-qualified fixed relations and allowlisted family branches; no SECURITY DEFINER or untrusted dynamic identifiers. Existing transaction boundaries remain. Do not import census/captured immutability guards into receipt membership. Metadata-only partial create/drop needs explicit view/store dependencies and insert-function lifecycle cleanup.

## Test Strategy and Traceability

| Requirements | Test/evidence | Expected initial failure |
| --- | --- | --- |
| FR-001/002/003/004, DR-002/003 | `test_cost_manifest_members.py`: five exact logical shapes, one store, collisions, all targets, duplicates, wrong tenant/shape, ORM and SQL INSERT/UPDATE/DELETE RETURNING | Missing shared store and routing/views |
| FR-005/006/007, DR-001/003 | `test_costing_services.py`, `test_costing_tools.py`, `test_cost_records.py`; member loss, late cost/replacement/correction, unknown amounts, permissions and no read flush | Existing regressions must remain green; new physical-specific history proof fails before consolidation |
| FR-008/010, DR-001 | `test_cost_manifest_member_migration.py`: populated all-family/tenant collision, exact original DDL and all-authority snapshots, post-upgrade writes, downgrade/re-upgrade, abort proof | New revision absent |
| FR-009 | `test_cost_manifest_members.py`: metadata lifecycle, original view columns, FK indexes, Alembic exclusion, count/purge once; schema/reporting tests | Physical/logical lifecycle not registered |
| SC-001–004 | Focused plus full required gates, exact physical -4, reviewed source manifest and `verification.md` | Not accepted until all required evidence passes |

## Rollout and Rollback

Prepare/rehearse only in isolated owned PostgreSQL. Preserve supported old interfaces through the whole migration chain. Keep original DDL frozen in migration, test upgrades through 0109/0110/0111/0112 and pin predecessor fixtures when appropriate. Full backend suite and serial existing performance benchmark must pass unchanged. Run lint/spec, docs generation/reproducibility/build and web build. No live migration, deployment, branch switch, staging or commit is included.

## Review Risks

- Exact view columns conflict with hidden family defaults: use explicit insert routing rather than adding an unnoticed public column.
- Trigger RETURNING, generated member IDs, ORM flush row counts and supported direct updates/deletes require real PostgreSQL proof.
- Family routing must not alter historical digest input or merge original ID namespaces.
- Frozen rollback DDL/indexes must match actual predecessor schema, including 0088 key changes.
- Shared-workspace changes and constrained Docker capacity require an owned isolated database and immutable source evidence; do not touch another task's server or index.

## Complexity Tracking

No Constitution exceptions. The insert trigger is a bounded adapter for exact old SQL columns, not a general mutation framework. Native views with an exposed discriminator and untyped JSON/polymorphic target storage were rejected; details in [research.md](research.md).
