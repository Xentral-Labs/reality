# Feature Specification: Self-hosted Installer

**Feature Branch**: `187-self-hosted-installer`
**Created**: 2026-09-13
**Status**: Implemented (2026-09-13); manual owner steps listed in the plan's rollout section
**Language**: English
**Input**: Owner request (German, 2026-09-13): research how n8n is installed and which options are
popular, then decide what Reality should adopt so that people can install Reality themselves.

## Context and Intent

### Problem

The Site promises "Self-hostable" and the licence is MIT, but nobody outside the team can install
Reality without reading the repository. Today:

- `compose.yml` builds all seven images from source. There is no public image; the only registry
  is the private ECR used by `deploy-testing.yml` for the team's testing cluster.
- `.env.example` ships `replace-me` passwords and an empty `REALITY_MASTER_KEY`, although the
  App refuses to run in production without a valid key and loses every encrypted credential when
  the key changes.
- The smallest documented installation still starts MinIO plus an init container, exposes the
  API on 8000 and MCP on 8001 in addition to the Web App on 8080, and has no HTTPS story.
- The docs page "Local installation" is one `docker compose up` line; "Operate with Docker" is
  prose without a single copy-and-paste upgrade or backup command. The Helm chart and the Railway
  script exist in the repository but appear nowhere as installation options.

n8n, the most installed self-hosted automation tool, converged on one answer: a one-line
`curl | sh` that writes a Compose project with generated secrets, starts prebuilt images, waits for
health and prints the URL; a manual Compose path for people who want control; and an "Install
options" index that lists every supported way side by side. Its known weaknesses are the SQLite
default that later forces a Postgres migration and the missing TLS story. Reality already runs on
PostgreSQL only and can therefore do better on both counts.

### Scope

- **Published images.** CI publishes the api, web, mcp, scheduler and worker images to a public
  registry on every release tag and on `main`, with immutable version tags and a moving `latest`.
- **One-line installer.** A shell script served from the product domain creates a `reality/`
  directory with `compose.yml`, `.env` and generated secrets, pulls the pinned images, starts the
  stack, waits for the App health check and prints the App URL and the initial owner login. It is
  idempotent and carries an `--upgrade` mode.
- **Small default profile.** The default installation runs PostgreSQL, the migration step, the
  API, the Web App, the invitation worker, the scheduler and the worker. Source binaries use the
  existing `file` artifact backend on a named volume. MCP is part of the default stack, keeps
  its origin-root contract and listens on loopback until a domain is set. MinIO becomes an
  opt-in profile.
- **One public port and optional HTTPS.** Only the Web App is reachable from outside the host.
  When the operator provides a domain, a reverse proxy with automatic certificates terminates TLS
  for the App and for MCP on its `mcp.` subdomain, and the cookie and origin settings follow.
- **Upgrade and backup as commands.** The installation directory carries one command each for
  stop, start, upgrade, backup and restore. Backup covers the database, the artifact volume and
  the `.env` file that holds the master key.
- **Documentation.** "Installation & Operations" gains an "Install options" index (One-line
  setup, Docker Compose, Kubernetes with Helm, Railway) in English and German, the environment
  reference documents the generated variables, and the Site states what self-hosting means:
  same images as the cloud, MIT licence, no feature gating.

### Non-Goals

- No `pip install reality` or `npm install` path. n8n deprecates its npm install with 3.0, and
  Reality's Python core plus Node front ends offer no sensible single-runtime install.
- No SQLite or other database. PostgreSQL stays the only database (AGENTS.md rule 9).
- No managed cloud provisioning, no Terraform, no Kubernetes operator and no multi-node Compose.
  The Helm chart keeps its current contract and is only listed, not changed, here.
- No marketplace listings (Coolify, Railway template gallery, DigitalOcean 1-Click) in this
  feature. The installer output is designed so a later template can reuse the same Compose file.
- No migration of existing MinIO-backed installations to the `file` backend. Existing operators
  keep the `s3` profile; the installer only changes the default for new installations.
- No licence keys, telemetry, "registered community" tier or feature gating. Self-hosted Reality
  is the complete product.
- No change to authentication, onboarding admission or the demo profile beyond passing the
  variables the installer generates.

### Existing Contracts

- [Local installation](../../apps/docs/content/operations/installation.md) and
  [Operate with Docker](../../apps/docs/content/operations/deployment.md): the current public
  installation contract that this feature replaces and extends.
- [App Environment](../../apps/docs/content/reference/environment.md): variable inventory the
  installer must respect; `.env.example` stays the exact inventory of the checked-out version.
- [Infra deployment boundary](../../infra/README.md) and `helm/reality`: production shape on AWS
  and Kubernetes; unchanged, listed as install options.
- `deploy-testing.yml`: the team's testing deployment to ECR; unchanged and separate from the
  public image publication.
- Spec 003 (tenant access) and spec 146 (company setup and demo profiles): the platform admin
  variables and the demo profile the installer relies on for the first login.
- [Scheduled background work](../../docs/features/scheduled-jobs.md): scheduler and worker are
  separate deployment roles and never run migrations; the installer keeps that order.

## User Scenarios & Testing

### User Story 1 - Install Reality with one command (Priority: P1)

An operator with Docker on a Linux host or a Mac runs one command, waits for the health check,
opens the printed URL and signs in as the initial owner. No repository checkout, no image build,
no hand-edited secrets.

**Why this priority**: This is the entire promise of self-hosting. Without it the other stories
have no entry point.

**Independent Test**: On a clean 2 vCPU / 4 GB host with Docker Compose v2, run the installer,
open the URL, sign in with the printed credentials and create a demo company. Only the App port
is listening on the host.

**Acceptance Scenarios**:

1. **Given** a host with Docker and the Compose v2 plugin and no `reality/` directory,
   **When** the operator runs the installer, **Then** it creates `reality/compose.yml` and
   `reality/.env` with a generated PostgreSQL password, a valid Fernet `REALITY_MASTER_KEY` and
   a generated owner password, pulls the pinned images, starts the stack, waits until the App
   health check passes and prints the App URL, the owner email and the owner password once.
2. **Given** the installer finished, **When** the operator lists listening ports,
   **Then** only the App port is bound on a public interface and MCP only on loopback;
   PostgreSQL, API, scheduler and worker are reachable inside the Compose network only.
3. **Given** a `reality/` directory already exists, **When** the installer runs again without
   flags, **Then** it changes nothing, reports that an installation exists and prints the
   upgrade command.
4. **Given** Docker is missing, the daemon is stopped or the Compose plugin is the standalone v1
   binary, **When** the installer runs, **Then** it stops before writing any file and names the
   missing prerequisite.
5. **Given** the health check does not pass within the wait budget, **When** the installer gives
   up, **Then** it leaves the directory in place, prints the log command and exits non-zero.
6. **Given** the operator passes `--email owner@example.com`, **When** the installer runs,
   **Then** that address becomes the platform admin instead of the prompted or default value.

---

### User Story 2 - Upgrade, back up and restore with one command each (Priority: P1)

The operator upgrades to the next release, or takes a backup before doing so, without reading
the repository. A restore on a fresh host brings back companies, credentials and source binaries.

**Why this priority**: An installation that cannot be upgraded or restored is abandoned within
months. n8n's upgrade flag and the "back up your encryption key" warning are the parts operators
quote most.

**Independent Test**: Install version A, create a company with an encrypted credential and an
uploaded source file, run backup, destroy the host, install version B on a new host, restore, and
find the credential decryptable and the file traceable.

**Acceptance Scenarios**:

1. **Given** an installation pinned to version A, **When** the operator runs the installer with
   `--upgrade`, **Then** `.env` is updated to version B, images are pulled, the migration step
   completes before the API, scheduler and worker start, and the health check passes.
2. **Given** the upgrade's migration fails, **When** the installer reports, **Then** the API,
   scheduler and worker of version B do not start, the error is printed and the previous images
   remain on the host for a rollback of the application image.
3. **Given** a running installation, **When** the operator runs the backup command,
   **Then** one archive contains a PostgreSQL dump, the artifact volume and the `.env` file, and
   the command prints where it wrote the archive and that the archive contains the master key.
4. **Given** a fresh host and a backup archive, **When** the operator runs the restore command,
   **Then** the stack starts with the restored `.env`, database and artifacts, and a credential
   encrypted before the backup decrypts.
5. **Given** an `.env` without `REALITY_MASTER_KEY`, **When** the stack starts, **Then** the API
   refuses to start with the existing message, and the installer documentation says the key must
   be restored from the backup.

---

### User Story 3 - Publish under a domain with HTTPS (Priority: P2)

The operator sets a domain, points DNS at the host and gets a valid certificate, secure cookies
and correct public URLs without editing a proxy configuration.

**Why this priority**: Missing TLS is the most frequent n8n community question. Reality cookies
are secure-only in production, so a domain without TLS is not a working installation.

**Independent Test**: Run the installer with `--domain reality.example.com` on a host with a
public IP and matching DNS record; the App answers on 443 with a valid certificate and sign-in
works.

**Acceptance Scenarios**:

1. **Given** `--domain` is passed or `REALITY_DOMAIN` is set, **When** the installer runs,
   **Then** a reverse proxy service is included, ports 80 and 443 are bound instead of the App
   and MCP ports, `APP_URL` uses the domain, `MCP_URL` uses its `mcp.` subdomain at the origin
   root, and `REALITY_COOKIE_SECURE` is true.
2. **Given** no domain, **When** the installer runs, **Then** no proxy is started, the App is
   bound to the App port on the host only, and the printed URL is `http://localhost:<port>`.
3. **Given** the certificate cannot be issued, **When** the operator opens the domain,
   **Then** the proxy log names the ACME failure and the installer documentation lists the DNS
   and port prerequisites.

---

### User Story 4 - Choose an install option from the docs (Priority: P2)

A visitor opens Installation & Operations and sees every supported way to run Reality side by
side, picks one and lands on a page with copy-and-paste commands.

**Why this priority**: The Helm chart and the Railway script exist but are invisible; the Site
says "self-hostable" without a link that proves it.

**Independent Test**: Open the docs in English and German at 1440px and 390px; the index lists
four options with a one-sentence "choose this when" each; every command block on the linked
pages matches the shipped script and Compose file.

**Acceptance Scenarios**:

1. **Given** the docs sidebar, **When** the visitor opens Installation & Operations,
   **Then** an "Install options" index lists One-line setup, Docker Compose, Kubernetes (Helm) and
   Railway, each with prerequisites and a "choose this when" sentence, in English and German.
2. **Given** the One-line setup page, **When** the visitor copies the command and the stop,
   start, upgrade, backup and restore commands, **Then** they are identical to what the installer
   prints and generates.
3. **Given** the Docker Compose page, **When** the visitor follows it, **Then** the Compose file
   uses the published images, references `.env.example`, and states how to enable the MinIO
   profile and the reverse proxy.
4. **Given** the Site, **When** the visitor reads the self-hosting statement, **Then** it says
   the self-hosted product uses the same images as the cloud, is MIT licensed, has no feature
   gating, and links to the Install options page.

---

### User Story 5 - Run a manual Compose project with published images (Priority: P3)

A team folds Reality into an existing Compose project or wants every variable explicit. They copy
the shipped Compose file, fill `.env` by hand and run it with the same images the installer uses.

**Why this priority**: This is n8n's "full control" path. It also keeps the repository's own
`make dev` unchanged because developers keep building from source.

**Independent Test**: Copy the installer's Compose file and `.env.example`, set the required
values, `docker compose up -d`; the stack starts from the registry without a build step.

**Acceptance Scenarios**:

1. **Given** the shipped Compose file and a hand-filled `.env`, **When** the operator runs
   `docker compose up -d`, **Then** no image is built locally and the stack matches the
   installer's default profile.
2. **Given** the operator sets `COMPOSE_PROFILES=s3`, **When** the stack starts, **Then** MinIO
   and its init container run and the API and MCP use the `s3` artifact backend.
3. **Given** the repository developer profile, **When** a contributor runs `make dev` or
   `docker compose -f compose.yml up --build`, **Then** behaviour is unchanged: the source-built
   images and the current developer ports still work.

### Edge Cases

- The installer is run from a directory without write permission: it stops before pulling
  images and names the directory.
- The host already uses the App port: the installer prints the conflict and the `--port` flag
  and exits non-zero without starting containers.
- `--upgrade` is run in a directory that the installer did not create (no version marker in
  `.env`): the installer refuses and points to the manual Compose page.
- The operator downgrades the version in `.env` by hand: the migration step may fail; the docs
  say an application rollback does not reverse a committed migration (existing deployment
  contract) and the backup is the way back.
- Windows without WSL: the installer is a POSIX shell script and states that WSL 2 is required.
- The `file` artifact backend is shared by the API and MCP containers through one named volume;
  both must mount it at the same path or MCP cannot serve source binaries.
- A domain is set but DNS still points elsewhere: the proxy keeps retrying certificate issuance;
  the App is not reachable on plain HTTP by design.
- The generated owner password is printed exactly once; the docs explain how to reset it through
  the existing platform admin variables.

## Requirements

### Functional Requirements

- **FR-001**: CI MUST publish the api, web, mcp, scheduler and worker images to a public
  registry on every release tag and on every push to `main`, tagged with the release version
  (immutable) plus `latest` for release tags, and the short commit SHA (immutable) plus `edge`
  for `main`.
- **FR-002**: Every published image MUST report its version and commit through the existing
  `/healthz` or platform status surface so an operator can confirm what is running.
- **FR-003**: The installer MUST be a POSIX shell script in the repository, served unchanged from
  a stable URL on the product domain, and MUST pass `shellcheck` in CI.
- **FR-004**: The installer MUST verify Docker, a running daemon and the Compose v2 plugin
  before writing any file, and MUST exit non-zero with the missing prerequisite named.
- **FR-005**: The installer MUST create a `reality/` directory in the working directory
  containing `compose.yml`, `.env` and a short README, and MUST refuse to overwrite an existing
  installation unless `--upgrade` is passed.
- **FR-006**: The installer MUST generate a random PostgreSQL password, a valid Fernet
  `REALITY_MASTER_KEY`, a platform admin password and any other secret the stack requires;
  no generated `.env` may contain a placeholder value.
- **FR-007**: The generated `.env` MUST pin the installed version (`REALITY_VERSION`) and the
  Compose file MUST reference images by that variable; `--upgrade` MUST rewrite only that
  variable and re-run the stack.
- **FR-008**: The default stack MUST consist of PostgreSQL, the migration step, the API, the
  Web App, the invitation worker, the scheduler, the worker and MCP, with the migration step
  completing before any service that uses the database starts.
- **FR-009**: The default stack MUST use the `file` artifact backend on a named volume shared by
  the API and MCP containers; MinIO and its init container MUST move to an opt-in Compose
  profile `s3` that switches the backend to `s3`.
- **FR-010**: Only the Web App (or the reverse proxy when a domain is set) MAY bind a public
  host port; PostgreSQL, the API, the scheduler and the worker MUST NOT be published on the host.
  Without a domain, MCP MAY bind its own port on the loopback interface only.
- **FR-011**: MCP MUST keep its existing origin-root contract (`MCP_URL` without a path, see
  the MCP configuration and the "Connect an MCP client" guide). With a domain, the reverse proxy
  MUST serve MCP on the `mcp.` subdomain of that domain over HTTPS; the installer MUST print both
  DNS names it needs.
- **FR-012**: When `--domain` or `REALITY_DOMAIN` is given, the stack MUST include a reverse
  proxy that obtains and renews certificates automatically, binds 80 and 443, forwards to the
  Web App, and the generated `.env` MUST set `APP_URL`, `MCP_URL` and `REALITY_COOKIE_SECURE`
  accordingly.
- **FR-013**: The installer MUST wait for the App health check with a bounded budget and MUST
  print the App URL, the owner email and the generated owner password exactly once on success.
- **FR-014**: The installation directory MUST provide stop, start, upgrade, backup and restore
  commands; backup MUST produce one archive with the PostgreSQL dump, the artifact volume and
  `.env`, and restore MUST rebuild a working installation from that archive on a fresh host.
- **FR-015**: The installer MUST support `--port`, `--email`, `--domain`, `--version` and
  `--upgrade`, and MUST print usage on an unknown flag.
- **FR-016**: The installer MUST be exercised in CI against locally built images through an
  image override, covering first install, idempotent re-run, upgrade and backup-restore.
- **FR-017**: The docs MUST provide an "Install options" index and one page per option
  (One-line setup, Docker Compose, Kubernetes with Helm, Railway) in English and German, and the
  commands on those pages MUST be generated from or verified against the shipped script and
  Compose file so they cannot drift.
- **FR-018**: The environment reference MUST document every variable the installer generates,
  including `REALITY_VERSION`, `REALITY_DOMAIN`, `REALITY_ARTIFACT_DIR` and the `s3` profile.
- **FR-019**: The Site MUST state that self-hosted Reality uses the same images as the cloud,
  is MIT licensed and has no feature gating, and MUST link to the Install options page, in
  every Site language.
- **FR-020**: The repository developer profile (`make dev`, source-built Compose) MUST keep
  working unchanged; the installer's Compose file is a separate artifact, not a rewrite of the
  developer file.

### Key Entities

- **Installation directory**: `reality/` with `compose.yml`, `.env` (pinned version, generated
  secrets), `README.md` (the five commands), created once and updated only by `--upgrade`.
- **Published image**: one per deployment role, addressed as `<registry>/reality-<role>:<tag>`.
- **Profile**: the Compose profile set: default (`file` artifacts, no proxy), `s3`, `proxy`.

## Success Criteria

- **SC-001**: On a clean 2 vCPU / 4 GB Linux host with Docker installed, the installer reaches a
  passing health check and a successful owner sign-in in under 10 minutes including image pulls,
  with no manual edit of any file.
- **SC-002**: After a default installation exactly one public host port is listening for Reality
  plus MCP on loopback; after a domain installation exactly ports 80 and 443.
- **SC-003**: Upgrade between two consecutive published versions requires one command and no
  manual step; the CI installer test proves it on every pull request that touches the installer,
  the Compose file or a migration.
- **SC-004**: Backup and restore across hosts keeps an encrypted credential decryptable and an
  uploaded source binary traceable from Reality to SourceRecord.
- **SC-005**: Every command block on the installation docs pages equals the shipped script output;
  a drift fails CI the way stale Tool Usage pages already do.
- **SC-006**: The Install options index renders at 1440px and 390px in English and German without
  horizontal overflow of its own.

## Assumptions and Dependencies

- **Registry (decided 2026-09-13)**: GitHub Container Registry under the repository's
  organisation, `ghcr.io/xentral-labs/reality-<role>`. Publishing from the existing GitHub
  Actions with the repository token needs no new credentials. The team's ECR testing deployment
  stays as it is.
- **Installer URL (decided 2026-09-13)**: `get.runreality.ai` redirects to the `install.sh`
  asset of the latest GitHub Release. The installer is thereby coupled to the release it
  installs and independent of Site deployments.
- **Versioning (decided 2026-09-13)**: semantic tags starting at `v0.1.0`, minor per feature
  batch, patch for fixes, created manually as a GitHub Release with short notes. Release tags
  produce the version tag and `latest`; pushes to `main` produce the short SHA tag and a moving
  `edge`. `--version` accepts either form.
- **Reverse proxy**: Caddy is assumed because it issues and renews certificates without extra
  configuration; the plan confirms it and the two-hostname proxy setup.
- **MCP on a subdomain, not a path**: the MCP configuration rejects an `MCP_URL` with a path
  ("must use the origin root without an extra path") and the connect guide teaches the origin
  root. A path prefix would reopen that hardening contract for no operator gain, so the domain
  installation uses `mcp.<domain>` through the same proxy and needs two DNS records.
- **File artifact backend across two containers**: assumed correct as long as both containers
  mount the same named volume at `REALITY_ARTIFACT_DIR`; the plan verifies concurrent access.
- **Version surface**: `/healthz` or the platform status endpoint may need a version field; the
  plan decides whether that is a spec impact on the platform status contract.
- **First login without email**: the platform admin variables already create the first owner.
  Invitations stay pending until an email provider is configured; the docs state this.
- **Follow-ups recorded for the owner, not part of this feature**: Coolify and Railway template
  listings; a DigitalOcean or Hetzner one-click; scheduled off-host backups; an `--uninstall`
  mode that removes volumes after the same double confirmation the danger zone uses (spec 186);
  a health page that shows the running version and available upgrade.
- **Gaps against n8n's first-run experience, recorded 2026-09-13 for the owner**: n8n asks for
  nothing at install and lets the owner sign up in the browser (or pre-provisions from
  environment variables), lets an owner copy an invitation link when no SMTP is configured, and
  resets the owner password from the CLI. Reality creates the owner from `.env` with a printed
  password, logs invitations without an email provider instead of offering a copyable link, and
  has no password change or reset. Candidate follow-ups: a copyable invitation link in the App
  when no email provider is configured; a password change in the App and an operator reset
  command; optionally a browser first-run owner setup as an alternative to the printed password.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001 | `.github/workflows/publish.yml`; `scripts/test_publish_workflow.py` |
| FR-002 | `services/platform.py` (`running_version`, `running_commit`), `web/app.py` system status; `tests/test_platform_admin_overview.py`, `tests/test_http_boundary.py`; Dockerfile `ARG`/`ENV`/labels |
| FR-003, FR-004, FR-005, FR-006, FR-007, FR-013, FR-015 | `installer/install.sh`; `installer/tests/test_install_sh.py` (16 dry-run proofs); shellcheck in `.github/workflows/installer.yml` |
| FR-008, FR-009, FR-010, FR-011 | `installer/compose.yml`, `compose.direct.yml`, `compose.proxy.yml`, `compose.s3.yml`, `Caddyfile`; `installer/tests/e2e.sh` port assertions |
| FR-012 | `install.sh` `write_env` domain branch; `test_domain_selects_proxy_mode_with_https_and_mcp_subdomain` |
| FR-014 | `install.sh` `cmd_backup`, `cmd_restore`; `installer/README.md`; `e2e.sh` backup, destroy, restore steps |
| FR-016 | `.github/workflows/installer.yml` end-to-end job running `installer/tests/e2e.sh` against locally built images |
| FR-017, FR-018 | `apps/docs/content/operations/{index,installation,docker-compose,kubernetes,railway,deployment}.md` (en, de), `reference/environment.md` (en, de), sidebar in `.vitepress/config.mts`; `apps/docs/scripts/install-options.test.mjs` |
| FR-019 | `provider-site/src/PlatformPage.tsx` self-hosted card, `localization.tsx` de/nl/es; Site i18n audit |
| FR-020 | root `compose.yml` and `make dev` untouched; `tests/test_repository_layout.py`, `apps/docs/scripts/docs-deployment.test.mjs` green |

## Verification (2026-09-13, Docker Desktop 27.3.1 on macOS, arm64)

`installer/tests/e2e.sh` against images built from this branch: install on port 18080 with the
owner passed by flag, health check passed, `/api/v1/system/status` reported the build tag,
published ports were exactly the App port and MCP on `127.0.0.1`, second run reported the existing
installation, owner sign-in and company creation succeeded, backup archive written, containers,
volumes and directory destroyed, restore on the empty directory brought the company, an artifact
marker and the unchanged master key back, upgrade to the second build tag repinned `.env` and
the status endpoint reported the new version. Exit 0.

### FR-013 regression clarification (PR #260)

The App readiness check must include the Web proxy, not only its API dependency.
A healthy API with a still-starting Web container must not produce the success message.
The published `/healthz` route must be usable when install/start/restore/upgrade returns.
Regression proof: `test_success_waits_for_web_proxy_health` covers delayed and failed
Web readiness; the existing installer end-to-end story exercises the real published port.
