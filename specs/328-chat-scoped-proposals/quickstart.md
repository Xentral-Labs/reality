# Quickstart and Verification

## Backend
```bash
cd packages/reality-core
PYTHONPATH="$PWD/src" ../../.venv/bin/pytest -q tests/test_chat_scoped_proposals.py
PYTHONPATH="$PWD/src" ../../.venv/bin/pytest -q tests/test_chat_confirmation.py tests/test_chat_streaming.py \
  tests/test_master_data_api.py tests/test_migrations.py tests/finance tests/test_application_catalog.py \
  tests/test_schema_indexes.py tests/test_reporting_graph_coverage.py tests/tenant_isolation
```

## Web
```bash
cd apps/web
npm run build && npm run i18n:audit && npm run test:i18n && npx prettier --check src scripts
```

## Manual check
1. Open Chat, start a conversation and ask for a change (for example `run normal month` without an AI provider).
   The proposal appears under that answer.
2. Ask another question. The proposal stays above it.
3. Start a new chat. No proposal is shown; the header shows "1 Other pending approval" and opens Decisions.
4. Reject or approve the proposal and return to the first chat. It is still there with its decision line.

## Evidence
Recorded in the pull request.
