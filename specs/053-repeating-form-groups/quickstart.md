# Quickstart: Repeating Form Groups

1. Select Order Operations and start manual order creation.
2. Confirm that one order-line row appears and no JSON editor is visible.
3. Select an item, enter quantity and unit price, add a second row, then remove it.
4. Review and confirm; verify the submitted request contains `lines: [{...}]`.
5. Run `cd apps/web && npm run test:contracts && npm run i18n:audit && npm run build`.
6. Run `make lint && make spec-check`.

## Verification Evidence

- 55 frontend contracts passed.
- Strict localization audit passed with 801/801 keys per language.
- Production TypeScript/Vite build passed.
- Ruff lint, Spec Kit policy, and diff whitespace checks passed.
- The parent Feature 046 backend suite passed with 374 tests and 7 skips; this follow-up changes no backend or persistence code.
