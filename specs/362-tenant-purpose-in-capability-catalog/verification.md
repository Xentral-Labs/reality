# Verification

Date: 2026-10-05. Scope: spec 362 FR-001, FR-002, DR-001, SC-001.

## Local evidence

- The MCP boundary test was checked against a defect: with the purpose replaced by a constant
  `business`, it fails; restored, it passes.
- Focused PostgreSQL suite: `tests/test_capability_catalog.py` 20 passed.
- Touched-area suite: capability catalog, HTTP MCP runtime, AI MCP adapter, tool and
  application catalogs, tenant isolation families and spec policy: 149 passed, 2 existing skips.
- Ruff check: passed.
- `make spec-check`: passed.

Fixtures create isolated PostgreSQL databases. No user company, credential or deployment is
changed by these tests.
