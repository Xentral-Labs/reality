# Census membership storage assessment

Date: 2026-10-02. Status: repository audit and accepted implementation.
Spec impact: none. This report inspects existing metadata, service contracts and frozen
migrations; it changes no executable behavior, schema or business data.

## Finding and recommendation

The four census member families share one retained-observation grain: tenant, opaque
member identity, census identity, a typed observed subject, exact `observed_values`
and retained `content_hash`. Sharing their physical storage is a coherent candidate,
but they cannot be replaced by current Reality reads or generic Facts. Later source
versions and manual corrections must not alter the original capture.

Recommend a bounded four-to-one typed `cost_company_census_member` store, retaining
the census header and four exact-column logical interfaces. Potential net saving:
**three physical tables**. Integrated with current main, the implementation produces
**150 physical tables and 25 compatibility views**, down from 153/21 after the other
four consolidation slices. Cumulative reduction is 18. The additional company-currency table belongs to upstream spec 309; integrated-source revalidation is recorded in spec 327.

## Exact family inventory

The [metadata inventory](census-storage-inventory.json) records all four original
column sets, checks, keys, outgoing/incoming FKs and indexes. It is repository
metadata, not inspected deployed DDL or live rows. The current PK of each family is
`(tenant_id,id)`; historical creation DDL had global IDs before tenant-key migrations.
An implementation must freeze actual revision-0118 predecessor DDL rather than reuse
migration 0077 verbatim.

| Logical family | Required typed subject | Additional original columns | Incoming physical FK |
| --- | --- | --- | --- |
| `cost_company_census_movement` | `movement_id` → Movement | None | None |
| `cost_company_census_document` | `document_id` → Document | None | Census line: `(tenant_id,census_id,document_member_id)` |
| `cost_company_census_line` | `document_line_id` → DocumentLine | Required `document_member_id` | Company contribution input: `(tenant_id,census_line_id)` |
| `cost_company_census_source` | `source_record_id` → SourceRecord | Nullable `interpretation_outcome_id` | None |

All families retain non-null `census_id`, `observed_values`, `content_hash`, `id`
and `tenant_id`. All hashes have length 64. Original uniqueness includes
`(tenant_id,id)`, `(tenant_id,census_id,id)` and the family-specific
`(tenant_id,census_id,subject)` tuple. Source outcome has its own true tenant FK;
NULL is valid. A line's captured document link enforces the same tenant AND census.
It does not additionally enforce a live DocumentLine's document identity in SQL;
do not silently add that new behavioral constraint during consolidation.

## Smallest family-safe link design to prove

The store needs a closed family discriminator and family-qualified opaque PK
`(tenant_id,member_family,id)`. Keep the four typed subject columns and real composite
FKs. Require exactly the selected subject, prohibit other subjects, require document
membership only for line, and admit interpretation outcome only for source.
Preserve family-specific tenant/census/subject uniqueness using partial unique indexes.
Retain JSON observations and hashes verbatim; neither the discriminator nor storage
helpers may enter existing public rows or hash inputs.

Two original incoming links rule out simply changing all four old names to views:
PostgreSQL FKs cannot target views. Pointing a link at `(tenant_id,id)` in the store
would either reject valid equal IDs in different families or permit wrong-family
references. Partial unique indexes are not FK targets. These are design constraints,
not reasons to weaken the old FKs.

A candidate that avoids extra physical registries and consumer columns is two stored
generated identity aliases on the backing store:

- `document_member_identity = CASE WHEN member_family='document' THEN id END`,
  with ordinary UNIQUE `(tenant_id,census_id,document_member_identity)`.
- `line_member_identity = CASE WHEN member_family='line' THEN id END`, with ordinary
  UNIQUE `(tenant_id,line_member_identity)`.

These mechanically expose existing identity only for the required family. Normal
NULL-distinct uniqueness permits unrelated families and equal legacy IDs. The line
self-FK references the document alias with tenant AND census. The existing company
contribution input FK changes its physical target to the line alias, retaining its
exact original columns and values. No business decision or observation is derived
or stored by those aliases. They are private storage support for the existing typed
relationships, not a generic object registry. Exact behavior must be proven in
PostgreSQL, including NULL handling, wrong-family IDs, equal IDs and old FK timing.

Reject alternatives that remove these links, route arbitrary subjects through JSON,
introduce a registry cancelling savings, globally uniquify old cross-family IDs or
add visible discriminator fields to hashed downstream input rows. A simpler fallback
is sharing only movement/source storage (one-table saving), leaving document/line
physical FK targets intact if the full candidate cannot pass narrowly.

## Lifecycle and historical boundaries

Migration `0077_company_cost_census.py` installs `guard_company_census()` and the
header/member triggers. Every member UPDATE/DELETE is refused, even while building.
INSERT locks the same-tenant census header `FOR UPDATE` and requires `building`.
Sealed headers cannot be updated/deleted. Migration 0077 downgrade refuses any retained
census history. These differ from receipt manifest members in spec 326.

A candidate attaches the member guard at the physical store and preserves the header
guard and parent-lock semantics. Every insert through an original interface must
reach the physical guard. Native view UPDATE/DELETE must retain refusal. Prove a
concurrent member insert versus sealing; family routing must never bypass admission.
Admin corruption tests currently disable a trigger on a physical family table and
must move that test-only operation to the backing store without weakening integrity
assertions. Physical-only tenant purge/count and metadata lifecycle need fresh proof.

`services/cost_census_storage.py` captures one clean REPEATABLE READ snapshot, inserts
members in chunks of 500 within a savepoint, seals the header and verifies hashes.
Replay identity remains tenant/request-qualified. `_member_hash` hashes the exact
original row except `content_hash`; `_content_hash` includes the unchanged context,
family counts and sorted `(member_id,member_hash)` tuples. Preserve each original
view's column set exactly, including the two family-specific extras. Extra columns
with NULL would also change hashes and byte-size checks.

Keep capture limits (100,000 records, 1 MiB/member, 64 MiB/capture), family order,
request hashes, snapshot identity, paging/capture-bound cursors, unknown outcomes,
read-only verification and `publication_eligible=False`. Existing captured-basis
resolution and company generation must continue using their retained selections.

## Required next specification and acceptance

1. Specify the bounded four-to-one scope, exact public interfaces, immutable lifecycle,
   two family-safe physical links and populated reversible transition. Exclude other
   cost families, source reconstruction, new public writes and live deployment.
2. Capture actual predecessor columns/PK/FK/unique/index names and trigger/function
   dependencies on isolated PostgreSQL. Inventory non-FK SQL dependencies as well.
3. Write red-first tests for all four families/two tenants/equal IDs; NULL source
   outcome; wrong tenant/census/family; missing/duplicate targets; every closed shape;
   original view columns; bulk inserts/RETURNING; physical guard and concurrent seal.
4. Prove exact populated upgrade/downgrade/re-upgrade with company contribution inputs,
   original hashes/observations/cursors, all unrelated authority snapshots and restored
   predecessor DDL/guards/FKs after rollback. Moving storage must not delete history.
5. Verify all complete FK lookup indexes (ordinary, not partial), metadata create/drop,
   Alembic view exclusion, record inspection, physical counts and tenant purge once.
6. Reuse census storage/migration, captured-basis, company generation and record tests;
   run complete backend plus unchanged serial benchmark and docs/Web/catalog gates.
   No candidate is accepted until every required check is green.

## Evidence and limits

Reviewed: `db/cost_census.py`, `db/company_generations.py`,
`services/cost_census_storage.py`, `services/cost_captured_basis.py`, migrations 0077
and 0080, the retained-observation contract in `docs/features/receipt-costing.md`,
and `test_cost_census_storage.py` / `test_cost_census_migration.py`.
Repository metadata confirms exactly two incoming member FKs. No database was started,
no live rows queried and no migration/schema/runtime code changed by this audit.
This is a design assessment, not populated migration or concurrency acceptance.

Validation: inventory JSON parsed and reconciled (four families, 6/6/7/7 columns, two incoming member FKs, tenant-qualified PKs); `make spec-check` and `git diff --check` passed. Spec impact is none because only assessment documents were changed; no additional runtime suite was needed for this audit.

## Selected specification follow-up

The owner selected the specification step. [Spec 327](../../specs/327-consolidate-census-members/spec.md) records reviewed requirements and acceptance scenarios; planning, analysis and implementation are recorded there. Final acceptance evidence is collected in the verification record.
