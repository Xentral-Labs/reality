# Research: Census Membership Consolidation

Status: planning research complete; executable acceptance remains pending.

## Typed incoming links

Decision: use two stored generated identity aliases on one typed store, with ordinary
NULL-distinct unique constraints. Line self-FK selects document identity in the same
tenant/census; company contribution input retains its existing local columns and
selects the line identity alias. Change the latter declaration explicitly in
`db/company_generations.py`; avoid mutating SQLAlchemy private constraint internals.
Rationale: original equal IDs across families must remain valid while wrong-family
references fail. Original public rows and downstream hash fields remain unchanged.
Alternatives: partial unique keys cannot serve incoming FKs; unqualified store IDs
weaken type identity; global ID uniqueness rejects valid predecessor data; consumer
discriminator columns leak into row/hash contracts; an identity registry cancels the
three-table saving. A movement/source-only reduction would be smaller scope but would
not meet the selected four-to-one requirement and must not be substituted silently.

## Schema and trigger compatibility

Decision: retain original mapped census models as exact-column filtered views with
fixed INSERT-only invoker-rights routing, stored RETURNING and native UPDATE/DELETE.
Install a physical member BEFORE guard with the original update/delete refusal and
same-tenant `building` parent `FOR UPDATE` check. Use a store-owned guard function,
so metadata cleanup never removes the predecessor header's shared function.
Rationale: view INSERT routing alone cannot protect direct physical writes; CHECK
OPTION is not sufficient with INSTEAD OF triggers. The old header guard remains
unchanged. Guard code must not access generated values before generation.
Alternatives: triggers with dynamic caller identifiers, SECURITY DEFINER, application-
only integrity, hiding observations in Facts, reconstructing current state.

## SQL documentation evidence

Primary sources reviewed: [PostgreSQL generated columns](https://www.postgresql.org/docs/17/ddl-generated-columns.html),
[constraints](https://www.postgresql.org/docs/17/ddl-constraints.html),
[trigger behavior](https://www.postgresql.org/docs/17/trigger-definition.html), and
[views](https://www.postgresql.org/docs/current/sql-createview.html).
Stored generation uses immutable row-local expressions; constraints document ordinary
unique/FK targets and NULL-distinct uniqueness. Trigger behavior documents underlying
physical write enforcement and RETURNING responsibilities. These support the design;
actual alias-FK, routing, guard, concurrency and rollback behavior still requires tests.
Use explicit STORED rather than the newer virtual-column default.

## Migration and rollback

Decision: provisionally migration `0121_census_members.py`, parent
`0120_manifest_members`; recheck actual head before implementation. Freeze actual
isolated predecessor DDL, FKs, indexes, trigger/function definitions and dependencies.
Lock header, all four members and company contribution input. Copy document rows
before line rows into the unguarded new store, exact bidirectional parity, redirect
incoming company FK, replace old tables with views, then install physical/routing guards
before transaction commit. Rollback mirrors the ordering and recreates exact guards.
Rationale: copying sealed captures through the admission guard would fail; original
history must move while unobservable outside the migration transaction. Do not
re-seal headers, change hashes or disable constraints globally. No CASCADE or live ORM
imports; test injected parity failures and retained downstream inputs.

## Counts, purge and metadata

Decision: reuse physical-only counts/purge and view exclusion. Preserve the existing
purge result, including census-protected DELETE refusal and rollback; no bypass.
Evidence: `services/core.py::_purge_tenant_records` deletes physical tables directly;
0077 guards refuse member DELETE and sealed-header DELETE. No scoped authorization
bypass was found. FR-010/US3.4 were clarified accordingly without expanding scope.
A migrated populated baseline must prove that refusal, not use unguarded create_all as
a proxy for deployed history behavior. Metadata lifecycle tests independently prove
store-owned routing/guard function cleanup and actual physical target dependencies.

## Independent design review

The plan skill required research delegation. Read-only reviewer
`/root/projection_research` inspected current models, original guards, services and
company input dependency. Review accepted generated aliases, ordinary unique targets,
physical guard, original public columns, document-first copy and downgrade ordering;
identified purge preservation and metadata/index/concurrency risks recorded here.
No design blocker remains. No database or production code was changed by this research.
