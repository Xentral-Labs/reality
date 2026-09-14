# Learning Playground

## Continuing a sandbox

The left cockpit pane opens with **Business operations**, not an automatic stock
form. The same cards return after every completed operation: opening stock, sale
from existing stock, supplier purchasing/payment and customer returns. Opening stock is standalone. Card
selection/cancellation never creates or replaces a sandbox; pending proposals keep
their review and cannot be bypassed through the chooser. Progress is shown only
while an operation is selected. Planned workflows are disclosed separately.

After a completed sales lesson, **Start another operation** opens another customer
order in the same run. Existing inventory, obligations, receivables and history remain
visible. Additional opening stock can be recorded explicitly; it is not a supplier
receipt. Each mutation still uses a reviewed, confirmed shared command. The current
progress and invoice/payment evidence belong to the latest operation; the timeline
keeps earlier operations. **Start a fresh sandbox** is a separate confirmed reset of
context, not the normal continuation. A supplier order and linked goods receipts
can also be started after a completed operation in the same sandbox. Partial receipts
leave an incoming obligation and offer the remaining quantity; each receipt requires
confirmation. These steps use the ordinary purchase order and Movement commands.
After final receipt, the supplier flow offers invoice evidence and allocated payment.
Customer returns select a previously recorded shipment and reuse its Commitment/item/
location. Return, stated credit and refund are separate confirmed actions. Credit
lines point to their sales order line; no return silently generates money or reopens
the original delivery promise. The return card requires a recorded shipment.
Safety quotas remain; the workspace does not promise unlimited retained steps.

Authority: `specs/096-learning-playground/spec.md` and its approved implementation plan.
Status: private entry/reference slice implemented; full learning product and release remain pending.

## Implemented boundaries

Entry offers a new sandbox and six directly clickable recent sandboxes, with expansion
for the remaining loaded history. There is no duplicate scenario library or saved-run
select. New sandboxes use the standard reference preset; operation selection lives
inside the cockpit. Opening history and cancelling setup create nothing; confirmed
replacement preserves archived history. Pending retries retain their preset and key.
Existing partial-delivery presets remain readable and runnable. Sales, purchase-to-payment
and customer returns use shared commands in the same sandbox, not a simulator engine.
Accounting lessons remain outside this implemented increment.

Supplier payment and customer refund compose evidence, balanced postings and
settlement atomically, preserving the original currency and trusted action identity.
Failures roll back every child record even if a caller later commits. Supplier invoice
and return credit recording compose the shared evidence and posting functions; stated
amounts are never calculated from price. Return credit quantity is checked by the
shared returned-minus-credited reader. A full or partial payment/refund completes one
exercise; any remaining financial position stays visible in the shared open-items view.

The shared customer-payment command now records payment evidence, balanced ledger
entries and the invoice settlement allocation in one transaction. Allocation failure
rolls back the entire payment, and confirmed payments attribute their three events
to the trusted action identity. The trading cockpit now exposes a stated invoice
and an allocated payment after shipment. Invoice creation composes the shared source,
evidence and ledger services; the invoice line points directly to its billed order
line. Supplied totals are preserved, never recalculated. The current lesson records
one invoice per order line and one full or partial allocated payment; it does not
generate invoices, execute bank transfers or promise split-billing workflows.
Current open items and exceptions come from the normal finance readers. Generic
sandbox financial writes remain denied outside the exact owned, reviewed step.

Tenant purpose is immutable and defaults existing companies to `business`. Run and step
metadata preserve same-tenant proposal links and historical observations, not a second
inventory ledger or execution state.

Business-only services check persisted tenant purpose before accessing credentials,
creating provider clients or mutating external-access configuration. The check has no
owner/admin, auth-disabled or feature-flag override. It currently protects:

- Secret creation, replacement, resolution and revocation.
- Generic AI settings, legacy/vault key resolution and both generic provider call paths.
- MCP token creation and authentication, including pre-existing sandbox tokens.
- Source-system/capability configuration and connector-shell installation.
- Invitation creation, acceptance, resend and revocation; member removal.
- Invitation enqueue and actual delivery-token issuance, including previously queued work.
- All 80 core mutations enumerated by the existing tenant-isolation catalog.
- Generic proposal creation/confirmation/rejection, across all 62 mutating tools.
- Generic company archive, restore, permanent deletion and demo seeding.
- Reality Gap/rule mutations and file staging/interpretation before storage access.

A forbidden queued delivery becomes permanently failed with a safe policy error code.
It retains its evidence but issues no token, sends nothing and is not retried. Account
verification mail is a separate workflow and is not disabled by this business boundary.
The HTTP host renders this policy exception as 403 with `playground_operation_denied`.
Detached AI settings cannot resolve a key because their persisted tenant purpose cannot
be checked through an owning session.

## Shared run ownership

The shared run resolver now requires the actual owner, current owner membership,
verified email and an enabled account. A verified pending-production account may resolve
its own run. A platform administrator cannot take over another person's run. A write
eligibility check additionally requires an active run and non-archived tenant. This
resolver is not an execution permission and does not bypass the business-only guards.

Generic tenant HTTP endpoints now enforce that ownership independently of local
auth-disabled mode. Only explicitly listed inspection routes are readable for ready or
archived runs; generic writes, configuration and unknown surfaces remain denied. Verified
pending-production users may inspect their own runs but not their business tenants.
Normal company selectors and the platform company overview exclude sandboxes, including
for administrators and local mode.

## Causal event evidence

The shared event recorder now correlates all seven V1 handlers with their confirmed
proposal. Shipment records emit `reservation.consumed`, `reservation.created` for an
active remainder and `commitment.fulfilled` on the actual transition. These automatic
effects reference the Movement event through `causation_id` and commit with the records.
Consumption distinguishes the original Reservation quantity from the shipped portion;
a remainder is explicitly labelled `shipment_remainder`, not a new user reservation.
New source versions created by a confirmed manual action have `source_record.stored`
evidence; document events expose actual line IDs and the source link. Existing return
values and domain quantities remain authoritative. No additional Fact mirrors are written.

## Private initialization service

The internal `start_run` service now creates an owner-private trading-v1 run after explicit
confirmation and account verification. Account-scoped HTTP entry now delegates to this service;
the internal browser entry is connected, while lessons and public discovery are still pending.
Setup contains Acme, Müller, Huber, LightWorks, Augsburg and the three sample articles.
It creates no stock, order, Reservation, Fact or artificial source payload. The eight ordinary
reference events remain setup evidence, not user lesson steps.

Owner locking serializes concurrent starts. The same owner/request key returns the same run;
another key cannot implicitly replace an active run. Initial metadata is durable before seed;
references and readiness commit atomically. A safe `seed_failed` outcome retains the run without
partial data; the same key retries safely. Archived replay returns history without reseeding.
The temporary seed permission cannot commit midway, access another tenant, invoke business-only
services or perform lesson actions. It expires on scope exit, including failure.

Deployment configuration (not activated by this change):

- `REALITY_PLAYGROUND_ENABLED`: off by default; `true` or `1` permits confirmed start.
- `REALITY_PLAYGROUND_DAILY_RUN_LIMIT`: 5 new retained run records per user/UTC day by default.
- `REALITY_PLAYGROUND_RETAINED_RUN_LIMIT`: 20 retained runs per user by default.

Failed runs count toward limits. Retrying an existing key consumes no new slot and never deletes
history. These are run-creation limits only; applied-step/chat quotas remain pending.

## Authenticated HTTP entry

`GET /api/playground` returns only the current owner's runs with active owner membership,
newest first, bounded to 25 rows by default and at most 100. It includes the total, supported
preset/lesson version, remaining creation quotas and next UTC-day reset. Chat is explicitly
unavailable in this implementation stage. `GET /api/playground/runs/{id}` returns setup state
and the ready reference-ID map. Initializing/failed runs expose neither partial reference
maps nor an inspectable tenant ID. Missing and foreign runs share the same 404 response.

`POST /api/playground/runs` accepts a request key, supported preset/version and a strict boolean
confirmation. It accepts no caller-supplied user or tenant identity. It calls the shared start
service, returning actual setup status; a 200 response with `initialization_failed` is not a
ready dataset. Retrying its key can finish setup. Conflicts return 409, invalid input 422,
and exhausted quotas 429 with remaining capacity/reset guidance and a saved-run alternative.

All three routes independently require a real non-revoked, non-expired account session, even
in auth-disabled local mode. Current verification/account eligibility is rechecked. Pending
production users gain only this narrow lane, not production API admission. Disabling entry
does not remove owner access to retained run history. These APIs add no lesson execution,
provider invocation, restart, account-less CLI command or sandbox MCP token permission.

## Browser entry

The `/playground` browser entry has its own account-scoped navigation. It never mounts the
production company shell, loads its tenant preference or invokes its Copilot. Active/pending
users can see setup state, review/confirm a start or retry, select saved runs and read actual
Parties/Items/Locations. Unknown/read failures are not rendered as empty or zero data. New
entry disabled, loading, setup failure and archive states remain distinct. The page uses the
shared header and Tailwind primitives, all four product languages, and original-content
protection for business names/IDs. Request identity survives reload; local account return
paths are allowlisted. The page labels learning actions and chat unavailable.

## Storyline mode (spec 182)

A storyline is a business story played chapter by chapter in a practice company of its
own. Storyline runs are practice runs: the same `playground_run` row, quota, ownership and
tenant purpose, with `storyline_key`, `storyline_version` and a small `storyline_state`
(branch choices). Chapters do not use the Playground lesson scopes; they run through the
ordinary `create_change_proposal` / `approve_and_execute_proposal` path that practice
companies already admit, so a chapter is refused, held or executed exactly as the same
command would be in a business company. Read chapters call read tools and write nothing.

What the mode adds:

- **Packages.** `packages/reality-core/storylines/*.storyline.yaml` are the built-ins;
  accounts can import their own (`storyline_package`, private to the importing account).
  A package names its seed (parties, items, locations, terms, a backdated history), its
  chapters (command, symbolic input, view, texts in the UI languages, expected findings,
  branches) and is validated against the tool catalogs before anything is stored.
- **Recorder.** Every read, proposal, confirmation and GET view made in a storyline company
  is recorded in `storyline_trace_entry` (bounded per entry and per run), inside a chapter
  or outside one (free play). A confirmation carries a marker: the timeline sequence and
  the open findings before it.
- **Delta.** From a marker, the service reads forward: events after the sequence, Facts by
  `recorded_at`, records first seen, findings raised and cleared by snapshot difference and
  the record graph around the primary record. Nothing is stored for this; it is a read.
- **Free play and restart.** A person may leave the story, work in the company and come
  back; the protocol lists what they did and what each confirmation added. A chapter whose
  precondition no longer holds names the missing record or finding and offers a fresh
  company (a new practice run under the same quota; the old company is kept).
- **Presentation mode.** The page prepares, confirms, takes the default branch and
  advances on a timer through the same routes a person clicks; any interaction switches it
  off, and so does an error. It is one small control in the step card, not the main way
  through the story.
- **Draft export.** A run exports as a storyline draft: confirmed commands in order, seed
  identities as `$ref`, created records as `$chapter`, dates as day offsets, texts marked
  missing, unsupported commands named in place. The draft validates except for its gaps
  and imports once they are filled.

The storyline mode reaches the browser through the unified `storyline` destination; the
retired Playground browser UI stays retired.

## Remaining implementation

The shared internal `prepare_step` service supports the first opening-stock proposal. It
validates run ownership, positive exact quantities, active run-local item/location references
and explicit timezone-aware timestamps. A missing timestamp is resolved once and shown in the
preview. Proposal and step persist atomically; retries preserve both identities, while changed
intent conflicts. Preparation creates no Movement, Fact, Document, Commitment or business event.
The applied-step preparation cap defaults to 50 (`REALITY_PLAYGROUND_STEP_LIMIT`); unresolved
executing proposals block new preparation. Opening-stock confirmation now rechecks capacity.
Internal confirm/reject/read services use the existing proposal lifecycle and the verified owner.
Confirmation binds a preview revision and rechecks relevant stock/reference state. It stores the
before-observation before execution and verifies the resulting Movement through its correlated
event. Repeated confirmation never reexecutes. Rejection creates no domain effect.
Authenticated private HTTP routes now delegate to these services for prepare/detail/confirm/reject;
they accept only an owned run ID and never a tenant selector. The web UI still has no action controls.
Other lesson actions remain pending.

An internal run-lock primitive now keeps a dedicated PostgreSQL connection across service
commits and rollbacks. Contention returns busy; read access remains available. Current ownership
is checked before and after acquisition. Connection loss stops the operation, and physical
cleanup prevents a stranded session lock. The lock grants no mutation permission and has no
HTTP/tool adapter yet. The internal opening-stock decision service now uses it.

These guards do not constitute complete Playground isolation. Account-aware tool/CLI adapters and restart,
the remaining all-entrypoint drift audit, policy for subsequent lesson actions,
settling interrupted execution, full Facts/Exceptions/current-picture reads, chat quotas, the
remaining lesson, bounded managed chat and the full learning UI remain
pending. Do not create interactive runs or publish entry links on this foundation.

Generic sandbox mutation paths remain closed. Internal reference setup and explicitly confirmed
opening-stock steps are the only allowed domain-write paths. The decision scope is bound to the
session, connection, owner, proposal and exact Movement intent; it cannot grant other core tools
or egress. If execution is interrupted, actual Movement evidence may be visible while the proposal
remains unsettled; no action is retried. An executed action's unavailable observation can be
recovered without reexecution. New mutations wait for pending execution/observation, but owner
reads remain available. Stored before/after observations are historical, not live stock authority.

The eventual managed Playground provider context is deliberately separate from generic
company chat; the generic provider paths are currently denied for sandbox tenants.

## Evidence

`tests/test_playground_runs.py` and `tests/test_migrations.py` cover storage constraints.
The run suite additionally covers concurrent starts on separate PostgreSQL connections,
atomic seed rollback, interruption recovery, account eligibility, quotas and seed-permission limits.
`tests/test_playground_security.py` exercises direct services, legacy credentials/tokens,
queued delivery, generic HTTP with local authentication disabled, real CLI invocation,
canonical MCP dispatch and provider calls before HTTP-client creation. The core mutation
and proposal tests enumerate their existing registries rather than a handpicked subset.
Normal company regression tests remain required.
Actual command results and remaining release gates live in the feature's `quickstart.md`.

`tests/test_playground_api.py` covers generic read admission, owner-only access without
an admin bypass, account eligibility, archived reads, denied writes and selector privacy.
It also covers authenticated start/replay, setup failure/retry, bounded private history,
expired/revoked sessions, lost membership, strict inputs, entry flag and quota responses.

`apps/web/scripts/playground-contract.test.mjs` belongs to both normal Web test gates.
`scripts/playground-browser.mjs` is an optional local headless-browser acceptance harness,
configured with an installed `PLAYWRIGHT_MODULE` and optional `PLAYWRIGHT_EXECUTABLE`.
Its synthetic HTTP fixtures prove UI behavior, not backend isolation or real-provider execution.

## Archive and restore a sandbox (spec 186)

An owner archives a sandbox or practice company from the Danger zone in Companies settings.
`reality.services.playground.archive_run` sets the run to `archived` the same way restart does;
the playground tenant and every record stay, and `practice_company_runs` no longer lists the
company, so it leaves the switcher. `restore_run` brings it back unless the tenant itself is
archived or another active run already carries the same storyline. Both are owner-only,
confirmed explicitly, and exposed as `POST /api/playground/runs/{id}/archive` and `/restore`.
Deleting the data behind an archived run is not offered yet.
