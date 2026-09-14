# Docker Compose

The manual path: the same files the one-line setup writes, filled in by hand. Choose it when you
need every variable explicit, want to fold Reality into an existing Compose project, or run a host
without `curl`.

## Files

Download them from the release you want to run, for example
`https://github.com/Xentral-Labs/reality/releases/latest`:

| File                 | Purpose                                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `compose.yml`        | The stack: PostgreSQL, migration, API, Web App, invitation worker, scheduler, worker, MCP. Publishes no host port. |
| `compose.direct.yml` | Adds the App on one host port and MCP on loopback.                                                                 |
| `compose.proxy.yml`  | Adds Caddy on ports 80 and 443 with automatic certificates for the App and for `mcp.<domain>`.                     |
| `compose.s3.yml`     | Replaces the artifact volume with MinIO (S3 API).                                                                  |
| `Caddyfile`          | The two hostnames Caddy serves in domain mode.                                                                     |
| `env.example`        | Every variable with its meaning; copy to `.env` (shipped without the leading dot).                                 |
| `install.sh`         | Optional: the installer, also usable as `reality.sh` for upgrade, backup and restore.                              |

## Images

All services use the published images, pinned by `REALITY_VERSION`:

```text
ghcr.io/xentral-labs/reality-api:<version>
ghcr.io/xentral-labs/reality-web:<version>
ghcr.io/xentral-labs/reality-mcp:<version>
ghcr.io/xentral-labs/reality-scheduler:<version>
ghcr.io/xentral-labs/reality-worker:<version>
```

Release tags publish `<version>` and `latest`; every commit on `main` publishes `sha-<short>` and
`edge`. Images are built for `linux/amd64` and `linux/arm64`.

## Modes

`COMPOSE_FILE` in `.env` selects the mode. Compose reads `.env` from the directory you run it in.

```text
COMPOSE_FILE=compose.yml:compose.direct.yml     # App on REALITY_PORT, MCP on 127.0.0.1:REALITY_MCP_PORT
COMPOSE_FILE=compose.yml:compose.proxy.yml      # Caddy on 80/443 for REALITY_DOMAIN and mcp.REALITY_DOMAIN
```

Append `:compose.s3.yml` to either mode and set `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` to store
source binaries in MinIO instead of the `artifacts` volume. Existing installations keep the store
they started with; there is no migration between the two.

## Required values

Generate these yourself; the example file marks them:

- `POSTGRES_PASSWORD`: any strong password.
- `REALITY_MASTER_KEY`: a Fernet key, 32 random bytes URL-safe base64 encoded, for example
  `openssl rand -base64 32 | tr '+/' '-_'`. Losing it makes stored credentials unreadable.
- `REALITY_PLATFORM_ADMIN_EMAIL` and `REALITY_PLATFORM_ADMIN_PASSWORD`: the first owner.
- With a domain: `REALITY_DOMAIN`, `APP_URL=https://<domain>`, `MCP_URL=https://mcp.<domain>/`,
  `REALITY_COOKIE_SECURE=true`, `REALITY_MCP_ENV=production`. MCP keeps the origin root; a path in
  `MCP_URL` is refused.

## Run

```bash
docker compose up -d
docker compose ps
curl --fail http://localhost:8080/healthz
```

The `migrate` service runs `alembic upgrade head` and every service that touches the database waits
for it. To upgrade, change `REALITY_VERSION`, then `docker compose pull && docker compose up -d`.
Backups: see [Operate with Docker](./deployment).

## Developer profile

The repository's own `compose.yml` at the root is the developer profile: it builds the images from
source and exposes the API and MCP ports for local tooling. It is unchanged by this guide; use
`make dev` from a checkout.
