# Quickstart: Verify Governed ERP Logic Ownership

Run from the repository root with the normal PostgreSQL test environment available.

## 1. Specification and catalog governance

```bash
make spec-check
cd packages/reality-core
pytest -q tests/test_erp_governance.py tests/test_application_catalog.py tests/test_capability_guidance.py tests/test_action_discovery.py
```

Expected: every governed command/read has one complete trace; planted missing, duplicate, stale and
excluded cases fail with capability and owner/boundary named.

## 2. Critical calculation parity

```bash
cd packages/reality-core
pytest -q tests/scenarios/test_erp_calculation_parity.py tests/scenarios/test_fulfillment_safety_parity.py tests/finance/test_party_balances.py
```

Expected: inventory, fulfilment, finance and contribution consumers agree on value, evidence cutoff
and known/unknown/stale/refused state. Any pre-existing disagreement is recorded in `review.md` and
keeps that slice incomplete.

## 3. Registry and adapter compatibility

```bash
cd packages/reality-core
pytest -q tests/test_tool_catalog.py tests/test_agent_command_parity.py tests/test_proposal_review_parity.py tests/test_mcp_permission_parity.py tests/test_demo_entrypoint_parity.py tests/tenant_isolation
```

Expected: ordered metadata/bindings are unchanged, duplicate fragments refuse, and tenant,
authorization and confirmation behavior remains intact.

## 4. Generated external reference

```bash
make docs-generate
make docs-catalog-check
```

Expected: governance docs and JSON come from the validated trace with no parallel inventory.

## 5. Full completion gate

Run repository lint/format, the complete PostgreSQL backend suite and applicable Web catalog/build
checks named by tasks. Review `review.md`: all capabilities covered; exceptions narrow and used;
critical consumers passing; no unresolved discrepancy, public-contract change, migration or red
required check.
