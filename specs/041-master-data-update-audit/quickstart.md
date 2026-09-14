# Quickstart: Auditable Master Data Updates

## Validation scenarios

1. Ask Chat to update one Party, Item, and Location; verify opaque-ID preview and no mutation before approval.
2. Approve and verify stable IDs, new values, one linked event, and exact `before`/`after` fields.
3. Cover nullable relationships, Decimal, boolean, and role-list changes.
4. Change a target after preview; stale approval must change nothing.
5. Put an invalid record late in a batch; all state, SourceRecord versions, and events must roll back.
6. Update through CLI/API/Web; normalization and event structure must match.
7. Activate/deactivate and inspect its state diff.
8. Inspect new and historical events through the normal event/Inspector response.

## Required commands

```bash
make spec-check
make lint
make test
make web-build
```

All gates must pass; tenant/stale/atomicity failures persist nothing; every effective supported field change is visible in immutable event history.

## Verification record

- Focused audit, Chat/MCP, catalog, tenant, API, CLI, and parity regressions passed.
- Complete PostgreSQL backend suite after rebase onto current `main`: 331 passed, 7 environment/provider skips.
- Ruff and specification policy passed.
- Product Web contract suite: 48 passed; English, German, Dutch, and Spanish audits passed.
- Production Web build passed with the pre-existing chunk-size advisory.
- Migration review: no schema change is required; rollback is code-only and additive event payloads remain readable.
