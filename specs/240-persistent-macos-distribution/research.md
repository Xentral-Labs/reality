# Research: Persistent macOS Distribution Increment 2

## Key custody

**Decision**: Let the native macOS shell own Security.framework access and deliver
installation-scoped secrets to Python through the existing private stdin channel.

**Rationale**: The native process already establishes the trusted desktop boundary.
This avoids shelling out to the `security` CLI, putting values in arguments or adding
Keychain access to browser/API code.

**Alternatives considered**: Environment variables expose a broader inherited surface;
a Python Keychain dependency duplicates native custody; retaining a `0600` key file
does not meet FR-006.

## Upgrade isolation

**Decision**: Restore the validated checkpoint into a sibling PostgreSQL data
generation, migrate and validate it there, then atomically replace a pointer.

**Rationale**: In-place Alembic execution can leave the only cluster partially changed.
A staged generation keeps acknowledged business data and original source bytes intact
until the newer application proves it can open the result.

**Alternatives considered**: Restoring over the active cluster risks a second failure;
filesystem copying is not a consistent PostgreSQL backup; relying on downgrade scripts
cannot cover arbitrary interrupted migrations.

## Checkpoint format

**Decision**: Continue using the bundled `pg_dump` custom format, add an authenticated
operational manifest, validate with `pg_restore --list`, and verify the restored schema
and application readiness before switching.

**Rationale**: The bundled tools and smoke proof already exist, and logical restore
avoids dependence on exact PostgreSQL data-directory binary compatibility.

**Alternatives considered**: Physical base backups add WAL and version-management
complexity not proven for the single-user desktop use case.

## User backup envelope

**Decision**: Wrap the validated custom-format PostgreSQL archive and a strict internal
manifest in a versioned AES-256-GCM envelope. Stream encryption and decryption through
private partial paths; publish only with an atomic rename after authentication,
installation, supported-schema, byte-count and SHA-256 checks pass.

**Rationale**: The encrypted manifest does not expose installation metadata, GCM binds
the complete archive and manifest, and streaming avoids holding a business database in
memory. A wrong key, truncation, tampering or incompatible identity cannot publish a
restore candidate.

**Alternatives considered**: Encrypting only the dump leaves operational metadata
visible; unauthenticated encryption cannot distinguish corruption from valid data;
decrypting directly into an active database violates staged recovery.
