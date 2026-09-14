# App Environment

This public reference covers the Docker-operated Reality App and PostgreSQL. Use the repository's
`.env.example` as the exact configuration inventory for the checked-out version.

## Database and encryption

| Variable                                            | Purpose                                                                       |
| --------------------------------------------------- | ----------------------------------------------------------------------------- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Initialise the packaged PostgreSQL service                                    |
| `REALITY_DATABASE_URL`                              | SQLAlchemy connection used by App services and migrations                     |
| `REALITY_MASTER_KEY`                                | Required production key for encrypted credentials; keep it outside PostgreSQL |

Losing or rotating `REALITY_MASTER_KEY` without a migration makes existing encrypted credentials
unreadable. Do not expose PostgreSQL outside the private Docker network.

## Installer values

The [one-line setup](/operations/installation) writes these in addition; a manual Compose
installation sets them by hand from `.env.example` in the release assets.

| Variable                                                          | Purpose                                                                                        |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `REALITY_VERSION`                                                 | Release the images are pinned to (`0.1.0`, `edge`, `sha-<short>`); `upgrade` rewrites it       |
| `REALITY_IMAGE_REGISTRY`                                          | Image registry, default `ghcr.io/xentral-labs`                                                 |
| `COMPOSE_PROJECT_NAME`, `COMPOSE_FILE`                            | Container and volume prefix; the Compose files that make up the mode                           |
| `REALITY_BIND`, `REALITY_PORT`, `REALITY_MCP_PORT`                | Host address and ports in direct mode; MCP always binds loopback                               |
| `REALITY_DOMAIN`                                                  | Public hostname in domain mode; Caddy also serves `mcp.<domain>`                               |
| `MCP_URL`                                                         | Public MCP origin root; a path is refused, HTTPS is required when `REALITY_MCP_ENV=production` |
| `REALITY_COOKIE_SECURE`                                           | `true` behind HTTPS                                                                            |
| `REALITY_ENV`, `REALITY_MCP_ENV`                                  | `production` makes a missing master key and a plain-HTTP MCP origin hard errors                |
| `REALITY_ARTIFACT_DIR`                                            | Directory of the `file` artifact store inside the containers, backed by the `artifacts` volume |
| `REALITY_PLATFORM_ADMIN_EMAIL`, `REALITY_PLATFORM_ADMIN_PASSWORD` | The first owner, created or re-activated on every start                                        |
| `REALITY_AUTO_APPROVE_LIMIT`                                      | Automatic admission of sign-ups; `0` keeps every request pending for an owner                  |
| `REALITY_COMMIT`                                                  | Commit baked into the image; reported next to the version                                      |

Optional groups, all empty by default: transactional email (`REALITY_EMAIL_PROVIDER`,
`REALITY_EMAIL_FROM`, `RESEND_API_KEY`, `REALITY_SMTP_*`), the internal Copilot
(`ANTHROPIC_API_KEY`, `ANTHROPIC_WORKSPACE_ID`) and MinIO for the `s3` override (`MINIO_ROOT_USER`,
`MINIO_ROOT_PASSWORD`, `REALITY_S3_BUCKET`, `REALITY_S3_REGION`).

## App address and capacity

| Variable                                                          | Purpose                                                      |
| ----------------------------------------------------------------- | ------------------------------------------------------------ |
| `APP_URL`                                                         | Public Reality App origin used for browser and account links |
| `API_URL`                                                         | Application API origin used by the Web client                |
| `APP_PORT`, `API_PORT`                                            | Optional local Docker host-port overrides                    |
| `REALITY_BACKEND_DB_POOL_SIZE`, `REALITY_BACKEND_DB_MAX_OVERFLOW` | PostgreSQL connection limits for the App                     |
| `REALITY_DB_POOL_TIMEOUT`                                         | Maximum pool wait in seconds                                 |

## Optional App capabilities

Authentication, transactional email, onboarding admission and the internal Copilot have additional
server-only values in `.env.example`. Configure only the capability you use. Never place secrets in
browser builds, screenshots, public documentation or committed environment files.

The product provider's Site and Docs configuration is outside this installation contract. A future
managed Reality infrastructure will publish its own configuration contract.
