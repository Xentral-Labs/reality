# Verification and review

2026-09-10, isolated worktree based on main 7f84c18:

- Layout unit tests (`apps/web/scripts/flight-recorder-layout.test.mjs`): interval choice
  at the 6-hour and 3-day boundaries, per-interval columns, eight-row stacks with
  sub-columns that widen the column, label steps on six-hour boundaries with day starts,
  compact earlier-reference area, empty graph. Written before the module; they failed on
  the missing module and pass with it.
- Frontend contract suite: 81 passed, zero failures (includes the unchanged
  `flight-recorder-graph` tests; `buildFlightGraph` is untouched).
- TypeScript/Vite production build passed; the existing chunk-size warning remains.
- Localization audit passed in English, German, Dutch and Spanish (1221/1221); four new
  keys for the interval and stacking strip, the unused "Spacing follows recording order"
  key removed from all dictionaries.
- Prettier on changed files and spec policy passed.
- Browser check against the worktree dev server with the spec 138 recorder fixtures
  (21 events over two recording days, older-read failure, retry, selection, Details):
  a compact first page auto-requests older history until the band overflows; the failed
  older read shows the retry state with 20 events kept; the 15-minute raster is announced;
  twenty events in one interval stack in eight rows and three sub-columns with a distinct
  cell each; retry prepends the older day, switches to the hourly raster with six-hour
  labels and day marker, and keeps the viewed anchor (scrollLeft ≥ 200); selecting the
  source dot draws its incident edges and opens Details; dark theme renders lane colours
  on the dark surface; at 390px the page does not scroll horizontally. Screenshots
  reviewed (desktop light and dark).
- Second pass after the owner reviewed the live tenant (paper ended at the last record, the
  burst sat at the far left, no recorder feel): the axis now runs to the present with a now
  mark and fills the band, lanes draw a baseline trace, every held reference is a faint
  stitch, newest events refresh every 30 seconds, the view opens on the newest record, and
  older pages are anchored to the instant at the left edge. Layout tests extended (paper to
  now, minimum columns, instant↔pixel round trip; 6 tests). Focused browser check re-run:
  hourly raster to now, older load from the left edge, failure and retry, daily raster after
  the older day arrives with chronology kept, traces and stitches drawn, now mark present,
  selection, Details, dark, mobile. The spec 138 suite's pixel-anchor assertion was replaced
  by the raster semantics (paper fills the band; older day left of newer).
- Rendered with the 247 real events of the local Northstar tenant served as fixtures: one
  hourly column at 21:00 holds the seed burst in widened stacks, stitches fan from the
  source records to their documents and commitments, the paper runs empty to the now mark
  the next morning. This is the true recording history of that tenant.
- Zoom added on the owner's request: six raster levels behind zoom in/out buttons, centre
  instant kept, buttons disabled at the ends; layout test for the override and label steps
  (7 tests); focused browser check zooms out to a day raster and back in and asserts the
  strip wording and the centred instant.
- Hover card added on the owner's request: the record card opens next to a hovered or focused
  dot as a non-interactive overlay; the focused browser check hovers a dot and asserts the card
  with kind, label and recorded time.
- Controls moved from the page heading into the widget's own toolbar on the owner's request
  (Load older events, Latest events, zoom in, zoom out beside the interval strip); focused
  check re-run green.
- `unified-inspector-browser.mjs` fails on this base before reaching the recorder section
  (`getByText('No matching records')` strict-mode violation at line 497). Reproduced with
  this change stashed, so it is pre-existing and not a regression; its recorder section
  was re-run as the focused browser check above.

Cross-artifact review: FR-001–005 map to T001–T004 and US1–US3; no unresolved clarification,
critical finding or Constitution exception. The diff contains the layout module and its
tests, the recorder rendering, lane tokens in both themes, four localization keys,
`docs/WEB_SPEC.md`, the coverage matrix and this spec. Reads, references, selection
semantics, Inspector and tenant scope are unchanged.

## Aggregate seismograph refinement — 2026-09-10

- The owner approved one aggregate pulse per lane and recording interval, stronger visual
  intensity for larger counts, and removal of the default grey connection web.
- Tests were added first and failed on the absent pulse contract. The final focused suite
  has 12 passing tests covering exact grouping and membership, earlier references, bounded
  logarithmic diameter/opacity, fixed-width aggregate columns, compact five-lane height,
  pulse rendering, member drill-down and edge suppression until record selection.
- The complete frontend contract suite passes 92/92. The localization audit passes
  1456/1456 in English, German, Dutch and Spanish. TypeScript/Vite production build,
  Prettier, spec policy and diff whitespace checks pass; the existing Vite chunk-size
  warning remains informational.
- The web image was rebuilt and restarted in the preserved local stack. Visual inspection
  against the live Northstar tenant showed all five compact lanes together, pulse counts
  from 4 through 247 with bounded intensity, no overview relationship lines, a bounded
  57-record drill-down, and exactly three explicit incident connections after selecting
  one SourceRecord. The existing Details route remained available.
- No API, read, schema, migration, service, tenant scope, identity or business-authority
  behavior changed. Aggregation remains a read-time presentation observation.

## Connection constellation refinement — 2026-09-10

- Selecting an exact record from a pulse now replaces the member list with an opt-in
  spatial constellation. The chosen record is centered; its direct Inspector links are
  arranged deterministically on bounded radial rings and connected with explicit colored
  lines. No inferred or transitive relationship is introduced.
- Opening a linked bubble re-centers the same view on that record and loads its own direct
  links through the existing tenant-scoped Inspector read. Back restores the prior center;
  Inspect and zoom remain available. The standard Record graph variant is unchanged.
- Tests were written first for the radial layout and Timeline mount. The complete frontend
  contract suite passes 95/95, localization passes 1458/1458 in each of English, German,
  Dutch and Spanish, and production build, Prettier, spec policy and diff whitespace checks
  pass. The existing Vite chunk-size warning remains informational.
- The preserved local stack was rebuilt on port 8080. Live Northstar verification covered
  pulse → SourceRecord → constellation, re-centering from the source to its Document, the
  Document's direct item and commitment links, and Back navigation. A transient failed read
  during the web-container replacement was retried after the container became healthy; the
  stable deployed flow then passed.

## In-place pulse orbit — 2026-09-10

- Pulse selection now opens up to 16 numbered, accessible member bubbles directly around
  the pulse inside the recorder. The former below-recorder member list is removed. Larger
  pulses use a `+N` orbit control to cycle through bounded pages without hiding records.
- Each orbit bubble carries the exact record kind and business label as its accessible name
  and tooltip. Selecting it closes the orbit, restores the existing exact-record focus and
  opens the Connection Constellation without another intermediate click target.
- The focused contract failed before implementation and now passes. The complete frontend
  contract suite passes 95/95; all four localization catalogs pass 1466/1466. Targeted
  formatting, production build, spec policy and diff whitespace checks pass. The global
  frontend format gate is temporarily red only because the unrelated concurrently modified
  `finance-settings-dialog-browser.mjs` is not formatted; it was deliberately left untouched.
- The web image was rebuilt and only the web container was replaced (`--no-deps`) on port 8080. Live Northstar verification opened the 16-record Reference pulse, exposed all 16
  business-partner orbit bubbles in the graph, and opened Brightwater Home directly into
  its 14-link Connection Constellation.

## Readable orbit and immediate graph — 2026-09-10

- Numeric orbit dots were replaced by 144×38 px compact cards showing the localized record
  kind and original business label. Sixteen cards remain bounded in two columns around the
  selected pulse; overflow paging is unchanged.
- A deliberate 320 ms pointer hover now makes the same exact-record selection as click and
  starts the tenant-scoped Inspector constellation read. Click remains immediate and keyboard
  activation remains available without focus-triggered navigation.
- The former full-width selected-record strip was removed. Its essential name, kind, direct
  link count and actions now sit in a compact constellation header, and selection scrolls the
  graph to the nearest visible position.
- Focused orbit/constellation contracts, localization and the production build pass. The
  web-only image was rebuilt and only the port-8080 web container was replaced; API,
  migrations and database were not restarted. Live verification showed all 16 named Business
  partner cards and a direct transition to Brightwater Home's 14-link constellation with no
  intervening detail strip.

## Responsive timeline/constellation split — 2026-09-10

- Opening a pulse now reserves a stable desktop 3:2 split: the recorder and readable orbit
  stay on the left, while the right pane explains hover/click until a graph is active. This
  prevents the hovered card from moving when preview appears. Below 1024 px the panes retain
  document order and stack.
- Deliberate hover updates separate transient preview state after 320 ms; pointer exit clears
  only that preview and restores any pinned graph. Click pins the member, keeps its orbit card
  marked and leaves graph-node re-centering click-only.
- The recorder no longer renders focused individual nodes, off-screen controls or blue
  relationship edges while the constellation owns relationship exploration. This removes the
  duplicated graph language visible in the prior vertical composition.
- The focused split contract failed before implementation and now passes. Production build and
  all four localization catalogs pass. The web-only image was rebuilt and only the web
  container on port 8080 was replaced; no API, migration or database service was restarted.
  Live Northstar verification covered pulse opening, stable named orbit, click pinning and the
  right-hand Brightwater Home constellation with the left card still marked and no duplicate
  timeline detail layer.

## Split clipping regression — 2026-09-10

- The reviewed desktop state exposed two layout defects: orbit cards were clamped against
  the complete scrollable paper and disappeared beneath the right pane, while repeated
  Inspector rows created overlapping constellation nodes for the same linked record.
- A regression contract was written first and failed on both absent safeguards. Orbit
  placement now uses the recorder's measured `scrollLeft + clientWidth` boundary and falls
  back to one column when two cards cannot fit. Constellation input is deduplicated by the
  linked record's kind and opaque ID before bounded radial positioning.
- The complete frontend contract suite passes 97/97; localization passes 1482/1482 in all
  four languages. Production build, targeted formatting, spec policy and whitespace checks
  pass. The existing Vite chunk-size warning remains informational.
- The web image was rebuilt and only the web container on port 8080 was replaced. API,
  migrations and database services were not restarted.

## Aligned split headers — 2026-09-10

- The Timeline toolbar previously spanned the full widget while the constellation header
  began below it, so their controls and canvases had unrelated vertical origins.
- Both sides now own matching pane-local headers. Desktop gives them the same minimum height
  and bottom-aligns their primary control rows; mobile removes the forced height through the
  existing breakpoint. The recorder raster and graph work area consequently begin on one
  shared horizontal axis.
- A rendering regression contract covers the two local headers. Focused tests and the
  TypeScript/Vite production build pass; the existing bundle-size warning remains
  informational.

## Designer-led focus-mode composition — 2026-09-10

- A separate UI/UX review identified three competing levels: Timeline overview, pulse members
  and record relationships. Sixteen loose cards across the lanes and ambiguous Clear selection
  semantics made those levels hard to leave or understand.
- Pulse members now open in a bounded six-record selection cluster with paging and its own
  close action. The right header separates Unpin record from closing the complete focus mode;
  Escape uses the same complete close path. Hover remains reversible preview and click remains
  pinning.
- Active recorder lanes expand to a 620 px bounded work area. The constellation removes the
  redundant Inspect button and disabled Back state, uses smaller nodes and a spacious 520 px
  single ring for up to eight unique links. Both panes retain matched 128 px headers.
- Focused layout and rendering tests and the TypeScript/Vite production build pass. No API,
  service, persistence, authority or tenant behavior changed.

## Pulse inspector and directed relationship trace — 2026-09-10

- Owner review rejected the remaining orbit metaphor. Pulse selection now leaves the Timeline
  unobstructed and shows every exact member as a scannable list in the right detail pane. Hover
  is label-only; click opens the selected record.
- The radial constellation was removed. Its replacement is a deterministic three-column trace:
  evidence/origin links, selected record, operational consequences. Nodes are readable cards,
  lines are short and directional in layout, and unique Inspector links remain the only edges.
- Back to pulse restores the list; Details opens the existing Inspector; the header close action
  and Escape close the complete focus mode. The obsolete radial layout module was removed.
- Focused tests cover side classification, list/trace state, absence of orbit rendering and
  hover-driven graph loading. Localization and the production build pass. No backend contract,
  tenant boundary, persistence or authority changed.

## Stacked ERP record drill-down — 2026-09-10

- Owner review rejected the competing desktop panes. Timeline, pulse contents and relationship
  trace now form one vertical reading order at every breakpoint; opening a pulse never narrows or
  artificially stretches the recorder.
- The pulse contents are a compact semantic table with record type, business label, secondary
  opaque ID, recorded time and an explicit Open action. Hover remains inert; click or keyboard
  activation opens the existing relationship trace, and Back returns to the table.
- The obsolete responsive split CSS and matched pane-header sizing were removed. Contracts were
  written first and failed against the prior split. All 99 frontend contracts, 1484 localization
  keys in four languages and the production build pass.

## Readable pulse lane spacing — 2026-09-10

- Live review found the compact five-lane recorder vertically cramped. Aggregate lanes now use
  a 60 px minimum instead of collapsing to the pulse diameter plus padding.
- The recorder gains 60 px overall breathing room while remaining far below the removed 620 px
  focus-mode height. A regression assertion failed first and now fixes the intended proportion.
