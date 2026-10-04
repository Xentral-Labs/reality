# Implementation Plan: Existing-tool evidence boundaries
**Language**: English
## Technical Context
Python 3.12, SQLAlchemy 2/PostgreSQL and the existing shared application tools. No new dependencies or migrations.
## Constitution Check
| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality, source losslessness | PASS | Presentation-only fields, no new authority |
| Typed fields and shortest relationships | PASS | Existing condition codes and identities; no FKs |
| Shared application tools and tenant scope | PASS | Decorate existing scoped reads, no additional query |
| Confirmation and external effects | PASS | No mutation or automatic provider retry |
| PostgreSQL and Decimal | PASS | Existing quantities used without recomputation |
| English artifacts and Spec Kit | PASS | Accepted scope, traced tasks and test-first gates |
## Design
Introduce pure `services/read_interpretation.py` functions for blocker kind, historical cause and exception association boundary. Apply projection interpretation only in `operational_page` and `projection_rows`, after derivation/storage reads; canonical readiness accepts optional interpretation disabled in cached builders. Exception service similarly exposes presentation metadata by default, explicitly disabled by projection builders. No cache version bump is needed because caches contain unchanged payloads.
Capability index/topic results add external-runtime visibility without inspecting the client. Both providers inspect stop signals before interpreting executable tool arguments. Streaming decoder raises a dedicated output-limit exception before JSON argument parsing; adapters reset streamed content and return the same localized incomplete-output notice as ordinary responses. No continuation, retry or replay.
## Research
See research.md. Research-agent review identified the exception cache reconstruction trap and hold-condition versus unique-hold counting distinction.
## Test Plan
Test public MCP/shared tools for queue/readiness/explain parity and mixed blockers; exception read metadata plus unaltered cached payloads; capability discovery and grants. Test both providers, stream/nonstream, text and complete-looking or malformed tool payloads stopped by the limit; assert zero dispatch and durable/reset notice. Existing normal, transport failure and security tests are required.
Run focused pytest, Ruff, generated reference check, spec policy, full Quality workflow and final independent diff review. Perform a live synthetic read round if configured safely; report residual free-form errors without guaranteeing prose.
## Rollback
Revert additive presentation fields and adapter handling; no schema or business-state repair.
## Complexity Tracking
No constitutional exceptions.
