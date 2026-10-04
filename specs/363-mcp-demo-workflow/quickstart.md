# Validation

Use the disposable PostgreSQL test database, never a business tenant. Run focused
`test_demo_mcp_workflow.py` and `test_chat_tools.py` with worktree source on PYTHONPATH.
Run web source contracts, build, i18n and generated catalog checks. Confirm the MCP story
uses separate explicit propose/read/confirmation rights, review fingerprint, receipt
and replay; negative authority/stale/foreign cases must have no unintended effects.
Verify `order_explain` retains a shipment Movement even when `shipments_list` is empty.
Run all required CI jobs on the final pushed commit; do not infer green from a prior head.
