# Verification: Web and MCP Proposal Review Parity

Verified on 2026-09-22 against the local PostgreSQL and Docker development stack.

- MCP/Web registry contract: 102 proposal-producing definitions, all classified; 5 focused
  service/API tests passed for redaction, tenant isolation, malformed input, rejection,
  execution receipt and list/detail routing parity.
- Related backend regressions: 35 passed across unified Web API, MCP HTTP, supply assignment,
  returns and proposal review.
- Web: 334 contract tests passed; four-language audit passed at 2122/2122 keys per language;
  TypeScript and Vite production build passed.
- Browser: `proposal-review-browser.mjs` passed in Chromium against port 8080 for lot,
  payment term, price list and cost proposals, including confirmation, receipt and reload.
  Existing specialized reviews remain delegated through `ActionCard` and their own suites.
- Visible Chrome checks against the live company opened `payment_term_create`, `lot_create`
  and `movement_create` from Chat/Decisions. Each restored the exact stored proposal in a
  centered modal with origin, input, preview and explicit Reject/Confirm controls. No live
  proposal was confirmed during visual inspection.
- `ruff`, Prettier, `make spec-check`, `git diff --check`, i18n and Web build passed.

The existing `unified-shipments-browser.mjs` currently stops before proposal review at its
stale “Physical contents” assertion; this feature neither changes that shipment-page label
nor downgrades the specialized shipment review. Shipment service regressions and the shared
specialized-review routing contract remain green.
