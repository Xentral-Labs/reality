# Mapping and reference storage consolidation assessment

Date: 2026-10-02. Status: source/schema assessment and proposed future scope.
Spec impact: none. This audit changes no schema, service behavior or business data.
The owner subsequently approved the bounded catalog slice (spec 324); this assessment itself changes no behavior.

## Finding

Versioned mappings are retained decisions rather than disposable output or simple
preferences. Common audit columns alone do not establish a common business grain.
The stronger next candidate is the pair of Finance reference catalogs: their shared
identity/label/state/revision structure could use one typed physical store, while
internal classifications and external target references remain separate logical resources.
Potential reduction: one physical table. This is not yet a migration design or proof.

## Disposition

| Existing table | Authoritative grain and constraints | Disposition |
| --- | --- | --- |
| `source_classification_mapping_revision` | Tenant/source system/namespace/field kind/source code/revision; typed internal reference; one current revision; predecessor and reviewed snapshot | Keep logical decision family. Do not move into Facts or current-value Settings. |
| `finance_target_mapping_revision` | Tenant/target plus local account or transaction/case/group scope; typed account/tax outputs; separate shape/current/revision uniqueness and overlap refusal | Keep logical decision family. Shared physical storage with source mappings would save one table but require a broad, sparse union of unrelated routing keys; lower priority than catalog consolidation. |
| `cost_policy_revision` | Tenant/item/revision, owner, method, currency, unit and history boundary; predecessor; inventory reviews link to the exact policy | Keep typed authority. A generic mapping envelope would hide calculated/filterable/constrained fields or introduce many irrelevant nullable columns. |
| `financial_component` | Normalized received header or line amounts with one opaque identity; assignments reference that exact identity | Keep for now. Inlining values into Document/DocumentLine does not by itself preserve the common assignment FK or cross-owner component identity. A replacement identity registry would cancel the table saving. |
| `component_assignment_revision` | Received component/revision, exact basis, case/group and immutable reviewed snapshot | Keep: reviewed assignment to evidence is not a source-code lookup or external route. |
| `component_assignment_part` | Assignment revision plus cost-center reference and positive received amount | Keep: distinct multi-row allocation grain; neither catalog nor Settings. |
| `finance_reference` | Internal cost center/case/coding group; tenant/kind/code uniqueness; immutable kind/code; mutable name/state with revision | Candidate shared typed catalog storage, preserving the existing logical interface. |
| `accounting_target_reference` | External account/tax code belonging to one accounting target; tenant/target/kind/code uniqueness; exact target/kind FKs | Candidate with `finance_reference`, preserving target ownership and separate ID namespace. |
| `accounting_target` | Identified external accounting destination with namespace, lifecycle and revision | Keep distinct destination identity. It is not a catalog entry or installed connector. |

## Why Action, Fact and SourceRecord do not replace these decisions

ChangeProposal/Action already carries proposed intent and confirmed action identity.
It does not itself enforce one current mapping per business scope, typed references,
predecessors, exact route shapes or historical revision selection. Replacing mapping
rows with Action JSON would remove those constraints or rebuild a second query/index
system around the payload.

Facts represent source-supported observations about Reality subjects. These rows select
classification/routing/policy behavior, so recording them as Facts would change authority.
SourceRecord preserves received statements losslessly; it does not independently choose
the current confirmed mapping. Reviewed snapshots retain the decision as confirmed and
must not be reconstructed from subsequently changed catalog labels.

## Reuse of original evidence storage

Received net/tax/gross/base values could technically be typed on their Document or
DocumentLine owner without making documents the operational authority. However,
`financial_component` also supplies the common opaque identity used by assignment
revisions. Removing its storage while keeping a union read view would not provide a
PostgreSQL FK target. Preserving that identity across two owner tables, every assignment,
uniqueness and exact rollback requires a separate proven design; a replacement identity
registry would save no table. Do not move the fields alone and claim equivalent storage.
The two-reference-catalog candidate retains a single physical FK target and is narrower.

## Bounded catalog candidate

A possible future slice consolidates exactly `finance_reference` and
`accounting_target_reference` into one physical typed Finance catalog store, retaining
both original logical names and application service contracts. It introduces no
cross-domain object registry, preference namespace or business rule engine.

Required preservation and design decisions:

1. Preserve every opaque ID, including the same ID in the two original families and
   in separate tenants. Generated `fref`/`tref` prefixes are not a collision guarantee.
   A family-qualified physical identity must preserve the original per-family tenant/ID
   uniqueness; do not rewrite received or retained identities.
2. Preserve local kinds (`cost_center`, `case_code`, `coding_group`) versus external
   kinds (`account`, `tax_code`). External rows require the exact target FK; local rows
   must not gain an invented target. Preserve local code length 100 and external length
   200 through family-specific checks, not an implicit widened local contract.
3. Preserve local tenant/kind/code uniqueness and external tenant/target/kind/code
   uniqueness. Identical external codes in different targets remain valid.
4. Redirect all incoming FKs to physical storage, not PostgreSQL views. Current internal
   links all include tenant/ID/kind; external links include tenant/target/ID/kind.
   Their disjoint allowed kinds may permit preserved FK shapes without adding a new
   routing column to dependent business records, but this needs executable proof.
5. Preserve the two original tenant/ID identity namespaces independently. A global
   tenant/ID unique key would incorrectly reject valid cross-family collisions.
   All lookup services and view predicates must enforce family as well as tenant.
6. Internal references have no persisted creation/update timestamps. External references
   do. Do not manufacture timestamps for historical internal rows or add them to the
   internal API merely because the shared store contains such columns.
7. Preserve shared finance locking, revisions, owner-confirmed changes, stale-preview
   refusal, immutable kind/code/target, existing before/after audit and blocked lookup
   behavior. Neither current labels nor a storage migration rewrite reviewed snapshots.
8. Decide logical view writes explicitly. Catalog services currently insert and update
   mapped rows; plain read-only views would break them. Options are family-safe writable
   compatibility views or adapting writes to the shared store while retaining read views.
   Compare the cost of either approach before committing to the slice.
9. Prove bidirectional exact-column parity, unchanged assignments/mappings/ledger/source
   authorities, populated downgrade/re-upgrade and older pinned migration compatibility.
   Inventory all changed FK names/backing unique keys before retiring old storage.
10. Prove one fewer physical table using inspection, while retaining distinct resources,
    code search/paging, permissions and error contracts. Shared storage is not permission
    to present external target accounts as local posting accounts.

## Acceptance tests to reuse and extend

- `tests/finance/test_references.py`: lifecycle, immutable history, tenant/kind rejection,
  stale approval, permissions, competing changes, migration and CLI/service parity.
- `tests/finance/test_target_mappings.py`: duplicate codes across targets, wrong target/kind
  database rejection, stale reference change, snapshots, received-case provenance and
  local account routing independent of tax codes.
- `tests/finance/test_source_mappings.py`: wrong kind/tenant, current revision races,
  replacement snapshots, blocked sources/references and exact declared source codes.
- `tests/finance/test_components.py` and handoff regression suites: retained assignment
  identities, exact received amounts and retained mapping/snapshot references.
- New populated migration tests: equal IDs across families/tenants, unchanged retained
  authorities, all incoming FK semantics, exact rollback schema and no extra timestamps.

Do not expand schema or start implementation until the concrete catalog scope is reviewed,
a specification and Constitution-PASS plan establish these contracts, tasks map every
requirement to tests, and analysis leaves no critical finding.

## Evidence and history limits

Models: `db/finance_references.py`, `db/source_mappings.py`, `db/target_mappings.py`,
`db/components.py`, `db/inventory_costing.py`. Services: `services/finance/references.py`,
`source_mappings.py`, `target_mappings.py`. The existing Finance-specific design is
recorded in [spec 148 target mappings](../../specs/148-accounting-journal-cost-centers/target-mappings.md).

The available Git history starts on 2026-09-14. Finance reference and mapping models are
already present in that baseline; they cannot be attributed to a later Journey change
from this history. Inventory costing models entered on 2026-09-20 (`4be2a374`). This
assessment is an independently discovered consolidation candidate, not a claim that all
these tables were added in the requested 34-day window. No live database rows were read.

Validation: source/model/service/FK and available-history references reviewed;
`make spec-check` and `git diff --check` passed. Specs 316/319 acceptance is recorded
separately and does not count as a migration proof for this proposed catalog slice.

## Subsequently accepted implementation

The owner approved this bounded candidate and spec 324 implemented it. Two physical
catalogs now share `finance_reference_store` while both original logical resources,
IDs, typed relationships and service contracts remain intact. Populated exact rollback,
all eight incoming FK constraints, metadata/deletion/counting and complete backend
coverage are accepted in [spec 324 verification](../../specs/324-consolidate-finance-references/verification.md).
Net saving is one physical table, eleven together with specs 316/319. This does not
change the assessment that mappings, components and targets have distinct retained
business grains. No live migration was executed.
