# Verification

## Completed checks

- New service tests failed first for the stated reason
  (`TypeError: enter() got an unexpected keyword argument 'content'`), then passed:
  both starts create their company, the empty start reports the `company-empty` preset
  and the name "My company", the receipt reports the start that was taken, a repeated
  request replays the same company, the conflicting start raises `Conflict` and an
  unknown one `InvalidOperation`.
- A company created through the empty start connects and starts Demo Data afterwards,
  which is what US3 promises.
- API test proves the closed adapter literal: an unknown content is rejected with 422
  before anything is created, the empty start returns 201 with the `company-empty`
  preset, and the following read reports that company as the receipt.
- Focused free playground and company setup API suites: 23 passed.
- Browser run passed on the real UI: the two cards render, `posts` stays 0 until a card
  is clicked, each card sends its own content, the chosen start decides the progress and
  failure copy, retry still replays, and the archived receipt still creates nothing. The
  choice screen fits a 390 px viewport in all four languages; screenshots reviewed for
  desktop and German mobile.
- Web checks: 171 contract tests, the four-language audit (1863/1863 in every language),
  TypeScript project build and the Vite production build.
- Lint, format and spec coverage policy clean.

## Completion

Full PostgreSQL suite: 2531 passed, 9 skipped in 20:56.

The automatic creation is replaced by an explicit one under exactly the same condition,
so no account that already holds a ready receipt is asked again. Rollback is a code
revert; receipts already written stay valid and no migration exists to undo.
