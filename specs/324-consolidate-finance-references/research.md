# Research: Finance Catalog Storage

## Decision: disjoint kinds identify families
Use one typed store with primary key (tenant_id,id,kind), and partial unique tenant/id indexes for internal and external kind sets separately. Existing kinds already distinguish the families; no new family field or dependent routing field is required. Incoming internal FK tuples use the primary key; external tuples use a target-qualified unique key.

Rejected: global tenant/id uniqueness (loses valid collisions), generic registry (adds abstraction), JSON storage (loses typed constraints).

## Decision: automatically writable filtered views
Retain both ORM models as simple filtered views with LOCAL CHECK OPTION over the store. Inserts supply the existing kind; no hidden discriminator default is needed. PostgreSQL maintains INSERT RETURNING, updates and deletes, and the check option rejects crossing families. Services retain existing immutable identity rules and finance locking; storage does not add new domain rules.

Rejected: INSTEAD OF triggers duplicate all writable columns and PostgreSQL semantics; read-only views require adapting every write and historical fixture.

## Decision: frozen schema migration
Capture revision-0110 original catalog DDL and all eight incoming FK names/shapes from disposable PostgreSQL. Lock old catalogs and dependent tables, copy exact typed columns, verify bidirectional EXCEPT, redirect FKs, retire old tables and create views. Downgrade reverses using frozen DDL including backing indexes. No live ORM imports in migration.

## Remaining proof
Executable tests must verify ORM RETURNING, identity namespaces, view CHECK OPTION, all eight constraints, schema parity and partial metadata ordering. Independent research review is requested by the planning skill and must be incorporated before implementation.

Independent planning review: kind-only design approved; no architecture or requirements blocker. All eight incoming FK shapes, partial identity uniqueness and explicit family-shape checks must receive executable proof.
