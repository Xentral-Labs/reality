# Validation
From packages/reality-core run ../../.venv/bin/pytest tests/test_tool_evidence_boundaries.py tests/test_chat_scope_security.py tests/test_chat_streaming.py tests/test_mcp_read_contract.py tests/test_fulfillment_readiness.py.
From repository root run make docs-generate, stage generated references, make docs-catalog-check and make spec-check. Run full Quality CI on the exact final PR head. Expected: clear read boundaries, unchanged cached payloads, zero dispatch on output limits, successful normal paths.
