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
