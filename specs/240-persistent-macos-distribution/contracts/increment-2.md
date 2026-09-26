# Contract: Keychain Custody and Staged Upgrade Recovery

## Native-to-runtime handoff

The native shell sends one bounded versioned JSON message over child stdin containing
the installation ID, database credential and vault master key. The runtime rejects
unknown fields, wrong installation identity, missing values and repeated initialization.
It never echoes the message or includes it in diagnostics.

## Startup

An existing installation with unavailable Keychain custody does not start PostgreSQL or
product roles. A legacy password file is removed only after an exact Keychain round trip.
API, scheduler and worker processes receive no migration authority.

## Upgrade

An application-version change blocks product roles, validates a checkpoint, restores
and migrates a sibling generation, verifies it, then switches the active pointer
atomically. Failure before switching preserves the previous pointer. Failure after the
atomic switch is reconciled from the durable journal; it is never guessed from process
state alone.

## Erasure

Confirmed erasure removes only the selected installation's data generations and exact
Keychain service/account pairs. Any mismatch or Keychain failure stops erasure without
claiming completion. Unrelated installations and Keychain entries are untouched.

## Backup admission

A backup is one versioned authenticated-encryption envelope containing a strict
manifest and a PostgreSQL custom-format archive. Restore decrypts only to a private
staging path and publishes that candidate only after authentication, exact installation
identity, supported schema, byte count and digest all pass. Failure removes the partial
plaintext and cannot change the active generation.

The native maintenance entrypoint obtains database and vault custody through the same
private Keychain handshake as normal startup. Backup needs no mutation confirmation.
Restore requires an explicit confirmation flag and runs without API, scheduler, worker
or WebView startup until staged activation succeeds.
