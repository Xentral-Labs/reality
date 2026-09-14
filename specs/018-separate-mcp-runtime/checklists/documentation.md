# Documentation Review Checklist: Separate MCP Runtime

**Reviewed**: 2026-08-31

- [x] README identifies Web/API and MCP as independently deployable processes.
- [x] README documents the exact root-origin `MCP_URL` contract without a redundant path.
- [x] Architecture shows both runtimes using the same application services and PostgreSQL schema.
- [x] Web and CLI contracts contain no supported mounted MCP or stdio path.
- [x] Health and readiness endpoints and their different meanings are documented.
- [x] Separate database-pool budgets and their aggregate ceiling are documented.
- [x] Tenant authority comes from the authenticated token, never a request argument or URL.
- [x] Mutation tools remain proposal-first and require separate confirmation.
- [x] Operation context is described as trace metadata, not business truth.
- [x] Compose, environment examples, and current-state documentation agree on ownership and ports.

Review completed against the implementation and repository scans on 2026-08-31.
