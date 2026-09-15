# Verification
Run pytest tests/test_chat_scope_security.py tests/test_anthropic_copilot.py tests/test_ai_mcp.py tests/test_playground_security.py tests/test_chat_confirmation.py against PostgreSQL. Attack transport tests must send no unauthorized confirmation, preserve caller tenant and reject forged history before network calls. Fake model responses do not measure real-provider refusal rates.
