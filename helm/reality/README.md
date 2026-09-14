# Deploying Reality with the Helm chart

This chart deploys Reality to any Kubernetes cluster. It makes no assumption about
the account, registry, DNS zone or secret store you use: every operator-specific
value is a chart value. The maintainers' own deployment configuration lives in a
separate operations repository — see [docs/REPOSITORY_BOUNDARY.md](../../docs/REPOSITORY_BOUNDARY.md).

| | |
|---|---|
| Registry | `image.repository` (**required**) — one repository addressed as `<repository>:<component>-<tag>`. See [Images](#images). |
| Secrets | Any External Secrets Operator store, or a hand-made Secret via `secrets.existingSecret` |
| Ingress | Any IngressClass; the defaults are written for the AWS Load Balancer Controller |
| Database | Any PostgreSQL 14+ reachable from the cluster |

If you want a single-host install instead of Kubernetes, use the installer:
`curl -fsSL https://get.runreality.ai | sh`.

## Architecture the chart deploys

```
                      ALB (dedicated, group.name=reality)
                                  │
          app.<your-domain>       │       mcp.<your-domain>
                │                 │                 │
         ┌──────▼──────┐          │          ┌──────▼──────┐
         │ web (nginx) │          │          │     mcp     │  :8001
         │  SPA + /api │          │          └──────┬──────┘
         └──────┬──────┘          │                 │
    proxy_pass  │ /api/ /healthz  │                 │
         ┌──────▼──────┐          │                 │
         │     api     │  :8000   │                 │
         └──────┬──────┘          │                 │
                │        ┌────────▼─────────┐       │
                └───────►│    PostgreSQL    │◄──────┘
                         └──────────────────┘
        invitation-worker ──┘        migrate (pre-upgrade hook)
```

**The single public app host is a hard constraint, not a preference.** The SPA
issues every request with a relative path (`apps/web/src/api.ts` is the only
`fetch()` in the bundle) and the session cookie is set with no `domain`
attribute. There is no configurable API base URL. A split
`app.<domain>` + `api.<domain>` layout requires a frontend code change — no
values edit can produce it. The web pod's own nginx proxies `/api/` to the api
Service, so the API needs no public listener and no CORS.

## Install

1. Provide a PostgreSQL database. `REALITY_DATABASE_URL` must point at a
   **writer** endpoint — several GET handlers refresh projections synchronously
   and take write locks, so a read replica fails — and must use the `+psycopg`
   driver.
2. Provide the secrets, either through an External Secrets Operator store
   (`externalSecret.enabled: true`, pointing `secretStoreRef` and `path` at your
   own store) or as a plain Secret (`externalSecret.enabled: false` plus
   `secrets.existingSecret`). With no store, the pre-install migration hook
   cannot mount its env and the install never completes.
3. Install:

```bash
helm upgrade --install reality ./helm/reality \
  -n reality --create-namespace \
  -f my-values.yaml \
  --set image.tag=<tag>
```

Your `my-values.yaml` supplies at minimum `image.repository`, `urls.*`,
`storage.bucket`, and the secret-store coordinates. See
[values.yaml](values.yaml) for the full contract; every key is commented.

## Images

The chart addresses **one repository with component-prefixed tags**:
`<image.repository>:api-<tag>`, `:mcp-<tag>`, `:web-<tag>`, `:docs-<tag>`,
`:scheduler-<tag>`, `:worker-<tag>`. That is the shape a single ECR (or similar)
repository gives you, and `image.repository` has no default — an unset value
fails the render rather than producing a broken reference.

The images published to GHCR by `publish.yml` use a different shape: one
repository **per component** (`ghcr.io/xentral-labs/reality-api`,
`…-mcp`, and so on). To deploy those with this chart, set each component's
repository and clear its tag prefix:

```yaml
image:
  repository: ghcr.io/xentral-labs/reality-api   # fallback for anything not listed
  tag: sha-abc1234
api:              { image: { repository: ghcr.io/xentral-labs/reality-api,       tagPrefix: "" } }
mcp:              { image: { repository: ghcr.io/xentral-labs/reality-mcp,       tagPrefix: "" } }
web:              { image: { repository: ghcr.io/xentral-labs/reality-web,       tagPrefix: "" } }
docs:             { image: { repository: ghcr.io/xentral-labs/reality-docs,      tagPrefix: "" } }
scheduler:        { image: { repository: ghcr.io/xentral-labs/reality-scheduler, tagPrefix: "" } }
worker:           { image: { repository: ghcr.io/xentral-labs/reality-worker,    tagPrefix: "" } }
invitationWorker: { image: { repository: ghcr.io/xentral-labs/reality-api,       tagPrefix: "" } }
migrations:       { image: { repository: ghcr.io/xentral-labs/reality-api,       tagPrefix: "" } }
```

`invitationWorker` and `migrations` run the api image; `docs` is optional.

If you only want to run Reality on one host, the installer handles all of this:
`curl -fsSL https://get.runreality.ai | sh`.

## Secrets contract

All keys live at one path in your secret store. The chart adds keys to the
ExternalSecret as you enable the matching feature.

### Required for a green deploy

| Key | What it is | Notes |
|---|---|---|
| `REALITY_DATABASE_URL` | `postgresql+psycopg://user:pw@host:5432/reality?sslmode=require` | **The only variable that fails startup.** Resolved at module import in `reality/db/core.py`, so every Python workload dies immediately without it. Must be `postgresql`; the driver installed is `psycopg` 3, so a bare `postgresql://` URL passes validation and then fails at connect — keep `+psycopg`. |
| `REALITY_MASTER_KEY` | Fernet key, `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"` | Envelope-encrypts every stored tenant credential. **Generate once and never rotate** — losing it makes all stored secrets permanently undecryptable. Because the chart sets `REALITY_ENV=production`, a missing key is a hard error instead of a silently generated per-pod ephemeral key. |

### Add when you enable the matching feature

**Write the value into your store first, then flip the values toggle.** The chart
appends these keys to the ExternalSecret automatically, and ESO's v1 API has no
per-key optional flag — one missing property fails the whole sync, so *every*
key stops resolving, not just the new one.

| Key | Added by | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | `copilot.managedKey: true` | Read lazily per message; without it chat degrades to a deterministic keyword responder rather than failing, so this is genuinely optional. |
| `ANTHROPIC_WORKSPACE_ID` | `copilot.sendWorkspaceId: true` | Required for an **organisation-level** key, which Anthropic rejects with `400 invalid_request_error` unless the `anthropic-workspace-id` header is present. A key created inside a workspace is already scoped and needs neither. |
| `RESEND_API_KEY` | `email.provider: resend` | |
| `REALITY_SMTP_USERNAME` | `email.provider: smtp` | For Amazon SES this is the **IAM access-key id**, not a role. See [Sending mail over SMTP](#sending-mail-over-smtp). |
| `REALITY_SMTP_PASSWORD` | `email.provider: smtp` | For Amazon SES, the SMTP password **derived** from that key's secret. |
| `REALITY_PLATFORM_ADMIN_EMAIL` | `bootstrap.platformAdmin.enabled: true` | The only way to create a platform admin. |
| `REALITY_PLATFORM_ADMIN_PASSWORD` | as above | Applied on every API start; promotes an existing user but does **not** rotate their password. Run this once with `api.replicaCount: 1` — the bootstrap is not advisory-locked and `AppUser.email` is unique, so two cold replicas can crash on `IntegrityError`. |

### Deliberately *not* secrets

- **`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`** — must be **absent** when you
  use IRSA. boto3 is constructed with no explicit credentials, so the default
  chain resolves the role; env credentials outrank web identity and would shadow
  it. They appear in `compose.yml` only to reach local MinIO.
- **`REALITY_S3_ENDPOINT_URL`** — must be **absent** so botocore resolves the real
  AWS S3 endpoint. The code maps an empty value to `None`. Set it only for an
  S3-compatible store such as MinIO.
- Everything else (`APP_URL`, pool sizes, `REALITY_AUTH_MODE`, …) is plain config
  and is set by the chart.

## Connection budget

Per-replica ceiling is `database.poolSize + database.maxOverflow`. Budget against
the **HPA ceiling**, not `replicaCount`. With the defaults and
`api.autoscaling.maxReplicas: 6`, the worst case is
`(6 api + 2 mcp + 1 worker) x 15 + 1` for the NullPool migration job = 136
connections. Size your database accordingly.

## Sending mail over SMTP

The app sends mail with `smtplib` + STARTTLS and `smtp.login(username, password)` —
there is no boto3 SES client anywhere in the codebase. If you use Amazon SES, note
that an assumed IRSA role **cannot** authenticate SMTP: the SES SMTP endpoint only
accepts credentials derived from a long-lived IAM access key. `REALITY_SMTP_PASSWORD`
is not the secret access key itself but an HMAC derivation of it:

```python
import base64, hmac, hashlib
def ses_smtp_password(secret_access_key: str, region: str) -> str:
    sign = lambda key, msg: hmac.new(key, msg.encode(), hashlib.sha256).digest()
    sig = sign(sign(sign(sign(("AWS4" + secret_access_key).encode(),
        "11111111"), region), "ses"), "aws4_request")
    return base64.b64encode(b"\x04" + hmac.new(sig, b"SendRawEmail", hashlib.sha256).digest()).decode()
```

A new SES account is in the **sandbox**, which delivers only to verified
identities, so invitation mail to an arbitrary address is rejected — the app logs
a provider error, not a delivery. Either verify your recipient addresses or
request production access. Until then, leave `email.provider: log`.

`auth.exposeCodes` returns the email verification code in the
`/api/auth/signup` response body. It exists only for environments where no mail
provider is wired. **Keep it `false` anywhere reachable from the internet:** true
publishes verification codes to anyone who can POST to that endpoint.

## Known sharp edges this chart works around

| Trap | How the chart handles it |
|---|---|
| `reality invitation-worker-once` runs `alembic upgrade head` on **every** invocation (the Typer root callback is `init_db()`), which at a 5s tick is ~17k unlocked migrations a day racing the release migration | The worker Deployment imports `deliver_next_invitation` directly with `python -c` and never touches the CLI |
| `MCP_BIND_HOST` / `MCP_BIND_PORT` are **inert** — the Dockerfile `CMD` hardcodes `0.0.0.0:8001` and FastMCP's host/port only affect its own unused `.run()` helper | The chart keeps port 8001 and does not pretend the env vars work. To move the port you must override the container `command` |
| MCP pins `allowed_hosts` to the exact netloc of `MCP_URL`, so a rewritten Host header returns 421 on every protocol request | `urls.mcp` and the MCP Ingress host must agree; an ALB forwards Host unchanged by default — do not add a host-rewrite annotation |
| `REALITY_BACKEND_DB_*` / `REALITY_MCP_DB_*` from `.env.example` are **never read** by Python | The chart sets the real names, `REALITY_DB_POOL_SIZE` / `_MAX_OVERFLOW` / `_POOL_TIMEOUT` |
| `poolTimeout` default of 5s starves under load — several GET handlers refresh projections synchronously and Copilot chat can hold a connection ~270s | Raised to 30s; raise your load balancer's idle timeout to match (300s) |
| FastAPI's `/docs`, `/redoc`, `/openapi.json` are anonymous — the auth middleware only guards paths under `/api/` | Not exposed: the web nginx proxies only `/api/` and `/healthz`, so those paths hit the SPA fallback instead. `ingress.blockOpenApi` is an opt-in 404 for the case where you add a direct API route |
| Artifact staging writes to local disk even in `s3` mode | `REALITY_ARTIFACT_DIR` points at a mounted `emptyDir` |
| Stock `nginx:1.27-alpine` binds `:80` and cannot run as UID 1001 | `web`/`docs` override the pod securityContext to the image default (root master, non-root workers); `api`/`mcp` run as 1001 |
| Spot capacity consolidating frequently evicts pods | PodDisruptionBudgets on api, mcp and web; `maxUnavailable: 0` on rollouts. The api Deployment always emits a replica floor even under HPA, so a `minAvailable: 1` PDB never sees a single-replica window with `disruptionsAllowed: 0` |
| The AWS ALB controller's default target-group check is `GET /` expecting 200, but MCP's `/` is the protocol endpoint and answers 401 unauthenticated — every mcp target would be permanently unhealthy and the host would return 503 forever | `alb.ingress.kubernetes.io/healthcheck-path` is set **on the Service** (where it is target-group scoped and beats the Ingress): `/healthz` for mcp and docs, `/` for web |
| Sharing one ALB group across unrelated workloads retimes every member — `listen-ports`, `ssl-redirect` and `load-balancer-attributes` are LoadBalancer-scoped, not Ingress-scoped | `group.name: reality` gives Reality its own dedicated ALB |
| A `ClusterSecretStore` with no `conditions` is readable from every namespace, so anyone able to create an ExternalSecret anywhere could extract `REALITY_MASTER_KEY` | Restrict your store to the `reality` namespace with a `conditions` block |
| `API_UPSTREAM` must be fully qualified — nginx resolves it with its own `resolver`, so there is no ndots expansion — but a **trailing dot** makes nginx reject the reply with "unexpected DNS response" and serve 502 | The helper emits `<svc>.<ns>.svc.cluster.local` with no trailing dot; both failure modes were reproduced against the real image |

## Not wired, and why

- **S3 is latent.** `stage_artifact` is the only writer of artifact rows and has
  **no caller** — there is no upload route, CLI command or MCP tool that reaches
  it. The env wiring and IAM surface are in place, so it works the moment an
  ingest route lands, but none of it is required for a green deploy.
- **No Redis or ElastiCache.** Reality has no Redis dependency at all — the only
  mentions in the repository are ADRs explicitly forbidding it. Sessions are
  database rows and the invitation queue is `FOR UPDATE SKIP LOCKED`.
- **`docs` is off by default.** It bakes `APP_URL`, `SITE_URL` and `DOCS_URL` at
  image build time — its nginx config goes to `conf.d/` rather than `templates/`,
  so there is no envsubst and no runtime configuration. Deploying it to your own
  hosts means building your own image. `web` is the exception: `API_UPSTREAM` is
  a genuine runtime knob, so one `web` image promotes across environments.
- **The chart is ArgoCD-ready** but ships no Application manifest: the migration
  Job carries `argocd.argoproj.io/hook: PreSync`. Point your own Application at
  the chart and patch `image.tag` as a Helm parameter.
