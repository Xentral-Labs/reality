# Verification: Persistent macOS Distribution — Increment 1

**Date**: 2026-09-21
**Scope**: User Story 1 and the non-destructive half of User Story 3. Distribution
signing, notarization, updates, Keychain custody and the website contract are not
covered and are listed as unmet below.

| Check | Result | Evidence |
|---|---|---|
| Desktop Python suite | 47 passed | `.venv/bin/python -m pytest apps/desktop/tests -q` |
| Ruff on apps/desktop | All checks passed | `ruff check --no-cache apps/desktop` |
| Ruff format on changed files | Clean | `ruff format --check` on the nine touched files |
| Rust formatting | Passed | `cargo fmt --check` |
| Spec policy | Passed | `python3 scripts/check_spec_policy.py` |
| Native shell rebuild | Compiled, 48 s | Rust 1.98.1, Tauri 2.11.5, isolated toolchain |
| Lifecycle against the built runtime | Passed | evidence/persistence-run.json |
| Packaged application quit and reopen | Passed | evidence/application-cycle.json |
| Recovery from a forced quit | Passed | evidence/forced-quit.json |
| Release build with the current core | Passed, migration 0088 | evidence/release-build.json |
| Reopening straight after a quit | Passed | evidence/release-build.json |

## What the runs actually did

**Lifecycle (evidence/persistence-run.json)**: against a real Application Support base,
the first start created installation `605bfeb1…`, migrated to `0069_inventory_generations`
and created a company. The second start returned the same owner and the same company and
reported `identity_is_stable: true`. A second concurrent start was refused. Raising the
application version from 0.1.0 to 0.2.0 moved the checkpoint count from 0 to 1 before
migration. Erasure removed the installation, kept an unrelated file beside it and kept
the base directory. PostgreSQL never listened on TCP in any run.

**Packaged application (evidence/application-cycle.json)**: the ad-hoc signed
`Reality Local.app` was launched, a company was created through the real service against
the application's own running cluster, and the application was quit. The data directory
remained, no PostgreSQL process survived, and the next launch reused installation
`ba28dfc6…` with the same owner `usr_283f97acbb` and the same company
`ten_2b7cac8108` — "Company From The App". The bundled erasure command then removed it.

**Forced quit (evidence/forced-quit.json)**: the shell and every Python supervisor were
killed with SIGKILL. PostgreSQL was left genuinely orphaned with a live pid file. The
next launch stopped that process, started a new postmaster and read the company back.

**Release build (evidence/release-build.json)**: the artifact published for testers was
assembled from the current core wheel, the current web frontend and a release-profile
shell. Its cluster reaches `0088_tenant_scoped_keys`. The database was serving 1.2 s
after launch, a quit took 3.8 s and left no database process, and reopening took 0.6 s
and returned the same company.

Two defects surfaced while verifying that build and were fixed here. Reopening
immediately after a quit hit the installation lock while the previous process was still
stopping, so a start now waits up to 60 seconds for that shutdown instead of refusing.
The native shell turned any failed start into a non-unwinding Rust panic and a macOS
crash report; it now prints the reason and exits.

## Boundary

The earlier runs used the core wheel built on 2026-09-19, which stops at migration
`0069_inventory_generations`. The release build above carries the current
`0088_tenant_scoped_keys`.

Twenty consecutive cycles under SC-001 were not run; three application launches and
three scripted lifecycle runs were. Everything below is not implemented:

- FR-006 Keychain custody. The cluster password is a `0600` file in the installation.
- FR-007 validated checkpoints. A `pg_dump` is written before a changed version
  migrates and the newest three are kept, but it is neither validated nor restored
  automatically, and a failed migration does not roll back.
- FR-008 backup and restore as a product surface.
- FR-010 Developer ID signing, Hardened Runtime, notarization, stapling. The package is
  ad-hoc signed and requires the tester to clear quarantine manually.
- FR-011 clean-machine qualification. Every run above happened on the development Mac.
- FR-012 signed updates. A new version is a new download.
- FR-013 diagnostics, FR-014 the website download contract, FR-016 release manifests.

No business schema, service, tool or web behavior was changed. No migration was added.
