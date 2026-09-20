# Retained captured review basis: storage proposal

Status: owner explicitly approved the three tables and staged implementation in this conversation on 2026-09-19. Implementation evidence is recorded in tasks.md.
Scope: FR-007/012/014/019, continuation after T178–T181. This retains a captured review
selection. It is not the historical financial input manifest accepted by company publication.

## Decision

Add three typed, tenant-scoped tables: a retained basis header, inventory members and
contribution members. Reuse the retained census and existing confirmed review/input
history. Persist the exact selected identities, verification metadata and missing-input
explanations. Do not copy calculated EK, acquisition value, carrying value, DB1 or DB2
into authoritative tables. Monetary results remain derivable from the referenced inputs.

Why: the current resolver returns a deterministic vector, but it has no durable identity
that a later report can reference. Re-running latest-review selection is not the same
contract as loading a pinned selection. A digest alone cannot retain that selection.

## Alternatives evaluated

| Alternative | Decision |
|---|---|
| Reuse cost_input_manifest | Reject: its required knowledge_at and receipt admission contract cannot honestly describe this captured observation vector. |
| Add the vector to cost_company_census | Reject: census is already sealed, may predate resolution and has a separate schema/version/authority boundary. |
| Reuse disposable generation rows | Reject: clearing calculation caches must not discard the pinned review selection. |
| Store one untyped JSON object | Reject: review/member FKs, uniqueness and paged inspection would be lost. |
| Store only review IDs or a digest | Reject: loses unknown subjects, selected-context/gap explanations and integrity binding. |
| Store another copy of all financial inputs | Reject: reviewed input history already exists; references are the shortest true link. |

## Tables

All tables have opaque UUID-based id, tenant_id, same-tenant identity uniqueness, scoped
indexes and composite foreign keys with restrictive deletion. Human numbers are never keys.

### cost_captured_basis

- census_id: same-tenant FK to cost_company_census; the existing census holds context,
  observed values, sources and the effective/event boundary. Do not duplicate its times.
- request_id: internal retry key, unique with tenant_id; maximum 128 characters.
- request_hash: binds census ID, fixed basis version and explicit subject/byte bounds.
- basis_version: fixed supported assembly version, initially captured-review-basis-v2.
- state: building or sealed; sealed_at is present exactly for sealed rows.
- inventory_count, contribution_count: nonnegative, combined maximum ten in this stage.
- basis_digest: canonical content integrity binding, independent of lifecycle metadata.
- observations: versioned JSONB allowlist containing coverage, coverage_scope and exact
  source/header gaps from the verified assembly. These are derived observation metadata,
  not financial facts. No money, source payload or caller-supplied approval flag.

Sealing is only an atomic completeness/integrity transition. It grants no financial
approval, supported historical knowledge_at, live freshness or publication permission.

### cost_captured_inventory_basis

- basis_id: same-tenant FK to cost_captured_basis.
- item_id: same-tenant FK to item; unique with tenant_id/basis_id.
- review_id: nullable same-tenant FK to cost_inventory_review.
- observations: exact versioned vector metadata: state, selected review content hash,
  own knowledge time, policy/profile/link metadata, canonical result/historical-result
  digests, ordered freshness proof and explicit gaps.
- content_hash: canonical member digest binding typed identities and observations.

The item is required even when review_id is absent. No per-item policy FK is duplicated:
actual policy and authority remain reachable through review_id. Metadata repeats the
observed context only to explain and verify the selected version. Validate policy-to-item
identity through its shortest existing link when sealing/replaying.

### cost_captured_contribution_basis

- basis_id: same-tenant FK to cost_captured_basis.
- document_line_id: same-tenant FK to document_line; unique with tenant_id/basis_id.
- review_id: nullable same-tenant FK to cost_contribution_review.
- observations and content_hash: same versioned vector contract as inventory.

Do not add Document, Source, revenue-basis, inventory-review or policy FKs here. Reach
these through the original line/review and retained census. The service verifies exact
line-to-review/revenue-basis identity, captured membership and linked inventory context.
Unknown service/credit candidates stay present with nullable review and explicit gaps.

SQL enforces tenant FKs, duplicate-member refusal and sealed immutability. Service
verification additionally proves exact census membership, subject/review correspondence,
vector shape, counts and content. A successful FK check alone is never a sealed proof.

## Canonical version and lifecycle

Version 1 currently hashes retained=false and publication_eligible=false with its vector.
Do not persist that payload and silently flip a hashed flag. Introduce explicit version 2:
its digest covers version, census context, typed vectors, coverage and gaps only. Lifecycle
fields sit outside the content digest. Read-time assembly reports retained=false; a durable
read reports retained=true plus its basis_id. Both remain publication_eligible=false.

Keep an explicit version-1 digest verifier for existing exported version-1 responses;
never relabel a v1 digest as v2. No persisted v1 basis exists to backfill. The immutable
census schema and existing selected financial review versions are unchanged.

## Shared service and transactions

Implemented internal entrypoints in services/costing.py:

- retain_captured_cost_basis(session, tenant_id, census_id, request_id, max_subjects=10).
- captured_cost_basis(session, tenant_id, basis_id): bounded metadata/verified membership.
- replay_captured_cost_basis(session, tenant_id, basis_id): explicit canonical financial
  reconstruction against pinned reviews, with result-digest verification.

These accept identities and bounds, never client-provided vectors, booleans or amounts.
No public mutation tool, job or company setup hook is introduced by this proposal.

1. Require a clean caller-owned REPEATABLE READ transaction and strict subject bounds.
   Validate tenant and request key before any write. Foreign records behave as absent.
2. On retry, verify the stored request/content and return the same basis. Changed arguments
   refuse. Do not rerun latest selection or reinterpret an old request under new rules.
3. For a new request, call the existing verified resolver once in that snapshot. Exact
   expected subjects come from its census collector, independently of successful reviews.
4. In a savepoint, insert building header and both typed member families; verify all
   content, exact membership, versions and bounds, then seal. A caught error followed by
   outer commit must not leave partial state. The caller owns final commit or rollback.
5. Enforce at most ten combined subjects, 1 MiB canonical data per member/header and
   8 MiB for the complete retained basis. Refuse overflow; never truncate. These are
   admission limits, not claims about peak memory or reference-scale performance.
6. Concurrent identical requests are constrained by the tenant/request unique key. On
   serialization/unique conflict, retry only after rollback in a fresh transaction.
7. No new business event is emitted: recording a reproducibility reference changes no
   financial input or review. Avoid making the act of retention invalidate its own basis.

## Reads, replay and retention

Metadata/membership reads are SELECT-only, verify canonical stored content and return
all members within the ten-subject bound. They do not run costing, flush, enqueue work
or invoke latest-review selection. They preserve unknown rows and source/header gaps.

Explicit financial replay uses each stored review_id, including the stored distinction
between available and historical-only results. Existing canonical inventory/contribution
readers verify retained inputs and perform all arithmetic. Reconstructed result digests
must match; mismatch, missing dependencies or unsupported versions refuse explicitly.
Never select a newer review or silently rewrite the retained digest. Algorithm changes
need a declared version and an explicit historical replay compatibility strategy.

Protect sealed header and members from direct SQL update/delete and new-member insertion.
References retain the census and selected reviews/input chains independently of disposable
calculation caches. No automatic retention cleanup is introduced. The downgrade refuses
populated retained history; an empty upgrade/downgrade/upgrade must remain supported.

## Tests before implementation

| Area | Required proof |
|---|---|
| Domain/version | v1 verification; v2 lifecycle-independent digest; exact order/Decimal/UTC semantics; versions and size limits refuse. |
| Migration | ORM/schema parity, same-tenant FKs, uniqueness, sealed SQL immutability, empty round trip, populated downgrade refusal. |
| Atomicity | rollback and caught-failure savepoint; no partial basis; same-request replay; changed request; concurrent fresh-transaction retry. |
| Membership | exact census sets including unknown subjects; missing/extra/duplicate/substituted/wrong-review members refuse. |
| Isolation | foreign census/basis/review FK refusal; every public service classified and exercised in the tenant catalog. |
| Replay | fixture A stock 420, DB1 570, DB2 456 when supported; missing DB2; old pinned basis unchanged by later reviews/evidence; corrupted dependency refuses. |
| Read behavior | metadata performs no costing/flush/write; replay performs no approval/write; independent coverage and external gaps preserved. |
| Integration | existing census/resolver/generation/finance regressions, executable schema/resource documentation, generator reproducibility and spec/lint gates. |

## Approval and delivery boundary

The owner approved the financial input model and five census tables earlier. This proposal
adds a distinct durable captured-selection family with different knowledge semantics;
that earlier approval did not explicitly cover these three tables. The owner subsequently
answered yes to this concrete proposal on 2026-09-19. This approves the three tables,
version-2 content boundary and staged implementation/tests.
No live migration, policy activation, financial confirmation, deployment or release is
part of this approval. Choose the migration revision only after checking current heads.

After retention is implemented, company reporting still needs a supported common financial
context, economic candidate inclusion/exclusion, exact population closure, disposable
outputs and atomic publication. A retained captured basis cannot be passed directly to
CompanyGenerationBasis or falsely advertised as complete company coverage.

## Delivered storage boundary

Migration 0078_captured_cost_basis follows 0077_company_cost_census; it implements
exactly the three approved tables with SQL immutability and populated downgrade refusal.
All three services require a clean REPEATABLE READ caller transaction. Retention uses a
savepoint, while the caller owns commit. Metadata reads validate the existing retained
census and pinned subject/review references without financial calculation. Census
verification retains its existing 100,000-record/64-MiB admission boundary; a ten-subject
basis is not a claim of constant-time census verification or a report-ready company scan.

Replay passes verified pinned review rows through the existing resolver, bypassing latest
selection and comparing the complete version-2 basis digest before returning results.
No API/UI mutation surface, job, company generation or live policy activation was added.
