# Tasks: Self-hosted Installer

**Language**: English

Tests precede the implementation they prove. Stories: US1 install, US2 upgrade/backup/restore,
US3 domain and HTTPS, US4 docs and Site, US5 manual Compose.

## Phase 1 - Version surface (FR-002)

- [x] T001 Tests: `deployment_posture` and `GET /api/v1/system/status` return `version` and
  `commit` from `REALITY_VERSION` / `REALITY_COMMIT`, defaulting to `dev` and empty
  (`packages/reality-core/tests/`).
- [x] T002 Implement in `services/platform.py` and `web/app.py`.
- [x] T003 Dockerfiles api, mcp, scheduler, worker: `ARG`/`ENV REALITY_VERSION`, `REALITY_COMMIT`
  and OCI labels; web: labels only.

## Phase 2 - Installer assets (US1, US2, US3, US5)

- [x] T004 Dry-run tests `installer/tests/test_install_sh.py`: prerequisite refusal, `.env`
  without placeholders, valid Fernet key, pinned version, idempotent refusal, `--domain` proxy
  mode with secure cookie and `mcp.` URL, `--port` conflict, unknown flag usage, `--email`
  precedence, `upgrade` refusal without version marker (FR-003 to FR-007, FR-012, FR-015).
- [x] T005 `installer/compose.yml`: db, migrate, api, web, invitation-worker, scheduler, worker,
  mcp; `file` artifacts on shared volume; no host ports; migrate ordering (FR-008 to FR-010).
- [x] T006 `installer/compose.direct.yml`, `installer/compose.proxy.yml`, `installer/Caddyfile`,
  `installer/compose.s3.yml` (FR-009 to FR-012).
- [x] T007 `installer/install.sh`: install, upgrade, start, stop, logs, status, backup, restore;
  flags; secret generation; health wait; one-time credential print (FR-003 to FR-007, FR-013
  to FR-015).
- [x] T008 `installer/.env.example` and `installer/README.md` (the five commands) (FR-005, FR-014).
- [x] T009 Run T004 green; run shellcheck (container `koalaman/shellcheck` when not installed).

## Phase 3 - Publish and verify in CI (FR-001, FR-016)

- [x] T010 Test `scripts/test_publish_workflow.py`: five components, both platforms, GHCR names,
  tag rules, release asset list equals `installer/` shipped files.
- [x] T011 `.github/workflows/publish.yml`: build and push on `main` and `v*`; release assets
  on tags with `REALITY_INSTALLER_VERSION` substituted into `install.sh`.
- [x] T012 `.github/workflows/installer.yml`: shellcheck, pytest dry-run tests, end-to-end with
  locally built images (install, ports, idempotent re-run, backup, restore, upgrade).
- [x] T013 Run the end-to-end sequence locally with Docker Desktop and record the result in the
  PR body (SC-001, SC-002, SC-004).

## Phase 4 - Docs and Site (US4, FR-017 to FR-019)

- [x] T014 Drift test `apps/docs/scripts/install-options.test.mjs` (FR-017, FR-018, SC-005).
- [x] T015 English pages: `operations/index.md` (Install options), `installation.md` (One-line
  setup), `docker-compose.md`, `kubernetes.md`, `railway.md`, `deployment.md` commands,
  `reference/environment.md` variables.
- [x] T016 German edition of the same pages.
- [x] T017 Sidebar labels in `apps/docs/.vitepress/config.mts` for every docs locale.
- [x] T018 Site self-hosted card copy and link in `PlatformPage.tsx`; de, nl, es strings in
  `localization.tsx` (FR-019).

## Phase 5 - Gates and hand-off

- [x] T019 Gates: `make lint`, backend tests for touched modules, `make spec-check`, docs
  `npm run format:check && npm test && npm run build`, site `npm test && npm run i18n:audit &&
  npm run build`, existing `test_repository_layout.py` and `docs-deployment.test.mjs` green
  (FR-020).
- [ ] T020 PR with `- Spec impact: specs/187-self-hosted-installer` and the manual owner steps
  (GHCR visibility, `v0.1.0` release, `get.runreality.ai` redirect); update the spec's
  traceability table with the real paths.

## FR-013 readiness regression repair (PR #260)

- [x] T021 Observe failing delayed/unready Web regression tests.
- [x] T022 Add proxied Web health check and wait for Web in shared start_stack.
- [x] T023 Verify installer unit suite, shellcheck and real e2e install/restore/upgrade; record evidence.

PR #260 regression evidence: both new cases failed before the repair; 18 installer
tests passed afterward, along with shellcheck, 5 publish-workflow tests, 6 docs
installation tests, Ruff and spec policy. Isolated real Docker e2e completed install,
published-port health, owner sign-in, backup, destroy/restore and upgrade successfully.
Local evidence: /private/tmp/privacy188-installer-e2e.log (contains disposable test
credentials; not committed). No production or existing preview containers were changed.
