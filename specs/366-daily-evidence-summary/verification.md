# Verification: Daily evidence summaries

## Baseline and regression proof
Baseline: merged PR 371, main e2c48e155b26c6d3dd296d18fdb839a899e71b6c.
Eleven added regressions failed before implementation (missing summary/cause/context).
Focused read/provider/demo/HTTP/delivery/readiness selection: 125 passed. Ruff passed.
Generated catalog consistency and docs build passed. Spec policy passes after adding
required traceability/language declarations; final committed diff is checked by CI.
HTTP proof uses real authenticated MCP tools/call and canonical server dispatch, no browser.

## Live synthetic-company acceptance
Existing paused synthetic tenant ten_f5328569e6; no new business action or credentials.
A temporary loopback source API loads this worktree; regular stack remains unchanged.
Initial actual Anthropic daily round correctly reports four customer return and three
supplier-return records and marks five shipment movements as a sample with more data.
It also adds unrequested mixed-item quantity totals and produces a truncated final
answer. These are recorded as model-output limitations, not concealed as acceptance.
Concise full-stage guidance was added. The final real round includes every stage without
truncation, keeps the return counts 4/3, and reads the complete retained shipment set of
27 movements (independently verified, has_more=false). A separate actual SO-005 query
correctly says 5 pcs open, 0 fulfilled, no current blockers and unknown nonexecution cause.
Pending proposal identity sets remained unchanged in all runs.

The final broad free-form report is still NOT accepted as wholly accurate: it invents
return item names/quantities (Cove Glass Set becomes Summit Bottle; Beacon Desk Organizer
becomes Lamp Item), mixes current blockers across orders, and assumes UTC/workflow setup
without verified external agent controls. These model errors are not repaired by the
new service fields and are explicitly remaining work. The deterministic tools and the
focused cause answer pass; arbitrary broad provider prose is outside this feature's guarantee.

## Required completion gate
Full Quality workflow [37234873015](https://github.com/Xentral-Labs/reality/actions/runs/37234873015)
passed all 24 jobs on reviewed implementation head
`9be89c7c283a18cbd65bfad515017a24ec622897`: complete backend shards/aggregate gate,
frontend, public docs, browser scripts and all live-browser stories. Spec policy passes
across the committed feature. The final commit only records completion and extends the
canonical English read documentation; behavior remains this tested implementation.
Native actual model results do not prove external Claude scheduled execution or arbitrary
external prose accuracy. No scheduler or browser dependency is added by these reads.

## Canonical label refinement
Three additional label regressions failed before implementation. Movement/Commitment/
Reservation quantity references now read canonical Item.name/SKU from the existing scoped
unit lookup. Multiple-item association, missing labels and tenant boundaries are proved.
The final real label-enabled round correctly names all seven return records and keeps
counts 4/3. However it still conflates readiness with historical causality for a blocked
example, calls derived blockers manual holds, invents a finance-exception relationship,
and assumes external setup state. Its closing question is truncated. The earlier focused
SO-005 cause response remains correct; broad prose remains explicitly unaccepted.
