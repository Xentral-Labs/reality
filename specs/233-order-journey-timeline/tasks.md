# Tasks: Order journey timeline

## Setup and foundation
- [x] T001 Record accepted scope and domain/time decisions in specs/233-order-journey-timeline/spec.md and research.md (FR-001–011).
- [x] T002 Add service/HTTP regression stories in packages/reality-core/tests/test_order_journey.py before implementation (FR-004–008, FR-011, SC-002).
- [x] T003 Implement typed membership, loaded-record edges, search and shared timeline predicate in packages/reality-core/src/reality/services/order_journey.py and services/core.py (FR-004–008, FR-011).
- [x] T004 Expose thin GET adapters in packages/reality-core/src/reality/web/api.py and apps/web/src/api.ts (FR-004–008, FR-011).

## US1 — Business lanes
Independent proof: eligible events occupy correct lanes, repeated changes survive, collisions retain all members.
- [x] T005 [US1] Write recording-time/collision tests in apps/web/scripts/order-journey-layout.test.mjs (FR-001–003, SC-003).
- [x] T006 [US1] Implement pure viewport layout in apps/web/src/unified/orderJourneyLayout.ts (FR-001–003).
- [x] T007 [US1] Replace active recorder presentation with apps/web/src/unified/OrderJourneyTimeline.tsx using theme tokens (FR-001–003, FR-010, SC-003).

## US2 — Selected order journey
Independent proof: selection reads exact server membership and record/event Inspector actions remain available.
- [x] T008 [US2] Add browser journey tests in apps/web/scripts/order-journey-browser.mjs before integration (FR-004–008, FR-011, SC-001–003).
- [x] T009 [US2] Integrate searchable order selector, true edge labels and chronological details in apps/web/src/unified/OrderJourneyTimeline.tsx (FR-004–008, FR-011).

## US3 — Stable reading and responsive controls
Independent proof: fixed ranges, paging, retry, refresh and tenant/order race guards; 390px/1440px keyboard and containment.
- [x] T010 [US3] Extend apps/web/scripts/order-journey-browser.mjs for errors, paging, ranges and responsive state (FR-003, FR-008–010, SC-004).
- [x] T011 [US3] Implement refresh/paging/state guards and local overflow in apps/web/src/unified/OrderJourneyTimeline.tsx and apps/web/src/tailwind.css (FR-003, FR-008–010).
- [x] T012 [US3] Add four-language presentation in apps/web/src/localization.tsx (FR-010).

## Verification and review
- [x] T013 Update superseded browser/contract checks and durable docs/WEB_SPEC.md; run required suites and record results in specs/233-order-journey-timeline/review.md (FR-001–011, SC-001–004).

## Dependencies and execution
T001 → T002 → T003 → T004; T005 precedes T006–007; T008 precedes T009; T010 precedes T011–012; all precede T013. Tests and design research can proceed independently; implementation is sequential through shared services then adapters. US1 is the first UI increment, US2 adds order context, US3 completes usability. No implementation delegation is required. Tests may run independently once the relevant code is ready.

## Completion evidence

See [review.md](review.md). Required spec233 gates pass: complete backend coverage across disjoint runs (2,886 passed, 7 skipped), 274 frontend tests, build, localization, formatting, lint, spec policy, catalog check and dedicated journey browser acceptance. The legacy Inspector browser fails before Timeline on unchanged HEAD as well; that separate baseline limitation is preserved in review.md rather than represented as green. Human PR review/merge is not claimed.
