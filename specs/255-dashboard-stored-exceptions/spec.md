# Feature Specification: Welcome exception count from the stored register

**Feature Branch**: `255-dashboard-stored-exceptions`
**Language**: English
**Created**: 2026-09-23
**Status**: Approved
**Input**: Owner request: the Exceptions count on Inbox Welcome must agree with the Exceptions register it links to, and Welcome should load faster.

## Context and Intent
### Problem
Inbox Welcome (spec 225 FR-018) shows an open Exceptions count taken from the tenant dashboard read, which derives every exception class live. The Exceptions register it links to reads the stored `exceptions` projection (spec 180). The two numbers therefore disagree whenever the stored generation lags current records (measured 2026-09-23: Welcome 1,458, register 1,469 on the same company), and the dashboard pays about 1.1–1.5 s for a live derivation while the stored read takes about 60–75 ms. Spec 180 explicitly left the Home counts out of its scope.
### Scope
The dashboard read reports the exception total and its bounded sample of exception rows from the same stored generation the register reads, through the existing `attention_register` service. Welcome shows an unknown count, not zero, while that generation has never completed.
### Non-Goals
No change to any exception derivation, the catalog, the background refresh, the register, the Exception rules tab or the explanation of a finding. No change to the other dashboard totals or the `/exceptions` endpoint. No new stored authority, service, tool, schema or migration.

## User Scenarios & Testing
### User Story 1 — Welcome and the register tell the same number (P1)
A clerk opens Inbox Welcome, reads the open Exceptions count and follows the link to the register.
Acceptance: for the same stored generation, Welcome's count equals the register's total and the dashboard's sample rows are the register's first rows. The dashboard read derives no exception class. For a company whose generation has never completed, the dashboard reports the exception total as unknown and Welcome shows a placeholder instead of zero, as the register reports "awaiting first calculation". A generation that is pending or whose latest refresh failed keeps its prior total, as the register does.

## Requirements
- **FR-001**: The dashboard's `totals.exceptions`, `sample_scope.exceptions` and `exceptions` sample MUST come from the stored `exceptions` projection through the same service read as the Exceptions register, so the total equals the register's unfiltered total for the same generation.
- **FR-002**: While the projection has no completed generation, `totals.exceptions` and `sample_scope.exceptions.total` MUST be null, and `sample_scope.exceptions` MUST carry the projection state; Welcome MUST render a null count as unknown rather than zero.
- **FR-003**: The dashboard read MUST NOT derive exception classes or rebuild projections; staleness follows spec 180 (the stored generation, refreshed in the background).

## Assumptions and Dependencies
Spec 180's decisions apply unchanged: a stored generation may trail current records by about the refresh cadence, and a finding that cleared meanwhile is reported when it is explained. The Welcome web client reads only `totals` from the dashboard; the `exceptions` sample rows keep their fields and gain the register's `context` and `target` keys. No clarification remains.

## Success Criteria
Welcome's Exceptions count and the register total agree on the same tenant state. The dashboard read on the measured company drops from about 1.1–1.5 s by the live derivation cost.

## Requirement Traceability
FR-001–003 → US1 → T002–T004. Verified by a service/API regression test in `packages/reality-core/tests/test_attention_reads.py` that forbids derivation, plus the web contract tests and before/after timing on a local company.
