# Feature Specification: Timeline recorder raster

**Language**: English

## Context and Intent

### Problem

The Reality Inspector Timeline (spec 138 FR-026, internally the flight recorder) draws
one 224px column per recorded event and one 196×80px card per record. Because every
event touches exactly one record, four of the five lanes are empty in every column, and a
hundred events need twenty screen widths. When a batch arrives, every column header shows
the same minute. The user sees a nearly empty grid and no shape, although the events,
lanes and explicit links are already loaded.

### Scope

Keep the five lanes, the loaded events, the explicit references, selection, Inspector
details, older-page prepend and tenant isolation of spec 138 FR-026. Change only the
layout: records become dots coloured by lane; the horizontal axis becomes a fixed raster of
recording-time intervals (15 minutes, one hour or one day, chosen from the loaded range);
records recorded in the same interval and lane appear as one aggregate pulse. Selecting a
pulse reveals its individual records, and explicit connection edges appear only after an
individual record is selected. The header shows interval labels instead of one timestamp
per event.

### Non-Goals

No new reads, filters, routes, schema or service logic. No inferred links, no grouping of
events into cases, no expected-but-missing markers, no change to which references form
edges. The Record graph tab and the Inspector are unchanged. Business time
(`occurred_at`) stays in the selection details; it does not drive the axis, because many
recorded events carry the recording instant as business time and the recorder must stay
truthful to what was recorded when.

## User Scenarios & Testing

### US1 — Reading a day of recorded activity

The user opens the Timeline for a company with a hundred recorded events from one day.
Acceptance: the band fits a few screen widths instead of twenty; the header shows
interval labels (for example every full hour when columns are 15 minutes); every non-empty
lane and interval is one pulse; the strip above the band names the interval size; selecting
a pulse exposes its records, and selecting a record highlights its explicit connections
and offers Details as before.

### US2 — A burst recorded in one minute

An import records twenty events within one interval.
Acceptance: one pulse represents the records in each affected lane; its size, saturation
and visible count make the burst stronger than a single-record interval without allowing
large bursts to dominate the chart. Selecting a pulse reveals every member as a reachable
record control with kind and business label.

### US3 — Watching the recorder run

The user leaves the Timeline open on a company with continuous intake.
Acceptance: the now mark moves, new records contribute to the pulse at the right within a
minute, and the quiet baseline makes bursts and idle periods visible without a background
web of connections.

### US4 — Zooming the raster

The user zooms out from an hourly raster to see a month, then back in on one afternoon.
Acceptance: the strip names the new interval, records regroup into the coarser or finer
columns, the middle of the view stays on the same instant, and the buttons disable at the
finest and coarsest level.

### US5 — Loading older history

The user scrolls to the left edge.
Acceptance: older pages prepend, the raster extends to the left (and coarsens if the loaded
range crosses six hours or three days), the viewed anchor is preserved, and the earlier
reference area, retry, manual load and Latest events keep working.

### US6 — Exploring a pulse as a relationship trace

The user selects a pulse to see its exact records in a compact detail section below the full-width Timeline, then selects one
record to understand its connections beyond the time raster. Acceptance: the pulse inspector
first shows a scannable record list without covering the Timeline. Record selection replaces
that list with a directed trace: evidence and origin links on the left, the selected record in
the centre, and operational consequences on the right. Clicking a linked record continues the
trace; Back and Details remain available. The pulse and time position remain intact.

### US7 — Reading from time pattern to business record

The user reads one stable vertical sequence: aggregate seismograph, exact business records,
then the selected record's relationship trace. The record list uses familiar ERP table columns
instead of spatial bubbles or cards. Clicking a row opens the trace; Back returns to the list.

Acceptance: hover only exposes the native record tooltip and never loads or changes the large
relationship view; click opens the member; timeline relationship lines do not duplicate the trace;
and repeated Inspector rows for the same linked record produce one trace node. The Timeline
remains full width and compact while the list or trace follows below it at every breakpoint.

## Requirements

- **FR-001**: Position every record with a loaded subject observation at the column of the
  recording interval that contains its earliest loaded observation. Choose the interval
  from the loaded range: 15 minutes up to six hours, one hour up to three days, otherwise one
  day. Records known only by reference keep the earlier-reference area at the left.
- **FR-002**: Render aggregate pulses coloured by lane using theme tokens that hold
  contrast in light and dark themes; keep each member's business label and ID in the
  drill-down and existing selection details. Record selection, dimming, edges on selection,
  off-screen hints, Details and Clear selection keep their behaviour.
- **FR-003**: Group records of one lane and one interval into one pulse. Preserve the
  existing record positions internally for selected-record connection rendering, and keep
  every member rendered and reachable in the pulse drill-down rather than hiding records
  behind the aggregate count.
- **FR-004**: Keep Load older events, Latest events and the zoom buttons inside the widget's
  own toolbar beside the interval strip, not in the page heading. Replace the per-event header with interval labels at fixed steps (every hour
  for 15-minute columns, every six hours for hourly columns, every seven days for daily
  columns) in the user's locale, and state the interval size in the strip above the band.
  Keep occurred and recorded timestamps distinct in the selection details.
- **FR-005**: Anchor older-page prepend to the instant at the viewed left edge, keep the
  left-edge trigger for loading older pages (also when the view already opens at the edge or
  the page does not overflow), and keep Latest events scrolling to the newest column.
- **FR-006**: The paper runs up to the present: the raster ends at the current instant with a
  marked now line, spans at least the visible band width, and the interval is chosen from
  first loaded record to now. The now mark advances once a minute and newly recorded events
  are fetched every 30 seconds while the tab is visible. The view opens with the newest
  record in sight.
- **FR-007**: Every lane draws a quiet baseline trace so bursts and idle periods can be read
  without selection. Held references remain available to record drill-down, but their edges
  are not drawn until an individual record is selected.
- **FR-008**: Zoom in and zoom out buttons step the raster through five minutes, 15 minutes,
  one hour, six hours, one day and one week; the automatic choice applies until the user
  zooms; zooming keeps the instant at the middle of the view in the middle.
- **FR-009**: Hovering or focusing an individual record after pulse drill-down opens its
  record card next to it as an overlay: kind, business label, received quantity or amount,
  event type with sequence, and the recorded and occurred timestamps. The card never
  intercepts clicks and stays inside the paper.
- **FR-010**: The default Timeline renders one aggregate pulse for each non-empty lane and
  recording interval, including the earlier-reference area. A pulse exposes its exact
  record count, lane and interval to sighted and assistive-technology users. Its diameter
  and colour saturation increase on a bounded logarithmic scale so one, several and many
  records are distinguishable without letting an extreme count consume the lane.
  Each aggregate lane MUST retain at least 60 px of height so its baseline, pulse and adjacent
  lane boundaries remain visually distinct without turning the recorder into a large work area.
- **FR-011**: Selecting a pulse reveals every represented record in a compact semantic table
  immediately below the full-width recorder. The table presents record type, business label,
  recorded time or earlier-reference status, and an explicit drill-down action. Opaque identity
  remains available as secondary traceability information rather than the primary label. The
  section has a visible close action. Hover MUST NOT load another view; click and keyboard
  activation remain equivalent. Selecting one of those records restores
  the existing record selection, Inspector Details action, connected-component dimming,
  off-screen hints and explicit edge rendering. Clearing record selection returns to the
  selected pulse; clearing the pulse returns to the overview.
- **FR-012**: No reference stitch or connection edge is drawn in the unselected pulse
  overview. Pulse selection alone does not draw record-level edges. Only an individual
  record selection draws its incident explicit-reference edges; no inferred connection or
  aggregate business relationship is introduced.
- **FR-013**: Selecting a pulse MUST open its exact records as a scannable table below the
  recorder without overlaying or narrowing it. Selecting an individual member MUST replace that
  list with a directed relationship trace using the same tenant-scoped Inspector read and
  explicit links as the Record graph. Evidence and origin links MUST appear left of the selected
  record and operational consequences right of it. The compact selected-record summary MUST sit
  inside the relationship section header.
- **FR-014**: The relationship trace MUST support linked-node navigation, Back, zoom and
  Inspector details without changing the selected pulse, recorder zoom or horizontal time
  position. Loading, error, empty and incomplete-coverage states MUST retain the existing
  Record graph meanings.
- **FR-015**: Trace motion MUST be a brief layout transition only. It MUST not continuously
  move, obscure labels, imply link strength or introduce inferred edges. Small screens MUST use
  a readable bounded canvas with pan/scroll rather than overlapping the product shell.
- **FR-016**: The recorder, pulse table and relationship trace MUST use one vertical document
  flow at every breakpoint. Opening a pulse MUST NOT narrow the recorder, force taller lanes,
  create matched pane headers or introduce a side-by-side layout. The detail section follows
  immediately after the compact Timeline and uses the available full width.
- **FR-017**: Hover on a pulse-list member MUST only provide its normal label/tooltip and MUST
  NOT load or replace the relationship view. Clicking or keyboard-activating the member MUST
  pin it and open the trace. Hovering a trace node MUST only highlight it; continuing the trace
  remains click-only.
- **FR-018**: While the relationship trace is visible, the recorder MUST NOT render duplicate
  record-level connection lines or expand individual connected nodes. The selected pulse and
  pinned member remain visibly marked on the left. The constellation MUST render each unique
  linked record once even when the Inspector response mentions that link in multiple rows.
  A visible close action and Escape MUST clear pulse and record focus together; returning from
  a record MUST keep the pulse table open.

## Assumptions and Dependencies

Owner asked on 2026-09-10 for exactly this step ("Boxen enger, Raster für die Zeit weg,
oben festes Zeitraster alle 15 Minuten, Punkte aus den Boxen") after reviewing layout
alternatives, and chose the recorder as stage 0 before any case-based view. Uses the
existing timeline read and `buildFlightGraph`; no API change. No unresolved
clarifications. After reviewing the live raster, the owner approved an aggregate
seismograph view on 2026-09-10: records inside one time interval should read as one darker
or stronger pulse, while the excessive grey connection lines should be deferred to
drill-down.
On the same date, the owner approved a second spatial graph below the seismograph after
record selection, with expandable linked bubbles and a restrained moving-in-space feel.
The default is a deterministic two-dimensional radial constellation rather than literal
3D, preserving readable labels and accessible controls.

## Success Criteria

- SC-001: A hundred events recorded within one day render within at most four screen
  widths at 1440px, with every record still a clickable node.
- SC-002: Interval selection, stacking, widening and label steps are covered by a pure
  layout function with unit tests.
- SC-003: Existing frontend contracts, the Inspector browser suite, production build,
  four-language localization audit, Prettier and the spec gate pass.
- SC-004: In the 200-record reference view, the overview contains no more than one visual
  pulse per non-empty lane and interval and contains no connection lines until a record is
  selected.
- SC-005: A user can move from an aggregate pulse to any represented record and then to its
  existing Inspector details without losing its Source → Evidence → Reality trace.
- SC-006: From a selected pulse member, a user can open any returned direct link, navigate
  back and inspect the centred record without returning to the Record graph tab.
- SC-007: At 390px and 1440px, the constellation remains contained in its page region and
  every displayed bubble remains reachable by keyboard and scrolling.

## Requirement Traceability

FR-001, FR-003, FR-004 → US1, US2, T002, T003. FR-002, FR-007, FR-009 → US1, US3, T003. FR-005 → US5,
T003, T004. FR-006 → US3, T002, T003. FR-008 → US4, T002, T003. FR-010–012 and SC-004–005 →
US1–US3, T005–T008. FR-013–015 and SC-006–007 → US6, T009–T011. SC-001–003 → T004, T008,
T011.
