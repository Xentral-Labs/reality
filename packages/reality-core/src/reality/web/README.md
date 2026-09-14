# HTTP adapter

Read `docs/WEB_SPEC.md` first.

This package hosts the tenant-scoped JSON API, authentication endpoints and the
remote HTTPS MCP boundary. It deliberately contains no browser templates or
static presentation assets. The independently deployed React application owns
all marketing and product UI. Business decisions belong in `services/`, and
mutations must use the shared tool/service layer.
