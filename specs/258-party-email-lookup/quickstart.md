# Validation

1. Create two tenants and Parties, including a shared address in both tenants.
2. Propose and confirm a Party with a labelled mixed-case email.
3. Discover by its lower-case form and inspect the returned email list.
4. Replace and then remove the list through confirmed Party updates.
5. Prove the other tenant never appears.
6. Run `make spec-check`, focused Party/MCP tests, migration tests, `make docs-generate`, lint and the required suite.

## Verification evidence

- `python3 scripts/check_spec_policy.py` — passed.
- `ruff check` for the changed Python and migration files — passed.
- `alembic heads` — `0092_party_email_addresses (head)`.
- Focused Party, proposal, audit, MCP contract and catalog suite — 99 passed, 2 skipped.
- Catalog reference regenerated and formatted; a second generation produced the identical diff.
