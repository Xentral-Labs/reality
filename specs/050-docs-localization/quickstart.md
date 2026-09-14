# Quickstart: Verify Multilingual Docs

## Automated validation

From `apps/docs`:

```bash
npm run format:check
npm run test
npm run build
```

From repository root:

```bash
make spec-check
git diff --check
```

Expected: locale inventory, navigation/search, links, guide structure, deployment
contracts, formatting, build, and spec policy pass.

## Reader validation

1. Open English Docs and switch to Deutsch, Nederlands, and Español.
2. Verify localized navigation and search labels.
3. Switch language from a nested guide chapter and retain the chapter.
4. Search for a native phrase in every locale.
5. Visit every reader area in every locale.
6. Confirm old unprefixed English bookmarks still resolve.

## Semantic review

Compare guide examples across locales: quantities, currencies, formulas, Commitment
and Movement directions, Reservation lifecycle, corrections, postings, and settlements
must match.

## Validation results

Validated on 2026-09-03:

- Formatting passed.
- All 18 Docs contract tests passed.
- The VitePress production build passed and rendered all locale routes.
- Each translated locale mirrors all 29 canonical Markdown pages (87 translated pages).
- Specification policy and whitespace checks passed.
