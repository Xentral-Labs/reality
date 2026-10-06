# Shipping and control requirements-quality checklist

**Purpose**: Reviewer-owned review of the proposed shipping-input, forecast and responsibility requirements before implementation.
**Created**: 2026-10-06
**Language**: English
**Feature**: [spec 378](../spec.md)
**Depth/Audience**: Formal product/domain review; focus on shipping semantics and exceptional responsibility control.

All items are deliberately unchecked. Reviewer completion means the requirements are sufficiently clear, not that implementation passes. This generated checklist does not confer schema or forecast-policy approval.

## Completeness and clarity

- [ ] CHK001 Are dispatch deadlines explicitly distinguished from generic delivery dates and booked arrival slots? [Clarity, Spec FR-003, shipping contract]
- [ ] CHK002 Is site-cohort order completion distinguished from whole-order completion, with split-site deduplication specified? [Clarity, Spec FR-004/008]
- [ ] CHK003 Are physical contents, attributed handover, event-time conflicts and supersession rules defined without counting labels or event rows? [Completeness, Spec FR-004/005]
- [ ] CHK004 Are timed Soll and daily-only missing-plan states defined without invented hourly targets? [Coverage, Spec FR-006]
- [ ] CHK005 Is the exact capacity unit/work-mix meaning stated, with packages/hours explicitly excluded from implicit conversion? [Clarity, Spec FR-007, Data model §3]
- [ ] CHK006 Are completion-slot-v1 assumptions, budget consumption, partial-window pace and multi-site aggregation precisely reviewable? [Measurability, shipping contract]
- [ ] CHK007 Are confirmed versus requested/revoked/unresolved confirmation inputs separately specified? [Coverage, Spec FR-007, Data model §3]
- [ ] CHK008 Is the one-current-requirement-per-commitment admission boundary explicit, including quantity revision and unsupported individual-commitment splits? [Coverage, Data model §2]

## Domain consistency

- [ ] CHK009 Is each proposed typed field justified by repeated core calculation/selection/relationship use? [Consistency, Spec DR-002, Data model §Schema proof]
- [ ] CHK010 Are source versioning, current-review binding, replay and withdrawal semantics defined without mutating past payloads? [Completeness, Data model §Governance]
- [ ] CHK011 Do shortest commitment/source/site links avoid duplicated document identities and guessed hierarchy? [Consistency, Spec DR-001, Data model]
- [ ] CHK012 Are active-member cockpit access, default coordination readiness and existing mandate boundaries consistent across read/control/producer contracts? [Consistency, Spec FR-017/DR-003/004]
- [ ] CHK013 Are owned scope, already-started execution and exact handback rules explicit without promising external cancellation? [Coverage, Spec FR-013/014, interfaces contract]
- [ ] CHK014 Is human-owned register attribution derived from the authoritative control revision with absent-history behavior? [Completeness, Spec FR-015, interfaces contract]

## Observation, failure and acceptance quality

- [ ] CHK015 Are full-result totals, paged lists, changed-basis notices and company reset requirements consistent? [Coverage, Spec FR-010/018, interfaces contract]
- [ ] CHK016 Are unknown versus known-zero/stale states and incomplete global forecast coverage defined for every required input? [Coverage, Spec FR-018, shipping contract]
- [ ] CHK017 Is the independent two-site oracle sufficient to assess quantity/plan/forecast semantics without using the production evaluator? [Measurability, Spec SC-001, shipping contract]
- [ ] CHK018 Are workload population, cold/warm method, ten observers and acceptance timing sufficiently bounded for meaningful measurement? [Measurability, Spec SC-004, quickstart]
- [ ] CHK019 Are preserved shipping hierarchy, cut-offs/site table, contextual chat, mobile/desktop and language/theme requirements objectively assessable? [Measurability, Spec SC-002/FR-019/020]
- [ ] CHK020 Are product approval, proposed schema/model review, later-stage functionality and implementation completion clearly separate? [Consistency, plan authorization gate, migration map]

## All-day live observation quality

- [ ] CHK021 Are automatic update cadence, healthy display latency, rolling activity classification and recorded-versus-business-time meaning explicit? [Clarity, Spec FR-021, live contract]
- [ ] CHK022 Are stable history/scroll/chat/reviews, presentation-only following and changed-review guards distinguished from stopping or handing back a case? [Consistency, Spec FR-022, live contract]
- [ ] CHK023 Are quiet/stale coverage, bounded buffers/requests, hidden-tab recovery, company isolation and Today versus pinned-day rollover objectively assessable? [Coverage, Spec FR-023, live contract]
- [ ] CHK024 Are deterministic eight-hour proof, ten-observer sustained-refresh measurement and the separate real-time eight-hour soak clearly separated from implemented/passing evidence? [Measurability, Spec SC-007, quickstart]

- [ ] CHK025 Are named access/client identity, full paging, owner disclosure, exact observed-action attribution and unknown external runtime states explicit without equating access with working Agents? [Consistency, Spec FR-024, live contract]

## Review record

- Product/domain reviewer: pending explicit review of the concrete shipping model.
- Decision: pending; existing product-scope approval recorded separately in spec.md.
