# Quickstart: Validate Complete Chat and MCP Command Coverage

## Focused gates

```bash
make spec-check
pytest -q packages/reality-core/tests/test_agent_command_parity.py
pytest -q packages/reality-core/tests/test_agent_discovery.py
pytest -q packages/reality-core/tests/test_chat_mcp_orders.py
pytest -q packages/reality-core/tests/test_chat_mcp_business_commands.py
```

Expected: every command has a valid classification; discovery is bounded and tenant
scoped; proposing causes no business effect; approval atomically executes through the
shared service; orders preserve Source → Evidence → Reality; reject/stale/replay/auth
failures persist no partial effects.

## Repository gates

```bash
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

Expected: all gates pass and public MCP settings metadata renders structured schemas
without changing existing tool names or token grants.

## Verification record (2026-09-02)

- `make spec-check`: PASS.
- `make lint`: PASS.
- Complete backend suite: 341 passed, 7 skipped.
- Focused agent parity block: 64 passed, 2 optional runtime tests skipped.
- Web contract tests: 48 passed.
- Localization audit: 796/796 keys covered in each supported locale.
- Production frontend build: PASS (existing non-blocking chunk-size advisory only).
- Migration impact: none; no schema or Alembic changes.
