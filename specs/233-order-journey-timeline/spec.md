# Feature Specification: Order journey timeline

**Language**: English

**Created**: 2026-09-18
**Status**: Implemented and verified; human PR review pending
**Input**: Replace the Business Graph recorder with the understandable, order-focused timeline demonstrated at https://reality-timeline-demo.bene007.chatgpt.site/. The owner accepted the proposed concept with “ok mach”.

## Context and Intent

### Problem
The five technical recorder lanes hide all operational reality in one lane. Hourly aggregates and empty time ranges obscure the story even when records are loaded. Users need to follow the actual promises, bindings and movements of an order.

### Scope
Replace the Timeline tab with five business lanes, a compact sales-order selector, individual recorded changes, explicit relationships and a readable chronological journey. Preserve Record graph and the Inspector. First scope is sales-order commitments, reservations and movements, plus directly attached facts and ledger entries where held. Source and evidence remain accessible as provenance and in the journey, not additional primary lanes.

This supersedes spec162 FR-001–018 for the Timeline presentation, including obligatory hourly pulses, the stacked-only detail layout, and the second graph below the timeline. Its tenant, provenance and truthful-time protections remain. Existing recorder utility contracts may remain for other callers; they are no longer the active Timeline UI.

### Non-Goals
No schema changes, new stored process/case entity, inferred causal links, finance reconciliation, procurement journey expansion, simulated activity, automatic mutations, or alternative fulfillment calculations. No requirement that every order passes through every lane. No new scheduler or background infrastructure.

## User Scenarios & Testing

### US1 — Understand recorded reality (P1)
Open Business Graph and see Facts, Commitments, Reservations, Movements and Ledger entries with short explanatory captions. Each point represents a recorded change, including later changes to the same record.

Acceptance:
1. Given recent and old activity, opening the page fits the loaded business activity; it never starts on a blank present-day interval when eligible events exist.
2. Given simultaneous changes, their points remain separately reachable through an explicitly counted collision group and its member list.
3. Given a document/source event, it remains readable in the chronological journey and opens its Inspector, without being mislabeled as a Fact or Movement.

### US2 — Follow one sales order (P1)
Choose an order by number or customer, see its bounded history and inspect actual links.

Acceptance:
1. Two orders sharing customer, article and location remain separate when one is selected.
2. A reservation belongs through its commitment; a movement belongs through its commitment; neither requires a copied document relationship.
3. Selecting a point pins the change and reveals title, business context, recording time, business time and links to the record and event Inspector. Actual links are distinguishable from chronological order.
4. A foreign-tenant or non-sales-order root fails without exposing its records.
5. An order with no recorded eligible changes shows an explicit empty history, with evidence still inspectable.

### US3 — Read comfortably over time (P2)
Choose a 15-minute, one-hour, today or fit-history view. Read without refresh moving the current selection. Load earlier history explicitly.

Acceptance:
1. The default axis uses recording time and localized presentation; business time remains separately labeled.
2. A selected range containing no points says so and offers fit-history. Counts describe loaded events, not company totals.
3. Loading older pages retains the current range and selection; fit-history explicitly includes newly loaded history.
4. A refresh failure keeps prior data and exposes retry. Switching order/company cannot display a late response for the prior context.
5. Keyboard users reach all points and grouped members; at 390px the detail follows below, at a sufficiently wide viewport it sits beside the timeline. No second navigation sidebar is introduced.

## Requirements

- **FR-001**: Timeline MUST show canonical Facts, Commitments, Reservations, Movements and Ledger entries lanes with localized explanatory captions and theme-aware distinguishable colors. Only actual subjects of those types populate lanes; posting-group events share the Ledger entries lane while retaining their group identity and links to the held entries.
- **FR-002**: Each dated point MUST represent one recorded event, positioned by recorded time; repeated changes to one subject remain separate. Only visually overlapping points in the same lane may be grouped, and every group member MUST remain selectable.
- **FR-003**: The default view MUST fit the loaded eligible business events. Users MUST be able to select 15 minutes, one hour, today (user timezone), and fit loaded history; a selected order initially fits its loaded history. Short periods end at the latest loaded recording, avoiding an empty default for inactive companies.
- **FR-004**: A searchable, bounded sales-order selector MUST display business labels and use opaque identity. All activity remains a selectable overview. No automatic selection of an arbitrary order.
- **FR-005**: Order membership MUST be read by shared tenant-scoped services through document/line → commitment → reservation/movement and directly attached facts/ledger entries. Shared party, item, location, source, correlation or mere temporal proximity MUST NOT expand membership. Related source/evidence may be included as terminal provenance only.
- **FR-006**: Selected-order connections MUST name true record relationships returned by the shared read. They MUST NOT claim that successive events caused each other. Unloaded endpoints MUST NOT receive invented timestamps or positions; their references remain inspectable.
- **FR-007**: The detail panel MUST present the loaded chronological journey, selected change, separate recorded/occurred times and record/event Inspector actions. Source and document history remain reachable here. Source-stated values remain exact and current state MUST NOT be represented as historical state.
- **FR-008**: Reads MUST be bounded, with an older-history cursor and explicit partial-history notice. The UI MUST NOT claim “complete process” from a loaded page or turn event counts into totals. Empty, loading, error and retry states MUST be distinct.
- **FR-009**: Visible-tab refresh MUST reuse the existing 30-second read pattern, preserve selected event and time window, merge by event identity and reject stale responses on order/company changes. No fake “live connected” indicator; refresh failures MUST be visible. No automatic follow-to-now while inspecting.
- **FR-010**: Details MUST sit beside the timeline only when space permits and below on small screens; chart overflow MUST stay local. Native buttons and labeled controls MUST support keyboard selection, close and Escape. Text and labels MUST work in all four supported languages and themes.
- **FR-011**: The existing Record graph tab, Inspector paths and tenant authorization MUST remain unchanged. No business writes or persisted derived state are introduced.

### Key Entities
- Sales order: an existing evidence root identified by opaque ID and a human label.
- Recorded change: an existing immutable business event, not a new Fact.
- Relationship: an existing typed record reference, separate from time order.
- Journey: a bounded read-time view, never a stored operational authority.

## Success Criteria
- **SC-001**: A user can select an order, select one of its recorded changes and open its underlying record in at most three selections after searching.
- **SC-002**: A test story with two orders sharing references shows zero unrelated order changes in a selected journey.
- **SC-003**: Every loaded event remains reachable in the journey, including same-time bursts and provenance events; every plotted point has a distinct event identity or explicit member count.
- **SC-004**: At 390px and 1440px the timeline, selection and Inspector remain usable without expanding the document beyond its viewport.

## Assumptions and Dependencies
The owner accepted the concept and first sales-order scope on 2026-09-18. Recording time is intentionally retained because occurred times are not consistently independent timestamps. Today is an explicit filter; an empty today is truthful. Financial entries are included only where directly attached to this scope; invoice/payment traversal is future work. The existing Inspector supplies original payload traversal. Tests are required before implementation where practical: tenant/membership service stories, adapter checks, pure layout tests and browser interaction verification. Product implementation is authorized by the accepted concept; no unresolved clarification remains.

## Requirement Traceability

| Requirements | Stories | Tasks | Proof |
|---|---|---|---|
| FR-001–003 | US1, US3 | T005–007, T010–011 | order-journey-layout.test.mjs, order-journey-browser.mjs |
| FR-004–008 | US2 | T002–004, T008–009 | test_order_journey.py, order-journey-browser.mjs |
| FR-009–010 | US3 | T010–012 | browser refresh/range/mobile checks, localization audit |
| FR-011 | US2 | T002–004, T008–009, T013 | tenant/API and Inspector regression tests |
| SC-001–004 | US1–US3 | T002, T005, T008, T010, T013 | service, layout and browser acceptance |
