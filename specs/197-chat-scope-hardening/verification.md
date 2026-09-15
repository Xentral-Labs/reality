# Verification — 2026-09-15

- Before implementation: new adversarial adapter tests had 19 failures and 5 passes.
- Final new adapter attack tests: 24 passed, covering both providers.
- Full backend regression from packages/reality-core, excluding the separately run
  PostgreSQL integration family: 2541 passed, 9 skipped, one existing transaction
  teardown warning (561.69 seconds).
- Serial PostgreSQL integration: 10 passed.
- Backend Ruff, changed-file format check, spec policy and diff checks passed.
- Ten synthetic real Anthropic cases were manually reviewed; see live-evaluation.md
  and raw synthetic responses. No live OpenAI-compatible evaluation was performed.
- Local API module updated and restarted; /healthz returned status ok. Both main and
  side chats share this adapter. No real company records or allowance grants were
  used during the synthetic evaluation. Direct provider token usage applies.

The initial targeted run exposed a whitespace-sensitive assertion (tool results
crossed a newline); normalizing whitespace fixed the test. The initial full run
was launched from the repository root and interrupted after migration tests could
not find alembic.ini. The complete correct-directory run above supersedes it.

## Review
FR-001–005 implemented. Shared prompt, validated text history and unchanged canonical
read/propose dispatch preserve tenant/confirmation boundaries. No schema/catalog/UI
changes. Scope/refusal is still probabilistic; no claim of universal injection
resistance. Live refusals were sometimes verbose, and one speculated about proposal
existence without reading it; general factual accuracy is not established by these
security checks. Changes are locally committed; production deployment is not included.
