# Quickstart: Agent Capability Guidance

## Acceptance path

1. Describe `fact_observe_propose`; verify source evidence is mandatory and typed
   Reality must not be mirrored as Facts.
2. Describe `order_create_propose`, `reservation_propose`, and
   `movement_create_propose`; compare their use and prohibited-use conditions.
3. Request an unknown or internal tool and verify a bounded response without mutation.
4. Create but do not approve one proposal and verify Reality remains unchanged.
5. Approve a valid proposal, re-read its declared projection, and verify Reality rather
   than trusting the response alone.
6. Run twelve command-selection cases and planted catalog-drift fixtures.

## Required checks

```bash
make spec-check
make lint
make test
make docs-build
make web-build
```

## Expected boundary

Lookup is read-only metadata. Domain services retain validation, proposal tools retain
confirmation, and description lookup creates no business or governance record.

## Verification record

- Specification policy and Ruff: PASS.
- Focused capability, catalog, MCP/Chat parity, and discovery suite: 34 passed.
- Complete PostgreSQL backend suite: 356 passed, 7 skipped.
- Public Docs contracts and production build: PASS; 13 contract tests.
- Product Web contracts, localization audit, and production build: PASS; 48 contract
  tests and 796/796 strings per supported language.
- Schema and migration review: PASS; no SQLAlchemy model or Alembic migration changed.
- Diff whitespace and rollback review: PASS; metadata and read-tool removal require no
  business-data recovery.
