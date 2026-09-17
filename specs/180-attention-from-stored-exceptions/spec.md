# Feature Specification: Attention Reads from the Stored Exceptions Projection

**Feature Branch**: `180-attention-from-stored-exceptions`
**Created**: 2026-09-12
**Status**: Reviewed with the owner on 2026-09-12 (staleness and cleared-finding decisions recorded); implemented on 2026-09-12 after 179 (#229) and #227 merged
**Language**: English
**Input**: Owner decision (German, 2026-09-12): the Exceptions page and the Exception rules tab still take seconds because every read derives all exception classes live; feature 179 moves stored projections to event-driven background refresh, and the attention reads should be built on it.

## Context and Intent

### Problem

Every attention read (`attention_register`, `attention_summary`, `attention_detail`) derives all
35 exception classes for the whole company at request time. On a company with 6,641 documents
and 2,230 open items that took 229 seconds before PR #227 and still takes about two seconds
after it, because the derivation hydrates every document, line and commitment on each read. The
Exceptions page (spec 141) and the Exception rules tab (spec 178) therefore make the reader pay
for work that the background already does: feature 179 keeps the `exceptions` projection
current from committed business events and, because it is time-sensitive, at least once per
minute, yet no screen reads those stored rows.

### Scope

- The Exceptions page register, its per-class summary and the per-class filter read the stored
  rows of the `exceptions` projection and report the projection's freshness state, using the
  contracts feature 179 introduces (stored reads perform no refresh; metadata with state,
  processed and target event sequence and completion time).
- The Exception rules tab (spec 178) shows the same counts, from the same stored generation,
  with the same freshness line.
- Explaining one finding stays live: the explanation walks causes and current records, and the
  screen says so when a stored finding has cleared since the last calculation.

### Non-Goals

- No change to any exception derivation, the catalog or the background refresh itself; those
  are feature 179 and PR #227. The builder gains one key per stored row, its canonical
  `position`, so the stored register keeps the order the live queue had (see Decisions).
- No new stored authority: the projection rows remain disposable results (Constitution rule 11),
  and the explanation of a finding, every Change Proposal check and every MCP read keep their
  live consistency guarantee (179 FR-010).
- No caching of the explanation, no new URL parameters, no change to the Home activity counts.
- The Playground's `reality` read of a run keeps deriving live; a run has no worker.

### Existing Contracts

- [Background projections and responsive Inspector](../179-background-projections/spec.md) —
  FR-006 stored reads perform no refresh; FR-007 per-projection state; FR-008 consumers show
  pending and failure state and retain prior results; FR-009 time-sensitive projections become
  eligible at least once per minute.
- [Unified warehouse and attention](../141-unified-warehouse-attention/spec.md) — FR-004 reuse the
  canonical derivation with server-side filtering before pagination and canonical ordering.
- [Exception rules register](../178-exception-rules-register/spec.md) — FR-002 open counts per
  class; FR-005 the summary and class filter.
- Projection read services: `projection_rows`, `projection_snapshot`, `projection_metadata`
  (`reality.services.projections`).
- PR #227 — the builder cost that makes a minute-level refresh of `exceptions` affordable.

## User Scenarios & Testing

### User Story 1 - Open the Exceptions page at page speed (Priority: P1)

A clerk opens Abweichungen and sees the current findings within a moment, in canonical order,
with search, severity and class filter working as today, and a line saying when the result was
last calculated.

**Why this priority**: This is the reason for the feature; every other story refines it.

**Independent Test**: With the projection ready, the register read makes no call into any
exception derivation and returns the stored rows filtered and paged; the response carries the
projection metadata.

**Acceptance Scenarios**:

1. **Given** a company whose `exceptions` projection is ready, **When** the register is read,
   **Then** the rows equal the stored generation, filtered and paged as before, no derivation
   runs, and the response reports state `ready` with the completed time.
2. **Given** the same company, **When** the page is read twice while nothing changes, **Then**
   both reads return the same rows and the same completed time.
3. **Given** a query, a severity or a class filter, **When** the register is read, **Then** the
   stored rows are filtered before paging exactly as the live read filtered them.

---

### User Story 2 - Know whether the findings are current (Priority: P1)

The reader sees when the stored findings are still being updated, have never been calculated,
or could not be updated, and can refresh the read without triggering any calculation.

**Independent Test**: Exercise the `uninitialized`, `pending`, `failed` and `ready` states of the
projection and compare the page.

**Acceptance Scenarios**:

1. **Given** a company whose projection has never completed, **When** the page opens, **Then** it
   says the findings are awaiting their first calculation and does not say there are no
   findings.
2. **Given** a completed generation and a newer committed event, **When** the page opens,
   **Then** the older findings stay visible with their completed time and a notice that they are
   being updated.
3. **Given** a failed background calculation, **When** the page opens, **Then** it reports that
   the update failed, without an internal error and without implying a business action failed.
4. **Given** any state, **When** the reader presses Refresh, **Then** only a read happens; no
   refresh, enqueue, commit or cache write is caused by the page.
5. **Given** a stored result, **When** the reader presses Refresh, **Then** the control reports
   that it is reading and cannot be pressed again, and afterwards the notice states either that a
   newer result arrived or that the stored one is unchanged.
6. **Given** a stored generation behind the event stream, **When** the notice is shown, **Then**
   it states how many events are not yet included.

---

### User Story 3 - Explain a finding that may have moved on (Priority: P2)

The reader opens a stored finding's explanation. It is derived live, so it is either the current
truth about that finding or a clear statement that the finding has cleared since the last
calculation.

**Independent Test**: Clear a finding in Reality (for example reserve the shortfall) before the
projection catches up, then open its explanation from the stored register.

**Acceptance Scenarios**:

1. **Given** a stored finding that still holds, **When** it is explained, **Then** the explanation
   carries its causes, guidance and target exactly as today.
2. **Given** a stored finding that no longer derives, **When** it is explained, **Then** the API
   answers not found with `finding_cleared` and the generation's completed time, and the page
   says the finding has cleared since the last calculation rather than showing a bare error.

---

### User Story 4 - The Exception rules tab shows the same counts (Priority: P2)

The open counts per class and the preview of open findings in the Exception rules tab come from
the same stored generation as the Exceptions page and carry the same freshness line.

**Acceptance Scenarios**:

1. **Given** a ready projection, **When** the tab loads, **Then** the per-class counts sum to the
   register total of the same generation and the tab shows the completed time.
2. **Given** a pending projection, **When** a row's preview opens, **Then** the listed findings
   are the stored ones and the preview shows the pending notice.

### Edge Cases

- A company created moments ago has no generation yet: the page and the tab show "awaiting
  first calculation"; the counts column shows a placeholder, not zero.
- Rows and counts of one response MUST come from one completed generation; a refresh between
  the two reads of a page load is reported as pending rather than mixed.
- A stored row whose target record was deleted still lists; its explanation reports that it has
  cleared.
- Search still matches id, class id, title, impact and record id on the stored rows.
- A tenant the user cannot read returns not found for register, summary and detail alike.

## Requirements

### Functional Requirements

- **FR-001**: `attention_register` and `attention_summary` MUST read the stored rows of the
  `exceptions` projection for the tenant and MUST NOT call any exception derivation, refresh,
  enqueue, commit or cache write (179 FR-006).
- **FR-002**: Both reads MUST return the projection metadata of the generation they read (state,
  processed and target event sequence, completed time, calculation mode) alongside rows or
  counts; rows, counts and metadata in one response MUST belong to one completed generation.
- **FR-003**: Filtering by query, severity and class id, canonical ordering and paging MUST
  behave exactly as the live register did; an unknown severity or class id is still refused.
- **FR-004**: `attention_detail` MUST stay live through the canonical explanation. When the
  stored finding no longer derives, the API MUST answer not found (the existing 404 path) with
  the distinct classification `finding_cleared` and the completed time of the generation the
  caller read, never a 200 with an empty explanation; the Web app renders it as cleared since
  the last calculation.
- **FR-005**: The Exceptions page MUST show the freshness line for all four states, keep the
  prior rows visible while pending, never present an uninitialized generation as "no current
  findings", and offer a read-only refresh.
- **FR-006**: The Exception rules tab MUST take its counts and preview rows from the same stored
  read path and show the same freshness line.
- **FR-007**: The new texts MUST exist in all four UI languages.
- **FR-009**: The freshness notice MUST report what pressing Refresh did. While the read is in
  flight the control MUST be unavailable and say so, and the notice MUST be marked busy. When it
  completes, the notice MUST state whether a newer generation arrived or the stored result is
  unchanged — the ordinary outcome, because Refresh reads and never advances the calculation
  (US2 scenario 4), and a silent no-change reads as a broken control. Where the stored generation
  is behind the event stream, the notice MUST state how far behind it is. The control MUST NOT be
  renamed and no new endpoint may be introduced.
  Owner refinement (2026-09-17): keep the Refresh label, button position and notice height
  stable across repeated reads at desktop and mobile widths. The spinner supplies visible
  click feedback; do not display additional checking/updated/unchanged sentences. Announce
  results to assistive technology only. Place the last-calculated timestamp immediately
  beside Refresh in a wrapping row, not at the opposite edge of a wide panel. Show pending,
  uninitialized and failed calculation state and event backlog compactly below; omit the
  redundant "Stored result" label when a completed timestamp is present. Keep read errors
  visible and never report them as successful outcomes. No new endpoint or background work.
- **FR-008**: Response shapes MUST stay compatible: existing fields keep their names; `metadata`
  is added.

### Key Entities

- **Stored exception row**: one `exceptions` projection row, the serialized output of the
  canonical derivation for one finding; disposable, never authority.
- **Projection metadata**: state, processed and target event sequence, completed time,
  calculation mode (179).
- **Live explanation**: the canonical per-finding explanation with causes and guidance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: On the representative large company the Exceptions page register and the rules tab
  summary answer in under 300 ms server time each, measured with the same harness that measured
  229 s and 2 s before.
- **SC-002**: Service tests prove that the stored reads run with every builder and derivation
  forbidden, in the pattern feature 179 establishes.
- **SC-003**: All four freshness states are exercised in service, HTTP and browser proofs for the
  Exceptions page and the Exception rules tab.
- **SC-004**: A finding cleared before the projection catches up is explained as cleared, never
  as a bare not-found error, in a service test and in the browser.

## Decisions

Recorded with the owner on 2026-09-12.

- **Staleness.** Up to about two minutes between a business change and the Exceptions page is
  accepted. Committed events trigger the refresh, so after a reservation, a shipment or a posting
  the list catches up within about 30 seconds (179 SC-003); the 90-second bound applies only to
  time-only transitions such as a promise becoming overdue, which nobody needs to the second.
  The page is a work list, not an authorization: the explanation of a finding, every Change
  Proposal check and every MCP read stay live, so a stale row cannot cause a wrong action. The
  freshness line and the cleared-finding answer make the delay visible instead of hiding it.
- **Cleared finding.** A stored finding that no longer derives is answered as not found with the
  classification `finding_cleared` and the generation's completed time, on the existing 404
  path. A 200 with an empty explanation would present missing data as a confirmed empty result,
  which 179 forbids, and an agent reading the same API would take it for "nothing to do".
  Today's callers already receive 404 here, so nothing breaks; the Web app only learns the code.
  410 Gone would be more precise but the repository routes every not-found through one 404
  path, so the distinction lives in the body, not in a second status code.

- **Canonical order.** The live queue orders by severity, class rank, the finding's own
  instant and record id; the stored payload never carried that instant. The builder now records
  each row's canonical `position` and the stored read orders by it. The projection version is
  not bumped: the `exceptions` projection is time-sensitive and republishes within a minute, and
  until it does a generation without positions orders by severity, class rank and record id.

## Assumptions and Dependencies

- Feature 179 is merged first; this feature uses its read services and metadata unchanged.
- PR #227 is merged first; without it the minute-level refresh of `exceptions` costs the worker
  minutes per run on large companies.
- The stored row payload keeps the shape of `operational_exception_rows`, so the attention
  enrichment (context labels, targets, delivery ids) applies unchanged.
- See Decisions for the accepted staleness and the cleared-finding answer.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001, FR-002, FR-003 | `reality.services.attention_reads.stored_exceptions`, `attention_register`, `attention_summary` (one snapshot, no builder); `tests/test_attention_reads.py` (`_forbid_derivation`, canonical order, filters, refusals, same metadata for register and summary); `tests/test_unified_operations_api.py` |
| FR-004 | `FindingCleared` in `attention_reads.py`; `get_attention_detail` in `reality.web.api` (404 body with `code` and `completed_at`); `test_detail_explains_live_and_classifies_a_cleared_finding`; `test_attention_detail_classifies_a_cleared_finding_over_http` |
| FR-005, FR-007 | `AttentionPage.tsx` (`ProjectionFreshness`, `data-attention-empty`, `data-finding-cleared`); `localization.tsx` de/nl/es; `node scripts/i18n-audit.mjs`; focused browser run over the four states, the cleared preview and German at 1440px and 390px |
| FR-006 | `ExceptionRulesRegister.tsx` (freshness line, placeholder counts while uninitialized); `unified-inspector-browser.mjs` asserts the ready freshness line |
| FR-008 | `test_unified_operations_api.py`: existing fields unchanged, `metadata` added, plain not-found keeps no `code` |
| SC-001 | measured on the local stack company `ten_de87f2e90b` after the worker published a generation (recorded in the PR) |
| SC-002 | `test_register_reads_the_stored_generation_in_canonical_order`, `test_uninitialized_company_is_awaiting_calculation_not_empty` run with derivations and builders monkeypatched to fail |
| SC-003 | service: `test_stale_generation_keeps_rows_and_reports_pending`, uninitialized test; HTTP: metadata assertions; browser: ready, pending, uninitialized, cleared (`shots180/`) |
| SC-004 | `FindingCleared` service and HTTP tests; browser cleared preview |

Owner refinement: show a permanent 14px refresh-arrows icon beside the button label.
It stays still when idle and rotates immediately for at least 1000 ms after activation,
and longer while the read is pending. Never leave an empty icon slot. Dimensions stay
fixed across idle/loading/completed states. Keyboard activation uses the same action.
Keep duplicate activation disabled throughout this feedback interval; announce checking
to assistive technology until it ends. Reduced motion keeps the indicator static. Clear the timer on
unmount. Data can arrive immediately; the minimum interval only affects feedback.

Busy controls retain keyboard focus using aria-disabled and reject repeat activation.
