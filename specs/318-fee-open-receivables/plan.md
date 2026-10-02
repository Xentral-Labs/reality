# Implementation Plan: Fee Open Receivables

**Branch**: `codex/journey-consistency` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

Expose existing fee charges through canonical OP reads and confirmed payment settlement. The owner approved separate payable charges without renewed dunning or inherited maturity/discounts.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL, Decimal, pytest; existing finance services and tool confirmation. Reuse the existing fee documents and control entries. No migration is currently justified.

## Constitution Check

- Source/evidence/reality, operational authority, tenant boundaries, storage and received-value principles: PASS for the proposed reuse of existing records.
- Specification/test gate: PASS; owner policy is resolved, tests are planned before implementation, and tasks require cross-artifact analysis.
- No exception to the Constitution is proposed.

## Project Structure and Ordered Work

1. Record the approved policy in `spec.md`; complete test planning, tasks and analysis.
2. Add failing `tests/finance/test_fee_open_receivables.py` stories and adapter proofs before changes. Pin original ledger/source identities, currency, tenant and reversal behavior.
3. Define the shared fee claim vocabulary beside settlement control types in `domain/finance.py`; extend `services/core.py:financial_open_items` and `with_invoice_aging` according to the reviewed policy.
4. Extend `services/finance/settlement_flows.py` through existing confirmed payment/credit allocation services. Audit `finance/settlement.py` separately: noncash reductions must not be enabled accidentally by allowing payment allocation.
5. Extend `services/credit_exposure.py` and canonical balance/read consumers. Audit the open-items projection and `web/read_models.py` so filtering, counts and sums include the same claims.
6. Keep `dunning_runs.py:DUNNABLE_TYPES` and manual dunning eligibility unchanged. Ensure `finance/worklists.py` excludes fee charges from dunning worklists even when a maturity was explicitly stated.
7. Update command/projection descriptions, German resource labels where applicable and generated references. Replace the resolved limitations in specs 295/297 with a link to this contract.
8. Run full finance, story, adapter, backend, Web and documentation gates; review and only then mark complete.

Web adapter changes: `unified/FinancePage.tsx` exposes existing payment actions for both fee types; `finance/SettlementFlow.tsx` respects the service's `reduction_allowed` flag. Plan regressions in `scripts/fee-open-receivables-contract.test.mjs` first and browser checks in `scripts/fee-open-receivables-browser.mjs`. Backend mutation eligibility remains authoritative.

## Risks and Rollback

- Reversal must disable effective allocation without deleting history.
- Exposing historical fees changes balances immediately; explain the release behavior and rebuild finance projections with a version change if necessary.
- Dunning and discount policy must be reviewed across manual and run paths.
- Revert code, vocabulary and generated references together; never reverse or rebook historical fees merely to roll back a reader.
