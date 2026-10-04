# Verification: Daily evidence summaries

## Baseline and regression proof
Baseline: merged PR 371, main e2c48e155b26c6d3dd296d18fdb839a899e71b6c.
Eleven added regressions failed before implementation (missing summary/cause/context).
Focused read/provider/demo/HTTP/delivery/readiness selection: 124 passed. Ruff passed.
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
Full Quality workflow is pending at PR preparation. No full-CI completion claim yet.
Native actual model results do not prove external Claude scheduled execution or arbitrary
external prose accuracy. No scheduler or browser dependency is added by these reads.
