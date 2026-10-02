# Implementation Plan: Fee Open Receivables

**Branch**: `codex/journey-consistency` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

Prepare the existing fee charges for canonical OP reads and confirmed settlement. This is a reviewable technical outline, not an implementation-ready plan: FR-004 needs an owner decision.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL, Decimal, pytest; existing finance services and tool confirmation. Reuse the existing fee documents and control entries. No migration is currently justified.

## Constitution Check

- Source/evidence/reality, operational authority, tenant boundaries, storage and received-value principles: PASS for the proposed reuse of existing records.
- Specification/test gate: BLOCKED until FR-004 is clarified; no fee implementation authorized by this outline alone.
- No exception to the Constitution is proposed.

## Project Structure and Ordered Work

1. Resolve the policy in `spec.md`; complete the Constitution Check, test plan, tasks and analysis.
2. Add failing `tests/finance/test_fee_open_receivables.py` stories and adapter proofs before changes. Pin original ledger/source identities, currency, tenant and reversal behavior.
3. Define the shared fee claim vocabulary beside settlement control types in `domain/finance.py`; extend `services/core.py:financial_open_items` and `with_invoice_aging` according to the reviewed policy.
4. Extend `services/finance/settlement_flows.py` through existing confirmed payment/credit allocation services. Audit `finance/settlement.py` separately: noncash reductions must not be enabled accidentally by allowing payment allocation.
5. Extend `services/credit_exposure.py` and canonical balance/read consumers. Audit the open-items projection and `web/read_models.py` so filtering, counts and sums include the same claims.
6. Keep `dunning_runs.py:DUNNABLE_TYPES` unchanged under the proposed no-redunning option. Review manual dunning in `dunning.py` and `finance/worklists.py` too; automatic-run exclusion alone is insufficient.
7. Update command/projection descriptions, German resource labels where applicable and generated references. Replace the resolved limitations in specs 295/297 with a link to this contract.
8. Run full finance, story, adapter, backend, Web and documentation gates; review and only then mark complete.

## Risks and Rollback

- Reversal must disable effective allocation without deleting history.
- Exposing historical fees changes balances immediately; explain the release behavior and rebuild finance projections with a version change if necessary.
- Dunning and discount policy must be reviewed across manual and run paths.
- Revert code, vocabulary and generated references together; never reverse or rebook historical fees merely to roll back a reader.
