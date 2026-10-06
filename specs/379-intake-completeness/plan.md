# Implementation Plan: Essential intake completeness

**Branch**: `codex/intake-completeness` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary

Implement the owner-approved essential-value rules with a small pure policy module and existing service validation/review paths. Keep raw intake open and accepted effects exact. Add negative proofs before implementation.

## Technical Context

Python 3.12, SQLAlchemy 2, PostgreSQL, Pydantic v2, Decimal and UTC. Existing nullable price/date fields and prepared-review issue strings suffice. No new schema, MCP argument, queue or transport. Existing web review renders retained issues; no browser business rules are needed. Shared review presentation renders server issues and unknown prices, with existing four-language browser acceptance.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Preserve raw payload/artifact; approved services write evidence and promises | PASS |
| Reality owns operational state | Completeness is a review observation; no Document status | PASS |
| Proven schema only | Existing nullable price/date and review issues; no migration | PASS |
| Tenant + shared service boundaries | Existing scoped reference resolution and canonical writers | PASS |
| Spec/test traceability | Every FR/DR has test tasks before implementation | PASS |
| Explainable web behavior | Existing review/Inspector/source links; retained coded refusal | PASS |
| Received values not recomputed | Omitted prices stay None; amounts are never multiplied; simulator authors its fixture quotation | PASS |
| Smallest coherent design | One pure policy and focused service integration instead of a new validation framework | PASS |

Pre- and post-design checks pass. No exception or unresolved product decision is required; owner request approves the preceding analysis and its bounded implementation.

## Repository Structure and Layer Changes

- `packages/reality-core/src/reality/domain/intake_completeness.py`: pure required-value, currency, order-gap and stock-unit rules.
- `services/core.py`: translate pure validation to localized errors, preserve omitted price, observe order gaps in previews and enforce sales-unit meaning.
- `services/shopify_intake.py`, `services/artifact_intake.py`, `services/intake.py`: require source currency and bank date/direction; append shared order gaps; carry file dates; retain profile unit inheritance and unknown-item evidence.
- `services/file_interpreters.py`: expose existing date/unit/amount mapping fields and required bank mapping fields.
- `services/live_company.py`: author one timestamp, company-local document day and explicit synthetic unit price before normal order recording.
- `config/service_refusals.json`: English/German field-specific errors.
- `tests/test_intake_completeness.py`, existing intake/simulator/adapter suites: negative, positive, raw-retention, date, price, unit and replay evidence.
- `apps/web/src/unified/CompletenessIssues.tsx`, `OrderCard.tsx`, `IntakeBatchReview.tsx`, `api.ts`, localization and existing order-entry browser proof: presentation of server observations and nullable prices.
- `docs/features/intake-completeness.md`, source intake/simulator contracts and generated documentation: shared rule matrix.

## Design

### Reality flow

Capture immutable Sources independently of validation. Pure profiles prepare exact received values and completeness observations. Essential-value failures retain a preparation failure. Existing exact decisions atomically accept only the offered evidence and its shortest-linked commitments/postings.

### Service and adapter flow

One pure missing-value predicate handles omitted, None, empty and whitespace while preserving numeric zero. Domain rules raise a structured missing/unsupported value; services translate it to the existing refusal catalog. Order gaps are appended to PreparedIntake.issues and manual-order previews. Existing HTTP/MCP/CLI readers expose these without new rules. Mandatory source currency has no silent EUR fallback. Existing direct human currency defaults stay visible and supported.

File order dates preserve explicit document_date; otherwise `_source_document_day` converts ordered_at using the company timezone. Conflicting nonblank header dates within one order refuse. Different explicit sales quantity units refuse; purchase quantity conversion remains unchanged. Known-item inheritance is documented profile meaning and never the generic pieces fallback for physical promises.

Simulator release uses a single instant and an explicitly authored fixture price EUR 10/piece. Its document date uses the company's timezone. No source correction or historical backfill occurs.

### Data and migration impact

None. Unknown prices use existing nullable columns. Historical reviews retain their frozen values/digests; tightening applies to newly prepared meaning and new manual evidence. No migrations, source mutations or authority tables.

### Failure, security, and tenant behavior

Coded refusals name the field. Existing preparation savepoints preserve raw and prevent accepted effects. Current references, finance revision, review digest and permissions are rechecked on confirmation. Cross-company reads/writes, replay and independent bulk acceptance remain existing contracts.

## Test Strategy and Traceability

| Requirements | Test level and planned evidence | Expected initial failure |
|---|---|---|
| FR-001/002/008, DR-001/003 | `tests/test_intake_completeness.py`: source currency and bank field matrix, raw and no effects; intake/financial/bulk regression | Defaults currently accepted |
| FR-003/004 | Same: omitted/blank versus zero price and missing-order review fields across manual/file/shop | Omission becomes zero; date issues absent |
| FR-005 | Same: explicit/local-day/date conflict; HTTP register date | File date omitted |
| FR-006, DR-001 | `tests/scenarios/test_live_company.py`: actual source/evidence/register/replay at local midnight | Simulator date/price omitted |
| FR-007 | Completeness unit tests and service orders; existing purchase/unknown-item suites | Unsupported units accepted |
| FR-009, DR-002 | Durable rule matrix, full backend/frontend/docs/spec gates, final PR review | New contract not yet present |

## Rollout and Rollback

No migration. Newly prepared bank files require stated direction/date/currency; incomplete files stay retained for correction/reimport. Existing reviews remain exact. Rollback restores former admission behavior but cannot rewrite accepted evidence. Deploy shared adapters/core together. Existing undated simulator orders are unchanged.

## Review Risks

- Do not make optional price/total/deadline a universal order rejection.
- Preserve explicit zero and inconsistent received amounts.
- Update legitimate test/examples to state currency/direction rather than weakening negative tests.
- Do not accidentally treat historical source arrival as a booking date.

## Complexity Tracking

No Constitution exceptions. The custom requirements checklist remains reviewer-owned; the owner's explicit implementation/green-PR request authorizes proceeding. Its unchecked markers are not implementation or CI completion claims.
