# Verification

1. Create competing direct, group and default price lists and quantity tiers.
2. Call `price_quote_read` with a complete commercial context.
3. Compare the selected entry with `resolve_price` and inspect provenance.
4. Repeat below all tiers and with a foreign Party ID.
5. Run focused pricing/MCP tests, spec policy, catalog generation and lint.

## Verification evidence

- Spec policy passed.
- Ruff passed for changed Python and test files.
- Focused pricing, MCP read-contract and application-catalog suite: 82 passed, 2 skipped.
- Public catalog reference regenerated with the repository formatter.
