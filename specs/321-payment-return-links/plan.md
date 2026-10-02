# Implementation Plan: Payment Returns Store No Forward Links

**Branch**: `321-payment-return-links` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

Drop `ledger_reversal_id`, `fee_document_id` and `fee_charge_document_id` from `payment_return`. `return_detail` reads the three links back:

- **Reversal**: the reversal whose `original_posting_group_id` is the payment's receivable posting group.
- **Fee documents**: the documents of type `payment_return_fee` and `payment_return_fee_charge` that carry the return's `source_record_id`.

Migration `0110` compares every stored link with that derivation and refuses on any difference. Its downgrade backfills the columns from the same derivation.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The fee documents keep the return's source record; the reversal names the posting group. |
| II. Reality is the operational authority | PASS | No document fields change. |
| III. Proven schema only | PASS | Three columns removed, none added. |
| IV. Tenant and service boundaries | PASS | Every derivation filters by the return's company. |
| V. Specification and test evidence | PASS | Tests changed first. The red runs were "column still there" and "migration did not refuse". |
| VI. Explainable Web product | PASS | The read output is unchanged. |
| VII. Simplicity and storage discipline | PASS | 14 → 11 columns. One copy of each link. |
| VIII. Received values are recorded, never recomputed | PASS | The stated values are untouched. |

## Design

1. `db/core.py`: the `PaymentReturn` model loses the three columns, their foreign keys and `uq_payment_return_reversal`.
2. `services/payment_returns.py`:
   - `_caused()` derives the three links.
   - `return_detail` uses it.
   - `record_return` no longer writes the links. Its event still names the reversal.
3. Migration `0110_payment_return_links`: check, then drop. The downgrade restores the columns, foreign keys, indexes and the unique constraint under their 0103 names.
4. Docs: `config/data_model.yaml` and `docs/SPEC_COVERAGE_MATRIX.md`.

## Rollback

The downgrade restores the three columns from the derivation. Nothing is lost in either direction.

## Complexity Tracking

None.
