# Quickstart: Chat Master Data Proposals

## Focused validation

From the repository root:

```bash
.venv/bin/pytest -q packages/reality-core/tests/test_chat_master_data.py packages/reality-core/tests/test_ai_mcp.py packages/reality-core/tests/test_mcp_chat.py
make spec-check
```

Run the PostgreSQL-marked master-data batch stories with the repository's documented
test database configuration before completion.

## Acceptance walkthrough

1. In an empty tenant, ask Ask Reality to create three Items with distinct SKUs and
   names but no source information.
2. Verify one pending Item proposal lists all three records, uses `pcs`, and no Item or
   SourceRecord exists yet.
3. Confirm the proposal and verify all three Items exist with opaque IDs and null source
   links.
4. Repeat for a Party with a name and role and a Location with only a name; verify the
   Location uses `warehouse`.
5. Submit a two-Item request whose second record has a blank name; confirmation must
   create neither Item.
6. Submit a Location referencing another tenant's parent; confirmation must disclose no
   foreign values and create nothing.
7. Submit an Item with source system, external ID, and extra payload; verify the confirmed
   Item has one shortest link to the immutable lossless SourceRecord.

## Expected outcome

Manual master-data creation never requires an import artifact. Every mutation is visible
as an exact pending proposal and only explicit confirmation creates an all-or-nothing
same-family batch through the shared service boundary.

## Verification record

Verified on 2026-09-02:

- Focused Location hierarchy, Chat, and MCP regression suite: 26 passed, 2 provider-specific skips.
- Complete backend PostgreSQL suite: 318 passed, 7 environment/provider skips.
- Ruff: passed.
- Specification policy: passed.
- Product Web contract suite: 46 passed; `en`, `de`, `nl`, and `es` audits passed.
- Product Web production build: passed with the pre-existing large-chunk advisory only.
- Nested batch proposal rendering regression: passed; record objects render as labeled values rather than implicit `[object Object]` strings.
- Migration review: no schema or Alembic change.
