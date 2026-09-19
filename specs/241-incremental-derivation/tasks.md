# Tasks
- [x] T001 Add the equivalence property test — incremental against full — before any builder narrows (FR-006).
- [x] T002 Collect the change set from events between checkpoint and target; pass it to the builders (FR-001,002).
- [x] T003 Merge a partial result instead of replacing, and remove rows that disappear for a narrowed subject (FR-003).
- [x] T004 Select time-based transitions by indexed date (FR-004).
  - [x] Measure which projections read the clock at all. Two of the three on the
    cadence did not, and no longer rebuild every minute; `test_clock_sensitivity.py`
    keeps the list a measurement rather than a recollection.
  - [ ] `exceptions` still evaluates the company on the cadence. Half its classes
    compare against a stated date and could be selected by index; the other half
    compare against a threshold learned from finished promises, which moves for every
    record at once and has no per-record date to select by. Its own feature.
- [x] T005 Keep full evaluation for version changes, operator rebuilds and decliners (FR-005).
- [ ] T006 Narrow the first builders, one at a time, each behind the equivalence test (FR-002).
  - [x] `journal` — posting groups and subledger accounts; follows the stored reversal
    relation to the reversing group no event names; declines a `tenant` subject.
  - [x] `document_register` — documents, commitments, source records, parties and
    payment terms resolve to documents; a party reaching more than
    `MAX_NARROWED_ROWS` of them declines.
  - [x] `inventory` — movements, reservations, promises and observations about them
    resolve to articles; follows the stored movement correction to the compensating
    and replacement movements no event names; declines a location, a master-data
    change and the tenant.
  - [x] `item_supply_demand` — the same articles stock resolves, plus a party: a
    delivery hold names only the party it was placed on, and the open promises say
    which articles stop moving. The blocking rules and the row shape are now written
    once and used by both the whole-company path and the narrowed one.
  - [x] `fulfillment_queue` and `fulfillment_blockers` — one derivation, so one step:
    promises, documents, source records, parties, articles, movements and reservations
    resolve to orders; the movement correction is followed because a replacement may be
    booked against a *different* promise and settle two orders the event does not name.
    Each speaks for what it resolved rather than what it produced — an order that
    finished and a blocker that cleared both leave no row to find.
  - [x] `commitment_register` — promises, documents, articles, parties, movements and
    reservations resolve to promises, and the movement correction is followed for the
    same reason. It is a register, not a queue: it keeps the promise that was cancelled,
    so nothing here is bounded by open work and a wide subject declines instead.
  - [x] `timeline` — the five records it prints resolve directly, an article resolves to
    the promises, reservations and movements that print its name, and both hidden
    producers are followed: the movement correction and the ledger reversal, whose
    records would otherwise be missing lines of history rather than stale ones. Subjects
    no row prints are declared rather than declined, so a window of documents and parties
    produces nothing and speaks for nothing.
  - [x] `open_financial_items` — a posting group, a settlement allocation, a party and a
    payment term all resolve to the documents whose open amount they move; a payment run
    names the tenant and is declined. What it speaks for is the documents it resolved,
    because a document with no control posting is not an open item and its row must go.
  - [x] `payments` — a posting group holds the cash entry, a party and a document are
    printed on the row, and a settlement allocation names the control entry beside the
    cash one, so it resolves through that entry's group. Allocations are carried in both
    directions: reversing an invoice's group changes what the payment has allocated. A
    payment run names the tenant and is declined.
  - [ ] the remaining two: `tenant_usage`, which answers about the company rather than
    about a record, and `exceptions`, which loads the company by construction.
