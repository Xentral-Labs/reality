# Implementation Plan: Agent Email Handoffs

## Scope review

The owner authorized implementation through a green PR on 2026-10-03. Preserve
existing approval rights. Receipt/capture operations record external evidence;
only dispatch authorization is a business decision. Explicitly scoped MCP mutation
permissions govern evidence intake and execution handoff without granting approval.

## Technical approach

1. Domain: Pydantic closed schemas for message envelopes, attachment references,
   exact dispatch requests, claims and reports. Preserve arbitrary external payload.
2. Storage: reuse SourceRecord/SourceStream and SourceArtifact. Attachment metadata
   belongs to each email occurrence, not the deduplicated artifact's filename.
   Add only EmailDispatch: tenant/proposal identity, opaque execution ID, approved
   fingerprint and authenticated executor claim. Results remain immutable Sources.
3. Services: email handoff service, source-backed outcomes, no provider calls. Lock
   dispatch rows for claim/report. Never release a claim automatically. Reconciliation
   produces evidence; another send requires a separately reviewed proposal.
4. Tools: ordinary email dispatch authorization proposal, workflow/history reads,
   permission-scoped direct evidence/claim/report MCP operations. All call services.
5. Files: bounded retryable chunk staging through existing artifact storage; final
   checksum required. Existing tenant deletion removes artifacts. No remote fetches.
6. Adapters/UI: existing Decisions common review exposes the exact structured payload;
   history supplies source/decision/download links. Expose shared service Web routes,
   retain safe JSON/text rendering and download disposition, never render raw HTML.
7. Docs: canonical agent workflow and generated catalogs; update source/decision/data
   contracts. Add German labels in the resource catalog.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Original messages/files/receipts are Sources; no inferred Document; send evidence is explicit |
| Operational authority | PASS | Dispatch execution is not a business Document status |
| Proven schema | PASS | One dispatch row enables atomic claim, version checking and actor-bound execution |
| Tenant/service boundaries | PASS | Composite tenant FKs, scoped reads and shared services |
| Specification/tests | PASS | Accepted scope; tests planned and written before implementation |
| Explainable Web | PASS | Existing Decisions and navigable source/history chain |
| Simplicity/storage | PASS | PostgreSQL, existing artifacts, no mailbox or provider infrastructure |
| Received values | PASS | Preserve supplied values and distinguish acceptance from delivery |

## Migration and rollback

Append migration after the current Alembic head. Existing evidence is unchanged and
not backfilled. Downgrade refuses to discard populated dispatch records; archive them
before removing the feature. Disable executor permissions before rollback. Existing
SourceArtifact retention/company deletion remains authoritative.

## Tests and review risks

Test lossless multipart/file retention, missing content, versions and retries; exact
proposal/review/approval parity; rejection and changed payload; tenant and executor
isolation; concurrent claims; accepted/failure/unknown/deviation/conflicting reports;
chunk integrity/limits/retries; both API and MCP adapters; migration round trip.
Run spec policy, lint, backend suite, web and docs gates, then inspect PR checks.
No exactly-once provider guarantee: executor must reconcile uncertainty and use
provider idempotency. No assertion of recipient delivery or independently verified
human approval.

Matching payloads across separately approved proposals also share the existing
company business lock during claim. An unresolved claimed/unknown/conflicting
send blocks another authorization/claim of identical content until reconciled.
This prevents a new proposal ID from bypassing uncertainty protection.

Outcome provenance uses one minimal `email_dispatch_receipt` relationship
(tenant, dispatch ID, source ID). Repeated report selection and reverse navigation
require this typed link: a caller-selected origin/type on a generic source import
must not fabricate executor-bound results. Only the authorized reporting service
creates the link; arbitrary imported receipts remain evidence without closing a
claim. The relationship stores no duplicate payload or derived outcome.

Graph analytics intentionally defers the personal-correspondence execution slice:
its privacy policy and report grain are separate from this operational handoff.
The graph completeness audit explicitly names both dispatch tables and the reason;
this does not remove email_history/Decisions access or hide a coverage gap.

## Mandatory business context extension

Owner approval on 2026-10-04 covers mandatory explicit linking for all relevant
business-partner roles and business objects in this same PR. No clarification or
constitutional exception is needed. Add one minimal indexed polymorphic membership
with source FK and composite tenant scope; reuse the validated-object boundary used
by Fact observations. This schema is proven by repeated object-filtered reads and
bidirectional original-evidence navigation. JSON-only payload search was rejected:
it cannot provide authoritative indexed memberships separate from arbitrary imports.

Domain requires bounded distinct references on capture and proposal. Services
validate target existence before writing, normalize reference order, persist source
memberships idempotently, inherit proposal context for actual reports, and expose
paged object history including proposals. Context is separate from original message
content and source-supported business observations; no business Facts are invented.
Existing evidence versions are not rewritten and historical context is not guessed.
A new migration follows the email dispatch migration; downgrade refuses populated
memberships. Graph analytics explicitly defers this correspondence membership slice.

API/MCP use the existing history tool and capture/proposal schemas. Inspector object
views load object-filtered correspondence through the shared read; email evidence
shows names and object routes, with full source/file navigation. Contract and schema
examples must require returned existing object IDs. Tests precede implementation.
Constitution Check remains PASS: lossless source, shortest relationship, demonstrated
schema need, tenant/service validation, accepted scope/test trace, shared UI reads,
one PostgreSQL membership table, no recomputed source values. Manual analysis finds
no unresolved critical requirement/plan/task conflicts.
