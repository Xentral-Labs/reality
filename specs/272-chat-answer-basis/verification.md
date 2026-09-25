# Verification: Compact Chat Answer Basis

## Green evidence

- `packages/reality-core/tests/test_storyline_trace.py` and `test_storyline_chat.py`: **15 passed**.
- Migration upgrade/model parity/downgrade plus full migration-chain test: **2 passed**.
- `apps/web/scripts/chat-answer-basis.test.mjs`: **2 passed**.
- Product Web TypeScript/Vite production build: **passed**.
- Product Web localization audit: **English, German, Dutch, and Spanish passed with zero missing strings**.
- `make lint`: **passed**.
- `make spec-check`: **passed**.
- `git diff --check`: **passed**.
- Local Docker migration image rebuilt; `api` is healthy on port 8000 and Product Web returns HTTP 200 on port 8080.

## Full-suite status

`make test` collected 4,390 tests and reached 18% before it was stopped after unrelated failures were already established. The isolated failures in `tests/scenarios/test_international_demo.py` are demo scheduling `handler_timeout` failures while seeding the canonical profile. They occur before chat-answer-basis behavior and do not reference the changed files. The full-suite gate therefore remains open and task T020 is intentionally not marked complete.

## Local acceptance

The rebuilt local application is available at `http://localhost:8080`. Existing replies intentionally have no retroactive basis. Ask a new open-customer-order question, then expand **Grundlage dieser Antwort**. A supported fulfillment answer shows up to four business rows and keeps eligible call details under the secondary **Technische Aktivität** disclosure.

## Worktree preservation

Pre-existing changes in `reality/agent/mcp_chat.py`, `reality/agent/streaming.py`, and `tests/test_anthropic_copilot.py`, plus the untracked database dump, were not edited by this feature.
