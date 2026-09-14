# Research: Temporary Hosted Product Demo

## Decision 1: Use Railway only as a temporary demo provider

**Decision:** Use the owner's dedicated `reality-demo` Railway project for a short-lived hosted Product Web, private API, and managed PostgreSQL deployment.

**Rationale:** Railway can build the existing Dockerfiles, provides automatic private service DNS, managed PostgreSQL, provider variables, logs, health-gated deployments, and a generated HTTPS domain. This is the smallest independent hosted environment while AWS work continues.

**Alternatives considered:** A local Cloudflare/ngrok tunnel still depends on the owner's laptop. Render offers equivalent service primitives but would require a second provider setup. A VPS can run Compose directly but adds host, TLS, patching, firewall, and backup administration. None improves this short demo enough to justify the extra work.

## Decision 2: Publish one same-origin Product Web boundary

**Decision:** Publish only Product Web. Keep API and PostgreSQL on Railway private networking and proxy browser `/api` and `/healthz` requests through Nginx.

**Rationale:** This preserves the repository's browser/API split, avoids cross-origin cookie complexity, and minimizes public attack surface. Railway private service DNS uses `<service>.railway.internal`, while local Compose uses the service name `api`; therefore the upstream must be runtime-configurable.

**Alternatives considered:** Publishing API separately creates unnecessary CORS and cookie configuration. Hard-coding Railway DNS would break local Compose. Combining Web and API into one image would collapse an established deployment boundary.

## Decision 3: Gate every API release with Alembic

**Decision:** Run `alembic upgrade head` as the API pre-deploy command and use `/healthz` as the database-aware health check. Configure Product Web `/healthz` to verify the full proxy path.

**Rationale:** A fresh database otherwise reaches API startup before tables exist. Railway blocks a release when pre-deploy fails. The existing health endpoint executes a database query, and Nginx already proxies it.

**Alternatives considered:** A long-running migration service is unnecessary and can race. Running migrations during the image build cannot reach private runtime networking and would couple immutable builds to one database.

## Decision 4: Use managed PostgreSQL and ephemeral file artifacts

**Decision:** Persist all business records in managed PostgreSQL. Use the existing file artifact backend only for the demo and prohibit uploads/durable artifact claims.

**Rationale:** PostgreSQL is the required business database and survives application redeploys. The first demo can use bundled synthetic fixtures without binary uploads. Adding MinIO or an object-storage provider would add another service and credential set without proving the Atlas/Reality slice.

**Alternatives considered:** Public MinIO is unsafe and unnecessary. A private bucket is the next step if uploaded evidence becomes part of the demonstration.

## Decision 5: Keep authentication enabled and separate owner/evaluator access

**Decision:** Use secure hosted cookies, keep verification codes hidden, bootstrap a strong owner-only platform administrator, and disable public signup whenever the demo has no transactional email provider. A future non-admin evaluator account requires a real mail provider and explicit membership in its prepared tenant.

**Rationale:** The platform administrator bypasses tenant membership and must not be shared. With no mail provider, public signup can place verification messages in logs, so the public endpoint must refuse account creation rather than merely hiding codes from the response.

**Alternatives considered:** Disabling authentication violates the product boundary. Sharing platform-admin credentials exposes every tenant. Adding production email and general rate limiting expands this temporary deployment beyond its purpose.

## Decision 6: Automate only within the supplied token's authority

**Decision:** Use the local ignored project token and Railway CLI/API. Probe project-scoped provisioning operations and stop for user action if Railway rejects them; never request or print the token.

**Rationale:** Railway project tokens are scoped to one environment and are intended for deployment automation, but not every infrastructure mutation is guaranteed. The token already resolves to the dedicated `reality-demo/production` environment.

**Alternatives considered:** An account token has broader authority than needed. Interactive dashboard work remains the fallback for an operation unavailable to the project token.
