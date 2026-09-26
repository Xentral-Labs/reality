# Quickstart: Human Chat Confirmation

## Focused proof

```bash
.venv/bin/pytest -q \
  packages/reality-core/tests/test_mcp_chat.py \
  packages/reality-core/tests/test_chat_scope_security.py \
  packages/reality-core/tests/test_chat_master_data.py \
  packages/reality-core/tests/test_chat_mcp_orders.py \
  packages/reality-core/tests/test_playground_chat.py
```

Expected: production Chat exposes reads/proposals but no decision tool; Playground exposes reads;
Chat proposals stay pending with zero effect; Web human review still confirms or rejects with
truthful attribution; external MCP permission tests remain green.

## Repository gates

```bash
make spec-check
make docs-catalog-check
make lint
make test
```

No documentation generation diff is expected because public MCP contracts do not change.

## Browser acceptance

1. Ask Chat to create a test customer or order.
2. Verify it reads current references and prepares a pending decision.
3. Verify no target record exists before review.
4. Open the decision card and confirm as an authenticated operator.
5. Verify one effect, human attribution and a current read-based explanation.

## Verification evidence — 2026-09-26

- Focused Chat/security/review suite: **116 passed**.
- Complete PostgreSQL backend suite: **4410 passed, 10 skipped**, one pre-existing SQLAlchemy
  teardown warning; duration 54:57.
- Web test/build gate: **399 passed**, all four localization catalogs passed, production build
  succeeded.
- `make spec-check`: passed.
- `make docs-catalog-check`: passed with no generated catalog change.
- `make lint`: passed.
