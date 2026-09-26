# Implementation Plan: Persistent macOS Distribution — Increment 1

**Feature**: `240-persistent-macos-distribution` | **Date**: 2026-09-21 | **Spec**: [spec.md](spec.md)
**Checkout**: isolated worktree on `240-persistent-macos-distribution` from `origin/main`.
**Language**: English for repository artifacts and evidence.
**Status**: Planned for User Story 1 plus the non-destructive half of User Story 3.
No release capability, signing, notarization or public download is claimed.

## Summary

Spec 239 keeps the whole installation in a temporary directory: `runtime-smoke.smoke()`
creates the PostgreSQL cluster inside `tempfile.TemporaryDirectory`, and
`local-runtime.py` generates a fresh `uuid4()` installation identity on every start.
Quitting therefore destroys the company, and a second start would not recognize an
earlier owner even if the data survived.

This increment moves the durable state into a per-installation directory under
Application Support, makes the installation identity stable, reuses an existing cluster
instead of initializing a new one, and adds an explicit erasure command. The disposable
behavior stays reachable behind a flag so release qualification keeps its clean harness.

No business schema, service or web behavior changes. The persistent path uses the same
`--prepare` migration process, the same shared job roles and the same owner bootstrap
that already exist; only the location and lifetime of their storage change.

## Technical Context

**Languages**: Python 3.12 for the installation lifecycle; existing Rust shell unchanged.
**Storage**: PostgreSQL 17 cluster owned by one installation directory; file artifacts
beside it; a `0600` password file until Keychain custody lands.
**Testing**: pytest in `apps/desktop/tests`, plus a real start/stop/start run against the
built runtime recorded in verification.md.
**Target**: Apple Silicon, macOS 14+.
**Scale**: one installation per user by default; the layout admits more without change.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | No domain code touched; storage location only | PASS |
| Reality owns operational state | Installation metadata stays in a file, never in tenant tables (DR-004) | PASS |
| Proven schema only | No migration and no new column | PASS |
| Tenant + shared service boundaries | Existing `bootstrap_owner` and job roles are reused unchanged | PASS |
| Spec/test traceability | Each task names its FR and carries a test | PASS |
| Explainable web behavior | Web surface unchanged | PASS |
| Received values not recomputed | No calculation added | PASS |
| Smallest coherent design | One module owns the lifecycle; the disposable path is a flag, not a fork | PASS |

## Design

### Layout

```
~/Library/Application Support/ai.runreality.local/
  current                      # installation id of the active installation
  installations/<id>/
    installation.json          # id, created_at, app_version, layout_version
    secret                     # 0600 SCRAM password until Keychain custody
    data/                      # PostgreSQL cluster
    artifacts/                 # existing artifact backend
    backups/                   # pg_dump checkpoints, newest three retained
    run.lock                   # exclusive lock held while the app runs
    postgres.log
```

The Unix socket directory is not in this tree. macOS limits socket paths to about
104 bytes, which the Application Support path plus a UUID exceeds; PostgreSQL would
fail to listen. A private `0700` directory is therefore created per start under the
system temporary directory and removed on stop. It holds no durable state.

### Lifecycle

1. Resolve the base directory from the bundle identifier, read or create `current`.
2. Take an exclusive non-blocking lock on `run.lock`; a second start refuses clearly.
3. If `data/PG_VERSION` is absent, initialize the cluster and persist the password;
   otherwise reuse both.
4. Clear a stale `postmaster.pid` and stop an orphaned postmaster left by a crash.
5. Start PostgreSQL on the private socket, wait for readiness.
6. If the recorded application version differs from the running one and the cluster
   already carries data, write a `pg_dump` checkpoint before migrations run.
7. Hand the existing `core_env` to the unchanged product start path.
8. On exit, stop children, stop PostgreSQL, remove the socket directory, keep the data.

### Erasure

`installation.py --uninstall` takes the same lock, refuses while the app runs, verifies
the target carries a matching `installation.json`, and removes exactly that directory.
It never deletes the Application Support parent of another product, and it never
touches Keychain. A double-clickable `Uninstall Reality Local.command` in the bundle
calls it with a typed confirmation.

## Out of Scope for This Increment

Keychain custody (FR-006), validated checkpoint restore (FR-007), backup/restore product
surface (FR-008), Developer ID signing, notarization, stapling (FR-010), clean-machine
qualification (FR-011), signed updates (FR-012), diagnostics (FR-013), the website
download contract (FR-014) and release manifests (FR-016). verification.md lists these
as unmet rather than silently absent.

## Increment 2 Plan: Keychain Custody and Staged Upgrade Recovery

**Status**: Planned for T011 and T013. This increment does not claim portable
backup/restore, signed updates, notarization or public distribution.

### Technical context

- macOS 14+, Apple Silicon, the existing Tauri shell and bundled Python/PostgreSQL 17.
- The native process owns Security.framework access. Python receives required secret
  material only through the existing private stdin control channel; values never enter
  command arguments, browser state, logs or persisted operational manifests.
- `reality.security.secrets` gains a process-local key-provider boundary used by both
  the generic secret store and legacy AI-key migration. Hosted deployments retain their
  existing configured-key behavior.
- Persistent database storage changes from one mutable `data/` directory to immutable
  generation directories selected by an atomic `current-data` pointer. Existing
  Increment 1 installations are adopted as generation 1 without changing business data.

### Keychain design

The native shell creates or reads two installation-scoped generic-password items:
the PostgreSQL SCRAM password and Reality's secret-vault master key. Account names use
the opaque installation ID; service names use the stable bundle identifier plus a
purpose suffix. Retrieval failure is fatal and must not generate a replacement key.

The native shell passes both values to `local-runtime.py` over its already private
stdin. The runtime forwards only the required value to each child over that child's
stdin. A process-local provider supplies the vault key to `security/secrets.py`; no
environment-variable or filesystem fallback is enabled in desktop mode. Existing
hosted configuration and development fallback remain unchanged outside desktop mode.

The transitional `secret` password file is migrated only after its value has been
stored and read back successfully from Keychain. The file is then removed. Full erasure
deletes exactly the two items whose service/account pair matches the installation; a
failed or cancelled erasure retains both data and custody.

### Staged upgrade recovery

On an application-version change, the installation lock blocks all writers. Reality
creates a custom-format logical dump and validates its archive listing, manifest,
schema revision, source installation ID and available staging space. It then restores
into a fresh sibling data generation, runs migrations only against that generation and
checks database revision plus bounded product readiness before switching `current-data`
with an atomic replace.

Any dump, restore, migration or validation failure deletes only the incomplete staged
generation and leaves the previous pointer and database bytes unchanged. The newer app
shows a recovery error and does not start API, scheduler or worker against the old
schema. Successful reopening marks the switch complete; only then may retention remove
older generations/checkpoints. API, scheduler and worker startup never run migrations.

### Increment 2 touch points

- `apps/desktop/src-tauri/src/keychain.rs` and `main.rs`: native custody and private
  stdin handoff.
- `apps/desktop/scripts/installation.py`, `local-runtime.py` and a focused recovery
  helper: generation journal, validation, staging and atomic switch.
- `packages/reality-core/src/reality/security/key_provider.py`, `security/secrets.py`
  and `agent/settings.py`: shared process-local vault-key resolution without changing
  tenant-scoped secret records.
- `apps/desktop/tests/test_keychain.py`, `test_recovery.py` and focused core secret
  tests: failures first, followed by real native and PostgreSQL acceptance.

### Increment 2 Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Recovery copies stored records and original artifacts without reinterpretation | PASS |
| Reality operational authority | Generations and Keychain items remain operational state outside business tables | PASS |
| Proven schema only | No business migration or typed business field is introduced | PASS |
| Tenant and service boundaries | Existing services and tenant-scoped secret records remain authoritative | PASS |
| Specification and tests | T011/T013 require failing tests and executable acceptance evidence | PASS |
| Explainable web product | No browser business rule or alternative action path is introduced | PASS |
| Storage discipline | PostgreSQL remains the only business database | PASS |
| Received values | Recovery copies values and performs no business recomputation | PASS |

### Rollback and review gates

The active data pointer is never switched before staged validation succeeds. Removing
the Increment 2 app leaves the last active generation and Keychain entries intact.
Rollback testing covers Keychain denial/missing items, legacy-file migration, corrupt
dump, insufficient disk, killed restore, failed migration, failed readiness and crashes
immediately before/after pointer replacement. Architecture review must approve the
native/Python custody boundary before implementation; release review remains deferred.

## Increment 3 Plan: Explicit Unsigned Tester Beta

**Status**: Planned for FR-017. This increment enables named-user testing while Apple
Developer Program enrollment is unavailable. It does not satisfy or weaken the public
release gates in FR-006, FR-010, FR-011 or FR-014.

### Technical context

- The beta remains ad-hoc signed and Apple Silicon/macOS 14+ only. It uses the stable
  `ai.runreality.local` bundle identifier so a later signed app resolves the exact same
  installation; its display name, prerelease version and immutable channel marker identify
  it as an unsigned beta everywhere visible to the tester.
- Packaging requires an explicit `--unsigned-tester-beta` input. Normal persistent package
  creation continues to target Keychain custody and must fail when that custody is denied.
- The beta stores only its generated PostgreSQL password and vault master key in one atomic,
  installation-owned `0600` custody record beneath Application Support. It never stores
  Anthropic or other upstream credentials there; those remain encrypted tenant records.
- Native and Python exchange the same in-memory secret shape in both channels. The selected
  custody provider is derived from signed package metadata, never a user-controlled runtime
  flag or environment variable.

### Lifecycle and migration

1. Packaging writes a value-free beta channel marker into the signed bundle resources and
   changes the visible product name/version label. The installed app presents a persistent
   warning and the bundled tester guide explains Finder's Open/manual macOS approval flow.
2. On beta first start, the runtime creates both random values, atomically publishes the
   private custody record, verifies owner-only mode and reads it back before cluster setup.
3. Reopening requires a valid, private record. Missing, malformed, symlinked or permissive
   custody fails closed and never generates replacement values for an existing installation.
4. A signed successor finds the same installation. Native code writes both exact values to
   its installation-scoped Keychain entries and reads them back. Only an exact match permits
   removal of the beta custody record; denial or interruption leaves it intact and starts no
   business processes.
5. Full erasure quarantines the installation first and removes the active custody provider.
   Recovery follows the existing erasure journal and never claims completion for a partial
   Keychain or filesystem state.

### Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Custody packaging does not alter business records or provenance | PASS |
| Reality owns operational state | The beta marker and generated custody are installation metadata outside business tables | PASS |
| Proven schema only | No schema or typed business field is added | PASS |
| Tenant and shared services | Existing tenant-scoped services and encrypted upstream-secret records remain unchanged | PASS |
| Confirmation | Public release stays blocked; full erasure retains its explicit confirmation | PASS |
| Storage discipline | PostgreSQL remains the sole business database | PASS |
| Received values | Migration copies exact generated values and verifies equality; it never recomputes them | PASS |
| Smallest coherent design | One runtime and one installation are shared; only the custody adapter and visible channel differ | PASS |

### Test and rollback gates

Tests precede implementation and cover explicit packaging opt-in, visible warnings,
owner-only atomic storage, symlink/permission/malformed/missing rejection, absence from
arguments/logs/browser/package/backup/diagnostics, ten reopen cycles, exact Keychain
migration, interruption before and after Keychain write, and erasure. Release workflow
tests must prove that the beta artifact cannot enter the public publish job. Removing the
increment restores the existing signed-only custody path without changing business data.
