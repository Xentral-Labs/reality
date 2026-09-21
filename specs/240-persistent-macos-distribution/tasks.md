# Tasks: Persistent macOS Distribution — Increment 1

**Input**: spec.md, plan.md.
**Status**: Increment 1 complete; see verification.md for actual results and for the
requirements that remain unmet. Later increments cover Keychain custody, validated
backup/restore, signing, notarization, updates and the website contract.
**Gate**: All design Constitution rows PASS. Tests precede implementation.
Paths are repository-rooted.

## Phase 1: Persistent installation

**Independent acceptance**: create a company, quit, reopen, find the same records;
see verification.md.

- [x] T001 [US1] [FR-001, FR-002] Add failing tests in apps/desktop/tests/test_installation.py
  for a stable installation identity across starts, a created layout, a refused second
  start, and preserved data after a simulated quit.
- [x] T002 [US1] [FR-003] Extract cluster initialization, start, readiness, URL and stop
  helpers in apps/desktop/scripts/runtime-smoke.py without changing its disposable
  behavior, so one implementation serves both paths.
- [x] T003 [US1] [FR-001, FR-002, FR-003] Implement apps/desktop/scripts/installation.py:
  base resolution, `current` pointer, identity file, exclusive lock, cluster reuse,
  private short-path socket directory and clean stop.
- [x] T004 [US1] [FR-004] Add failing stale-process tests, then recover a stale
  postmaster.pid and an orphaned postmaster in installation.py.
- [x] T005 [US1] [FR-005] Wire apps/desktop/scripts/local-runtime.py to the persistent
  installation by default and keep the disposable path behind an explicit flag.

## Phase 2: Upgrade safety and erasure

**Independent acceptance**: an application-version change writes a checkpoint; app
removal preserves data; the erasure command removes exactly one installation.

- [x] T006 [US2 partial] [FR-007] Add failing checkpoint tests, then write a pg_dump
  checkpoint before migrations when the recorded application version changes and retain
  the newest three.
- [x] T007 [US3] [FR-009] Add failing erasure tests for a refused erasure while running,
  a rejected foreign directory and an untouched sibling installation, then implement
  `--uninstall` in installation.py.
- [x] T008 [US3] [FR-009] Ship the erasure entry point and the tester instructions in the
  packaged application through apps/desktop/scripts/package-preview.py.

## Phase 3: Evidence

- [x] T009 [US1] Run the desktop suite plus Ruff and record results in
  specs/240-persistent-macos-distribution/verification.md.
- [x] T010 [US1] Run the real packaged application against the built runtime: create a
  company, quit, reopen, confirm the same records and no orphan process; record the
  actual output and the unmet requirements in verification.md.
