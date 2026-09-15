# Verification — chat response latency

## Base and scope
Implementation worktree `/private/tmp/reality-chat-latency`, branch `perf/chat-response-latency`, initially from `origin/main` (`f20a3336`), then rebased onto the latest fetched main `2c1c4ddc` (the chat removal dialog). Streaming/composer browser tests, all frontend contracts and the production build passed again after that rebase. The owner's original dirty worktree was not changed. No schema migration or deployed service change.

## Pre-implementation review
The accepted scope has no unresolved questions. All Constitution checks pass; requirements cover tenant/source authority, confirmation, streaming failure and exact values. Analysis found no critical or high consistency/coverage gaps. Requirements map to tests/tasks in spec.md and tasks.md. No extensions/hooks are installed.

## Test-first evidence
- Inventory scaling test initially failed: 13 queries for one item vs 222 for twenty. It now passes with a constant query count (at most 12), revised supplier commitments, active reservations and cross-tenant data.
- History test initially loaded sixteen turns instead of twelve. It now proves SQL LIMIT and chronological presentation, including deterministic user/assistant timestamp ties.
- Stream tests initially failed because no parser/endpoint existed. They now cover byte-at-a-time Unicode, indexed tool arguments, completion markers, truncation, errors and exact dispatch.
- Real Anthropic traffic exposed an empty partial_json fragment for no-argument tools. A regression reproduced JSONDecodeError before the fix; an empty fragment now preserves `{}`. Three failed exploratory calls were not treated as timing successes; all four subsequent measurements completed successfully.
- Browser fixtures prove visible text before done, clearing tool-round preambles, exactly one final answer across stale metadata reads, mobile width, and draft recovery without automatic resend after truncation. Screenshots were visually inspected.
- API tests cover cross-tenant refusal and no full-history read in preflight. The preflight connection is released before the worker owns a new session. A disconnect test proves the original send completes once and closes its session.

## Local gate results
- Final affected backend families: **86 passed** (tenant isolation, application catalog, streaming, inventory/history, Anthropic adapter and chat scope security). This includes every failure from the complete run plus the authenticated preflight regression.
- Frontend contracts: 191 passed (includes streaming decoder tests).
- Frontend formatting, en/de/nl/es localization audit and TypeScript/Vite production build: passed. Existing bundle-size warning remains.
- Ruff from `packages/reality-core`: passed. An initial root-directory invocation inferred imports differently; it was corrected without unrelated lint edits.
- Spec policy: passed.
- Catalog regeneration: completed with Prettier; generated output is unchanged against HEAD.
- Complete backend run (`pytest -n 2 --dist worksteal --durations=15 -q`): **2,583 passed, 10 failed, 9 skipped** in 833.89 seconds. Nine failures were the missing classification of the new `get_chat_session` operation; one was logging capture after migration logging configuration disabled an existing logger. Registered the tenant-scoped read, added foreign/unknown lookup evidence, updated the catalog operation count from 485 to 486, and isolated the logging test. The final 86-test rerun above passes all affected families. The full suite was not repeated a third time; its initial red result is retained here rather than represented as an all-green single run.
- An earlier four-worker run had demo timeout failures and a 60-second integration bound exceeded under concurrent load; the stable two-worker run passed those cases (10,000-source replay: 33.73 seconds). A source-inspection failure from editing during that earlier run also did not recur.
- Browser checks passed: dedicated streaming (desktop/mobile/error), existing composer, analytics, collapsible navigation and full Storyline matrix. Storyline fixtures now seed their independent conversation and use the current `/app/chat` route. The broader delivery browser stops before chat at the obsolete Home heading `Your business, in focus.`; the identical failure was reproduced against an untouched main snapshot at f20a3336. It is an existing browser-fixture limitation, not a passing check.
- Authenticated preflight regression first failed because accessing expired ORM user attributes after rollback reopened a transaction. Copying caller/options before rollback fixes it; the final test asserts no transaction is retained at stream construction.
- `make` itself is unavailable due to the host Xcode license state; the exact underlying commands were executed directly instead. No license or system configuration was changed.

## Real-provider measurements
Same managed Haiku provider and tenant as the original investigation, new empty conversations, two questions repeated twice. Ran the isolated code in a temporary directory in the existing API container, without replacing its running service. Streaming callback times measure internal arrival; browser rendering is separately validated. Static cache was warm. The full PostgreSQL suite ran concurrently, so tool wall times are not an isolated throughput comparison.

| Question | Run | First text (s) | Final-answer round starts (s) | Complete (s) |
| --- | --- | --- | --- | --- |
| Open customer orders | 1 | 1.372 | 3.215 | 9.220 |
| Stock shortages | 1 | 1.095 | 3.016 | 8.235 |
| Open customer orders | 2 | 1.216 | 3.363 | 16.170 |
| Stock shortages | 2 | 1.086 | 2.693 | 7.908 |

All four replies used two provider rounds and one business read tool. Every round reported 34,037 cached input tokens; uncached initial input was 329–331 tokens. Both tools issued 27 SQL statements instead of the baseline 130 (79% fewer). Complete responses were 1,338–2,576 characters; the longer order response explains part of the 16-second total. No claim of reliably lower total response time or production percentile is made. The clear measured improvement is earlier visible output and verified cache/query reuse. Cold-cache time and concurrent production load remain unmeasured.

Baseline full replies were 8.088–12.647 seconds with no incremental output and zero reported cached input tokens. The baseline local deployment predates the newest main; provider output length/page selection and concurrent load also vary, so the two sets are not a controlled total-latency benchmark.

Metadata-only measurements: measurements.json. Temporary raw probes/logs/screenshots: `/tmp/reality-chat-perf/`.

## Rollout
Changes are prepared on the isolated branch. No model switch, schema update, provider tool search, or removal of allowed tools. JSON clients remain supported. Reverting the app/UI change restores prior delivery without affecting persisted conversations.

## Final review
Reviewed service quantity parity, tenant catalog registration, completed tool assembly, confirmation preservation, stream error/disconnect handling and saved-message reconciliation. No critical findings remain in the changed behavior. All failures attributable to this change have passing regression evidence; the unrelated Home browser fixture limitation is explicit above. No deployment or merge was performed.
