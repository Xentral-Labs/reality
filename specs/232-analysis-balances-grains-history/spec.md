# Feature Specification: Balance, inventory-grain and effective-date analysis

**Language**: English

## Context and Intent
The owner approved closing analysis limits: net customer/supplier balances, inventory
by location/lot/serial, and historical measures after a retained-history audit.

### Non-Goals
No persisted derivation or schema expansion; no historical reservation/available stock,
historical due/overdue terms, knowledge-time reconstruction or invented pre-opening
coverage. Labels and item units remain current metadata. No new business mutations.

## User Scenarios & Testing
### US1 — Complete current money position (P1)
Given debts, unused payments/credits, refunds and reversals, customer/supplier balance
rows match Finance without its pagination limit. Party, side and currency define grain.
### US2 — Explain current inventory (P1)
Given movements and reservations with locations/lots/serials/handling units, detail
rows sum back to article totals. Missing tracking values form explicit unknown groups.
Transfer source/destination and compensation movements remain true; no wildcard nulls.
### US3 — Effective-date position (P1)
Choose an explicit calendar cutoff (end of day UTC) for physical inventory or numeric
open/credit/net balances. Exclude later movement/posting/allocation/reversal effects.
Opening coverage and unsupported histories produce an explicit refusal rather than
current values disguised as historical results. These are reconstructed effective-time
values from retained evidence, not what Reality knew then.

## Requirements
- **FR-001**: Extract/reuse unpaged canonical party balances for customer/supplier
  position nodes with opaque read-time identity, currencies and credit/net measures.
- **FR-002**: Expose canonical inventory detail at item/location/lot/serial/handling-unit
  grain, retaining null identities and current active-reservation semantics; reuse
  shared movement-leg arithmetic and verify aggregation parity with current inventory.
- **FR-003**: Add optional effective-before cutoffs to canonical numeric settlement
  readers and physical stock derivation. Respect both allocation endpoint timestamps,
  allocation time and reversal time; no use of today's aging terms for history.
- **FR-004**: Historical nodes require one equal snapshot_date filter. It selects the
  entire UTC day, rejects future dates and missing/conflicting inputs. Refuse historical
  finance/stock before imported opening coverage. Unsupported historical measures are
  absent from historical nodes, never substituted by current measures.
- **FR-005**: Shared date-input metadata enables editable cutoff controls and unsaved
  current/history templates. Preserve query/Cypher/chat/save round-tripping and display
  effective-date/current-label limits. No hidden default cutoff or automatic saving.
- **FR-006**: Preserve tenant, Decimal, currency/unit, row grain, fanout, timeout, input
  bounds and truthful read counts across forward/reverse joins and multiple positions.

## Assumptions and Dependencies
Existing movements and financial allocation/reversal events retain effective times.
Reservation status and payment terms have incomplete history. Existing source payloads
remain lossless. State rows are ephemeral, identity hashes only opaque source IDs and
semantic dimensions. Shared services remain authoritative in all adapters.

## Success Criteria
Canonical current parity, >100 balance parties, tracking/null-grain conservation,
cutoff-boundary/correction/reversal tests, historical refusals, editor tests and all
required checks pass; no migration or business write added.

## Requirement Traceability
| Requirement | Story | Tasks | Tests |
|---|---|---|---|
| FR-001 | US1 | T001,T002 | Current balance/register parity, credits, >100 parties |
| FR-002 | US2 | T001,T003 | Tracking/transfer/null buckets, sum parity |
| FR-003 | US3 | T001,T002,T003 | Before/after posting/payment/reversal/movement |
| FR-004 | US3 | T001,T004 | Missing/conflicting/future cutoff, opening boundary |
| FR-005 | US1–3 | T004,T005 | Templates, date control and query roundtrip |
| FR-006 | US1–3 | T001–T005 | Currency/units, tenant, grain/fanout and limits |
