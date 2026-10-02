# Research Decisions

## Shared settings failure
Decision: separate public MCP URL display validation from runtime validation; use API_URL issuer fallback.
Rationale: reproduced `configured_mcp_url({REALITY_ENV: production, MCP_URL: https://mcp.runreality.ai/, API_URL: https://app.runreality.ai})` raising an HTTP issuer error. Helm already provides these values; spec265 FR-023 defines API_URL as issuer. Baseline owner configuration API test passes outside production.
Alternatives: add a duplicated chart-only issuer variable (does not fix inappropriate coupling); change historical credential/token storage (no evidence and outside scope); disable production HTTPS (rejected).

## Membership presentation
Decision: absent role means no active membership, not Member. Only private library list explains membership explicitly; report detail/change remain non-disclosing.
Rationale: platform admin visibility does not supply membership. Existing `useRead` retains error code, allowing localized refusal without another authorization rule.
Alternatives: grant platform admins private author access (rejected); change every NotFound to membership error (unnecessary detail behavior change).

Research was dispatched read-only through Spec Kit plan's research-agent instruction. No unresolved technical or product clarification remains.
