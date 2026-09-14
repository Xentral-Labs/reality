# Research
Plan research by order_research audited agent/settings.py, agent/mcp_chat.py, mcp/auth.py and settings web adapters.
- Decision: managed/company Anthropic only. Other preset configuration is stored but current copilot_api_key and mcp_chat use Anthropic; pretending they power Ask Reality would be false. Backend multi-provider transport is out of scope.
- Anthropic PUT fixes model/base URL, empty key retains current compatible credential, nonblank key replaces vault secret. Managed PUT revokes company secret.
- GET requires owner and may initialize AISettings/migrate an old secret. GET metadata never returns clear keys; PUT response shapes vary, so refresh after success.
- MCP allowlists distinguish read/propose/confirm. UI defaults to no tools and sends explicit names. Existing wildcard grants remain visible. Tokens are tenant-bound, have no expiry, duplicate names allowed, and secret is returned once.
- No request receipt/retry key: explicit current-state inspection after ambiguity. A lost token cannot be reconstructed. Never auto-create or auto-revoke by matching name.
- Existing test_ai_mcp.py, test_master_data_api.py, test_mcp_http_runtime.py, test_mcp_chat.py and practice security suites cover shared authorities.
