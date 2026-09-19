# Data Model: Desktop Identity and Installation State

## Business domain

No new business table, Source/Evidence/Reality field or relationship. All company,
source, demo, credential and scheduled-job records retain existing tenant scope.
Setup calls company_setup.create_company and its existing durable receipt/replay path.

## Account identity schema

Proposed additive field on existing global account identity AppUser:

| Field | Values/default | Repeated use and proof |
|---|---|---|
| authentication_method | email, local_os; non-null default email | Account admission, company eligibility, practice reads, scheduler actor eligibility and login rejection |

This is account security metadata, not a tenant business table. Check constraint
restricts values. Existing accounts backfill to email with no reinterpretation.
Local accounts keep email_verified_at NULL. The unique email column contains an opaque
`<installation-id>@desktop.invalid` technical label, never displayed as verified contact
information, used as identity, or accepted as a mail destination. The opaque user ID
is the owner binding. Password authentication for local_os is denied regardless of hash.
Local owner is not a platform administrator. Add no AccessApplication or admission-counter
side effect. Human schema review is required before applying this design.

A central account policy provides equivalent Python and SQL predicates:
email identity requires the existing status/verification rules; local_os requires
active status AND desktop mode AND exact installation-bound owner ID. Hosted mode
has no local owner binding. Membership and tenant policies remain additional checks.
Missing binding, mismatched user or corrupted manifest fails closed; never scan for
“the first active owner”. Restore validates and explicitly rebinds the restored owner.

Migration path: allocate the next free revision during implementation, descriptive
suffix `_desktop_identity.py`; do not reserve a stale numeric ID in a busy checkout.
Downgrade refuses if any local_os account exists. Hosted code rollback after migration
is safe only if local accounts cannot be admitted by that old code; otherwise restore
a matched pre-migration checkpoint. Do not claim additive schema alone makes rollback safe.

## Installation metadata (not business authority)

`installation.json`, owner-readable/writable only, outside the app:
format version, opaque installation ID, bound owner ID, setup request ID, runtime/data
format versions. Atomic write/rename with directory fsync; exclusive lock guards writes.
No secrets or business status. If setup crashes after owner commit but before file write,
recover by the unique installation technical label under the bootstrap service lock;
validate local_os and installation intent rather than creating another owner.

`maintenance.json`: operation ID, kind (update/restore), stage, old/new release IDs,
checkpoint reference and active data-generation ID. Stages:
prepared -> quiesced -> checkpoint_verified -> staged -> validated -> switched -> complete.
Every stage is durable before its irreversible next step. Any non-complete stage blocks
ordinary startup until reconciled. An exclusive maintenance lock also blocks CLI/API writers.
The normal generation pointer changes atomically only after validation; retain prior generation.

Release manifest: app/core/frontend revision, dependency versions/checksums, architecture,
minimum OS, PostgreSQL major, accepted schema revisions, backup-format version and signatures.
Backup manifest: format/release/schema versions, owner binding, source artifact checksums,
dump identity, creation UTC and encrypted master-key recovery entry. Manifest and archive
contents are authenticated; no plaintext business identifiers in the outer archive header.

## Local runtime states

Stopped -> starting -> migrating (exclusive maintenance only) -> ready.
Failures yield locked, recovery_required or degraded with safe error codes. At most
three automatic child restarts per role in five minutes, then explicit Retry. Readiness
is derived from probes; no database business fact records runtime health. Provider
availability is independent of system readiness. Stop denies new writes/claims and waits
up to 60 seconds for in-flight work before terminating roles; PostgreSQL stops last.
