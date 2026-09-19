# Tasks
- [x] T001 Add the equivalence property test — incremental against full — before any builder narrows (FR-006).
- [x] T002 Collect the change set from events between checkpoint and target; pass it to the builders (FR-001,002).
- [x] T003 Merge a partial result instead of replacing, and remove rows that disappear for a narrowed subject (FR-003).
- [ ] T004 Select time-based transitions by indexed date (FR-004).
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
  - [ ] the remaining nine.
