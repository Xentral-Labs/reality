# One-line setup

The fastest way to run Reality. One command creates a `reality/` directory with your configuration,
starts the published images and prints the address and your first sign-in.

## Prerequisites

- Linux or macOS with Docker and the Compose v2 plugin (`docker compose`, not `docker-compose`). On
  Windows use WSL 2.
- `curl`.
- 2 vCPU and 4 GB RAM are enough for a team; the App, PostgreSQL, the MCP endpoint and the
  background workers share the host.
- For a public installation: a hostname whose DNS points at the host, plus a second record for
  `mcp.<hostname>`. Ports 80 and 443 must be free.

## Install

```bash
curl -fsSL https://get.runreality.ai | sh
```

The script checks Docker, refuses to overwrite an existing installation, writes `reality/.env` with
generated secrets, starts the stack, waits for the health check and prints:

- the App address (`http://localhost:8080` without a domain),
- the MCP address (loopback only without a domain),
- the first owner's email and password, shown exactly once.

Pass the owner up front and, for a public installation, the domain:

```bash
curl -fsSL https://get.runreality.ai | sh -s -- --email owner@example.com --domain reality.example.com
```

With `--domain`, Caddy terminates HTTPS on ports 80 and 443 for `https://reality.example.com` and
`https://mcp.reality.example.com/`, obtains and renews the certificates itself, and the App uses
secure cookies.

### Flags

| Flag                  | Meaning                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------- |
| `--email <address>`   | First owner (platform admin). Default `owner@reality.local`. See below for adding an owner later. |
| `--domain <host>`     | Public hostname. Enables HTTPS and serves MCP on `mcp.<host>`.                                    |
| `--port <n>`          | Host port for the App without a domain. Default `8080`.                                           |
| `--bind <address>`    | Host address for that port. Default `0.0.0.0`.                                                    |
| `--mcp-port <n>`      | Loopback port for MCP without a domain. Default `8001`.                                           |
| `--version <release>` | Release to install, for example `0.1.0`, `edge` (main) or `sha-a204c14`.                          |
| `--dir <path>`        | Installation directory. Default `./reality`.                                                      |
| `--dry-run`           | Write the files, skip the Docker and port checks.                                                 |
| `--help`              | Usage text.                                                                                       |

## Commands

The installer leaves a copy of itself as `reality/reality.sh`:

```bash
./reality/reality.sh status                 # containers and health
./reality/reality.sh logs                   # follow logs
./reality/reality.sh stop                   # stop, keep data
./reality/reality.sh start                  # start again
./reality/reality.sh upgrade                # move to the latest release (or --version 0.2.0)
./reality/reality.sh backup                 # database + source binaries + .env in one archive
./reality/reality.sh restore <archive.tar>  # rebuild from a backup on a fresh host
```

`upgrade` repins `REALITY_VERSION` in `.env`, pulls the images and runs the migration before the
App, scheduler, worker and MCP start. If the migration fails, the new services do not start and the
previous images stay on the host.

## On a server without a domain

Without `--domain` the App binds `0.0.0.0:8080` and is reachable as `http://<server-ip>:8080` inside
your network. Sign-in works there, but the links Reality puts into emails use `APP_URL`, which is
`http://localhost:8080` in this mode, and cookies travel unencrypted. For anything beyond a laptop
or a trusted LAN, use `--domain`.

## Remove Reality

```bash
./reality/reality.sh stop
cd reality && docker compose down -v && cd ..   # also deletes the database and source binaries
rm -rf reality                                  # deletes .env with the master key
```

Take a backup first if you may want the data back.

## What to keep

`reality/.env` holds `REALITY_MASTER_KEY`, the key that encrypts stored credentials. Losing it makes
those credentials unreadable; it cannot be regenerated. Every backup archive contains `.env`, so
protect the archives like the key itself. The database lives in the `postgres_data` volume, uploaded
source binaries in the `artifacts` volume.

## After the install: optional settings

The installer asks for nothing else. Everything below is optional, lives in `reality/.env`, and
takes effect after `./reality/reality.sh start` (which recreates the containers with the new
values).

| Setting             | Variables                                                                                                            | Without it                                                                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Transactional email | `REALITY_EMAIL_PROVIDER` (`resend` or `smtp`), `REALITY_EMAIL_FROM`, `RESEND_API_KEY` or the `REALITY_SMTP_*` values | Invitations and sign-up mails are logged, not sent; colleagues cannot join by invitation.                                                            |
| Internal Copilot    | `ANTHROPIC_API_KEY`, optionally `ANTHROPIC_WORKSPACE_ID`                                                             | The product works fully; the chat assistant is unavailable.                                                                                          |
| Automatic admission | `REALITY_AUTO_APPROVE_LIMIT`                                                                                         | `0`: every sign-up waits for an owner's approval.                                                                                                    |
| Another owner       | `REALITY_PLATFORM_ADMIN_EMAIL` and `REALITY_PLATFORM_ADMIN_PASSWORD`                                                 | The installed owner stays; a new email with a new password creates a second platform admin on the next start. Existing accounts keep their password. |
| Object storage      | `:compose.s3.yml` appended to `COMPOSE_FILE`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`                               | Source binaries stay in the `artifacts` volume, which is fine for one host.                                                                          |

The [Environment reference](/reference/environment) lists every variable.

## First steps

Sign in with the printed credentials, create a company and use the guided demo for connected Source,
Evidence, operational and financial records. Then
[trace your first result](/getting-started/first-trace). Invitations to colleagues stay pending
until you configure an email provider in `.env` (see the
[Environment reference](/reference/environment)).

To connect an agent, use the MCP address with a token from the App: see
[Connect an MCP client](/api-tools/connect-mcp).
