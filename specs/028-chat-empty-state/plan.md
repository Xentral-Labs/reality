# Implementation Plan: Focused Chat Empty State

## Technical Context

The React Ask Reality page already receives sessions, messages, suggestions, and an active session ID. Remove the redundant conversation header, add a presentation branch based only on loaded session count, and reuse the existing send handler. Extend existing CSS and static frontend contract tests. No API, domain, service, tool, database, or dependency changes.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | No domain or traceability behavior changes. |
| Reality authority | PASS | Browser derives layout only from existing chat state. |
| Proven schema | PASS | No schema changes. |
| Tenant/service boundaries | PASS | Existing tenant-scoped API and send flow are reused. |
| Specification and tests | PASS | Spec and failing proof precede implementation. |
| Explainable web product | PASS | Empty chrome is removed without hiding existing-session context. |
| Simplicity | PASS | One conditional layout and scoped styles. |

## Project Structure and Design

- `apps/web/src/App.tsx`: select focused or standard chat presentation.
- `apps/web/src/chat.css`: centered desktop/mobile focused layout.
- `apps/web/scripts/product-boundary.test.mjs`: static regression contract.
- `docs/features/chat_sessions.md`: durable conditional minimum-UI rule.

Treat `data !== null && data.sessions.length === 0` as the focused state. Do not use an empty active ID alone because it also occurs while loading. Always omit the conversation header; additionally omit the aside and apply a single-column workbench when empty. Retain the same callbacks.

## Verification

Run frontend contracts, the TypeScript/Vite build, spec policy, and desktop/mobile visual inspection. Rollback removes the focused branch and styles. Post-design Constitution Check: PASS.
