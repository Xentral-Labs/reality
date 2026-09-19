# Tasks
- [x] T001 Add the equivalence property test — incremental against full — before any builder narrows (FR-006).
- [x] T002 Collect the change set from events between checkpoint and target; pass it to the builders (FR-001,002).
- [x] T003 Merge a partial result instead of replacing, and remove rows that disappear for a narrowed subject (FR-003).
- [ ] T004 Select time-based transitions by indexed date (FR-004).
- [x] T005 Keep full evaluation for version changes, operator rebuilds and decliners (FR-005).
- [ ] T006 Narrow the first builders, one at a time, each behind the equivalence test (FR-002).
  - [x] `journal` — posting groups and subledger accounts; follows the stored reversal
    relation to the reversing group no event names; declines a `tenant` subject.
  - [ ] the remaining eleven.
