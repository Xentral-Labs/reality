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
