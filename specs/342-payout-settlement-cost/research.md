# Research: Payout Settlement Cost

Statements counted with a `before_cursor_execute` listener around `create_change_proposal`
(review) and `approve_and_execute_proposal` (settlement), for payouts of N orders with a refund of
a credit note every 20 orders, a chargeback of a same-statement charge every 50 and a fee every 10.

## Before (main before spec 342, spec 336 as merged)

| N orders | lines | review | per line | settle | per line |
|---:|---:|---:|---:|---:|---:|
| 10 | 13 | 166 | 12.8 | 1,163 | 89.5 |
| 50 | 59 | 626 | 10.6 | 4,917 | 83.3 |
| 200 | 234 | 2,399 | 10.3 | 19,221 | 82.1 |

Top causes per settled line (N = 50):

| Cause | Statements per line |
|---|---:|
| Business and finance locks taken again by every payment, posting, allocation and event | ~12 |
| `_tenant_record` reads of parties, the proposal, source records and documents already held | ~19 |
| Line source records stored one at a time (lock, stream, duplicate, version reads) | ~8 |
| Company currency and account resolution per posting | ~5 |
| Order reference resolution per line (orders, lines, invoices, control entry, reversal) | ~9 |
| Reversal checks of posting groups just created | ~4 |
| Savepoint per payment | 2 |
| `active_settlement_allocations` reading every allocation of the company per allocation | 1 statement, growing rows |

## After

| N orders | lines | review | per line | settle | per line |
|---:|---:|---:|---:|---:|---:|
| 10 | 13 | 34 | 2.6 | 298 | 22.9 |
| 50 | 59 | 54 | 0.9 | 977 | 16.6 |
| 200 | 234 | 133 | 0.6 | 3,637 | 15.5 |

Growth per further line: settle 15.2, review 0.45. At N = 50 the settlement's statements were
445 SELECT, 297 INSERT and 233 UPDATE: about 7.5 reads, 5 inserts and 4 updates per line. The
updates are the finance revision and the event progress each flush writes.

## R04 story (400 orders, 12 refunds, 3 chargebacks, 2 fees)

| | test call time |
|---|---:|
| before | 150 s |
| after | 65 s |

Measured back to back on the same machine (load average about 4.5); most of the remaining time is
the story creating 400 orders and invoices. Statement counts are the pinned measure.
