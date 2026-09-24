# Plan: Welcome exception count from the stored register

In `packages/reality-core/src/reality/web/api.py`, replace the dashboard's live `exception_page(size=5)` call with the existing `reality.services.attention_reads.attention_register(size=5)`. Its `page.total` becomes `totals.exceptions` and `sample_scope.exceptions.total`, its items become the `exceptions` sample, and its metadata state is added to `sample_scope.exceptions.state`. When the metadata has no `completed_at`, the totals are null. In `apps/web`, the `Dashboard` type allows a null exception total and `HomePage` shows the existing unknown placeholder for null counts; `docs/WEB_SPEC.md` records the Welcome rule. The `/exceptions` endpoint and `exception_page` remain unchanged.

## Constitution Check
PASS: read-only adapter change that reuses a shared service (web UI invariant: no alternative business rule). No schema, stored authority, tenant-scope, command, tool or MCP change; the reused service already enforces tenant scope and is already catalogued, so no isolation catalog or generated docs change. Stored rows remain disposable projection results (rule 11).

## Verification and rollback
Write the regression test first in `tests/test_attention_reads.py`: uninitialized dashboard reports null; after one published generation and with every derivation forbidden, the dashboard total and sample equal the register's. Run the attention, dashboard, application catalog, tenant isolation and spec policy tests plus the web contract tests and build. Time the dashboard handler before and after on the local company. Revert the commit to roll back; no migration.
