# Data Model: Persistent macOS Distribution Increment 2

No business table or column is added.

## Operational installation manifest

- Opaque installation ID and layout version.
- Bound owner ID and recorded application version.
- Active data-generation ID.
- Keychain service/account identifiers, never secret values.

## Data generation

- Opaque generation ID and PostgreSQL directory.
- Source generation, source/target application versions and schema revisions.
- State: `preparing`, `restored`, `migrated`, `validated`, `active`, `retained`, or
  `discarded`.
- Checkpoint and manifest digests plus timestamps.

Only `validated` may transition to `active`. A failure before atomic activation leaves
the previous generation active. A generation is never interpreted as business truth;
it is a storage container for the same tenant-scoped records.

## Keychain custody

Two generic-password items belong to one opaque installation: database credential and
vault master key. Their stable service/account coordinates may be recorded; their
values may not. Missing or unreadable custody fails closed and never creates a new key
for an existing installation.

## Encrypted backup artifact

- Format version and authenticated encryption algorithm are fixed by the envelope.
- The encrypted manifest binds installation ID, application version, schema revision,
  archive byte count and SHA-256 digest.
- The encryption key is derived from the installation vault key with a backup-specific
  HKDF context; it is never persisted in the artifact.
- Decrypted archives exist only as private staging files and are removed after admission
  or failure.

## Unsigned beta channel marker

- Immutable packaged channel: `unsigned-tester-beta`.
- Visible prerelease version and product label; stable production bundle identifier.
- Contains no credential, installation identity or user-controlled value.

Only packaging creates this marker. Its absence selects normal signed custody; runtime
arguments and environment variables cannot select beta custody.

## Temporary beta custody record

- Bound opaque installation ID and fixed format version.
- Generated database password and vault master key only.
- State is implicit: absent before first beta initialization, present and valid while the
  beta owns custody, or removed only after exact Keychain readback succeeds.
- Atomic regular file owned by the current user with mode `0600`; symlinks, extra fields,
  invalid permissions and identity mismatches are rejected.

The record is operational installation state, not a business entity or backup member.
