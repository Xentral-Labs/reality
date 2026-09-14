# Feature: Shopify ingestion

## Contract

1. Read and validate the input as JSON.
2. Persist the complete payload as an immutable SourceRecord before interpretation.
3. Map only stable fields needed by core behavior into Document/DocumentLine.
4. Create one outgoing delivery Commitment per relevant item line.

Shopify order and line IDs remain external references and never become internal IDs.
Unknown fields remain losslessly available in raw payloads.

Re-ingesting the identical `(tenant, source system, source type, external ID, payload)`
returns the existing interpretation. A changed payload creates a new SourceRecord
version; it never overwrites source truth. Interpretation failures retain the source
record and become explainable issues.

Idempotency is enforced by the database over the tenant-scoped source identity plus a
SHA-256 hash of canonical JSON. Source insertion and creation of a unique ImportJob are
one transaction. Interpretation is a separate retryable transaction. Until automatic
order amendment is supported, a Shopify source version greater than one without an
existing interpretation produces `needs_review` before creating any business records.
Previous Documents, Commitments, Reservations and Movements remain unchanged. This
includes metadata-only changes and updates whose predecessor failed or was not yet
processed. SourceStream still points to the newest accepted source, not necessarily
the last interpreted one.

The fixed review explanation is visible through interpretation coverage and ImportJob
reads. Processing an already reviewed job is a no-op; explicit retries record another
review attempt but cannot bypass the guard. The synchronous Shopify helper reports
the review explanation instead of claiming stale delivery or successful interpretation.
First-version retries and already successful interpretation replays remain supported.
This guard does not repair old records or implement cancellation on initial import.
See `specs/081-shopify-update-guard/spec.md` for the bounded contract.

A tenant-scoped SourceStream owns the external identity and points to its current
SourceRecord. Moving that pointer never mutates a SourceRecord and stale/conflicting
deliveries cannot accidentally become the current version.

When Shopify supplies `updated_at`, it orders source versions. An older delivery is
stored losslessly but is not interpreted over a newer version. Equal source timestamps
with different payloads are retained and reported as conflicts. Without an upstream
version timestamp, arrival order is authoritative.

One Shopify order interpretation may create only one sales-order Document per
SourceRecord, one DocumentLine per non-null source line ID, and one customer-delivery
Commitment per interpreted DocumentLine. These constraints make worker retries safe.

Tests compare the stored decoded JSON with the complete fixture and verify tenant-local
idempotency, changed-payload versioning, and no cross-tenant collision.
