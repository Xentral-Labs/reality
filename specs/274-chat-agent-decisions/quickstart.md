# Quickstart: Verify Chat Agent Decisions

Use an isolated PostgreSQL test company and intercepted provider responses; never shared business data.

Run focused provider, lifecycle, attribution, interaction and migration tests. Verify ordinary Chat receives confirm schemas, prepare changes no business state, a later confirmation creates exactly one effect, replay creates none, decision detail reports `chat_agent`, protected operations still refuse without authority, and Playground stays read-only.

For the end-to-end story, make the provider propose a Party then confirm the returned decision ID. Expect ordered `propose` and `decide` interactions, one executed decision, Chat attribution and one Party/event. Repeat prepare-only and expect a pending decision.

Then run migration, backend, lint, spec and generated-documentation gates. Run `make docs-generate` before `make docs-catalog-check` when catalog wording or schemas change. Red gates mean incomplete.

## Verification evidence — 2026-09-25

- Focused Chat, scope, attribution, application, Playground and streaming suite: `80 passed`.
- Every directly affected proposal-metadata suite: `135 passed, 2 skipped`.
- Migration suite: `15 passed`; added 0098 upgrade/downgrade proof: `1 passed`.
- Chat decision interaction correlation proof: `1 passed`.
- Decision Trail frontend unit suite: `8 passed`.
- Core Ruff, spec policy, four-language audit and production Web build passed.
- Generated tool-usage documentation was refreshed; the committed-output catalog check passed.
- The complete serial PostgreSQL backend suite passed: `4388 passed, 10 skipped, 1 warning` in `3063.12s`. The warning is the existing SQLAlchemy transaction cleanup warning in `tests/conftest.py`.
