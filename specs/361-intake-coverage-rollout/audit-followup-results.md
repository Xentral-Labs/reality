# User audit follow-up results — 2026-10-04

Base: `9f3c9478dfac49bcb633ff8d68bd88a4c9913798` (latest fetched main).
All database qualifications use disposable PostgreSQL databases. No live business
company, provider payment, production credential or existing checkout was changed.

## Findings and corrections

- F01 reproduced with a failing HTTP worker regression: missing payment amount
  raised uncaught Pydantic validation after a durable no-effect failure. The shared
  preparation service now translates this to `intake_review_invalid`. Missing and
  explicit zero remain original data; both jobs fail once, no retry is invented,
  a valid sibling prepares, and no document/ledger is accepted.
- F02 not reproduced in controlled fixture and real-backend browser qualifications.
  The existing dialog Refresh loads the newly accepted invoice without reopening.
  Real owner login, external invoice approval, worker/scheduler projections and
  payment confirmation produced open amount `100.0000` → `95.0000` after payment
  `5`. No speculative lifecycle or polling change was introduced. The regression
  is included in the CI live-browser matrix. This does not disprove the original
  single observed sequence under other timings or environments.
- F03 single-source review now presents effect arguments once and exposes explicit
  original source/file downloads; known missing price/amount/item notices name
  one-based line positions. Batch children reuse the presentation. Exact digest,
  source bytes, effect arguments and technical inspection remain available.
  Page actions have explicit localized accessible names matching visible labels.
  Browser role/name queries succeed; the report's Codex-specific tree issue was
  not independently reproduced with that same desktop browser integration.

## Executable qualification

- Backend mandate/authority/MCP/demo selection: 89 passed (73.05s).
- Financial/source/file/bulk/recovery/HTTP-agent selection: 62 passed (14.26s).
  These selections overlap; they are not 151 distinct tests.
- New authenticated MCP HTTP regression: named owner-issued token limited to three
  review tools; complete original bytes read, forged digest refused, exact accepted
  decision attributed to token, replay free, second distinct source refused by
  daily quota of one, and revoked token rejected with HTTP 401. Credential material
  remains in test memory and is revoked in finally; no token is included in evidence.
- Existing service tests additionally cover mandate expiry/revision/revocation,
  issuer authority, role restrictions, commercial limits and competing transactions.
- Real payment refresh browser: passed (80.82s), actual API and projections.
- Fixture browser payment flow: passed, refresh from empty selection, partial payment,
  customer/supplier, response-loss recovery and 16 language/viewport/theme views.
- Fixture browser common/source review: passed; one source summary, original links,
  missing amount notice, collapsed technical data and exact confirmation token.
- Frontend contracts: 463 passed; build and formatting passed.
- Translation audit: all four languages pass (2770/2770 keys each).
- Ruff, spec policy and business annotations pass. Catalog regeneration followed
  by repository formatting produces no catalog change.

## Limits retained honestly

Provider-backed Chat/model judgement was not run: this managed environment has no
configured provider credentials. HTTP MCP transport and deterministic named-agent
verdict validation are tested, not cognitive understanding by a model. The existing
complete-coverage claim binds original byte ranges, not comprehension.

The long-paced full demo order-to-cash browser soak (up to hours), every shipment/
refund/restock profile, all infrastructure crash modes, maximum-volume/provider cost
benchmark and the exact Codex desktop accessibility tree are not newly qualified by
this follow-up. Existing regression evidence is not a substitute for those manual
coverage gaps. External email approval from PR #332 remains its existing separate
contract; no general external human grant or universal writer gate was added.

Real bulk-browser qualification passed (90.18s): original downloads, selection,
response-loss recovery and actual worker receipts. PR CI status is recorded on the
follow-up pull request and is required before this work is called complete.
