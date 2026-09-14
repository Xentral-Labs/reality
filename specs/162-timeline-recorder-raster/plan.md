# Plan: Timeline recorder raster

Add a pure layout module `apps/web/src/unified/flightRecorderLayout.ts` that takes the
existing `FlightGraph`, chooses the recording interval from the loaded range, assigns
every node a column (interval) and a stack position retained for record-level drill-down,
groups nodes into one pulse per lane and interval, and returns header ticks with label
steps. The axis always runs to the present and spans
at least the visible band, and the module exposes instant↔pixel mapping so older pages
keep the instant at the left edge in place.
`FlightRecorder.tsx` renders from that layout: aggregate intensity pulses with lane colours
from theme tokens in `tailwind.css`, interval labels and a now mark in the header, a baseline
trace per lane, a 30-second refresh of newest events while visible, and the same record-level
selection, edge, hint, prepend and load behaviour after pulse drill-down. `buildFlightGraph`
and its tests are unchanged. Implementation touches web adapters only; no domain, service,
tool, API or persistence change.

For the approved seismograph refinement, the pure layout additionally groups positioned
nodes by lane and interval (including the earlier-reference area) and derives a bounded,
logarithmic visual intensity from each exact count. `FlightRecorder.tsx` renders those
groups as the default pulses. Pulse selection exposes the group's existing records in a
compact drill-down; record selection continues to use the existing focus and Inspector
path. The overview emits no relationship lines, and only the selected record's incident
explicit-reference edges are rendered. No aggregation is persisted and no business
meaning is inferred from co-recording.

For the spatial drill-down, extend the existing `ObjectGraph` with an opt-in constellation
variant. A pure `connectionConstellationLayout.ts` assigns the root to the centre and
bounded direct links to deterministic inner and outer rings. The normal Record graph
presentation stays unchanged; `FlightRecorder.tsx` mounts the constellation variant only
after an individual pulse member is selected. It reuses `api.inspector`, current coverage
warnings, navigation history, zoom and Inspector controls. CSS transitions animate only
layout changes and respect reduced motion. No graph relationship is calculated in the
browser beyond positioning the links returned by the existing read.

## Constitution Check

All principles PASS. No schema, authority, mutation, confirmation or business calculation
changes. Reads, tenant scope and Source → Evidence → Reality links are untouched; edges
still come only from held explicit references. The recorder positions by recorded time,
which is what the timeline read already returns; nothing is inferred. Owner approved the
scope; every requirement maps to a task and an acceptance scenario.

## Verification and rollback

Add `apps/web/scripts/flight-recorder-layout.test.mjs` covering interval choice, column
assignment, stacking, widening and label steps; prove it fails without the layout. Run
the frontend contract suite, the Inspector browser suite (which drives the recorder with
21 events across two recording days, prepend, retry, selection and Details), TypeScript/
Vite build, the four-language localization audit, Prettier and the spec gate. Rollback
reverts this UI commit; no migration or data operation.

Extend the layout test first with pulse grouping, exact membership, reference grouping
and bounded intensity assertions. Add a focused rendering contract for default edge
suppression and pulse-to-record drill-down, then run the existing frontend and browser
gates. Rollback restores the individual-dot renderer; data and APIs remain unchanged.

Add pure radial-layout tests before the constellation module and a rendering contract that
proves the Timeline mounts only the opt-in variant after record selection. Run the same
frontend, localization, build, formatting, spec and live visual gates. Rollback removes
the variant and its Timeline mount without affecting the Record graph or data.

For the desktop split refinement, keep transient preview and pinned selection as separate
adapter state. Wrap the recorder and existing constellation in a responsive CSS grid; no new
read or graph model is introduced. A delayed member hover changes only the preview root and
pointer exit falls back to the pinned root. Click changes the pinned root. Suppress the
recorder's duplicate focused-node/edge layer whenever the constellation is active. Mobile
keeps document order and stacks the same panes. Rollback restores the single-column mount.

The split-layout regression fix clamps orbit cards against the recorder element's measured
scroll viewport (`scrollLeft` plus `clientWidth`), not the full timeline paper. The existing
Inspector rows are deduplicated by opaque linked-record kind and ID before radial positioning;
this changes presentation only and preserves the original rows and navigation targets.

The final composition replaces the sprawling sixteen-card orbit with a six-record paginated
selection cluster anchored inside the measured recorder viewport. Opening a pulse expands the
aggregate lane layout to a bounded minimum height. The constellation uses a compact control row,
one spacious ring for up to eight unique links, and a bounded canvas. A shared close function is
used by the cluster, the right header and Escape; unpin remains a separate record-only action.

Owner review rejected the remaining orbit/constellation metaphor. The final adapter keeps the
Timeline unobstructed and renders all exact pulse members in the right detail pane. Selecting a
member replaces that list with a deterministic three-column relationship trace: origin/reference/
source/evidence links on the left, the selected record in the centre, and Reality/event links on
the right. The trace reuses the same unique Inspector links; no relationship direction or business
meaning is persisted or inferred beyond the existing Source → Evidence → Reality presentation.

The final owner review also rejects the competing desktop split. Keep the Timeline full width and
compact, followed by a semantic ERP-style table of the selected pulse's exact records. Selecting a
table row replaces the table with the existing directed relationship trace below the Timeline.
No hover read, new endpoint, persistence or business rule is introduced.
