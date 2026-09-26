# Quickstart: Fulfillment Safety Parity

## Prerequisites

- PostgreSQL test database configured by the repository test harness.
- Python and Web dependencies installed.
- No production or retained qualification tenant is required; tests create isolated tenants.

## Focused proof

```bash
.venv/bin/pytest -q \
  packages/reality-core/tests/test_payment_terms.py \
  packages/reality-core/tests/test_fulfillment_readiness.py \
  packages/reality-core/tests/test_shipment_actions.py \
  packages/reality-core/tests/test_application_tools.py \
  packages/reality-core/tests/test_ai_mcp.py \
  packages/reality-core/tests/test_master_data_api.py \
  packages/reality-core/tests/scenarios/test_fulfillment_safety_parity.py
```

Expected evidence:

1. An unpaid prepayment order with stock and reservation is blocked with required, received and
   remaining amounts.
2. Web/application and MCP expose equivalent blocker codes and values.
3. A pre-payment dispatch proposal is absent and no shipment/package/movement exists.
4. Full allocation changes readiness and review state; dispatch then executes.
5. Final inventory is `30 - 10 - 10 = 10`, reservations are zero and both invoices are open zero.
6. Deterministic refusals are terminal failed; the unknown-outcome control remains executing.

## Contract and documentation proof

```bash
make docs-generate
make docs-catalog-check
make spec-check
cd apps/web && npm run i18n:audit && npm run build
```

Inspect the generated shipment entries and confirm both proposal tools expose the complete
purpose-discriminated schemas described in [contracts/shipment-tools.md](contracts/shipment-tools.md).

## Full repository gates

```bash
make lint
make test
make web-build
```

No task or acceptance criterion is complete while a required gate is red.

## Verification evidence — 2026-09-26

- `283 passed, 2 skipped` in the final serial impact suite covering payment terms,
  readiness, shipment review/execution, proposal lifecycle, MCP HTTP serialization,
  capability discovery, incremental projections, query-count bounds and the business story.
- `6 passed` in the final adversarial payment-evidence rerun covering foreign party/currency,
  reversal and ambiguous cross-order attribution.
- `78 passed` in the focused incremental-projection and operational-read performance rerun.
- `1 passed` for the isolated migration upgrade/default/downgrade proof.
- `make lint`, `make spec-check` and `git diff --check` passed.
- `make web-build` passed all 394 frontend tests, formatting, the four-language i18n audit,
  TypeScript compilation and the production Vite build.
- `make docs-generate` and the post-commit `make docs-catalog-check` passed.
- Pull-request CI completed the authoritative 4,415-test PostgreSQL backend suite in two
  shards; both shards and the aggregate `backend-quality` gate passed.
- Pull-request CI also passed `docs-quality`, `frontend-quality`, `end-to-end`, `script`,
  `spec-policy`, and `backend-changes` for commit `9d70e57e`.
- No known implementation or verification limitation remains for the Spec 275 scope.

## Post-merge regression proof

The HTTP MCP runtime must reject undeclared top-level and nested shipment arguments before
dispatch. This preserves FR-017 even when an MCP SDK binds arguments permissively.

```bash
.venv/bin/pytest -q \
  packages/reality-core/tests/test_mcp_http_runtime.py::test_http_runtime_rejects_unknown_shipment_fields_before_dispatch
```

The live proof rebuilds the MCP container, opens an authenticated MCP HTTP session, submits an
undeclared shipment field and confirms that the schema error names that field before any party,
item or fulfillment lookup. Its temporary access token is revoked immediately after the check.
