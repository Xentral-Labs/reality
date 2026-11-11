# Implementation Plan (draft): A Caller Key Makes a Payment or Invoice Proposal Safe to Retry

**Branch**: `387-proposal-idempotency-key` | **Spec**: [spec.md](spec.md)
**Status**: Draft, to be finished after the owner decides D-1 to D-3. No implementation yet.

## Summary

The proposed shape, assuming the spec's proposals for D-1 to D-3:

1. **Migration 0148** adds a nullable `action.request_fingerprint` and a unique partial index
   on (tenant_id, type, request_fingerprint) where it is not null. Existing rows stay null. The
   downgrade is refused once a fingerprint is stored, following the repository's migration
   convention.
2. **Service** `create_change_proposal` takes an optional key, for an allowlist of the two
   tools only:
   - It computes `sha256(tenant_id, tool, trimmed key)` and a digest of the caller's
     normalized arguments, kept in the proposal's existing input JSON.
   - It inserts the proposal. On a unique violation it reads the existing proposal and
     returns it when the digests match; otherwise it refuses with
     `proposal_idempotency_key_reused`.
3. **Tool and adapter.** The MCP input schemas of both tools gain `idempotency_key`
   (`OPTIONAL_STRING`). `_propose` passes the key to the service and leaves it out of the
   business arguments.
4. **Catalog.**
   - The two refusals go into `service_refusals.json`, with de/nl/es wording in
     `apps/web/src/localization.tsx`.
   - The capability guidance idempotency text is updated.
   - `DATA_MODEL.md` gains a paragraph on the column.
   - `make docs-generate` is run.

## Constitution Check (draft)

| Principle | Status |
|---|---|
| I Source → Evidence → Reality | PASS: no evidence or Reality record changes; the key only identifies a proposal. |
| II Reality is the authority | PASS: no document status. |
| III Proven schema only | NEEDS APPROVAL: one nullable column and index; justification in spec D-2. |
| IV Tenant and service boundaries | PASS: fingerprint includes tenant; one shared service for every adapter. |
| V Specification and tests first | PASS once tasks list the tests in the spec's traceability table. |
| VII Simplicity | PASS: reuses the existing fingerprint scheme; no new table. |
| VIII Received values | PASS: arguments compared as stated, never recomputed. |

## Tests (planned, written first)

- `tests/test_proposal_idempotency.py`:
  - same key and arguments return one proposal;
  - a changed amount is refused with its code;
  - a blank key is refused;
  - no key behaves as today;
  - the key is scoped per company and per tool;
  - two concurrent calls create one proposal.
- Migration test: the index exists, and the downgrade is refused when populated.
- MCP schema test for both tools; capability guidance test; refusal gate and web localization test.

## Rollback

Revert the code. The column stays nullable and unused until the migration is downgraded,
which is allowed only while no fingerprint is stored.
