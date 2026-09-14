# Contract: Independent Browser Deployments

`provider-site` and `apps/web` each own:

- a locked dependency manifest;
- a production build;
- focused browser contract tests;
- a Dockerfile and Nginx configuration;
- an independent CI gate and Compose service.

The Site container serves static files only and has no API dependency. The Web
container may depend on and proxy to `api`. Neither browser app contains business rules.

Production host mapping and TLS are supplied by infrastructure outside this repository.
Release evidence must nevertheless verify the documented origin values and link targets.

Root developer commands map one-to-one to Compose service names: `make site` starts
`site`, `make app` starts `web`, `make api` starts `api`, and `make mcp` starts `mcp`.
Compose resolves required dependencies for API-backed services. Host port overrides use
`SITE_PORT`, `APP_PORT`, `API_PORT`, and `MCP_PORT`; public origins use the uniform
`SITE_URL`, `APP_URL`, `API_URL`, and `MCP_URL` contract and are never inferred from
container ports. Framework-specific build and bind variables are internal details.

Development is a separate Compose override contract. `make dev` runs all services in
the foreground with combined stdout/stderr; `make dev-up`, `make dev-logs`,
`make dev-status`, and `make dev-down` provide detached and agent-operable lifecycle
control. Site and Product Web use Vite hot reload; API and MCP use Uvicorn reload over
the mounted shared-core source. `make stack` retains production-like immutable images.
