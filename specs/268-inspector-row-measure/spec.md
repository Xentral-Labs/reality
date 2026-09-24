# Feature Specification: An Inspector row states one measure

**Feature Branch**: `268-inspector-row-measure`
**Language**: English
**Created**: 2026-09-24
**Status**: Implemented (written alongside the change on 2026-09-24; see Deviation from the mandated path)
**Input**: In the stock-at-a-location panel, the movement rows read "2 pcs · 21. Sept. 2026, 21:38" as one underlined link. The owner asked for a better idea and for every place in the product that would need it.

## Context and Intent

### Problem

An Inspector row is a two-column contract: a label on the left, a value on the right
(`apps/web/src/unified/Inspector.tsx:170-205`). Where a row has more to say than one
value, the producing code concatenates the rest into the same string with a middle dot:

```python
display_text(signed, f" {unit} · ", movement.occurred_at)   # "-12 pcs · 19. Sept. 2026, 02:00"
```

That composition happens in twelve places across two layers
(`services/operational_previews.py`, `web/api.py`), and the renderer makes the whole
compound one accent-coloured, underlined link.

Three things go wrong at once, and they compound in a list:

1. **Two scan directions share one column.** A quantity is read right to left against the
   other quantities above and below it; a timestamp is read left to right as a word. Glued
   into one right-aligned string, neither works: the digits of `2 pcs`, `-12 pcs` and
   `-5 pcs` land at different positions, so the column a clerk came to compare cannot be
   compared.
2. **The underline has no anchor.** Every character of a thirty-character compound is
   accent-coloured and underlined, so nothing in the row is visually load-bearing. The eye
   has to parse the string to find the number.
3. **Midnight is shown as a time.** Movements imported without a clock carry `00:00` UTC,
   which the reader's locale renders as `02:00`. Eight of the nine rows in the reported
   panel stated an hour that no source ever recorded.

The register table directly above the same panel already solves this
(`apps/web/src/unified/WarehousePage.tsx:305-311`): quantity right-aligned with a muted
unit, the movement type and the timestamp in their own cells. The Inspector falls behind
its own table.

The reported case is the stock-at-a-location panel from spec 262, but the shape is not
specific to it. The same `value · qualifier` compound appears as `quantity · status` in
three commitment lists, `quantity · location`, `quantity · item`, `amount · allocation id`
and `debit/credit · amount`.

### Principle

A row states one measure. What qualifies that measure — when it happened, which state it
is in, where it sits, which record it is — is a second field, not more characters in the
first. Two measures in one row are a different problem: a missing column, which this
feature does not invent.

### Scope

Extend the Inspector row contract with a qualifier field carried apart from the value,
typed the same way the value is typed, and render it as its own column. Convert every row
whose compound is a value plus a qualifier. Change no number, no derivation and no link.

### Non-Goals

No new entity, table, column, projection or migration: this is presentation of rows that
are already derived (Hard rule 11). No change to any quantity, amount, date or link
target. No new Inspector kind and no new endpoint. No MCP or catalog change — the agent
reads the underlying records, not the Inspector's rows. Rows that compose **two measures**
(a quantity and a money amount, `web/api.py:5343`,
`services/operational_previews.py:212`) are deliberately left as they are: a qualifier
field is the wrong home for a second measure, and giving them a real third column is
separate work. `_historical_pricing_summary` is prose, not a row, and is untouched. The
row markup remains duplicated across the three renderers; extracting a shared row
component is named in Assumptions as follow-up work, not delivered here.

## Inventory of the compounds (read 2026-09-24, `main` at 2a1725cd)

| Producer | Row | Compound today | Kind of second part |
|---|---|---|---|
| `operational_previews.py:381` | stock at a location · movements | `qty unit · occurred_at` | when |
| `operational_previews.py:393` | stock at a location · reservations | `qty unit · reserved_at` | when |
| `web/api.py:5186` | commitment · reservations | `qty · location_id` | where |
| `web/api.py:5198` | commitment · movements | `qty · occurred_at` | when |
| `web/api.py:5369/5452/5530` | document, party, item · commitments | `qty · status` | state |
| `web/api.py:5400` | document · Financial Reality | `debit_credit · amount` | state, stated before its measure |
| `web/api.py:5542` | item · recent movements | `qty · occurred_at` | when |
| `web/api.py:5633` | location · recent movements | `signed qty unit · item name · occurred_at` | what and when |
| `web/api.py:5992` | shipment · physical contents | `qty · item_id` | what |
| `web/api.py:6091` | payment · inactive allocations | `amount · allocation_id` | which record |
| `web/api.py:5343` | document · lines | `qty unit · gross amount` | **a second measure** |
| `operational_previews.py:212` | document · lines | `qty unit · gross amount` | **a second measure** |

## User Scenarios & Testing

### User Story 1 — A section's measures read as one column (Priority: P1)

A clerk opens the stock-at-a-location panel to see what moved. The quantities stand in one
column with their digits aligned; the dates stand in a second column; a glance across the
section answers "what came in and what went out" without reading a single string to its
end.

**Independent Test**: build a movements section with mixed-length signed quantities and
render it; the value and the qualifier occupy separate elements and the value carries
tabular figures.

**Acceptance Scenarios**:

1. **Given** a movements section, **When** it is rendered, **Then** each row shows the
   quantity with its unit in one right-aligned element and the moment in a second, muted
   element, and no element contains both.
2. **Given** the same section, **When** the quantities differ in digit count and sign,
   **Then** they align on their right edge in tabular figures.
3. **Given** a row with no qualifier, **When** it is rendered, **Then** it looks exactly as
   it did before this feature.

---

### User Story 2 — A time that was never recorded is not shown (Priority: P1)

A clerk reads a movement imported from a source that stated only a day. The row states the
day. No hour appears that no source ever recorded.

**Independent Test**: record two movements, one at midnight UTC and one at a real clock
time; the first is carried as a date, the second as an instant.

**Acceptance Scenarios**:

1. **Given** a movement whose `occurred_at` is midnight UTC, **When** its row is built,
   **Then** the qualifier is typed as a date and the reader sees a day.
2. **Given** a movement recorded at 21:38 UTC, **When** its row is built, **Then** the
   qualifier is typed as an instant and the reader sees the time in their own zone.

---

### User Story 3 — The link is the row, not the sentence (Priority: P2)

A clerk clicking a movement hits the row, not a thirty-character underlined phrase. The
accent and the underline mark the measure alone, so each row has one visual anchor.

**Independent Test**: render a linked row; the click target is the row element, the
measure carries the link styling, and the qualifier carries none.

**Acceptance Scenarios**:

1. **Given** a linked row, **When** it is rendered, **Then** the whole row is the click
   target and carries a hover surface.
2. **Given** that row, **When** the qualifier is inspected, **Then** it is neither accented
   nor underlined.
3. **Given** a keyboard user, **When** they reach the row, **Then** its accessible name
   states the label, the measure and the qualifier.

---

### User Story 4 — Nothing is lost where there is no second column (Priority: P2)

The same rows appear in the object graph, whose nodes hold one line of text. There the
measure and its qualifier are composed back into one string, so no reader of that view
loses the information the panel gained a column for.

**Independent Test**: the recomposition helper returns the joined string for a row with a
qualifier and the plain value for one without.

**Acceptance Scenarios**:

1. **Given** a row with a qualifier, **When** it is rendered in a graph node, **Then** the
   node states value and qualifier joined.
2. **Given** a row without one, **When** it is rendered anywhere, **Then** the output is
   unchanged.

### Edge Cases

- **A qualifier longer than its column**: the reserved column width is a minimum, not a
  maximum; a long qualifier widens its own row rather than truncating or wrapping the
  measure away from its column.
- **A narrow container**: the compact inline preview is roughly 300px wide inside the
  dialog grid, where two columns do not fit. There the qualifier stacks under the measure,
  right-aligned, instead of beside it.
- **A qualifier that is itself composite** (`item name · moment` at a location): it is one
  qualifier field built from typed parts, so the moment inside it is still formatted in the
  reader's locale rather than shipped as an ISO string.
- **An empty qualifier**: an absent or empty `meta` emits no field at all, so a consumer
  cannot tell it apart from a row that never had one.
- **A midnight instant in a non-UTC zone**: the reduction tests midnight *UTC*, which is
  what an import writes. A movement genuinely recorded at 02:00 Berlin is 00:00 UTC and is
  shown as a day. This is accepted: the product records and states UTC, and the alternative
  — showing `02:00` on every imported row — is the defect being fixed.

## Requirements

### Functional Requirements

- **FR-001**: An Inspector row carries its measure in `value`/`display_parts` and, where a
  qualifier belongs to that measure, in a separate `meta`/`meta_parts`. A producer never
  concatenates a qualifier into the value.
- **FR-002**: `meta_parts` uses the same typed presentation parts as `display_parts`
  (text, number, date, datetime, money), so a qualifier is formatted in the reader's
  locale. An ISO timestamp is never shipped inside prose for the client to find by regex.
- **FR-003**: A qualifier is what the measure is not: when it happened, which state it is
  in, where it sits, which record it is. A second **measure** stays in the value; it is a
  missing column and is out of scope (see Non-Goals).
- **FR-004**: A recorded instant whose UTC clock reads midnight is carried as a day, because
  that is what a source states when it states no time. Any other instant is carried whole.
  One helper decides this for every producer.
- **FR-005**: The full Inspector renders the measure right-aligned in tabular figures and
  the qualifier in a fixed-width, right-aligned, muted column beside it, so the measures of
  a section form one column. The compact preview stacks the qualifier under the measure.
- **FR-006**: A linked row is clicked as a whole row with a hover surface. The link's accent
  and underline mark the measure alone; the qualifier carries neither.
- **FR-007**: Where a row is rendered with room for one string only — object-graph nodes and
  element titles — the measure and the qualifier are composed back into one string, so that
  view loses nothing.
- **FR-008**: The row contract stays backward compatible. A row without `meta` renders
  exactly as it did before, and every consumer that ignores the field keeps working.
- **FR-009**: Both row builders offer the same argument: `_row(..., meta=)` in
  `services/operational_previews.py` and `inspector_row(..., meta=)` in `web/api.py`. Two
  layers producing the same contract do not gain two spellings of it.
- **FR-010**: No number, date, currency, link target or record changes. This feature moves
  characters between two fields of a read contract and nothing else.

### Key Entities

No new entity. The feature changes the presentation contract of rows already derived from
`Movement`, `Reservation`, `Commitment`, `DocumentLine`, `LedgerEntry` and `Item`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: No Inspector row that pairs a measure with a qualifier composes the two into
  one string; the twelve compounds of the inventory are reduced to the two two-measure rows
  that Non-Goals excludes, and a rendering test proves the two parts never share an element.
- **SC-002**: In a section of mixed-length signed quantities, the quantities align on one
  right edge, proven by the tabular-figure and column assertions in the rendering test.
- **SC-003**: A movement imported without a clock states no hour, proven for both the
  midnight and the real-clock case.
- **SC-004**: Every converted row still states everything it stated before — the location
  inspector's movement rows keep naming their item, and the graph nodes keep the joined
  string — proven by tests that assert the information's new home rather than its absence.
- **SC-005**: A row without a qualifier is byte-identical in its rendered classes to the
  row before this change, proven by a test.
- **SC-006**: All gates pass: `make lint`, `make test`, `make spec-check`, `make web-build`,
  the frontend contract suite and the i18n audit in all four editions.

## Decisions (owner, 2026-09-24)

1. **Prototype first, on `stock_at_location` only, then roll out.** Reason: the owner
   wanted to judge the optics on the reported panel before twelve call sites moved.
2. **The qualifier column is right-aligned.** It was built left-aligned first, so the
   qualifiers' own starts would line up. The owner chose right alignment: the section's
   right edge then flushes with every other row in the dialog, and a ragged right edge next
   to "Held here" was the more visible defect. Accepted cost: where one row carries a time
   and the rest do not, the qualifiers' starts differ.
3. **Two-measure rows stay compound.** Reason: `meta` renders small and muted, which
   understates a money amount. A quantity and an amount need a real third column, which is
   its own change.
4. **No explicit `+` on arriving quantities.** It was offered and not taken: a sign is
   content, not layout, and does not belong in a presentation change.

## Assumptions and Dependencies

- Builds on spec 209 (the preview read contract and its `{label, value, display_parts?,
  link?, tone?, hint?}` row) and spec 262 (the stock-at-a-location panel where the defect
  was reported). The contract document `specs/209-operational-previews/contracts/preview.md`
  is extended with the new optional field rather than replaced.
- `hint` already exists for the label side and is unsuitable here: it is pushed through
  `t()` and carries no typed parts, so a date in it would not be localised.
- The row markup is duplicated in `Inspector.tsx`, `ContextExplorer.tsx` and
  `ObjectGraph.tsx`. This feature keeps all three in step by hand. Extracting one shared
  row component is the follow-up that makes the next such change a one-file change; it is
  not delivered here and is not required by any requirement above.
- The i18n audit rejects multi-word class strings inside ternaries, which is why the new
  classes are module constants in `Inspector.tsx`, following the file's existing
  `compactGrid`/`compactSection` convention.
- Contracts to update with the behaviour:
  `specs/209-operational-previews/contracts/preview.md` and
  `docs/SPEC_COVERAGE_MATRIX.md`. No catalog entry changes, so `make docs-generate` is not
  required.

## Deviation from the mandated path

`AGENTS.md` requires specify → clarify → plan → tasks → analyze → implement. This
specification was written after the implementation, during the same session: the owner
asked for a design proposal, then for a prototype to judge, then for the rollout, and the
spec was recorded once the shape was settled. The requirements, decisions and traceability
below describe what was built and were checked against the code and the passing tests, not
against intent alone. The deviation is recorded here rather than hidden; the owner is aware
that the specification followed the change.

## Requirement Traceability

- FR-001–FR-003, FR-009, FR-010 → US1 →
  `packages/reality-core/tests/test_inspector_presentation.py`
  (a row states its measure apart from its qualifier; a plain row grows no fields),
  `packages/reality-core/tests/test_stock_at_location.py`
  (the pair's movements and reservations carry quantity and moment as separate fields, and
  the location inspector's rows keep their item in the qualifier).
- FR-004 → US2 → `packages/reality-core/tests/test_inspector_presentation.py`
  (`moment()` reduces a midnight-UTC instant to its day and keeps a real clock),
  `packages/reality-core/tests/test_stock_at_location.py`
  (a movement imported without a clock states only its day).
- FR-005, FR-008 → US1 → `apps/web/scripts/inspector-row-shape.test.mjs`
  (separate elements, tabular figures, the reserved column, the stacked compact preview,
  and the unchanged row without a qualifier).
- FR-006 → US3 → `apps/web/scripts/inspector-row-shape.test.mjs`
  (the row is the click target; the qualifier is not underlined).
- FR-007 → US4 → `apps/web/scripts/inspector-row-shape.test.mjs`
  (`inspectorRowText` recomposes with a qualifier and returns the plain value without one).
- Regression cover for the unchanged inspectors:
  `packages/reality-core/tests/test_operational_previews.py`,
  `packages/reality-core/tests/test_master_data_api.py`,
  `packages/reality-core/tests/test_unified_invoice_credit.py`,
  `packages/reality-core/tests/test_unified_delivery_reads.py`,
  `packages/reality-core/tests/test_shipment_api.py`,
  `packages/reality-core/tests/test_partial_invoicing_rebilling.py`,
  `packages/reality-core/tests/test_unified_customer_refund.py`,
  `apps/web/scripts/cost-record-inspector.test.mjs`,
  `apps/web/scripts/stock-at-location-browser.mjs`.
- FR-005 wording and theming → `cd apps/web && npm run i18n:audit`, `make web-build`.
- Full gates: `make lint`, `make test`, `make spec-check`, `make web-build`.
