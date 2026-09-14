# Reality

Reality is an agent-ready operations core built around **Source → Evidence → Reality**.
This repository is a deployable monorepo with independently scalable transport
boundaries around one shared business application core.

Reality is open source under the [MIT License](LICENSE). You may use, copy, modify, distribute,
sublicense, and sell copies subject to the license notice and disclaimer. Third-party components
retain their respective licenses; see [Third-Party Notices](docs/THIRD_PARTY_NOTICES.md).

## Install Reality (self-hosted)

You need a Linux or macOS host (Windows through WSL 2) with Docker and the Compose v2 plugin.
One command installs the published images, generates the secrets and prints the App address and
the first owner's sign-in:

```bash
curl -fsSL https://get.runreality.ai | sh
# public server with HTTPS:
curl -fsSL https://get.runreality.ai | sh -s -- --email owner@example.com --domain reality.example.com
```

The installer asks for nothing else. Email delivery, the internal Copilot's Anthropic key and
object storage are optional and are set afterwards in `reality/.env`. Upgrade, backup and
restore are single commands (`./reality/reality.sh upgrade|backup|restore`). The full guide, the
manual Docker Compose path, Kubernetes with Helm and Railway are documented under
[Install options](https://docs.runreality.ai/operations/) in the product docs; the shipped files
live in [`installer/`](installer/README.md). Self-hosted Reality is the complete product: the same
images as the cloud, MIT licensed, no feature gating.

## Application architecture

Reality is a modular business core, not a collection of independent business
services. Browser, API, CLI, Chat and MCP are adapters: they must use the same
application tools and services and must never implement alternative business rules or
write directly through the ORM.

```text
Product users       Docs readers       Enterprise agents
      |                   |                    |
      v                   v                    v
static Product Web    static Docs       remote MCP runtime
      |                   |                    |
      v                   |                    |
  Web/API runtime --------+--------------------+
                  |
                  v
       shared application tools/services
          |              |             |
          v              v             v
     PostgreSQL       workers     S3-compatible
  business records,   and event   object storage
  events, projections processing  immutable binaries
```

| Component | Responsibility |
|---|---|
| Static Product Web | Login, onboarding, Operations Cockpit and Business Reality Inspector; contains no business rules |
| Static product Docs | Public, tenant-independent product concepts, task guides, integration, deployment and reference content with local search |
| Web/API runtime | Browser authentication, tenant APIs, settings, token administration and human confirmation |
| Remote MCP runtime | Authenticated MCP protocol boundary for enterprise agents; exposes canonical application tools |
| CLI | Developer and operator adapter using the same application behavior |
| Workers | Retryable source interpretation and event-driven projection work |
| Shared application core | Commands, queries, proposals, confirmation, tenant rules and transactions |
| PostgreSQL | Authoritative tenant-scoped business records, Business Events, projections and metadata |
| S3-compatible storage | Private immutable source files and other binary objects referenced by opaque database keys |

Remote MCP runs as a separate HTTP-only process and deployment. It has its own public
URL, listener, health checks, lifecycle, and bounded PostgreSQL pool while retaining
the same codebase, application services, credentials, proposals, and business rules as
Web/API. The Web/API runtime does not mount or proxy MCP, and no alternate local MCP
transport is supported.

## Repository layout

```text
apps/
  api/     Web/API container definition
  docs/    public product documentation and static container definition
  mcp/     HTTP-only MCP container definition
  web/     authentication and product Web application with static container definition
packages/
  reality-core/  Shared Python domain, services, adapters, migrations and tests
infra/           deployment guidance and target-specific infrastructure
docs/            domain, product, feature and architecture contracts
specs/           approved and draft Spec Kit feature contracts
```

`apps/docs` is public and static with no API dependency. `apps/web` owns login,
onboarding, and the authenticated product. `apps/api` and `apps/mcp` are independently
deployable process boundaries, but both install the same `packages/reality-core`
distribution. Product screens belong in `apps/web`; no business rules belong in either
browser application or in container-definition directories.

## Storage

- **PostgreSQL**: tenant-scoped business records, journal, projections, metadata and object identities.
- **S3-compatible object storage**: immutable, lossless source binaries such as CSV, JSON, PDFs and attachments.
- **Local PostgreSQL + local files**: smallest supported developer profile.

Object storage is not a second business database. PostgreSQL keeps the tenant, checksum, media type, size, lifecycle and opaque object key. MinIO provides the S3 API locally; AWS S3 can replace it without domain changes.

## Local development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e './packages/reality-core[dev]'

docker compose up -d db
export REALITY_DATABASE_URL='postgresql+psycopg://reality:local-only@localhost:54329/reality'
export REALITY_PLAYGROUND_ENABLED=true
cd packages/reality-core
alembic upgrade head
reality web
```

In a separate core terminal, start authenticated remote MCP over HTTP:

```bash
cd packages/reality-core
export MCP_URL='http://localhost:8001/'
uvicorn reality.mcp.app:app --host 127.0.0.1 --port 8001
```

In another terminal, run the product Web app:

```bash
cd apps/web
npm ci
npm run dev
```

- Product Web: <http://localhost:5173>
- Web/API runtime: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- Remote MCP endpoint: <http://localhost:8001/>
- MCP liveness/readiness: <http://localhost:8001/healthz>, <http://localhost:8001/readyz>

## Complete local stack

```bash
make stack
```

Start one deployable boundary (plus its declared Compose dependencies) with:

```bash
make app   # Product Web and API dependencies
make api   # Web/API runtime and storage dependencies
make mcp   # MCP runtime and storage dependencies
```

### Reload-enabled development

`make stack` remains production-like and serves immutable built images. For active
development, start all boundaries with source mounts and automatic reload:

```bash
make dev
```

This stays in the foreground and combines prefixed logs from Product Web, API,
MCP, PostgreSQL, and object storage. Vite hot-reloads both browser applications;
Uvicorn reloads API and MCP when shared-core Python source changes.

Humans and coding agents can use the detached lifecycle when the foreground process
would occupy their terminal:

```bash
make dev-up      # build and start in the background
make dev-logs    # follow combined logs on stdout (Ctrl-C only stops following)
make dev-status  # show service and health state
make dev-down    # stop and remove development containers; named data volumes remain
```

To focus on one service, use the same override directly, for example:

```bash
docker compose -f compose.yml -f compose.dev.yml logs --follow api
```

- Web/API runtime: <http://localhost:8000> (`API_PORT`)
- Product Web: <http://localhost:8080> (`APP_PORT`)
- Remote MCP endpoint: <http://localhost:8001/> (`MCP_PORT`)
- MinIO console: <http://localhost:9001>
- PostgreSQL: `localhost:54329`

Compose starts migrations as a release step, separate stateless Web/API and MCP
runtimes, a private MinIO bucket, and an independent static Product Web
container. Production uses the same boundaries with edge-hosted static assets,
separate containers for Web/API and MCP, managed PostgreSQL, and private S3.

The browser split is atomic: deploy Product Web, API, MCP, CI, and operational
commands from one repository release. Mixed old/new paths and compatibility symlinks
are unsupported. Rollback means restoring the complete prior repository release, not
falling back one application directory independently.

## Public URLs

The deployable boundaries have separate public configuration:

- `SITE_URL`: optional marketing-site origin that Product Web and Docs link back to,
  for example <https://runreality.ai>; it is not served by this repository
- `APP_URL`: Product Web origin used by API redirects, email links, CORS and account links
- `API_URL`: Web/API origin
- `MCP_URL`: exact externally reachable MCP origin; no additional path is required
- `DOCS_URL`: public product documentation origin; typically `https://docs.runreality.ai`

URLs describe externally reachable origins. Compose host bindings are configured
independently with `APP_PORT`, `API_PORT` and `MCP_PORT`; changing a port
never silently rewrites a public URL. `MCP_BIND_HOST` and `MCP_BIND_PORT` are internal
listener settings, not public addresses.

## Reader analytics

Public reader analytics is optional, self-hosted, and never a dependency of a Reality
runtime. It runs as its own stack with its own database:

```bash
UMAMI_DB_PASSWORD=... UMAMI_APP_SECRET=... make analytics
```

Open `http://localhost:8084`, sign in with the default `admin` / `umami` credentials,
change that password, register a website for the Docs origin, and copy the generated
website id. Two build arguments then activate measurement on the Docs container:

- `ANALYTICS_SCRIPT_URL`: absolute URL of the collector script, for example
  `https://analytics.example.com/script.js`
- `ANALYTICS_WEBSITE_ID`: website id issued by the collector

Both must be set together. When either is empty the Docs build emits no analytics tag at
all, so local development, CI, and preview builds never appear in the numbers. The
collector sets no cookies and writes nothing to the reader's device.

A production topology is typically:

```text
https://app.runreality.ai  -> static Product Web
https://api.runreality.ai  -> Web/API runtime
https://mcp.runreality.ai  -> remote MCP runtime
https://docs.runreality.ai -> static product Docs
https://get.runreality.ai  -> 302 to the latest release's install.sh (self-hosted installer, spec 187)
```

`get.runreality.ai` is a redirect record, not a service: it points at
`https://github.com/Xentral-Labs/reality/releases/latest/download/install.sh` so
`curl -fsSL https://get.runreality.ai | sh` always installs the latest GitHub Release.
The Helm README describes how it is created in the `runreality.ai` zone.

`MCP_URL` is the exact origin advertised to clients. The dedicated MCP subdomain serves
the protocol at `/`, so no redundant `/mcp/` suffix is required. It is independent of
`API_URL`. `MCP_BIND_HOST` and `MCP_BIND_PORT` control only the MCP
listener. Reverse proxy, load balancer, and TLS routing must point `MCP_URL` to the MCP
runtime. Token creation and revocation remain in company settings on Web/API, while
the MCP credential itself authorizes exactly one tenant and an explicit tool
allowlist. Local and production clients both use authenticated Streamable HTTP.

Web/API and MCP have separate bounded database pools. The example Compose defaults
allow at most 15 Web/API connections and 7 MCP connections (22 combined); production
must also reserve PostgreSQL capacity for workers, migrations, and operator sessions.

## Quality gates

```bash
make test
make lint
make web-build
```

Read [AGENTS.md](AGENTS.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/WEB_SPEC.md](docs/WEB_SPEC.md) and [the deployment boundary decision](docs/decisions/0005-frontend-backend-object-storage.md) before changing behavior.

For the current combined app on localhost:8080, follow [the local stack guide](docs/LOCAL_STACK.md).
