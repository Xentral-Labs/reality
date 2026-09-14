# Quickstart: Internal Anthropic Copilot

1. Set `ANTHROPIC_API_KEY` in the API runtime environment.
   For an identity-linked key, also set `ANTHROPIC_WORKSPACE_ID`.
2. Run `pytest packages/reality-core/tests/test_ai_mcp.py packages/reality-core/tests/test_chat_confirmation.py`.
3. Run `node --test apps/web/scripts/ux-configuration-contract.test.mjs`.
4. Run `make spec-check`, `make lint`, `make test`, and `make web-build`.
5. Open Company settings → Copilot and confirm Reality-managed is preselected.
6. Select Anthropic, OpenAI, Google Gemini, Mistral, Groq, OpenRouter, or Custom; store a test key and confirm only its fingerprint returns.
7. Confirm the curated choice supplies a compatible default model and only Custom exposes an endpoint field.
8. Ask an inventory question and confirm the company provider is used through a registered read tool.
9. Switch back to Reality-managed and confirm the company key is revoked and the server credential is used.
