# Research: account-owned default selection

Independent read-only research confirms one role per account and no domain FK to the
old destination. The existing account service owns all production destination writes.

Decision: nullable retained selection ID on Account, not a separate Boolean.
Rationale: preserves old opaque IDs with one field and makes role ownership explicit.
Rejected: new generic settings registry (no table saving, weaker typed references),
Facts (wrong authority), duplicate Boolean (redundancy), loss of destination IDs.

Decision: DISTINCT read-only compatibility view.
Rationale: preserves readable old grain while refusing all writes; a normal writable
view could update the underlying account primary key through account_id.

Decision: marker transfer under existing delivery/finance locks, clear and flush first.
Rationale: immediate unique indexes require removal before transfer; stale preview/event
and account revision semantics remain unchanged. Blocked old defaults remain selected.

Decision: frozen DDL and exact parity in one locked transaction.
Rationale: actual legacy constraints/index names and backing-key order matter to older
0088 downgrades. Role-mismatched legacy rows cause explicit safe abort, never repair.

Decision: reuse existing compatibility compiler through a small storage-only module.
Rationale: cost and finance views need the same create/drop/index/Alembic mechanics;
registration remains specific and existing cost DDL is proven byte-for-byte stable.

Decision: keep canonical logical view readers and defer the new account marker.
Rationale: ordinary historical account reads and finance posting proofs continue to
work against pinned old migration revisions without production schema detection.
Pinned fixtures seed their legacy accounts through reflected test-only tables;
current production bootstrap always uses account-owned selections. FetchedValue
omits unset INSERT values and declares no SQL default.

Decision: shared deletion/counting skips compatibility views.
Rationale: a read-only view is not a second deletion target or stored record. Existing
confirmed deletion services remove the tenant-scoped physical storage. Existing
immutable cost-history purge limitations are outside this change; basic deletion
regressions do not establish deletion of populated immutable cost histories.
