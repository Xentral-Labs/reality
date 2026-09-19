# Tasks: Reality Local for macOS

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/desktop.md.
**Status**: Isolated packaging/port spike in progress. T002 passes; T003 runtime build/assembly/smoke and ad-hoc Tauri preview packaging pass; T004 has native cookie/command-denial evidence, with release signing and clean-Mac proof incomplete. Local identity/schema and shared sessions are implemented with targeted evidence; a disposable empty-company app is integrated. Persistent onboarding, AI and release gates remain open.
**Gate**: All design Constitution rows PASS; no unresolved requirements. Tests precede implementation. Paths below the core refer to `packages/reality-core/` unless explicitly rooted.

## Phase 1: Review and packaging foundation

- [ ] T001 [FR-003, DR-003] Review identity schema and desktop threat boundary in specs/239-macos-local-app/data-model.md and contracts/desktop.md; record architecture approval in specs/239-macos-local-app/review.md before production code.
- [x] T002 [FR-001, FR-017] Add clean-layout and actual socket allocation failing proof in apps/desktop/tests/test_package.py and apps/desktop/tests/test_ports.py; include occupied sentinels, race-free binding, exhaustion and stale-generation cases.
- [ ] T003 [FR-001] Create apps/desktop/scripts/build-runtime.py, runtime-dependencies.lock and package.sh plus apps/desktop/src-tauri/Cargo.toml and tauri.conf.json; build pinned relocatable runtimes and perform the native packaging spike.
- [ ] T004 [FR-001, FR-017] Record signed nested-runtime execution, WebView cookie insertion, clean-Mac dependency and bound-socket results in specs/239-macos-local-app/evidence/packaging.md; stop downstream integration on failure.
- [ ] T005 [FR-009, FR-012, DR-004] Add failing state/manifest transition tests in packages/reality-core/tests/test_desktop_domain.py then implement pure rules in packages/reality-core/src/reality/domain/desktop.py.

## Phase 2: First company

**Independent acceptance**: Execute US1 scenarios from spec.md on an isolated prepared installation; see quickstart.md.

- [ ] T006 [US1] [FR-002, FR-003, FR-004, DR-001, DR-002, DR-003] Add failing tests in packages/reality-core/tests/test_desktop_identity.py and test_desktop_setup.py covering hosted rejection, identity migration, exact owner binding, membership, demo provenance and request replay.
- [ ] T007 [US1] [FR-003, DR-003] Add authentication_method to packages/reality-core/src/reality/db/core.py and next available migrations/versions/*_desktop_identity.py; centralize Python/SQL admission in services/account_policy.py and update services/tenant_policy.py including worker and practice selection.
- [ ] T008 [US1] [FR-003, DR-002, DR-003] Implement packages/reality-core/src/reality/services/desktop_identity.py and account_sessions.py; refactor web/auth.py issuance; deny local password/email flows and audit bootstrap without verification events.
- [ ] T009 [US1] [FR-002, FR-004, DR-001, DR-002] Implement resumable confirmed local setup through packages/reality-core/src/reality/web/desktop.py and existing services/company_setup.py; suppress legacy tenant/admin bootstrap and preserve queued initializer/live completion.
- [ ] T010 [US1] [FR-002, FR-004, FR-016] Add apps/web/scripts/desktop-onboarding-browser.mjs failing setup/keyboard/locale cases, then implement apps/web/src/desktop/LocalSetup.tsx and desktopCapabilities.ts using existing forms/localization.
- [ ] T011 [US1] [FR-002, FR-004] Run US1 independently and record setup replay/Empty/Demo evidence in specs/239-macos-local-app/verification.md.

## Phase 3: Own AI credentials

**Independent acceptance**: Execute US2 scenarios from spec.md on an isolated prepared installation; see quickstart.md.

- [ ] T012 [US2] [FR-005, FR-006, FR-007, DR-003] Add failing packages/reality-core/tests/test_desktop_ai.py and test_desktop_secrets.py for synthetic-only tests, current Anthropic adapter, no inherited fallback, tenant isolation, key replacement and denied custody.
- [ ] T013 [US2] [FR-007] Implement packages/reality-core/src/reality/security/key_provider.py and integrate security/secrets.py and legacy agent/settings.py key paths; add apps/desktop/src-tauri/src/keychain.rs with fail-closed native custody and private-pipe delivery.
- [ ] T014 [US2] [FR-005, FR-006, DR-002] Implement shared AI test/availability service in packages/reality-core/src/reality/services/desktop_ai.py and adapt agent/settings.py plus web/desktop.py; advertise only qualified Anthropic/model initially and explicitly disable managed fallback locally.
- [ ] T015 [US2] [FR-005, FR-006, FR-007, FR-016] Extend apps/web/scripts/desktop-onboarding-browser.mjs before adding provider/skip/data-flow/error/settings controls in apps/web/src/desktop/LocalSetup.tsx and LocalSettings.tsx.
- [ ] T016 [US2] [FR-005, FR-006, FR-007] Run US2 with deterministic failures and opt-in synthetic live smoke; record secret-leak/network evidence in specs/239-macos-local-app/verification.md.

## Phase 4: Secure daily runtime

**Independent acceptance**: Execute US3 scenarios from spec.md on an isolated prepared installation; see quickstart.md.

- [ ] T017 [US3] [FR-008, FR-009, FR-010, FR-011, FR-015, FR-017, DR-003, DR-004] Add failing packages/reality-core/tests/test_desktop_http.py and apps/desktop/tests/test_lifecycle.py for origins, replay, tenant isolation, sleep, child failures, shutdown, diagnostics and endpoint changes.
- [ ] T018 [US3] [FR-008, FR-009, FR-017] Implement apps/desktop/src-tauri/src/supervisor.rs and ipc.rs with lock, retained bound sockets, endpoint generation and bounded failures; implement private socket storage in packages/reality-core/src/reality/desktop/storage.py.
- [ ] T019 [US3] [FR-008, FR-003, DR-003] Implement native cookie exchange in apps/desktop/src-tauri/src/webview.rs, restricted capabilities/maintenance.json and packages/reality-core/src/reality/desktop/control.py; lock down web/desktop.py exact Host/Origin and exclude hosted account endpoints.
- [ ] T020 [US3] [FR-009, FR-010, FR-011, FR-017, DR-004] Implement packages/reality-core/src/reality/desktop/runtime.py orchestration and apps/desktop/src-tauri/src/lib.rs close/Quit/menu handling; extend jobs/health.py bound-endpoint reporting with unchanged hosted defaults.
- [ ] T021 [US3] [FR-011, FR-015, FR-016] Implement safe status/diagnostic export in packages/reality-core/src/reality/desktop/diagnostics.py and apps/web/src/desktop/LocalSettings.tsx; add keyboard/theme and redaction assertions to desktop-onboarding-browser.mjs and test_lifecycle.py first.
- [ ] T022 [US3] [FR-008, FR-009, FR-010, FR-011, FR-015, FR-017] Run US3 real-socket, different-user, sleep/wake and orphan-process scenarios; record evidence in specs/239-macos-local-app/verification.md.

## Phase 5: Recoverable maintenance

**Independent acceptance**: Execute US4 scenarios from spec.md on an isolated prepared installation; see quickstart.md.

- [ ] T023 [US4] [FR-012, FR-013, FR-014, DR-001, DR-004] Add failing packages/reality-core/tests/test_desktop_maintenance.py and apps/desktop/tests/test_recovery.py for dump/artifact/key equivalence, corrupt archive, wrong key, stage interruption, schema rollback and confirmed erase.
- [ ] T024 [US4] [FR-012, FR-013, DR-001, DR-004] Implement packages/reality-core/src/reality/services/desktop_maintenance.py and desktop/storage.py authenticated encrypted backup/staging, writer quiescence, schema validation and matched checkpoint recovery.
- [ ] T025 [US4] [FR-012, FR-013, FR-014] Implement apps/desktop/src-tauri/src/maintenance.rs signed release staging, durable pointer switch, Keychain recovery, confirmed restore/erase and retained exports; never execute general shell text from web inputs.
- [ ] T026 [US4] [FR-012, FR-013, FR-014, FR-016] Extend apps/web/scripts/desktop-onboarding-browser.mjs recovery review/failure tests then add native-maintenance UI under apps/desktop/src/Maintenance.tsx with shared presentation conventions and localized messages.
- [ ] T027 [US4] [FR-012, FR-013, FR-014, DR-001] Run US4 on two supported Macs, source-byte comparison and failed migration/restore matrix; record specs/239-macos-local-app/verification.md.

## Phase 6: Release qualification

- [ ] T028 [FR-001, FR-012] Add .github/workflows/desktop-release.yml and apps/desktop/scripts/qualify.sh for pinned builds, nested signing/notarization, artifact verification, licenses and explicit release qualification; do not publish without release authorization.
- [ ] T029 [FR-001, FR-002, FR-016, FR-017] Execute clean-Mac platform/ports and four-language/theme matrix, 20 startup runs and ten-user pilot; record SC-001/002/005 results in specs/239-macos-local-app/verification.md.
- [ ] T030 [FR-003, FR-007, FR-008, FR-012, FR-013, DR-003] Perform security/schema/recovery review against checklists/desktop-security-recovery.md and record reviewer decisions in specs/239-macos-local-app/review.md.
- [ ] T031 [FR-001, FR-015, DR-002, DR-004] Update docs/features/macos-local.md, docs/WEB_SPEC.md and affected setup/job contracts with implemented entrypoints; run catalog generation/check if executable vocabulary changed.
- [ ] T032 [FR-016, DR-001, DR-002, DR-003, DR-004] Run full PostgreSQL backend suite, Ruff, web build/i18n, native tests, migrations and spec policy per specs/239-macos-local-app/quickstart.md; review diff and record actual results in verification.md before marking any acceptance complete.

## Dependencies and execution strategy

T001 precedes production implementation. Packaging proof T002–T004 is the first executable milestone; failure stops integration. Pure domain proof T005 precedes services. US1 precedes saved tenant AI configuration; US3 consumes its identity but can use prepared fixtures. US4 depends on lifecycle/quiescence. All four stories are required for public release; US1 alone is an internal milestone.

Parallel opportunities after prerequisites: US1 identity tests and UI tests use separate files; US2 provider and Keychain tests can run independently; US3 HTTP threat cases and native lifecycle cases can run independently; US4 archive corruption tests and native maintenance UI tests can run independently. Shared files are edited sequentially; no task is marked [P] because this plan chooses serial integration.

Tasks T005, T010, T015, T021 and T026 contain an explicit failing-proof step followed by implementation; execute those substeps in that order. Their IDs may appear in both coverage columns.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/design task(s) | Status |
|---|---|---|---|
| FR-001 | T002, T004, T029 | T003, T028, T031 | Pending |
| FR-002 | T006, T010, T011, T029 | T009 | Pending |
| FR-003 | T006, T030 | T001, T007, T008, T019 | Pending |
| FR-004 | T006, T010, T011 | T009 | Pending |
| FR-005 | T012, T015, T016 | T014 | Pending |
| FR-006 | T012, T015, T016 | T014 | Pending |
| FR-007 | T012, T015, T016, T030 | T013 | Pending |
| FR-008 | T017, T022, T030 | T018, T019 | Pending |
| FR-009 | T005, T017, T022 | T018, T020 | Pending |
| FR-010 | T017, T022 | T020 | Pending |
| FR-011 | T017, T021, T022 | T020 | Pending |
| FR-012 | T005, T023, T026, T027, T030 | T024, T025, T028 | Pending |
| FR-013 | T023, T026, T027, T030 | T024, T025 | Pending |
| FR-014 | T023, T026, T027 | T025 | Pending |
| FR-015 | T017, T021, T022 | T021, T031 | Pending |
| FR-016 | T010, T015, T021, T026, T029, T032 | T010, T015, T021, T026 | Pending |
| FR-017 | T002, T004, T017, T022, T029 | T018, T020 | Pending |
| DR-001 | T006, T023, T027, T032 | T009, T024 | Pending |
| DR-002 | T006, T032 | T008, T009, T014, T031 | Pending |
| DR-003 | T006, T012, T017, T030, T032 | T001, T007, T008, T019 | Pending |
| DR-004 | T005, T017, T023, T032 | T020, T024, T031 | Pending |

SC-001/002/005: T029; SC-003: T023/T027; SC-004: T012/T017/T030; SC-006: T031/T032 plus this coverage map. Pilot outcomes are release gates, not implementation assertions.

## Spike progress (2026-09-19)

T002 proof uses the dependency-free `apps/desktop/spike/Cargo.toml` harness to compile
`apps/desktop/src-tauri/src/supervisor.rs` before Tauri integration. Packaging preflight
is in `apps/desktop/scripts/runtime_audit.py`. Evidence: verification.md and
evidence/packaging.md. T003/T004 remain unchecked; do not mistake the health-only probe
for bundled Reality roles or a distributable app.

## Runtime packaging progress (2026-09-19)

T003 now has checked standalone Python/PostgreSQL inputs, hash-locked offline Python
dependencies, native relocation/architecture/minimum-OS checks, and a real bundled
core migration smoke with pg_trgm plus dump tools. Scripts and exact evidence are in
verification.md. T003 remains unchecked because its Tauri app-shell/package portion
is still missing; T004 remains unchecked for signed clean-machine/cookie proof.

## Fresh preview test cycle

- [x] T033 [FR-018] Add copy-isolation/failure-cleanup/source-preservation tests first;
  implement test-preview.py, run two native verification cycles, document the command
  and current stateless-only boundary. Do not mark persistent profile cleanup delivered.

### Approved session extraction execution

Owner explicitly approved session integration after automatic review requested it.
The shared service retains hosted token/expiry/cookie semantics. T008 remains partial
until the native desktop adapter and bootstrap exchange are integrated and verified.


### Interactive development milestone evidence

Implemented portions of T006–T010/T019: exact local owner admission, migration 0068,
shared session issuance/revocation, exact-origin HTTP wrapper, real bundled frontend
and empty-company setup. Native and real browser acceptance pass. These parent tasks
remain unchecked because demo/live, persistent binding, custody, the full bootstrap
capability protocol and release/security coverage remain incomplete. The development
runtime is explicitly temporary and performs preparation in a separate process.

- [x] T034 [FR-019, FR-020] Extend bundled browser acceptance for Home and visible
  sidebar; enlarge and center native startup, preserve restore navigation; build,
  run browser/native checks and review the resulting development artifact.
- [x] T035 [FR-004] Extend disposable onboarding to canonical demo/live creation
  with supervised shared scheduler and worker, trusted local identity in their job
  subprocesses, actual intake verification and complete child cleanup. Merely
  exposing the setup choice without functioning background execution is insufficient.
- [x] T036 [FR-022] Add the desktop-only optional Anthropic onboarding field, save it
  through shared AI settings after company readiness, and verify secret redaction,
  configured metadata and disposable cleanup in the real packaged flow.
- [x] T037 [FR-023] Generate the native icon from the web LogoMark, declare and package
  the multi-resolution ICNS, then verify Finder/Dock metadata and native launch.
- [x] T038 [FR-024] Add failing shared setup browser assertions, then default live
  simulation on whenever demo is selected in web and desktop while preserving opt-out.
- [x] T039 [FR-025] Add failing service/API/UI assertions, then expose AI readiness,
  replace the missing-provider placeholder and link Chat to existing AI configuration.
- [x] T040 [FR-026] Compact the first-company desktop layout, add a 1440 by 960
  no-scroll browser assertion, rebuild and visually verify the disposable app.
