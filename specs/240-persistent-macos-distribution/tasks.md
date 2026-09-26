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

## Phase 4: Convergence

- [x] T011 [US2] [FR-007, SC-002] Complete validated upgrade recovery by testing prior-version
  fixtures, checkpoint integrity, low-disk and interrupted migrations first, then restore the
  matching application/data checkpoint automatically while writers remain blocked.
- [ ] T012 [US5] [FR-008, SC-002] Add encrypted, versioned backup and staged restore with
  integrity, installation, schema and credential-recovery validation; prove corrupt, newer,
  incomplete and wrong-key archives leave active data unchanged (missing).
- [ ] T013 [US1, US3] [FR-006, SC-003, SC-005] Replace the retained password file and existing
  desktop credential custody with installation-owned macOS Keychain entries; test denied or
  missing custody, exact-installation erasure and secret absence from arguments, storage,
  logs and API reads before removing the transitional file path (missing).
- [ ] T014 [US1] [FR-004, SC-001] Run and record twenty consecutive real packaged
  quit/reopen cycles, including sleep/wake and forced termination, proving stable tenant data
  and zero orphan Reality or PostgreSQL processes (partial).
- [ ] T015 [US5] [FR-013, SC-005] Implement an opt-in, locally reviewable diagnostic export
  whose default scope excludes credentials and business payloads, with explicit selection
  for any expanded scope and automated secret/payload scanning (missing).
- [ ] T016 [US4] [FR-010, FR-016, SC-004] Produce versioned reproducible app and DMG
  manifests, sign every nested component with Developer ID and Hardened Runtime, notarize and
  staple the artifact, and fail qualification on undeclared inputs or invalid signatures
  (missing).
- [ ] T017 [US4] [FR-011, SC-004] Qualify every supported macOS/Apple-Silicon combination on
  clean machines without Homebrew, developer tools or an existing PostgreSQL installation;
  retain install, first-use, Gatekeeper and offline-verification evidence (missing).
- [ ] T018 [US2, US4] [FR-012, SC-002, SC-004] Select and document the signed-update
  framework, then test verified download, staging, disk-space, process-stop, migration and
  rollback failures without mixed releases or data loss (missing).
- [ ] T019 [US4] [FR-014] Publish the HTTPS download contract with version, release date,
  supported systems, checksum, release notes, installation and local-data guidance, backup
  status and exact full-erasure instructions only after the release gates are green (missing).
- [ ] T020 [US4] [FR-015] Re-run the shared company, Demo Data, live scheduler/worker and
  optional Anthropic onboarding acceptance against the release-qualified persistent artifact;
  verify no desktop-only business service or browser job authority was introduced (partial).

## Phase 5: Named-tester beta

**Independent acceptance**: On a clean supported Mac, install the explicitly labelled
ad-hoc beta through Finder's manual-open flow, create a company, reopen it ten times,
then install a simulated signed successor and prove the exact custody values moved to
Keychain without changing business records.

- [x] T021 [US6] [FR-017, SC-006] Add failing package-contract tests in
  apps/desktop/tests/test_packaged_installation.py for explicit beta opt-in, visible beta
  name/version/channel marker, bundled manual-open guidance and unchanged production bundle ID.
- [x] T022 [US6] [FR-017, SC-005, SC-006] Add failing custody tests in
  apps/desktop/tests/test_beta_custody.py for atomic `0600` creation/readback, exact-value reuse,
  and rejection of symlinked, malformed, missing-on-existing-installation or permissive records.
- [x] T023 [US6] [FR-017] Implement the installation-scoped generated-secret custody adapter
  in apps/desktop/scripts/beta-custody.py and select it only from immutable packaged channel
  metadata in apps/desktop/scripts/local-runtime.py; never accept a runtime flag or environment switch.
- [x] T024 [US6] [FR-006, FR-017, SC-006] Add migration failure tests first, then extend
  apps/desktop/src-tauri/src/keychain.rs and apps/desktop/src-tauri/src/main.rs so a signed
  successor writes and reads back both exact beta values before Python removes the custody record.
- [x] T025 [US6] [FR-017, SC-006] Package the opt-in beta channel, persistent in-product warning
  and tester guide through apps/desktop/scripts/package-preview.py and apps/web/src/App.tsx without
  adding desktop-only business rules.
- [x] T026 [US6] [FR-017] Add release-workflow policy tests and update
  apps/desktop/tests/test_release_workflow.py and .github/workflows/macos-release.yml so tester
  artifacts have a separate non-public artifact name and can never enter tag, pre-release, public
  download or auto-update publication paths.
- [ ] T027 [US6] [FR-017, SC-005, SC-006] Run and record the clean-Mac/manual-open flow, ten
  restart cycles, custody permissions, secret/payload scans, interrupted migration cases and exact
  erasure in specs/240-persistent-macos-distribution/verification.md before sharing the beta.

### Phase 5 dependencies

T021 and T022 are test-first and may run in parallel. T023 depends on T022. T024 depends
on T023. T025 depends on T021 and T023. T026 may run in parallel with T024–T025. T027 is
the final gate and depends on T021–T026. No Phase 5 task changes the T016/T017 public-release gates.
