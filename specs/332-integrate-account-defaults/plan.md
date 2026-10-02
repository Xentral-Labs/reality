# Implementation Plan: Integrate account defaults

Date: 2026-10-02. Language: English. Scope: [spec.md](spec.md), owner approved.

## Summary and Technical Context

Python 3.12+, SQLAlchemy 2, Alembic/PostgreSQL. Add one nullable typed
`default_destination_id` to SubledgerAccount. Its presence selects that account for
its existing role. Preserve the original ID; no Boolean or JSON registry is added.
Replace the old table with a read-only DISTINCT compatibility view. Existing services
write accounts under the unchanged finance lock, with no new public tools or UI.

## Constitution Check

| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Exact held financial records untouched | PASS |
| Reality authority | Default selection remains account configuration | PASS |
| Proven schema | Existing repeatedly resolved default selection; one typed marker replaces a table | PASS |
| Tenant/services | Tenant-scoped uniqueness and shared service mutations | PASS |
| Spec/tests/review | Approved concrete scope; tests first; independent design research | PASS |
| Explainable web | Existing account/results and readable legacy IDs retained | PASS |
| Received values | Copy-only migration, no recalculation | PASS |
| Smallest coherent model | One fewer table; no generic infrastructure/dependency | PASS |

No exception or further scope decision is required. Requirements review and research
resolve all unknowns before implementation. Reviewer checklist concerns writing quality,
not release acceptance.

## Design and Repository Structure

- `db/core.py`: typed nullable marker, unique `(tenant_id, default_destination_id)`,
  partial unique `(tenant_id, role)` where marker is non-null; old mapped class describes
  a view without changing its four logical columns.
- `db/schema_views.py`: move the existing metadata CREATE/DROP/index compilation support
  out of the cost-specific module, using explicit per-table compatibility-view DDL.
  Alembic excludes registered logical views. No business rules live in this support.
- `db/cost_projections.py`: continue registering identical cost view DDL/defaults and
  guards through shared schema support; physical indexes unchanged.
- `migrations/env.py`: use shared view filter; old imports may re-export it for compatibility.
- `services/finance/accounts.py`: stable logical selection reads and marker transfer under existing lock;
  clear/flush old marker before assigning same retained ID to the new account. Re-select
  accounts with populate_existing. Account revisions are unchanged by selection, while
  existing finance revision/event behavior remains exact. Bootstrap sets markers on
  newly created accounts directly and keeps finance revision zero.
- `migrations/versions/0118_account_defaults.py`: frozen transactional migration.
- `tests/test_account_defaults.py`: schema/identity/refusals/stale/initialization/tenant
  and competing-selection proofs.
- `tests/test_account_default_migration.py`: populated parity, incompatible legacy
  refusal, equal cross-tenant IDs, blocked selection and exact schema rollback.
- Existing finance/integration tests: clear markers or delete physical accounts when
  preparing missing-default/cleanup conditions. Do not delete read-only views.
- Existing schema/history tests: distinguish logical views and current metadata from
  pinned pre-0110 migrations, preserving earlier migration evidence.
- Durable docs and spec coverage updated; regenerate catalog only if required.

## Compatibility and Migration

The legacy view uses DISTINCT to prevent all automatic INSERT/UPDATE/DELETE. Read columns
remain `tenant_id,id,role,account_id`, with id copied from the marker. A simple updatable
view would allow account_id writes to mutate account identity and is rejected.

Lock both old tables ACCESS EXCLUSIVE before validating/copying. Check old mappings
join same-tenant accounts of matching role. Blocked selected accounts are valid and must
survive. Add marker/constraints, copy exact destination IDs, compare old mappings in both
directions, then retire old storage and create view in one transaction.

Downgrade locks the view/backing accounts, materializes the four logical values into
frozen original table DDL, verifies parity, then removes the marker and its indexes.
Freeze actual revision-0109 constraints/indexes/PK names rather than deriving old DDL
from current models. Recreate original foreign keys before the restored composite PK
where needed so downgrade0088 may replace primary keys. No source, amount, account
revision, finance revision or event history is recomputed.

## Tests and Gates

Observe a meaningful schema/identity failure before implementation. Test service switches,
repeat selection, unchanged invoice settlement accounts, missing/blocked/foreign/wrong-role
refusals, stale revision, simultaneous selection, one-default-per-role and tenant ID
namespaces. Test legacy writes fail without account mutation. Compare complete old
account columns and retained finance records across populated roundtrip. Reject invalid
legacy role state without any committed schema/data changes. Test metadata create/drop
and Alembic/index parity, including old-revision downgrade.

Run focused finance, cost/shared-view, PostgreSQL/schema/migration and adapter suites,
then complete backend, lint, spec, web, i18n, docs and catalog gates. Record actual results;
known demo failures/timeouts from the preceding slice are evidence, not permission to
claim green or change unrelated behavior. Final review precedes task completion.

Historical finance/cost fixtures seed their old physical defaults with reflected test
tables. The marker is deferred and omitted from INSERT when unset, like the existing
Document historical-schema support. Canonical selection readers retain their logical
view interface; production writers exclusively mutate marked accounts. This preserves
pinned old posting proofs without production schema detection or parallel business rules.

### Shared deletion integration

Existing confirmed account/company deletion must count and purge physical storage only, skipping all compatibility views. The defaults are removed with their owning accounts; shared cost storage remains the authority for its views. Reuse the existing account-deletion and admin API regression tests, preserving confirmation, tenant isolation and refusal assertions. This restores the already-specified deletion contract and adds no deletion operation.
