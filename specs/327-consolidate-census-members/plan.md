# Implementation Plan: Consolidate Census Membership

**Branch**: Existing shared workspace; no branch switch | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Language**: English.
**Status**: Foreign-currency main integration revalidation pending.

## Summary

Replace four census member tables with one private typed store and four original
exact-column filtered views. Two stored generated family identity aliases and ordinary
unique keys retain both incoming real FKs without adding consumer columns. Physical
member admission/immutability guard preserves original history protection. Three-table
net saving; no current-source reconstruction, financial approval or purge bypass.

## Technical Context

Python 3.12+, SQLAlchemy 2 Table/Computed/ForeignKeyConstraint, Alembic and PostgreSQL.
Use explicit stored generation compatible with the existing PostgreSQL baseline; no
new package or infrastructure. pytest uses isolated PostgreSQL, not SQLite/live rows.
Scope is one bounded storage module, one explicit existing consumer FK retarget, four
views and one frozen reversible migration. Existing shared services/tools/adapters and
Web behavior remain unchanged. Unknowns resolved in [research.md](research.md).

## Constitution Check

| Principle | Evidence in this plan | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Exact captured observations and original typed subjects preserved | PASS |
| Reality owns operational state | No document operational fields or state reconstruction | PASS |
| Proven schema only | Same membership grain; two private aliases required by existing typed incoming FKs | PASS |
| Tenant + shared service boundaries | Original services, eight tenant-qualified store FKs and typed consumer FK | PASS |
| Spec/test traceability | All 11 FR/3 DR mapped below; red-first and populated proof precede code | PASS |
| Explainable web behavior | Original inspection and traces retained; no Web rule or flow change | PASS |
| Received values not recomputed | Observations/context/hashes copied verbatim; aliases only expose existing ID | PASS |
| Smallest coherent design | One typed union; ordinary aliases avoid a registry and public fields | PASS |

Pre- and post-design checks PASS. Owner selected scope and planning; independent review
accepted the bounded design. No Constitution exception. Planning is not runtime acceptance.

## Repository Structure and Layer Changes

- Add `packages/reality-core/src/reality/db/cost_census_members.py`: private Table,
  stored aliases, shape/keys/FKs/indexes, original view registration, INSERT routing,
  physical guard and store-owned DDL lifecycle hooks.
- Update `db/core.py` import after original census/company models, before shared
  `index_foreign_keys`. Do not compile frozen DDL before core registration completes.
- Update `db/company_generations.py`: explicit composite FK from existing
  `(tenant_id,census_line_id)` to store line alias. Do not mutate ORM private internals.
- Add `migrations/versions/0121_census_members.py` provisionally parent 0118. Recheck
  head and capture actual predecessor DDL/dependencies before writing frozen constants.
- Add `tests/test_cost_census_members.py` and `test_cost_census_member_migration.py`;
  adapt explicit current-schema assumptions and test-only trigger corruption target in
  `test_cost_census_storage.py` / `test_cost_census_migration.py` without weakening tests.
- Reuse `db/schema_views.py`, `migrations/env.py`, count/purge helpers and
  `services/cost_census_storage.py`, `cost_captured_basis.py`, `company_generations.py`
  unchanged unless a demonstrated bounded compatibility defect requires repair.
- Update explicit schema-index, cost-record storage aliases and reporting graph
  disposition in their existing tests; never weaken generic catalog coverage.
- After acceptance update DATA_MODEL, ARCHITECTURE, SPEC_COVERAGE_MATRIX, receipt-costing
  storage explanation, audit/overview and this feature's verification/evidence.
- Domain → services → tools → adapters preserved: persistence-only change; no business
  algorithms, transport calls, command catalog or client behavior added.

## Design

### Reality flow

Census observes original Movement/Document/DocumentLine/SourceRecord plus optional
interpretation outcome. Retain exact JSON, digest and capture context. The line references
its captured document; downstream company input references the original captured line.
See [data-model.md](data-model.md) and [contract](contracts/membership.md).

### Service and adapter flow

Original mapped classes read/write exact logical rows. Fixed-family INSERT-only
invoker-rights routing writes the store, returns original stored fields and always
reaches the physical guard. Native UPDATE/DELETE remains refused. Same capture hashes,
chunking, cursor binding and replay semantics; original physical-only lifecycle helpers.

### Data and migration impact

Store PK includes tenant/family/id. Closed explicit shape, four typed subjects, optional
source outcome, line-only document link, original per-family selection uniqueness.
Generated document and line identity aliases have ordinary NULL-distinct unique keys;
real FKs enforce original incoming type and same-census requirements. Eight store FKs
and one retargeted consumer FK need unconditional complete-key lookup indexes.

Freeze actual isolated predecessor DDL/keys/index names and all function/trigger/view
SQL dependencies at 0118. Upgrade ACCESS EXCLUSIVE locks header/four members/consumer
in one deterministic order; copy unguarded document-first, parity both directions;
redirect consumer FK with original immediate actions; drop old line before document,
then other members, create exact views, physical guard and routing before commit.
Do not expose an intermediate schema or relax original header state. No CASCADE,
current-model imports, global constraint disabling or privileged dynamic routing.

### Failure, security and tenant behavior

Guard refuses all member UPDATE/DELETE; INSERT locks same-tenant building parent.
Aliases are stored after ordinary BEFORE checks and never used by guard. Original
header guard remains deployed and unchanged. Store-owned function cleanup does not
remove original shared header guard function. Preserve clean-session/savepoint,
not-found, request replay, unknown outcome and authorization boundaries.
Protected census histories already refuse purge: prove migrated baseline refusal and
atomic rollback, not a new bypass. Counts include backing store only once. Partial
metadata lifecycle must not rely on unguarded create_all as production parity proof.

## Test Strategy and Traceability

Write new test files first and observe representative missing-store/migration failures.
Use canonical existing capture/financial services for business fixtures; raw test SQL
only for schema boundary/adversarial cases. Freeze before full acceptance.

| Requirement | Planned executable evidence | Expected initial failure |
| --- | --- | --- |
| FR-001 | new member schema inventory + populated migration tests | Store/revision absent |
| FR-002 | new exact rows/IDs + existing history/replay tests | Store cannot preserve family collisions yet |
| FR-003 | new self/incoming FK wrong-type/census/tenant tests + company-generation tests | Alias target absent |
| FR-004 | new shape/outcome/duplicate tests | Closed store shape absent |
| FR-005 | new exact view/bulk/RETURNING + test_cost_records and census paging | View interfaces absent |
| FR-006 | new physical/logical guards + two-session race + old storage refusal tests | Backing guard absent |
| FR-007 | old storage/captured/company tests + populated hash/cursor parity | Transition absent |
| FR-008 | old census limits/replay/savepoint + new concurrent-seal test | New store admission absent |
| FR-009 | new populated roundtrip/DDL/guard/FK parity and injected abort | Revision absent |
| FR-010 | new migrated count/purge refusal + metadata lifecycle/index/exclusion; explicit coverage tests | Backing store absent |
| FR-011 | all unrelated authority snapshots; old captured/company retained results | Transition absent |
| DR-001 | original observation/hash/trace comparison and later knowledge case | Transition absent |
| DR-002 | real alias FKs, same IDs and rollback targets | Alias target absent |
| DR-003 | tenant refusal + canonical entrypoint review + purge rollback isolation | Store isolation absent |

Expanded targeted tests: census/captured-basis/company manifest and migration suites,
cost-records, schema indexes, reporting coverage, account deletion/core lifecycle and
preceding consolidation migrations. Current-model fixtures use head; pinned older
fixtures enumerate actual predecessor physical storage rather than future metadata.
Concurrency tests use bounded synchronization and observed locks, no timing-only sleeps.

Final gates: full PostgreSQL backend, unchanged serial 10,000-source benchmark (do not
relax limit/durability), lint/spec/diff; docs generation/catalog reproducibility/build;
Web format/i18n/tests/build. If generator inputs/output are unchanged, demonstrate
reproducibility rather than invent new public vocabulary. Retain raw failed/green logs,
frozen backend SHA manifest and exact physical/logical name reconciliation.

## Rollout and Rollback

No deployment/live migration authorized. In isolated tests, locks protect one atomic
revision. Rollback locks backing/views/header/consumer, drops routing views/functions,
creates exact predecessor tables unguarded, copies documents before lines, validates
all values, retargets consumer FK to restored line, restores original guards and removes
backing guard/store. Header shared guard/function remains intact. Existing migration
0077 retained-history downgrade refusal still applies to going below that feature.

## Review Risks

- Wrong-family equal IDs, generated NULL uniqueness and consumer FK target parity.
- Extra NULL/private columns changing member hash or capture byte limits.
- Parent admission/sealing serialization and BEFORE/generated-column ordering.
- Frozen predecessor FK names/actions/indexes and exact rollback guard definitions.
- Metadata dependencies/partial cleanup and implicit index helper covering only prefixes.
- Mistaking existing protected-history purge refusal for authorized cleanup.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| --- | --- | --- | --- |
| None | — | — | — |

Next phase: dependency-ordered tasks and non-destructive analysis before implementation.
