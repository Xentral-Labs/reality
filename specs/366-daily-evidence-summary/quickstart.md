# Validation

From packages/reality-core run ../../.venv/bin/pytest tests/test_mcp_read_contract.py
and tests/test_chat_scope_security.py, then the broader compatibility selections.

Read business_records_discover with family movement, query return, limit 100: the
summary counts match the exact shown IDs and distinguish customer/supplier types.
Repeat at limit 1 and follow next_cursor: each page reports its own coverage.
Read order_explain for ready and blocked open orders: current blockers remain, cause
of nonexecution stays unknown. Closed lines report cause not applicable.
Run generated docs/catalog checks and full Quality CI before completion.
