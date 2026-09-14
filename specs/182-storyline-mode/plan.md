# Implementation Plan: Storyline Mode

**Branch**: `182-storyline-mode` | **Date**: 2026-09-12 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/storyline-package.md](contracts/storyline-package.md),
[contracts/storyline-api.md](contracts/storyline-api.md).

## Summary

Storyline mode reuses the Playground run and step engine as its chapter engine, practice
companies as its sandbox, the proposal path as its only write path and the ordinary app pages
as its middle zone. It adds four things the spec names: a declarative storyline package with a
validator and a per-account library, a bounded call trace per run, a delta read after a
sequence marker, and a Storyline page in the unified app with narrator, embedded view and
protocol. Two chapters of the shipped story, dunning and period close, have no command today
(research R7); see [Open decision](#open-decision-for-the-owner).

## Technical Context

Python 3.12, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI; React and TypeScript in
`apps/web`; VitePress docs. Tests: pytest against isolated PostgreSQL (`session` fixture),
Node contract tests and Playwright scripts in `apps/web/scripts`, Node docs contracts. Bounds:
trace ≤ 2 000 entries per run, ≤ 16 KiB per entry; package ≤ 200 000 bytes; delta read
answers within the Inspector bound of spec 179 for a practice company (SC-006); no polling
below 10 s (HomePulse precedent).

## Open decision for the owner

FR-014 originally named seven chapters, two of which cannot run today:

- **Dunning notice**: no command, no document type, no event.
- **Close period**: no command and no period record; "carries open exceptions into the next
  period" has no substrate.

Both are business features with their own schema questions (a dunning document, a period
record) and belong in their own specs under Constitution III. The owner chose **assumption A** and approved the schema on 2026-09-12 (T003). The hand-play
(research R8) then reshaped the story to eleven chapters; FR-014 was amended accordingly.
Assumption A as recorded:

> Storyline v1 of *Order to close* ships with the five command chapters that exist today
> plus two read chapters in the same positions: chapter 4 **Explain the hold** (a read of the
> `party_hold_unreleased` finding and its cause, showing that reads are traced too) and
> chapter 7 **Month-end review** (a read over open findings and open commitments that names
> what would be carried into October). Dunning and period close become follow-up specs; when
> they land, *Order to close* version 2 replaces chapters 4 and 7 with the real commands, which
> the package versioning (FR-020) already allows.

Follow-up specs: `183-dunning-notices` and `184-period-close` (stubs in this branch). The
engine, the trace, the delta, the library and the page do not depend on them.

### Chapters of Order to close, version 1 (research R8, analysis T004)

The authored package is `packages/reality-core/storylines/order-to-close.storyline.yaml`; it
validates against the catalogs with all four languages. Default path in order:

| # | Chapter key | Command or read | Expected delta |
| --- | --- | --- | --- |
| 1 | `order` | `order_create` sales, 12 of an item with 8 on hand | ▲ `outgoing_commitment_at_risk` |
| 2 | `reference` | `fact_observe` `order.customer_reference` on the order document, source = the order's source record | + Fact |
| 3 | `receipt` | `movement_create` receipt 16 against the seeded purchase commitment of 20 | `overdue_incoming_supplier_commitment` stays with 4 open |
| 4 | `reserve` | `reserve` | ✓ `outgoing_commitment_at_risk` |
| 5 | `dispatch` | `movement_create` shipment | refused at preparation: customer hold; branches `explain-hold` (default), `call-customer` |
| 6 | `explain-hold` (read) | `exception_explain` on `$exception.overdue_receivable.<seed invoice>`, `finance.party_balances.list` | nothing written; requires `overdue_receivable` present |
| 7 | `overpayment` | `finance.settlement.apply` payment 1 300, allocation 1 180, `expected_revision` from context read `finance.settlement.context` | ✓ `overdue_receivable`, ▲ `unmatched_financial_event`, credit 120 |
| 8 | `release-hold` | `party_delivery_hold_release` | hold gone from blockers |
| 9 | `ship` | `movement_create` shipment | ▲ `shipped_not_billed` |
| 10 | `bill` | `sales_invoice_record` from the order line | ✓ `shipped_not_billed`; branches `allocate-credit` (default), `refund-credit`, `keep-credit` |
| 11 | `allocate-credit` | `finance.settlement.apply` allocate_credit 120 to the new invoice, credit document from context read `finance.credits.list` | ✓ `unmatched_financial_event` |
| 12 | `supply-check` (read) | `inventory`, `commitments` | branches `reorder-40` (default), `reorder-20`, `wait` → month-end |
| 13 | `reorder-40` | `order_create` purchase 40 | new supplier commitment |
| 14 | `month-end` (read) | `exceptions`, `finance.party_balances.list`, `commitments` | lists what remains |

Alternatives: `call-customer` (read), `refund-credit` (`finance.settlement.apply` refund_credit),
`keep-credit` (read), `reorder-20`. Every `$chapter` reference names a chapter on every path
(the validator checks dominators), so no branch can skip an output a later chapter needs.

## Constitution Check

| Principle | Design evidence | Gate |
| --- | --- | --- |
| I. Source → Evidence → Reality | Chapters run ordinary commands; the seed history runs ordinary commands under the profile scope. No new evidence chain. | PASS |
| II. Reality is the authority; no human numbers as identity | Packages carry symbolic references only (`$ref`, `$company`, `$seed`, `$chapter`, `$context`, `$exception`); the resolver maps them to opaque ids at run time and refuses raw ids. Trace and delta reference records by opaque id. | PASS |
| III. Proven schema only | Additions in [data-model.md](data-model.md), each filtered or joined by core logic: `fact.recorded_at` (delta filter; exercised by the Fact chapter), three run columns (library, resume, branches), two step columns and a nullable proposal (delta filter, read chapters), table `storyline_trace_entry` (protocol read per run and chapter), table `storyline_package` (per-account library). Approved by the owner on 2026-09-12. | PASS |
| IV. Tenant and service boundaries | Trace and step tables are tenant-scoped with composite FKs to the run; the package table is account-scoped by design (FR-018) and never joins business data. Web, MCP and Chat reach chapters through `services/storyline.py`, which calls the Playground and proposal services. No ORM writes from adapters. | PASS |
| V. Specification and test evidence | Every FR maps to tests and tasks in [tasks.md](tasks.md); tests precede implementation. | PASS |
| VI. Explainable web product | The middle zone is the ordinary page; the protocol links every item to Inspector, Facts register, Exceptions page and Context Graph. No business rule in the browser: raised and cleared are computed server-side. | PASS |
| VII. Simplicity and storage discipline | No new dependency, no broker, no request log for business tenants. The recorder is active only for tenants whose run carries a storyline key. Alternatives rejected in [Complexity Tracking](#complexity-tracking). | PASS |
| VIII. Received values recorded, never recomputed | The delta compares stored records; raised and cleared are a comparison of two derived snapshots, never stored as a finding. The exception snapshot on the step is a marker, not an authority. | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/182-storyline-mode/
├── spec.md
├── plan.md                      # this file
├── research.md                  # facts from the code
├── data-model.md                # schema additions and rollback
├── contracts/
│   ├── storyline-package.md     # the package format and its validation
│   └── storyline-api.md         # HTTP surface
├── tasks.md
└── quickstart.md                # evidence, written during implementation
```

### Source code

```text
packages/reality-core/
├── storylines/
│   └── order-to-close.storyline.yaml            # built-in package (shipped in the wheel like config/)
├── src/reality/
│   ├── storyline/
│   │   ├── __init__.py
│   │   ├── package.py            # Pydantic contract, loader, catalog validation, JSON Schema export
│   │   ├── references.py         # $ref / $chapter / relative date resolution, raw-id refusal
│   │   ├── recorder.py           # trace scope (ContextVar), HTTP recorder, run_read_tool hook, bound
│   │   ├── delta.py              # delta read after a marker: events, facts, records, exceptions, graph
│   │   └── export.py             # run → draft package
│   ├── services/storyline.py     # start/resume, chapter prepare/confirm/reject, branch, library
│   ├── services/playground.py    # generic storyline branch in prepare_step; marker capture in confirm_step
│   ├── services/core.py          # timeline_activity(after_sequence=…); observe_fact sets recorded_at
│   ├── tools/application.py      # run_read_tool calls the recorder hook
│   ├── web/storyline_api.py      # /api/storyline (library) and /api/tenants/{t}/storyline (run)
│   ├── web/api.py                # recorder dependency on the tenant router; labels on application-reference
│   ├── db/core.py                # columns and tables from data-model.md
│   └── catalogs.py               # load_catalog_labels() for commands and views per language
├── migrations/versions/0058_storyline.py
└── tests/
    ├── test_storyline_package.py
    ├── test_storyline_runs.py
    ├── test_storyline_trace.py
    ├── test_storyline_delta.py
    ├── test_storyline_library_api.py
    ├── test_storyline_export.py
    └── scenarios/test_storyline_order_to_close.py

apps/web/src/
├── unified/StorylinePage.tsx          # three zones, resume, presentation mode
├── unified/StorylineNarrator.tsx      # chapter list, situation, preview, explanation, branches
├── unified/StorylineStage.tsx         # embedded page with local header targets and row marking
├── unified/StorylineProtocol.tsx      # calls and delta, tool explanation, links
├── unified/StorylineLibrary.tsx       # built-in and imported packages, download, import
├── unified/storylineState.ts          # phase machine, marker bookkeeping, presentation timer
├── unified/routing.ts, UnifiedApp.tsx, Shell.tsx, pageIntroduction.ts, entryRouting.ts
├── api.ts, localization.tsx
apps/web/scripts/
├── storyline-browser.mjs, storyline-contract.test.mjs

apps/docs/
├── scripts/generate-catalog-reference.py   # storylines page (EN, DE), public/storylines/*.yaml, schema
├── content/storylines/index.md, content/de/storylines/index.md
└── content/public/storylines/               # generated copies for download
```

**Structure decision**: one new backend package `reality.storyline` for the parts that are new
(package, references, recorder, delta, export), one new service module for orchestration, one
new router. The chapter engine stays in `services/playground.py`; the storyline service calls
it. The web gets one destination with four components. Nothing is named `playground` in
`apps/web/src` (product boundary test).

## Design

### 1. Package and library

The package contract ([contracts/storyline-package.md](contracts/storyline-package.md)) is a
Pydantic model with `extra="forbid"` and a byte bound, like `ProfileManifest`. `package.py`
validates a document in four passes: shape, catalog names (commands through
`load_application_catalog()` and the MCP registry, views through `workspace_catalog.yaml`,
exception classes and Fact predicates through their catalogs), references (`$ref` against the
seed, `$chapter` against earlier chapters, `next` and branches against chapter keys, exactly
one default branch), and bounds. Errors are collected and reported together (SC-008).

Built-in packages live in `packages/reality-core/storylines/` and are force-included in the
wheel like `config/`. A contract test loads every built-in through the validator. Imported
packages are stored per account in `storyline_package` as received, with the validation
result, a checksum and the origin. The library read merges built-ins and the account's rows.
Export returns the stored document for imports and the file for built-ins. Import is a raw
body `POST` with `filename` like the item import artifact path; YAML and JSON are accepted;
the size bound is checked before parsing.

`package.py` also exports the JSON Schema of the contract; the docs generator writes it to
`content/public/storylines/storyline.schema.json` together with a copy of each built-in file
and the EN and DE Storylines pages. A package may name the Tool Usage `process` it plays; the
generated process page then links the storyline (FR-016).

### 2. Run, seed and chapters

A storyline run is a practice Playground run: `start_run(sandbox_kind="practice",
preset_key="storyline", company_name=<title>)` with `storyline_key` and `storyline_version`
set on the run. `find_preset` gains the `storyline` preset. Seeding replaces the profile
seed: `services/storyline.py` resolves the seed's parties, items and locations through the
ordinary create services under `_profile_scope`, then plays the seed history in order as
executed proposals with `effective_at` or `occurred_at` derived from the relative dates,
inside the same `begin_nested()` block `initialize_profile` uses. The resolved ids are written
to `initialization_progress["storyline"]["refs"]`, bounded like the profile references. Any
failure resets the run to `initialization_failed` with the failing history entry in the
error (edge case).

A chapter is a Playground step. `prepare_step` gains a storyline branch: when the run carries
a storyline key, the tool is any command of the catalog with `propose` or `confirm` access,
arguments are the chapter's declared input resolved by `reality.storyline.references`
(context reads performed first, in order, and recorded in the trace), and `lesson_step_key`
holds the chapter key. Before the proposal is created the service records the marker:
`marker_sequence = latest_sequence`, `marker_at = now()`, and the current exception
identities into `before_observation["exceptions"]`. **Confirmation and rejection go through
the storyline routes to `confirm_step` and `reject_step` only** (analysis C1): the narrator
renders the prepared proposal's review with confirm and reject controls; it does not open the
ordinary action card, whose confirm path would bypass the step receipt and the step-level
idempotency. The receipt already lists records and the last event sequence. Branch choices
are stored in `storyline_state["branches"]` on the run; nothing else about progress is stored.

Chapter status is derived (analysis H6):

| Status | Rule |
| --- | --- |
| done | the chapter has a step whose proposal is `executed`, or a completed read step, or a step whose preparation was refused (`before_observation["refused"]`) |
| current | the first chapter, or the successor of the last done chapter following `next` and the recorded branch (default branch when none recorded) |
| upcoming | everything after current on the default continuation |

A chapter may have several steps (a reject or a failure allows a retry with a new request
key); it cannot be *confirmed* twice because the executed proposal's step is unique per
chapter key on a run. After a chapter whose preparation was refused, the chapter counts as
done and the story continues; the person may also retry it once the cause is gone.

Read chapters are steps without a proposal: they record the marker and the trace of the
reads and complete immediately; their reads are live reads or the explicit live mode of a
stored projection (R8). A chapter whose preparation the system refuses (chapter 4) keeps its
step with the marker and the refused call in the trace; the narrator shows the refusal as the
chapter's outcome. Chapter inputs may name `$context.<read>.<field>`: the service performs the
read at prepare time, records it in the trace and substitutes the value. The step row needs `proposal_id` nullable for
this; see data-model.md.

### 3. Call trace

`recorder.py` holds a `ContextVar` scope `trace_scope(tenant_id, run_id, step_id | None)` and
one function `record(kind, name, access, input, result | error, duration_ms, actor)`. Three
producers:

- An HTTP middleware in `web/app.py` (analysis M2: a dependency cannot see the response):
  for `GET` requests on tenant routes it records, after the response, the route template,
  the path and query parameters and the status code, never the body, as a `view` entry.
  It decides per tenant through a per-process cache with a 30 s TTL that the storyline
  service also resets on run start and archive. Business tenants pay one cache lookup per
  request. The middleware also marks the context as an HTTP request so tool entries can
  say `person`.
- The dispatcher itself, wrapped in `tools/application.py`: `run_read_tool`,
  `create_change_proposal`, `approve_and_execute_proposal` and `reject_proposal` record
  `read`, `propose`, `confirm` and `reject` entries with input, result or error, duration
  and proposal id whenever the tenant belongs to a storyline run, whichever adapter called
  them (web, MCP, Copilot, CLI). A confirmation captures its marker and the open findings
  before it executes, so a free-play confirm has its own delta. The wrappers are inert for
  every other tenant and never break the call they explain.
- `services/storyline.py` enters `trace_scope(step_id=…)` around prepare, confirm and
  reject, so those entries carry the chapter.

Entries go to `storyline_trace_entry`, tenant-scoped, FK to the run and optional FK to the
step. Inputs and results are stored as bounded JSON (≤ 16 KiB, truncated with a flag); the
run keeps at most 2 000 entries and deletes the oldest beyond that. Free-play confirms carry
their own marker (`marker_sequence`, `marker_at`, `before_exceptions`) so their delta can be
read without a step (analysis M1). Implemented in `reality/storyline/recorder.py` with tests
in `tests/test_storyline_trace.py` (T007, T010).

### 4. Delta read

`delta.py` answers `GET /api/tenants/{t}/storyline/delta?after_sequence=&after_at=&record=`:

- events: `timeline_activity(after_sequence=…)`, which gains a forward mode (ascending,
  bounded, same enrichment);
- facts: `Fact.recorded_at > after_at` for the tenant, ordered by `recorded_at`, as subject,
  predicate, value with the register link;
- records: the receipt's `records` for a step, otherwise the distinct subjects of the events
  after the marker that did not exist before it (creation events in the event catalog);
- exceptions: current identities compared with the step's `before_observation["exceptions"]`
  (or, for a free-play marker, with a snapshot the recorder took before confirm); each raised
  or cleared item carries the class label and the catalog's `clears_through`;
- graph: the primary record's one-hop neighbourhood, composed from the typed explorer read
  in `services/inspector_register.py` and `services/delivery_reads.py` (never from the
  `web/api.py` builders, analysis M3), with nodes and edges marked new when they touch a
  record created after the marker. No new link table.

Nothing is stored. A marker older than the timeline retention is answered with
`range.available=false` for the truncated part.

### 5. Web page

`/app/storyline` is a destination with `storylineRun`, `storylineChapter` and `storylineView`
in the selection. `Shell` receives `dock="none"` for this route so the chat dock stays closed,
and a nav item under Company for sandbox and demo companies plus a home card open it.

`StorylinePage` owns the phase machine (`idle → preview → done | refused`) per chapter
and, later, the presentation timer. The narrator prepares a chapter through the run API and
renders the prepared proposal's arguments as the preview with confirm and reject through the
storyline routes (analysis C1); after a chapter runs the page stays on it until "Next
chapter". The stage reads the view the chapter names through the shared live reads
(`readLiveView`, extended with orders, open items, inventory and blockers) and marks the rows
that name a record or Fact of the delta; the full page is one click away. Mounting whole
page components was dropped while implementing: their register headers portal into the
shell header (research R6). The protocol reads the trace and the delta once per phase change
and every 10 s while a chapter is in preview, using the `HomePulse` guard set. The Shell keeps
the chat dock closed on this route and offers Storyline under Company for every company; a
company without a run shows the library, and starting a run opens its practice company.

Tool explanations come from one tenant route, `GET …/storyline/tool-reference/{name}`
(analysis M4), which reads the runtime catalog and `catalogs.load_catalog_labels()` (labels
per language from the resource catalog: German today, English fallback, spec 178 precedent)
and returns the docs link built like `RealityInspectorPage` builds it, pointing at
`/tool-usage/commands#command-<key>` through `languageHref(..., true)`. Free play is a
browser-only mode (analysis M9); every confirm outside a chapter is free play by definition
and the server returns no flag for it. Expected findings are shown as expected against
observed and never block the run (analysis M6). After the seed and after every confirm the
storyline service refreshes the practice company's stored projections through
`services/projections.refresh_operational_projections`, so the stage can show the blockers
view without waiting for the background job (analysis M7); the company is small by
construction.

### 6. Export of a run as a draft

`export.py` walks the run's confirmed proposals in sequence, rewrites ids that match the
resolved seed refs to `$ref.<group>.<name>`, ids that match a record created by an earlier
proposal to `$chapter.<key>.output.<field>` (using the receipt's `records`), dates to
day offsets from the run's `created_at`, and emits chapters with empty text fields marked
`missing: true`. Commands whose arguments contain an id it cannot rewrite are emitted as
`unsupported` at their position. The draft validates except for the missing texts.

## Migration and rollback

Migration `0058_storyline` adds the columns and tables in [data-model.md](data-model.md).
`fact.recorded_at` is added nullable, backfilled from `observed_at` in batches, then set
`NOT NULL` with `server_default now()`. Downgrade drops the two tables and the new columns; it
refuses while any run carries a storyline key, as 0057 refuses while internal runs exist, so
history is not silently lost. No business payload is rewritten. Operational rollback: hide the
destination and stop the recorder by feature flag `REALITY_STORYLINE_ENABLED` (same shape as
`REALITY_PLAYGROUND_ENABLED`); the additive schema stays.

## Verification

Backend: `make spec-check`, Ruff, the full pytest suite on isolated PostgreSQL including the
new files and `test_application_catalog.py` (counts unchanged under assumption A), migration
upgrade and downgrade on `postgres_database`. Frontend: build, `i18n:audit`, contract tests,
the new `storyline-browser.mjs` at 1440 px and 390 px in four languages with mocked API
(overflow 0, no page errors, no writes outside confirm). Docs: regenerate, docs contracts
(DE twin, link test), build. Scenario: `tests/scenarios/test_storyline_order_to_close.py`
plays the built-in storyline end to end through the service and asserts SC-002 and SC-003.
Evidence goes to `quickstart.md`; no task is marked done on red.

## Complexity Tracking

| Addition | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| `storyline_trace_entry` table | FR-004 needs reads recorded per run and chapter, including Copilot and MCP reads, readable after reload | A browser-side list cannot see Copilot or MCP reads and vanishes on reload; a JSONB list on the step has no home for free play and would exceed the 64 KiB bound in one session |
| Per-account `storyline_package` table | FR-018 stores imports per account and lets them outlive the practice company | Files only would lose the library on the next device; a tenant-scoped table would tie a storyline to one company, against spec 104's ownership model |
| `fact.recorded_at` column | FR-005 filters Facts after a marker; Facts have business time only | Filtering by `observed_at` mixes business time with recording time and misses backdated Facts written in the chapter |
| Recorder dependency on the tenant router | Web views never pass `run_read_tool`; the router dependency is the one place every tenant read passes | Instrumenting each page's fetch in the browser duplicates every endpoint and cannot be trusted after reload |
