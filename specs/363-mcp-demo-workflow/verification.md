# Verification and Review

## Test-first evidence

Before production edits, seven backend regressions failed for missing company/review/line tools, unbounded pending output and operational routing; the two UI regressions failed for lost signup language and the reserved-before-confirmation label. Existing product-query controls passed.

## Local checks

- Browser-free review/decision/receipt/replay and stale reservation proofs pass through canonical MCP dispatch with no browser.
- Scoped cursor, safe review, stored company identity and document-line navigation regressions pass.
- Existing focused suite: 195 passed, two retired-UI skips; the expected isolation-operation count needed updating for the two new reads. The corrected catalog subset passed (47 tests).
- Web contracts: 465 passed; TypeScript/Vite build passed; all four translation audits passed.
- Documentation Python contracts: 16 passed; generated tool references regenerated with the configured formatter.
- Ruff passed from the shared-core project directory. Spec coverage and whitespace gates are required before commit.

Full backend and browser execution is gated by GitHub's isolated PostgreSQL and Playwright CI jobs. T012/T013 remain open until the implementation head is green and its final review is recorded.

## Review boundaries

No migration, direct adapter ORM write, new scheduling infrastructure or broadened credential was added. Public pending reads default to bounded metadata pages; application callers preserve the existing legacy list contract. Exact details reuse the shared safe review. Only the retained delivery-review fingerprint is exported separately; credentials/private carriers remain redacted. Interactive author identity is server-owned; manual tokens have no user principal.

MCP confirmation still owns explicit approval, membership/credential authority, stale review refusal, execution and replay. Follow-up names are derived from the executable catalog and limited to registered reads; unavailable bases are explicit. Shipment Movements remain independent of consignment objects.

Full invoice allocation explanation, optional human review URL and external-agent schedule/isolation qualification remain deferred. The running local installation and original checkout were not replaced. No merge or deployment is requested.

## CI-discovered correction

The first implementation CI caught a real login regression: `languageHref` requires an absolute URL, but the new signup call supplied a relative path. Build/source checks did not detect the render exception. Resolve signup against `location.origin` before applying language. The login-to-signup browser proof exercises the actual constructor and navigation. Replace redundant source-pattern UI tests with rendered reservation-label/current-state assertions in the existing delivery browser journey. Re-run all required gates on the corrected head.

The corrected full company-setup browser journey passed locally against an isolated live stack (80.68 seconds). The actual login-to-signup locale fixture and delivery case/launcher/Chat browser matrix passed, including rendered proposed-effect wording with unchanged current stock before confirmation. The published EN and DE mission text is tested directly; product advice mentioning an operational agent remains advice.

Final MCP review also names the existing confirmation tool as its decision handoff, rather than exporting the Web-only review destination. Existing grants do not automatically gain the new reads; both connection guides name the deliberate read allowlist and keep propose/confirm permissions separate.

## Full-suite findings

Run 37219326781 completed the four PostgreSQL shards: three passed; the remaining shard had 1,536 passes and one refusal-ratchet failure for the new document-scope validation sentence. Register `discovery_document_scope_unsupported` and translate it in DE/NL/ES; do not weaken the gate or extend the uncoded-refusal ratchet. A direct wrong-family regression asserts the stable code.

The fixture catalog search also found two valid tools after the shipping description began citing `order_explain`. The test must select the canonical `mcp:order_explain` entry instead of assuming every full-text query returns one row. The complete catalog browser proof passed locally with that precise selection, including languages, mobile layout and no writes.
