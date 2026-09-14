# Implementation Plan: Self-hosted Installer

**Branch**: `187-self-hosted-installer` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)
**Language**: English

## Summary

Publish the five runtime images to GHCR from a new release workflow, ship one POSIX installer
script plus a small Compose asset set as GitHub Release assets, and document four install
options. The only Python change is a version and commit field on the existing system status and
deployment posture so an operator can see what runs. No schema, no new service, no new business
rule.

## Technical Context

**Language/Version**: POSIX sh (installer), GitHub Actions YAML, Docker Compose v2, Python 3.12
(status fields and tests), Markdown/VitePress (docs), React (Site statement).
**Primary Dependencies**: `docker/build-push-action`, `docker/metadata-action`,
`softprops/action-gh-release` (or `gh release`), `caddy:2-alpine`, `postgres:17-alpine`,
`shellcheck`.
**Storage**: PostgreSQL named volume, artifact named volume (`file` backend), Caddy data volume.
**Testing**: pytest (status fields, installer dry-run), `node --test` (docs drift), shellcheck,
a CI end-to-end job that installs from locally built images.
**Target Platform**: Linux amd64 and arm64 hosts with Docker Compose v2; macOS with Docker
Desktop; Windows through WSL 2.
**Constraints**: default stack fits 2 vCPU / 4 GB; one public port without a domain; ports 80 and
443 with a domain; installer must not require the repository.

## Constitution Check

- **I, II, VIII (Source → Evidence → Reality, authority, received values)**: not touched. The
  installer moves bytes and configuration; no business flow changes. PASS
- **III (proven schema only)**: no migration, no table, no typed field. Version and commit are
  read from environment variables baked into the image. PASS
- **IV (tenant and service boundaries)**: no new query, no transport writes. The status fields
  are added to the existing platform posture function and the existing system status endpoint,
  both already tenant-free operator surfaces. PASS
- **V (spec and test evidence)**: every FR maps to a task and a test below; installer behaviour
  is proven by a dry-run unit test, shellcheck and an end-to-end CI job; docs commands are
  pinned by a drift test. PASS
- **VI (explainable web product)**: no web product change; the Site statement is copy plus a
  link. PASS
- **VII (simplicity and storage discipline)**: PostgreSQL stays the only database; the `file`
  artifact backend and Caddy are existing or single-purpose pieces. Two new infrastructure
  items are justified below in Complexity Tracking (Caddy, GHCR workflow); simpler alternatives
  are recorded. PASS

## Research Findings (Phase 0)

1. **Web image already proxies the API.** `apps/web/default.conf.template` forwards `/api/` and
   `/healthz` to `API_UPSTREAM` (default `api:8000`), so the API needs no host port and the
   default service name `api` needs no configuration.
2. **MCP requires an origin-root URL.** `reality.mcp.config` rejects any `MCP_URL` with a path
   and requires HTTPS when `REALITY_ENV` is production. Hence the subdomain decision, and hence
   `REALITY_ENV=production` is set for MCP only in domain mode; the API always runs with
   `REALITY_ENV=production` so a missing master key is a hard error (`reality.security.secrets`).
3. **First owner exists already.** `bootstrap_platform_admin` runs in the API lifespan and
   creates or re-activates the platform admin from `REALITY_PLATFORM_ADMIN_EMAIL` and
   `REALITY_PLATFORM_ADMIN_PASSWORD`. The installer only has to generate both.
4. **`file` artifact backend.** `reality.services.artifacts` resolves `REALITY_ARTIFACT_DIR`;
   API and MCP containers mount one named volume at `/data/artifacts`. Writes are per-object
   files keyed by storage key, so concurrent readers are safe; only the API writes.
5. **Cookie and CORS follow `APP_URL`.** `allowed_origins = [APP_URL]` and
   `REALITY_COOKIE_SECURE` are environment driven, so domain mode only sets variables.
6. **No version surface.** `/healthz` returns `{"status": "ok"}`; `/api/v1/system/status` and
   `deployment_posture` carry no version. `pyproject.toml` says `0.0.1` and the repository has
   no tags. Version and commit therefore come from build args, not from package metadata.
7. **Existing tests pin the developer Compose file.** `test_repository_layout.py`,
   `docs-deployment.test.mjs`, `check_spec_policy.py` and `ci_backend_changes.py` all read the
   root `compose.yml`. The installer assets live in `installer/` and leave those files alone
   (FR-020).
8. **Published web image is provider-branded by design.** `apps/web/Dockerfile` bakes
   `SITE_URL` and `DOCS_URL` defaults to runreality.ai; those are links to the provider's Site
   and Docs, which the docs already declare outside the installation contract. Acceptable.
9. **Compose cannot make a port conditional.** Profiles are per service and a `ports` block
   cannot be toggled, so the installer selects an override file through `COMPOSE_FILE` in
   `.env` (see Design 2). This keeps "exactly one public port" and "exactly 80 and 443" true
   without templating YAML.
10. **arm64 matters.** The most quoted budget host (Hetzner CAX) and every Apple Silicon Mac
    are arm64. GHCR images are built for `linux/amd64,linux/arm64`; the ECR workflow stays
    amd64-only and untouched.

## Design (Phase 1)

### 1. Release and publish workflow

`.github/workflows/publish.yml`, triggered on `push` to `main` and on tags `v*`:

- Matrix over `api`, `mcp`, `web`, `scheduler`, `worker` (Site and Docs are provider-operated
  and not published). Context `.`, Dockerfile `apps/<role>/Dockerfile`, platforms
  `linux/amd64,linux/arm64`, `docker/metadata-action` tags:
  - tag push: `<version>` (for example `0.1.0`) and `latest`;
  - main push: `sha-<short>` and `edge`.
- Images: `ghcr.io/xentral-labs/reality-<role>`. Login with `GITHUB_TOKEN`
  (`packages: write`). The packages must be switched to public once in the GitHub UI; this is
  a one-time owner step recorded in tasks.
- Build args `REALITY_VERSION` and `REALITY_COMMIT` are passed to every Dockerfile, which sets
  them as `ENV` and as OCI labels (`org.opencontainers.image.version`, `.revision`, `.source`).
- On a tag, a final job creates the GitHub Release with assets `install.sh`, `compose.yml`,
  `compose.direct.yml`, `compose.proxy.yml`, `Caddyfile` and `.env.example` from `installer/`.
  The installer downloads its companions from the same release, so script and Compose files
  are always from one version.

### 2. Installer assets (`installer/`)

```text
installer/
├── install.sh          # the one script: install | upgrade | start | stop | logs | status | backup | restore
├── compose.yml         # base: db, migrate, api, web, invitation-worker, scheduler, worker, mcp (no host ports)
├── compose.direct.yml  # web -> ${REALITY_PORT}:80 on ${REALITY_BIND}; mcp -> 127.0.0.1:${REALITY_MCP_PORT}:8001
├── compose.proxy.yml   # caddy (80/443, caddy_data volume), no web/mcp host ports
├── compose.s3.yml      # object-storage + object-storage-init; switches REALITY_ARTIFACT_STORAGE=s3
├── Caddyfile           # {$REALITY_DOMAIN} -> web:80 ; mcp.{$REALITY_DOMAIN} -> mcp:8001
├── .env.example        # the installer's variable inventory with generated values marked
└── README.md           # the five commands, copied into reality/README.md
```

Behaviour of `install.sh`:

- `install` (default): check `docker`, `docker info`, `docker compose version` (v2 plugin;
  refuse the standalone `docker-compose`), `curl`, and write permission. Refuse if `reality/`
  exists (print upgrade command, exit 0). Resolve version: `--version` flag, else the release
  the script came from (`REALITY_INSTALLER_VERSION` substituted at release time, `edge` for a
  raw main copy). Download companions from
  `https://github.com/Xentral-Labs/reality/releases/download/v<version>/`, or copy them from
  `REALITY_INSTALLER_SOURCE_DIR` when set (CI and local testing). Generate secrets with
  `openssl rand` (fallback `/dev/urandom`); the Fernet key is 32 random bytes base64url. Write
  `.env` with `REALITY_VERSION`, `COMPOSE_FILE`, `REALITY_PORT`, `REALITY_BIND`,
  `REALITY_DOMAIN`, `APP_URL`, `MCP_URL`, `REALITY_COOKIE_SECURE`, `REALITY_MCP_ENV`, database
  credentials, `REALITY_MASTER_KEY`, `REALITY_PLATFORM_ADMIN_EMAIL`,
  `REALITY_PLATFORM_ADMIN_PASSWORD`, `REALITY_AUTH_MODE=enabled`,
  `REALITY_AUTO_APPROVE_LIMIT=0`. Run `docker compose pull` then `up -d`, poll
  `http://127.0.0.1:${REALITY_PORT}/healthz` (or `https://${REALITY_DOMAIN}/healthz`) for up to
  180 s, print URL, owner email and owner password once, then print the location of
  `README.md`.
- `upgrade`: requires `.env` with `REALITY_VERSION` (refuse otherwise), rewrites that line,
  re-downloads companions for the new version, `pull`, `up -d`; the `migrate` service runs
  before api, scheduler, worker and mcp through `depends_on: service_completed_successfully`.
  On failure prints `docker compose logs migrate` and exits non-zero; the previous images stay
  on the host.
- `backup`: `pg_dump -Fc` through `docker compose exec -T db`, a tar of the artifact volume via
  a throwaway `alpine` container, plus `.env` and the Compose files, into
  `reality-backup-<UTC timestamp>.tar`. Prints the path and that the archive contains the
  master key.
- `restore <archive>`: only into an empty or absent `reality/`; extracts, starts `db`, waits for
  health, `pg_restore --clean --if-exists`, restores the artifact tar, then `up -d`.
- `start`, `stop`, `logs`, `status`: thin wrappers over `docker compose`.
- Flags: `--port`, `--bind`, `--email`, `--domain`, `--version`, `--dir`, `--yes`,
  `--dry-run` (write files, skip Docker), `--help`. Unknown flag prints usage, exit 2.
- Non-interactive: `--email` or `REALITY_ADMIN_EMAIL`; without either and without a TTY the
  installer uses `owner@reality.local` and says so.

`.env` decides the mode: `COMPOSE_FILE=compose.yml:compose.direct.yml` (default) or
`compose.yml:compose.proxy.yml` (domain), optionally `:compose.s3.yml`.

### 3. Version surface (Python)

- `deployment_posture` and `api_system_status` gain `"version"` and `"commit"` from
  `REALITY_VERSION` (default `"dev"`) and `REALITY_COMMIT` (default `""`).
- Dockerfiles for api, mcp, scheduler and worker: `ARG REALITY_VERSION=dev`,
  `ARG REALITY_COMMIT=`, `ENV` of both, OCI labels. Web Dockerfile: labels only.
- Existing tests for the status endpoint and the posture assert the new keys.

### 4. Docs

`apps/docs/content/operations/` (and `de/`):

- `index.md` becomes the **Install options** index: a four-row table (One-line setup, Docker
  Compose, Kubernetes with Helm, Railway) with prerequisites, "choose this when" and the link;
  keeps the two-box responsibility drawing.
- `installation.md` → **One-line setup**: the command, what it creates, the five commands,
  flags, first login, where the master key lives.
- new `docker-compose.md` → **Docker Compose**: the asset files, `.env.example`, `COMPOSE_FILE`
  modes, `s3` profile, proxy prerequisites.
- new `kubernetes.md` → **Kubernetes with Helm**: chart location, the image repository values to
  point at GHCR, what the chart assumes (ingress, secrets), link to the chart README.
- new `railway.md` → **Railway**: the existing profile in `docs/RAILWAY_DEMO.md`, its safety
  boundary, the script.
- `deployment.md` (Operate with Docker) keeps its contract and gains the concrete upgrade,
  backup and restore commands.
- `reference/environment.md` documents `REALITY_VERSION`, `REALITY_COMMIT`, `REALITY_DOMAIN`,
  `REALITY_ENV`, `REALITY_ARTIFACT_DIR`, `COMPOSE_FILE` and the `s3` override.
- Sidebar in `.vitepress/config.mts`: labels `installOptions`, `oneLineSetup`, `dockerCompose`,
  `kubernetes`, `railway` in every docs locale; "Local installation" is renamed.
- Drift test `apps/docs/scripts/install-options.test.mjs`: the one-line command, the five
  commands and the flag list on the docs pages equal the strings in `installer/install.sh` and
  `installer/README.md`; the image references on the Compose page equal `installer/compose.yml`.

### 5. Site

`provider-site/src/PlatformPage.tsx` self-hosted card: copy becomes "Same images as the cloud. MIT
licence. No feature gating." with the primary link to the docs Install options page and the
secondary to Releases; German (and other Site locales) in `localization.tsx`; `npm run
i18n:audit` for the Site.

### 6. Tests

| Proof | Path | Covers |
| --- | --- | --- |
| Installer dry-run unit tests | `installer/tests/test_install_sh.py` (pytest, no Docker): prerequisites message, `.env` has no placeholder, Fernet key valid, version pinned, idempotent refusal, `--domain` sets proxy mode and secure cookie, `--port` conflict message, unknown flag usage | FR-003 to FR-007, FR-012, FR-015 |
| shellcheck | CI step over `installer/install.sh` | FR-003 |
| End-to-end | `.github/workflows/installer.yml`: build the five images locally with tag `local`, run install with `REALITY_INSTALLER_SOURCE_DIR` and `REALITY_IMAGE_TAG=local`, assert healthz, `ss -ltn` shows only the App port publicly and MCP on loopback, re-run is a no-op, backup, `down -v`, restore into a fresh dir, upgrade to a retagged `local2` | FR-008 to FR-011, FR-013, FR-014, FR-016, SC-001, SC-002, SC-004 |
| Version surface | `packages/reality-core/tests/test_platform_*.py` and system status test | FR-002 |
| Docs drift | `apps/docs/scripts/install-options.test.mjs` | FR-017, SC-005 |
| Environment reference | extend `docs-contract.test.mjs` to require the new variables | FR-018 |
| Site | Site vitest/i18n audit for the new strings and link | FR-019 |
| Developer profile | existing `test_repository_layout.py`, `docs-deployment.test.mjs` unchanged and green | FR-020 |
| Publish workflow | `scripts/test_publish_workflow.py`: five components, both platforms, GHCR names, tag rules, release assets list equals `installer/` contents | FR-001 |

### 7. Rollout and manual owner steps

1. Merge; the `main` push publishes `edge` and `sha-*` images (packages appear private).
2. Owner sets the five GHCR packages to public (one-time UI step).
3. Owner creates tag `v0.1.0` as a GitHub Release; the workflow attaches the installer assets.
4. Owner creates DNS `get.runreality.ai` and an HTTP redirect to
   `https://github.com/Xentral-Labs/reality/releases/latest/download/install.sh` (S3 website
   redirect bucket or CloudFront function in the existing AWS account; the Site container is
   the fallback with a single nginx `return 302`).
5. Until step 4 exists the docs show the GitHub URL as the command; the drift test pins whatever
   string the script's README carries.

## Project Structure

```text
installer/                                   # new, see Design 2
.github/workflows/publish.yml                # new: GHCR images + release assets
.github/workflows/installer.yml              # new: shellcheck + end-to-end
scripts/test_publish_workflow.py             # new
apps/api/Dockerfile, apps/mcp/Dockerfile,
apps/scheduler/Dockerfile, apps/worker/Dockerfile, apps/web/Dockerfile   # ARG/ENV/labels
packages/reality-core/src/reality/services/platform.py   # version, commit in posture
packages/reality-core/src/reality/web/app.py             # version, commit in system status
packages/reality-core/tests/...                          # asserts for both
apps/docs/content/operations/{index,installation,docker-compose,kubernetes,railway,deployment}.md
apps/docs/content/de/operations/...                      # German edition
apps/docs/content/reference/environment.md (+ de)
apps/docs/.vitepress/config.mts                          # sidebar labels
apps/docs/scripts/install-options.test.mjs               # drift test
provider-site/src/PlatformPage.tsx, provider-site/src/localization.tsx
specs/187-self-hosted-installer/{spec,plan,tasks}.md
```

**Structure Decision**: installer assets get their own top-level directory because they are a
shipped artifact with their own inventory, not part of any app; the developer Compose files at
the root stay untouched, which is what four existing tests pin.

## Complexity Tracking

| Addition | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Caddy reverse proxy (domain mode only) | Secure cookies and the MCP HTTPS rule make TLS mandatory for any non-localhost installation | "Bring your own proxy" is the n8n gap this feature exists to close; nginx would need a certificate tool and cron |
| Second CI workflow for publishing | Public multi-arch images are the precondition for installing without the repository | Extending `deploy-testing.yml` would couple the public release to the team's ECR account and its amd64-only cluster |
| Compose override files instead of one file | A port cannot be made conditional inside one Compose file | Templating YAML in shell is fragile; `COMPOSE_FILE` in `.env` is a documented Compose feature |
| One installer script with subcommands | Operators need upgrade, backup and restore without the repository | Separate scripts multiply the drift surface the docs test has to pin |

## Rollback

Revert the merge commit. No migration and no data change. Published images and releases stay
in the registry; an installed instance keeps working against its pinned version. The Python
change only adds two response fields.

## Review Risks

- The first release tag must exist before the documented one-line command works end to end;
  until then the docs point to the raw `edge` script and say so.
- `pg_restore` into a database created by a newer image than the dump: the migrate service
  brings the schema forward on the next `up`, which is the documented direction; downgrades are
  out of scope and named as such.
- The arm64 build roughly doubles publish time; acceptable on release cadence, and `main`
  pushes could be limited to amd64 if the queue becomes a problem.
- GHCR package visibility is a manual step; a private package makes the installer fail with a
  pull error the script reports verbatim.

## FR-013 readiness regression repair

CI observed a healthy API followed by a still-starting Web proxy and an empty response
from the published health route. Restore the existing readiness promise by adding a
Web container health check against its proxied `/healthz`, and wait for Web health in
the shared start_stack path. Preserve the 180-second bound and failure behavior. No
business/service/schema change. Constitution Check: PASS. Before implementation, add
fake-Docker tests with API healthy and Web delayed/permanently unready; then run the
installer unit suite, shellcheck and real isolated install/backup/restore/upgrade proof.
Analysis: no critical findings; this restores FR-013 without weakening the e2e check.
