# Implementation Plan: Chat response latency

## Summary and technical context
Python 3.12+, SQLAlchemy 2/PostgreSQL, existing httpx providers and FastAPI; React/TypeScript fetch streaming. No new dependency, table, migration or provider. Initial latest-main baseline f20a3336; final branch rebased onto 2c1c4ddc and frontend checks repeated. User scope approved in conversation.

## Constitution Check
| Principle | Before design | After design | Evidence |
| --- | --- | --- | --- |
| Source → Evidence → Reality | PASS | PASS | No value or evidence transformation |
| Reality authority | PASS | PASS | Existing inventory semantics |
| Proven schema | PASS | PASS | No schema expansion |
| Tenant/shared services | PASS | PASS | Same send/dispatch path and admission |
| Specification/tests first | PASS | PASS | Spec, planned proofs, tasks and analysis precede code |
| Explainable web | PASS | PASS | Provisional text becomes existing recorded answer |
| Simple storage discipline | PASS | PASS | Batched SQLAlchemy reads, no persistent cache |
| Received values | PASS | PASS | Lossless serialization and exact Decimal parity |

## Design and files
1. `services/core.py`: batch `inventory_rows` using existing commitment terms, movements and reservations; preserve movement order and per-item semantics. Query latest twelve chat turns with stable ordering. Optional event callback on `send_chat_message` passes to provider adapters; existing wrappers/recorders still call same service.
2. `agent/mcp_chat.py` and `agent/streaming.py`: optional streaming callback, standard SSE assembly, complete tools only, explicit end detection, redacted timing. Keep non-stream callers supported. Stable Anthropic tool/system cache breakpoints, once-built schemas, compact JSON values. No discovery heuristics.
3. `web/chat_stream.py`: request-scoped worker runs the synchronous service with its own database session and copied caller context. Async response reads transient events; disconnect does not replay or execute confirmations. The bounded six-round provider work can finish and persist for ordinary recovery. No durable job, scheduler or subsystem timer.
4. `web/api.py`: existing authenticated route accepts `stream=true`, performs ordinary tenant/session preflight before starting response, returns NDJSON start/reset/delta/done/error events with no-cache and no-buffer headers. Existing JSON return remains compatible. Captured principal and user presentation/allowance flow to service worker.
5. `apps/web/src/chatStream.ts`, `api.ts`, `unified/ChatPage.tsx`: decode split UTF-8/NDJSON frames, show provisional current-round text, reconcile final IDs immediately; retain final answer while metadata reloads. No auto resend; failures discard provisional text and preserve recovery state. Existing other clients retain JSON behavior.

## Validation
Tests first: provider fragmented tool arguments/text, truncation/error, schema/cache and permissions; bounded history; inventory parity and query scaling; HTTP admission and stream completion; JS parser split Unicode/errors plus browser delayed streaming/reconciliation. Full backend pytest, Ruff, spec gate, frontend contracts/i18n/build, catalog generation/staleness, migration checks through backend suite. Record real measured first text/completion/cache/tool timing after implementation with same questions using approved configured provider. No production latency claim.

## Risks and mitigations
Provider SSE differs: separate adapters, end markers required, no automatic retry after dispatch. Partial text is provisional; complete persisted answer/error replaces it. Per-request worker owns its session and caller context; no ORM session shared concurrently. An interrupted connection does not imply business cancellation. Compatibility JSON path retained. Nondeterministic provider latency means measurements are observations.

## Migration and rollback
No migration. Revert application and UI together to restore JSON-only sending; existing messages/proposals remain readable. No scope exceptions.
