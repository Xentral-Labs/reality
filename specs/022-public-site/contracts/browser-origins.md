# Contract: Browser Origins and Route Ownership

| Environment | Public site | Product Web | API | MCP |
|---|---|---|---|---|
| Production | `https://runreality.ai` | `https://app.runreality.ai` | `https://api.runreality.ai` | `https://mcp.runreality.ai` |
| Local | `http://localhost:5174` or `http://localhost:8082` | `http://localhost:5173` or `http://localhost:8080` | `http://localhost:8000` | `http://localhost:8001` |

The Compose host-port defaults are `SITE_PORT=8082`, `APP_PORT=8080`,
`API_PORT=8000`, and `MCP_PORT=8001`. They may be overridden independently. Their
public counterparts are uniformly named `SITE_URL`, `APP_URL`, `API_URL`, and
`MCP_URL`.

`https://www.runreality.ai/{path}?{query}` permanently redirects to
`https://runreality.ai/{path}?{query}` at the production edge.

## Public site ownership

- `/` and public section anchors
- Static language selection
- Absolute login/signup links composed from configured product origin
- No `/api` proxy, health proxy, authentication request, tenant state, or product routes

## Product Web ownership

- `/`, `/login`, `/signup`, `/verify-email`, `/access-pending`
- `/app` and all nested operational/settings routes
- `/profile` compatibility redirect
- `/api/*` and `/healthz` proxy to API in the container profile

At the product origin, `/` enters the existing unauthenticated/authenticated product
flow. It never renders the public landing page.
