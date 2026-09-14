# Quickstart: Controlled Fact Observation

## Acceptance path

1. Create a tenant, a SourceRecord containing a Shopify order payload, and a Commitment using existing services.
2. Call `fact_observe_propose` with `order.shipping_priority=express` and stable opaque source/subject IDs.
3. Verify the proposal preview and that the Facts register is unchanged.
4. Confirm through `proposal_approve_and_execute`.
5. Read the Facts register and Inspector; verify one Fact, one `fact.observed` event, and the original source payload.
6. Repeat confirmation/request with the same idempotency identity and verify no duplicate.

## Required checks

```bash
make spec-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

PostgreSQL migration tests must prove upgrade and downgrade of the Fact retry-identity column and unique constraint. The focused service and MCP tests must also be run independently during development.

## Expected boundary

Reservation, Movement, Commitment, and Ledger commands continue to create typed Reality and Business Events only. They do not create Facts. Unknown source payload fields remain only in the lossless SourceRecord until a reviewed observation or typed use case exists.

## Verification record — 2026-09-03

- Spec policy: PASS.
- Ruff: PASS.
- Focused Fact, MCP, catalog, HTTP-boundary, and Inspector suite: 53 passed.
- Complete backend suite after merging current `main`: 346 passed, 7 skipped.
- Product Web contracts, localization audit, and production build: PASS; 48 contract tests and 796/796 strings per supported language.
- Public Docs Fact guidance contracts and production build: PASS; 12 Docs contract tests.
- Migration upgrade/downgrade: PASS for `0032_fact_observation_identity`.
- Diff whitespace check: PASS.
