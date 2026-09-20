# Financial company generation: concrete storage proposal

Status: owner approved on 2026-09-19 for migration and internal implementation.

## Purpose and authority boundary

This proposal closes the remaining T080 storage gap for one exact company population.
It retains a historical financial-input manifest assembled from the owner-confirmed
inventory and contribution reviews already present in Reality, then publishes one
disposable company generation that covers every expected census subject exactly once.

The manifest does not create a company-wide accounting policy, approve an unknown amount,
or turn the current company census or captured diagnostic report into financial authority.
Each known result keeps its own approved review, policy/profile and retained input chain.
An unknown result is completed population work with incomplete financial coverage.

## Selected model

Use seven tenant-scoped typed tables. Generic `subject_kind` or JSON authority membership
is rejected because it would weaken same-tenant foreign keys and hide the two different
business grains.

| Table | Essential fields and constraints | Purpose |
|---|---|---|
| `cost_company_manifest` | tenant/id; retained census FK; effective/knowledge UTC cutoffs; target event sequence; inventory/contribution algorithm versions; canonical scope key; expected population digest and counts; header-gap count; source-gap count; canonical gap digest; building/sealed state; sealed/content metadata; unique tenant/scope key/content hash | Retained historical financial-input envelope. `knowledge_at` is captured after the tenant event lock establishes the committed cursor; it is never copied from census `observed_at`. Gap counts and digest bind every retained unresolved header/source member without copying its payload or inventing a financial subject. |
| `cost_company_inventory_input` | tenant/id; manifest FK; item FK; optional inventory review FK; exact input fingerprint; support state; unique tenant/manifest/item | One expected inventory subject derived from the manifest's retained census movements, including explicit unknown review. The review remains the shortest link to exact movement membership, policy and retained receipt inputs; the service verifies that membership against the manifest census before sealing. |
| `cost_company_contribution_input` | tenant/id; manifest FK; retained census line membership; optional contribution review FK; optional linked inventory review FK; exact input fingerprint; independent DB1/DB2 support states; unique tenant/manifest/document line | One expected commercial subject, including service, credit and unsupported economic-scope candidates. |
| `cost_company_generation` | tenant/id; manifest FK; fixed algorithm bundle; building/sealed state; expected/completed work and member counts; inventory/contribution content hashes; started/completed times; unique tenant/manifest/algorithm bundle | Disposable complete calculation envelope. Counts and hashes are derived from persisted typed members, never accepted from a caller. |
| `cost_company_inventory_result` | tenant/id; generation FK; manifest inventory member FK; nullable existing `cost_inventory_generation` FK; known/unknown result state; verified result fingerprint; unique tenant/generation/manifest member | Reuses the canonical inventory cache when known; null cache is permitted only for an explicit unknown result. |
| `cost_company_contribution_result` | tenant/id; generation FK; manifest contribution member FK; nullable existing `cost_contribution_generation` plus exact review FK; independent DB1/DB2 known states; verified result fingerprint; unique tenant/generation/manifest member | Reuses the canonical contribution cache without copying received revenue or recomputing DB arithmetic. |
| `cost_company_publication` | tenant plus canonical scope key; generation FK constrained to the same manifest scope; updated timestamp | Atomic CAS pointer for a sealed exact company generation. |

All foreign keys include `tenant_id`. Manifest and member authority rows are immutable
after sealing. Generation/result/publication rows are disposable observations and may be
reconstructed from the retained manifest. Referenced per-review generations cannot be
deleted while a company result points to them; company-cache disposal removes result rows
before releasing those caches.

## Manifest admission

1. Start a fresh READ COMMITTED transaction and acquire the existing tenant business lock.
2. Observe the committed tenant event cursor after prior lock holders commit; record that
   cursor and a new UTC `knowledge_at`. Never use the census observation timestamp as
   financial knowledge time.
3. Verify one sealed retained census with the same tenant/effective cutoff. Enumerate every
   retained inventory item and contribution line. Separately enumerate every unresolved
   header/source member in canonical typed-ID order and bind its tenant, census member ID,
   content hash and gap classification into `gap_digest`; record exact family counts.
4. Resolve reviews only through the existing retained-census rules at or before the target
   cursor. Later reviews cannot enter the manifest. Preserve missing/incompatible reviews as
   explicit unknown input members.
5. Verify each selected review's retained membership and calculate its canonical input
   fingerprint. The census record fingerprint alone is insufficient.
6. Seal only after exact expected membership, subject counts, gap counts, typed links,
   population digest and gap digest agree with the verified census. A missing, duplicate,
   extra, foreign or reclassified gap refuses sealing. Retry of identical content reuses
   the manifest; conflicting content under the same scope refuses.

Manifest admission assembles existing owner decisions. It performs no new financial
confirmation and therefore may run as bounded background work. The worker still revalidates
active owner authorization from the initiating request; an internal scheduler cannot invent
or elevate an actor.

## Generation and publication

The shared worker processes deterministic manifest-member ranges. Each result either
references a checksum-verified existing per-review generation or records explicit unknown.
It may build missing disposable per-review caches through their existing services, but it
cannot confirm a review, change a manifest member or follow a mutable latest pointer.

Finalization verifies exact expected/evaluated identity and fingerprint closure through
`domain/cost_population.py`; all typed result links and canonical cache checksums;
independent acquisition/carrying/DB1/DB2 coverage; expected/completed work, result and trace
counts; sealed manifest, compatible cutoffs, algorithms and event cursor; and the existing
company publication domain guard plus CAS expectation.

Publication runs in a short READ COMMITTED transaction under the tenant/publication lock.
A later tenant event makes a valid historical generation pending for current reads but does
not erase it. Same-generation retry is unchanged. Stale, obsolete, foreign or mixed-context
publication refuses atomically.

## Reads and findings

Inventory, contribution, totals, cursors and cost findings pin one company generation.
Relations join through the typed company result rows into the existing canonical inventory
and contribution relations; they do not run FIFO or DB arithmetic again. Unknown members
remain in coverage denominators and yield no invented zero. Page and total queries use the
same generation and protected snapshot. Cost findings may consume this publication only
after its manifest and population closure verify successfully.

## Rejected alternatives

- Promoting captured publication is rejected because it explicitly lacks historical
  financial knowledge and remains `publication_eligible=false`.
- Joining independent batch publications is rejected because they do not prove complete
  population or one shared knowledge context.
- Copying all monetary rows is rejected because it duplicates canonical arithmetic and
  received values; typed references plus verified fingerprints are sufficient.
- One polymorphic member/result table is rejected because it loses typed shortest links and
  database-enforced tenant isolation.
- A tenant-only latest pointer is rejected because current and historical scopes can coexist.

## Test-first acceptance

Before migration implementation, tests must cover migration parity/downgrade refusal,
same-tenant composite links, sealing immutability and deletion protection. Service tests
must cover committed-cursor capture, exact unknown membership, replay, foreign/stale review
refusal, exact header/source gap counts and digest changes, deterministic chunk retry,
checksum corruption, rollback and concurrent CAS.
Read tests must prove one-generation page/totals/findings, pending preservation, stable
history and no enqueue/autoflush. Fixture J remains a separate release qualification.
