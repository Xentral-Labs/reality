# Existing interfaces
Entry: /app/settings?tenant=...&settings_view=ai, owner-only.
GET settings/ai supplies metadata/catalog/tokens. PUT settings/ai uses provider_preset=managed or anthropic and api_key only (fixed Anthropic model and endpoint remain server-owned).
POST settings/mcp/tokens sends name and an explicit nonempty allowed_tools array. POST settings/mcp/tokens/{id}/revoke identifies exact token. Neither UI nor error rendering echoes clear credentials. New token is displayed once from successful response; no persistent secret recovery.
