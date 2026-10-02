# Remaining cost storage consolidation assessment

Date: 2026-10-02. Status: source/schema audit; recommended bounded candidate, not an implemented migration.
Spec impact: none. This assessment inspects model metadata and existing services/migrations and changes no runtime behavior, schema or business data.

## Finding

The current application metadata contains **47 physical `cost_*` tables**, including the four output stores introduced by spec 316. The remaining storage is not uniformly disposable: received basis records, confirmed decisions, exact historical memberships, captured observations and output have different authority and lifecycle contracts.

The strongest next bounded candidate is **five receipt-cost manifest membership tables sharing one typed physical store**, saving **four physical tables**. Keep the manifest header and every referenced basis/decision table. Preserve the five original logical resources and services. This would bring the accepted cumulative reduction from eleven to fifteen, only after a separately specified and verified implementation. The current count remains 151 physical tables.

## Exact schema inventory

The accompanying [metadata inventory](cost-storage-inventory.json) exhaustively records all 47 physical cost tables, columns/types/nullability/PK markers, unique constraints, checks, outgoing FKs and incoming physical FKs. It excludes compatibility views and their logical constraints. It was produced by importing registered SQLAlchemy metadata with an unused PostgreSQL URL; no live connection or rows were read. Trigger behavior is inspected separately below because metadata does not represent migration-installed trigger functions.

| Family | Classification and disposition |
| --- | --- |
| `cost_receipt_basis`, `cost_component_basis`, `cost_movement_basis`, `cost_correction_basis`, `cost_revenue_match_basis` | Retained admission/evidence relationships. Do not remove merely because the original Movement, component or DocumentLine still exists. Identity, admitted version, event boundary and later references need preservation. |
| Conversion, ownership, opening, policy, attribution, commercial matching, replacement and valuation revisions/parts | Received or confirmed authority with typed scope and history. Keep in this slice; common revision fields do not establish interchangeable grain. |
| Scope/inventory/contribution reviews, categories, ownership parts and members | Retained confirmation and exact selected membership. Keep; do not reconstruct an old decision from current selection. |
| `cost_input_manifest` plus five `cost_manifest_*` tables | Exact receipt-review input selection. Keep header and membership semantics; consolidate the five member stores as the first candidate. |
| `cost_company_census` plus four member tables | Retained observations under a captured PostgreSQL snapshot. Keep observations and parent identity. A later four-to-one member store could save three tables, but must preserve line-to-document membership and downstream company-input FKs. |
| `cost_captured_basis` plus inventory/contribution members | Pinned review selection, including unknown-at-capture, observations and content digest. Keep for now. Two-to-one member storage might save one, but incoming projection links must prove their family. |
| `cost_company_manifest` plus inventory/contribution inputs | Financial company input selection, distinct from non-publishable captured observations. Keep for now. Two-to-one input storage might save one, but downstream output references and different known/unknown contracts require family-safe FKs and lifecycle proof. |
| Four `cost_projection_*` stores | Already consolidated by spec 316. No further saving proposed here. |

The later savings of three/one/one are structural possibilities, not approved plans or executable migration proofs. They are not included in the recommended four-table saving.

## Recommended first slice: receipt manifest members

| Original logical resource | Typed selected identity | Referenced physical authority |
| --- | --- | --- |
| `cost_manifest_receipt` | `receipt_basis_id` | `cost_receipt_basis` |
| `cost_manifest_component` | `component_basis_id` | `cost_component_basis` |
| `cost_manifest_attribution` | `attribution_revision_id` | `cost_attribution_revision` |
| `cost_manifest_correction` | `correction_basis_id` | `cost_correction_basis` |
| `cost_manifest_replacement` | `replacement_id` | `cost_component_replacement` |

All five share tenant-qualified opaque row identity, `manifest_id`, a single selected identity, and uniqueness of tenant/manifest/selected identity. Each references the same `cost_input_manifest` parent. **No physical table has an incoming FK to any of these five member tables** in the inspected metadata. Their original logical names are nevertheless externally inspectable through `services/cost_records.py` and must remain honest and accessible.

A minimal candidate store, provisionally `cost_manifest_member`, can use `(tenant_id, member_family, id)` as physical PK, retain `manifest_id`, and retain the five original typed target columns as nullable columns. A family CHECK requires exactly its corresponding column and forbids the other four. Each target keeps its real composite tenant/identity FK; partial unique keys retain each family's original tenant/manifest/target uniqueness. Family-qualified identity permits the same old member ID in different families and tenants without rewriting it.

Five filtered writable compatibility views expose the original columns and family constants, with CHECK OPTION and a proven default for inserts. Services continue using their existing ORM shapes; old-family inserts/updates/deletes and RETURNING need real PostgreSQL proof. Adding a bare `subject_id` with no true FK, moving the members into JSON, or introducing a general business-object registry is unnecessary and would weaken integrity. This candidate adds one store and retires five: net four fewer, with five logical names retained.

The shared store has five sparse target columns because there are five real target types. This is a bounded typed union of one membership grain, not an assumption that arbitrary cost tables should be unified. If writable view defaults or metadata/index parity cannot be preserved narrowly, compare a service-write adaptation before accepting implementation complexity.

## Historical and lifecycle contracts

Receipt manifests are stored as `sealed`; `services/costing.py::_manifest_members` loads and sorts the five exact selections and `_verify_manifest` compares their hash to the retained header. Historical receipt reads join the retained members rather than selecting current attributions/corrections. The manifest construction block inserts the header and exact child IDs together. Keep digest input family keys and sorted target IDs unchanged: the new physical discriminator must not enter existing hashes. Migration must not turn missing cost evidence into zero or rewrite received amounts.

The inspected receipt membership declarations and migration 0071 do not provide the building/sealed member triggers used by the later census and captured-basis families. Preserve the existing contract rather than importing a stricter guard as an incidental behavior change. Census migration 0077 rejects member updates/deletes, admits inserts only against a same-tenant building parent under a lock, and makes sealed headers immutable. Captured-basis migration 0078 has analogous protection. Company-generation storage in migration 0080 has additional input/output guards. Any later consolidation must migrate those actual trigger dependencies, not infer lifecycle solely from ORM fields.

Census line membership has a composite `(tenant_id, census_id, document_member_id)` FK to a captured document member. Company contribution input points to a census-line identity. A shared census-member store must ensure both links still select the required document/line family, even when equal IDs exist across families. A PostgreSQL view cannot be the new FK target.

Captured inventory/contribution members have incoming FKs from `cost_projection_inventory` and `cost_projection_contribution` respectively. Their look-alike `review_id` fields reference different review tables. A shared store requires correct typed review columns and family enforcement on incoming references. Captured review observations are not financially admitted company inputs: `services/cost_captured_basis.py` returns `publication_eligible=False`, verifies exact census membership and digests, and replays pinned review selections. Replacing them with today's latest review would change historical results.

## Required acceptance proof for the recommended slice

1. Inventory all five old keys, indexes, FK names, column types and original SQL write behavior from a populated PostgreSQL database before designing the migration; metadata alone is insufficient for exact deployed DDL parity.
2. Preserve all row IDs and all tenant/manifest/target tuples, including equal IDs across families and tenants, empty families and a manifest containing all five families. Prove bidirectional exact-column parity.
3. Reject wrong tenants, missing target IDs, multiple target columns and wrong-family view transitions at the database boundary; preserve family-specific uniqueness and original duplicate behavior.
4. Reuse receipt-cost service/tool tests, retained cost-record detail/paging tests and historical-manifest/hash corruption tests without weakening assertions. Prove that newer attributions, corrections and replacements do not change old manifest reads or digests.
5. Prove writable ORM/SQL views, RETURNING, metadata create/drop ordering, Alembic autogeneration exclusions, FK indexes, company record counts and tenant purge exactly once per physical store.
6. Populated upgrade/downgrade/re-upgrade must preserve all source, evidence, decision, review and ledger values and restore exact original member DDL/indexes. Migration DDL must be frozen and must not import current models.
7. Run the required complete gates and review migration/rollback before marking the implementation accepted. No live migration or deployment is part of this assessment.

Existing acceptance sources: `tests/test_costing_services.py`, `test_costing_migration.py`, `test_cost_records.py`; retained census/captured/company contracts are exercised by `test_cost_census_storage.py`, `test_cost_census_migration.py`, `test_cost_captured_basis_storage.py`, `test_cost_captured_basis_migration.py`, `test_company_generation_manifest.py` and the spec 316 projection tests. New consolidation-specific populated and constraint tests are still required.

## Recommendation and validation

Prepare a separate Spec Kit change for the five receipt-manifest member tables if this bounded scope is selected. Leave census, captured selection, company inputs and underlying authorities unchanged. Detailed source paths: `db/costing.py`, `db/cost_census.py`, `db/cost_captured_basis.py`, `db/company_generations.py`; `services/costing.py`, `services/cost_records.py`, `services/cost_census_storage.py`, `services/cost_captured_basis.py`; migrations 0071, 0077, 0078, 0080 and the tenant-key/index changes in 0088.

Validation: physical metadata/FK inventory, source/service/trigger review, `make spec-check`, JSON parse/count reconciliation and `git diff --check`. This is documentation-only; no runtime changes or new acceptance claims require another backend run. No additional saving is implemented by this audit.

## Implemented follow-up: spec 326

The owner selected the bounded receipt-manifest membership slice. [Spec 326
verification](../../specs/330-consolidate-manifest-members/verification.md) records
accepted implementation of one typed physical `cost_manifest_member` store with
five original exact-column writable views. INSERT-only invoker-rights routing
preserves original SQL/ORM writes and RETURNING; no discriminator was added to the
public column sets. Native UPDATE/DELETE preserve the prior contract. All seven
physical FKs have unconditional complete-key indexes.

Populated two-tenant/five-family upgrade, post-upgrade mutation, exact-schema
rollback/re-upgrade and injected transactional parity failure passed. Historical
reviews, source amounts, member hashes, inspection, counts and purge are preserved.
Final backend coverage: 5,383 unique passes, 10 skips, including the unchanged serial
10,000-source benchmark; docs/Web/catalog/lint/spec gates passed. No live migration
or deployment was performed.

The historical 47-physical-table inventory above and in the JSON companion remains
the pre-326 audit snapshot. Current costing physical storage is **43 tables**. This
slice saves **four**; all four accepted consolidations together save **15**. Census,
captured-basis, company input and received/retained authority families remain in
place; their possible savings have not been accepted or implemented.
