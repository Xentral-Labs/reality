# Settings storage consolidation assessment

Date: 2026-10-02. Status: researched assessment; the default-account slice was subsequently approved for implementation in spec 319.
Spec impact: none. This document records a read-only source/schema audit and proposed
future scope. The original assessment does not itself authorize a live migration; subsequent account-default implementation is specified separately.

## Finding

The current repository does not contain a collection of independent simple tenant
preference tables that can immediately collapse into one registry. `ai_settings` is
its dedicated tenant AI preference store. Other apparent settings own operational
relationships, retained decisions, source-supported rules or concurrency state.

Replacing `ai_settings` with one new generic table removes one table and adds one:
net zero. Moving business rules and retained decisions into an untyped key/value
store would sacrifice constraints and traceability rather than simplify the model.
Do not introduce a generic settings table solely on an anticipated future need.

Git history begins with the public baseline on 2026-09-14; the requested 34-day
window begins before that baseline. The audit cannot prove introduction dates for
baseline tables. The dates below identify when definitions entered this available
history, not necessarily when the feature was originally developed. No live database
or user configuration values were read.

## Storage inventory and disposition

| Existing storage | What it actually owns | Recommended disposition |
| --- | --- | --- |
| `ai_settings` | Tenant provider/model/endpoint selection, tenant-scoped vault reference and legacy encrypted-key migration | Keep for now. Generalize this existing boundary only after a second simple tenant preference use case is specified. Preserve typed secret FK, access/redaction and legacy-key recovery. |
| `app_user` language/locale/timezone/display name | Account-wide preferences alongside authenticated identity | Already reuses existing account storage. Do not move into tenant preferences. Spec 112 confirms scope. |
| Browser `reality.theme` | Browser-local appearance | Already has no database table; keep browser scope. |
| `finance_role_destination` | One selected account per tenant/account role | Implemented in spec 319 using `subledger_account`, preserving destination identities and historical postings. Reduction: one physical table; accepted backend coverage recorded in spec 319 verification. |
| `finance_state` | Finance-wide mutation lock, revision and stale-preview detection | Keep. It is concurrency state, not a preference. Moving the lock to Tenant would require a separate concurrency/lock-order design. |
| `dunning_schedule_level` | Three source-supported escalation levels with waiting days and exact fees | Keep typed for now. Rules act on amounts/days; a shared rule-storage design could be assessed separately. No migration to ordinary Settings or Facts. |
| `cost_policy_revision` | Confirmed versioned method, ownership, currency/unit and history boundary | Keep as retained decision authority until a separate decision-family consolidation proves exact revision/reference parity. |
| `source_classification_mapping_revision` | Reviewed, versioned source-code classifications with typed reference kind and source-system scope | Keep typed revision relationships. Configuration-looking names do not make these ordinary preferences. |
| `finance_target_mapping_revision` | Reviewed accounting target mappings with predecessor, typed references and exact snapshots | Keep pending a dedicated mapping-family design; never replace with current-value Settings. |
| `accounting_target`, `accounting_target_reference`, `finance_reference` | Identified catalogs referenced by confirmed mappings | Keep typed catalogs; do not turn referenced identities into arbitrary JSON strings. |
| `item_reorder_point` | Exact item/location rule, nonnegative threshold and positive reorder quantity | Keep typed item/location grain. Item alone cannot represent different location rules. |
| `source_system`, `source_capability` | Source identity, connector association and admitted interpretation capabilities | Configuration already lives on its owning resource. Keep FK identities and admitted capability grain. |
| `demo_data_connection` | Source/schedule relationships, lifecycle, revision and request replay | Keep for this slice; any shared connector-lifecycle consolidation needs its own reviewed design. It is not a settings bag. |
| `scheduled_job`, `scheduled_job_run` | Versioned allowlisted job configuration, scheduling, claims, retries and execution evidence | Already share typed configuration envelopes. Preserve the shared scheduling contract; no settings migration. |
| `analytics_report` | Owner-private report definitions, revision, idempotency and tombstones | Already uses JSONB for a genuine definition. Keep owner/company permission boundary and saved report identities. |
| `secret`, `secret_audit_event` | Encrypted material and secret access history | Already generic security infrastructure. Keep outside ordinary preference payloads and Facts. |

Relevant additions after the available baseline:

- `cost_policy_revision`: migration 0072, introduced in this history on 2026-09-20.
- `dunning_schedule_level`: migration 0102, introduced on 2026-09-29.
- `item_reorder_point`: migration 0107, introduced on 2026-10-01.
- `ai_settings` and finance default/state tables were already in the 2026-09-14 baseline.

## Why Facts are not the settings store

The existing [Fact contract](../DATA_MODEL.md#invariants) defines immutable, scalar,
source-supported observations about an existing Reality subject. It explicitly excludes
process rules, mutation audit and duplicated operational authority. Provider selection,
job controls and default account choice are instructions/configuration; they are not
observations. A Fact write cannot stand in for typed references, expected revisions,
secret access controls or configuration lifecycle.

SourceRecords remain the lossless evidence for received rule statements. Reusing their
payloads alone still needs an explicit, deterministic current-rule selection and the
existing confirmation/stale-preview semantics. Removing a rule table without solving
those contracts is not an equivalent implementation.

## Next concrete consolidation candidate: default accounts

The current `set_default_account` service requires an active account whose existing
`role` equals the selected role. Accounts have one role, and destinations are unique
per tenant/role. No domain model declares a foreign key to a destination; the current
service result exposes account IDs rather than destination IDs. Thus the default
selection can potentially be owned by the selected account itself.

Account-default scope subsequently accepted by the owner (spec 319):

1. Retire the physical `finance_role_destination` table, using the existing account
   model for default selection. No generic preference table is added.
2. Preserve every old destination ID, account ID and tenant/role selection. A nullable
   destination identity on an account can mark the selection without adding both a
   Boolean and a redundant identity. This marker design was subsequently accepted for spec 319.
3. Preserve list/resolve/setup/default-change service shapes, confirmation, errors,
   finance revisions, locking and event audit. Existing invoices and LedgerEntries
   retain their original accounts when a default changes.
4. Preserve at most one selected account per tenant/role and uniqueness of retained
   destination IDs. A switch must transfer the destination identity atomically.
5. Inspect legacy mappings for role mismatches before migration. Current service
   validation is stronger than the existing destination FK; do not assume all old
   rows are valid, repair them silently or discard them. Unsupported legacy state
   must abort safely before retirement.
6. Decide the legacy logical SQL interface explicitly. A naive updatable view mapping
   `account_id` to account primary key would be unsafe: old writes could change account
   identity. Use a reviewed compatibility strategy, not an automatically writable view.
7. Copy/compare original identities and selections, verify unchanged retained finance
   records, and provide lossless rollback before dropping old storage.

Potential saving: one physical table, including an older baseline table. This candidate
is not responsible for recent Journey table growth; it is an independently discovered
opportunity to reuse the original structure. Migration 0109 from spec 316 remains the
separate first slice and must not be applied implicitly by this audit.

Required acceptance proofs before implementation:

- Existing `tests/finance/test_accounts.py` default changes do not rewrite invoice or
  payment account provenance; blocked-account and role/tenant refusals remain exact.
- Concurrent selection, stale preview, retry and initialization preserve existing
  finance lock/revision behavior and one-default-per-role semantics.
- Populated upgrade/downgrade preserves equal IDs in different tenants, all old
  destination IDs, exact mappings, account revisions and finance authorities.
- Invalid legacy role mappings abort without partial retirement or implicit repair.
- Legacy SQL/inspection resource identity remains honest; unsupported writes cannot
  mutate account primary keys through a compatibility interface.
- Adapt existing PostgreSQL integration cleanup and missing-default tests that directly
  use `FinanceRoleDestination`; do not weaken their refusal/provenance assertions.

## Future generic preference boundary

If a second genuine tenant preference namespace is proven, compare extending the
existing settings boundary with adding another subsystem table. The minimum contract
should include tenant scope, allowlisted namespaces, validated payload versions,
explicit defaults, revision-controlled writes, owner permissions, confirmation and
safe redacted reads. Secret relationships remain typed and tenant-constrained.
Reads must not implicitly create defaults, rotate keys or run migrations.

The present AI helper can create defaults and lazily transfer a legacy encrypted key
to the vault. A future read-only settings API must explicitly preserve or migrate that
behavior through the proper mutation service; it must not silently assume existing
AI reads are pure. Account-wide and browser-local scopes remain separate.

No speculative setting namespace, generic subject FK or configurable business-object
registry is introduced by this assessment.

## Evidence

- `packages/reality-core/src/reality/db/core.py`: Tenant, AppUser, AISettings, Fact,
  SubledgerAccount, FinanceRoleDestination, FinanceState, DunningScheduleLevel,
  ItemReorderPoint, SourceSystem and SourceCapability contracts.
- `packages/reality-core/src/reality/services/finance/accounts.py`: default role/state
  validation, selection resolution, finance lock and revision/audit semantics.
- `packages/reality-core/src/reality/services/dunning_runs.py`: immutable stated-rule
  SourceRecord, exact fee copying and finance revision invalidation.
- `packages/reality-core/src/reality/agent/settings.py`: owner/provider/key behavior and
  existing lazy legacy-key transfer.
- `packages/reality-core/src/reality/db/inventory_costing.py`, `source_mappings.py`,
  `target_mappings.py`, `demo_data.py`, `scheduled_jobs.py`, `analytics.py`: retained
  identities, constraints and typed configuration grain.
- [Spec 112](../../specs/112-unified-settings/spec.md): existing account/browser/company
  preference boundaries; no persistence redesign.
- [Scheduling contract](../features/scheduled-jobs.md) and
  [company setup/demo contract](../features/company-setup-demo.md): shared job and
  lifecycle authorities.

Validation: source/model/service references reviewed; `make spec-check` and
`git diff --check` passed. No runtime code changes or database actions require a
backend rerun for this documentation-only audit. Earlier spec 316 backend limitations and their subsequent passing acceptance
coverage remain documented in its verification report.

See [spec 319](../../specs/332-integrate-account-defaults/spec.md) for the accepted
account-default slice and its verification status. Generic preference infrastructure
remains outside that slice.

The subsequent [mapping/reference storage assessment](mapping-storage-consolidation.md)
keeps retained mapping decisions typed and identifies a narrower two-catalog candidate
implemented in spec 324 with a saving of one physical table. See the
[final table overview](table-storage-overview.md) for the complete inventory and next review scope.
