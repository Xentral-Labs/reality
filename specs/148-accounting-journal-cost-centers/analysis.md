
## Managed-reference slice review (2026-09-10)

Scope R001–R004 only, under FR-008/010/021/030/031. No critical or unresolved design
findings. Codes and kinds are immutable; names/status have reasoned revisions.
The same finance lock serializes snapshot/revision preview and acceptance. Shared
application confirmation supplies actor identity, stores receipt atomically and
makes replay safe. BusinessEvent carries immutable decisions; a second history
or balance projection is unnecessary. API/CLI/MCP/UI all delegate to shared services.
Tests explicitly retain original ledger values through migration and configuration.
Broad financial-component assignments, cost allocations and case mapping remain open.

Verification review found one stale HTTP catalog count (53→54 events), corrected to
include the new reference decision event. Mobile browser evidence must hide the chat
panel and show the actual reference controls in both themes; the journey now does so.
Completion depends on the final required gates and local preservation proof recorded
in verification-results.md; this review does not mark the broader roadmap complete.

Runtime review also detected a newer concurrently deployed UI (main plus spec160).
The integration preserves its source files for Sales/Purchasing navigation, page
counts, page-local tabs, Inspector and action directory; financial extensions remain.
The source worktree was not edited. Existing supplier-credit discovery tests were
retained instead of replacing them with the narrower main-only test. Final UI gates
include the real financial journey and the spec160 count/page-chrome browser matrix.
The other stale existing expectation was migration head 0050→0051 after transactional
downgrade refusal; no assertion about preserved account/posting values was removed.

## Received-component slice review — 2026-09-10

The reviewed bounded design separates held monetary evidence from internal attribution.
Document summaries are never additional line components. Only the named optional
`reality_finance_v1` contract is read; arbitrary upstream fields are not guessed.
No general ledger, tax determination, automatic mapping or global cost report is added.
Three tables have demonstrated uses: immutable received values, reasoned assignment
revisions, and constrained cost-center shares. Tenant/kind composite references,
owner confirmation and replay receipts reuse the existing application boundary.
Finance configuration and assignment acquire the same tenant-then-finance lock order;
this removes the inverse lock ordering between reference configuration and attribution.
No unresolved clarification or critical cross-artifact finding blocks this slice.
Verification and task completion remain conditional on the recorded gates.

## Operational matrix pre-implementation analysis

No critical finding blocks the bounded matrix read. External case/account mapping
requires target-specific references and remains a later slice. A configured default is
not labeled transaction readiness: original settlement accounts, explicit selection,
evidence eligibility and confirmation remain owned by existing actions. Canonical
customer credits use `credit_note`, while the prior attribution slice accidentally
recognized `sales_credit_note`; fix this with an actually posted credit regression.


Mobile review: a real credit-detail click reproduced desktop fixed-footer measurement overriding the existing mobile static-footer rule. The bounded RegisterTable correction restores that rule below 640px; it changes no posting or selection semantics. Required shared page-chrome checks remain in the verification gate. No critical design finding remains.


## Source classification pre-implementation review

Reviewed FR-030/033/034 and the approved target-independent source mapping design against current components/references. No unresolved clarification or critical finding for this bounded slice. Existing SourceSystem IDs supply the actual namespace owner; only explicit source code objects qualify. No inferred tax rules, automatic overrides, duplicated amount authority or target dependency. The owner authorized continuation; broad reviewer-owned checklist markers remain untouched. Verification must include no-effect reads/previews and replacement/blocked/conflicting resolution.

## Finance settings placement review

The user explicitly requested moving domain configuration into Finance after completing
the source classification slice. A fourth Finance tab provides a single home without
adding another global navigation item. Reuse the three current editors and their
permission boundaries. Separating the register body avoids accidental journal reads
and action menus on the settings view. No unresolved clarification or critical
finding blocks this UI-only slice; the existing backend suite remains valid for its
unchanged financial behavior. Catalog destination validation is required after retargeting.

## Delivery review

Final source-mapping and Finance Settings verification is green and recorded in
verification-results.md. Mapping preserves original source declarations, historical
active/blocked decisions and confirmed provenance; resolution never posts money or
overrides internal attribution. Finance Settings reuses the original tenant-scoped
editors, with explicit owner permission and tenant-keyed state. Real browser checks
cover canonical placement, reload, all financial flows and mobile history; local
migration preserves every existing ledger and finance snapshot. No critical finding
remains for S001–S004 or U001–U004. Broad external accounting work stays uncompleted.

Area navigation review: user approved the four-area vertical menu/mobile select.
No unresolved clarification or critical finding. Reuse editor business behavior;
area-scoped pending storage prevents reference reviews leaking across the split views.

Final area navigation review: no critical finding remains. Existing services and tenant/owner boundaries are preserved; prepared reviews survive both area switching and legacy storage recovery. Visual and live preservation evidence is recorded in verification-results.md.

Compact-action review: user approved consistent correction across all four settings
areas. A top-layer native popover avoids overflow clipping from account tables;
existing handlers and confirmation stay authoritative. No unresolved clarification,
schema change or critical finding. Preserve coarse-pointer touch size.

Compact-action final review: measured form/footer and row sizes, default/non-default menu behavior, owner restrictions and real confirmed financial operations pass. Popover bounds, Escape/outside dismissal and responsive visual checks pass. No critical finding remains for B001–B003.

## Target mapping pre-implementation review

Owner approval now covers the concrete three-table schema, after the field review
and explicit Finance-only catalog decision. Forty checklist markers are checked and
five broad roadmap/reviewer markers remain open; existing continuation authorization
covers this bounded slice and those markers remain untouched. Scope shapes, tenant
FKs, revision/lock requirements, source versus internal provenance, deferred profile
semantics and TM001–TM007 proof coverage are consistent. No critical design finding
or unresolved product clarification remains. No runtime verification claimed.


Target mapping implementation review: the Finance-only scope remains coherent with
the Constitution. Source amounts are read unchanged; target resolution does not
create financial effects. Catalog lifecycle uses the existing confirmed application
path and Finance revision lock. Immutable mapping snapshots retain reviewed values.
The final stale-evidence finding has a failing-then-passing regression and now derives
an explicit preview refusal from the confirmed action's evidence hash. No critical
implementation finding remains. Runtime rollout evidence is recorded separately.

Finance settings UX pre-implementation review: FR-059 covers all nine editor types.
The user's explicit request approves presentation scope and existing app design.
Existing broad roadmap checklist markers remain unchanged (40 checked, five open);
prior continuation authorization applies. Native dialog focus, busy states, review
recovery, member restrictions and no-write cancellation are included in verification.
No unresolved clarification or critical finding; no schema expansion.

FR-059 final review: existing app dialog tokens/patterns are reused without new
financial rules or persistence. Nine explicit create/edit entry points replace
permanent forms. Busy, error, owner/member, focus, history and pending-recovery paths
are verified in browser checks; the real confirmed financial journey passes.
Duplicate modal/section headings were removed. No critical finding remains.

FR-060 review: exact role keys already exist in the matrix response. No label-to-identity inference or new configurable posting rules are needed. Read-only matrix and owner-only confirmed default changes remain separate; global-role effect is explained. No critical finding or unresolved clarification. Prior broader checklist markers remain unchanged.

FR-060 final review: shared native dialogs and existing confirmed account-default service are retained. Exact role keys constrain active choices; original-account policies remain visible. Focused browser and real confirmed financial journey checks pass, with matching tested assets served locally. No critical finding remains. No schema or domain changes; broader roadmap checklist markers remain unchanged.

FR-061 pre-implementation review: the user authorizes intuitive list/create/edit dialogs throughout Finance settings. Existing inputs are filters, not writes; removing the permanent selector in favor of target-row navigation preserves the service boundary. No unresolved clarification, schema change, or critical finding. Tests precede implementation; prior broader checklist markers remain unchanged.

FR-061 final review: target-list navigation, empty states and native dialogs match the requested existing app pattern. Focused browser and real confirmed finance journey pass, and identical tested assets are served locally. Existing tenant scope, owner permissions, target-specific review recovery and financial service semantics are preserved. No critical finding remains; no schema change.

FR-062 pre-implementation review: explicit user approval covers consistent alignment, spacing and labels throughout Finance settings. Scope is presentation only; existing dialogs, services and confirmed mutations remain. Shared toolbar avoids divergent one-off alignment. No unresolved clarification or critical finding; no schema expansion.

FR-062 final review: shared presentation component prevents per-area toolbar drift. Native dialog/service boundaries and tenant-scoped configuration semantics are preserved. Desktop/mobile geometry, editor behavior, real finance journey and the final complete frontend gate pass. Matching release assets are served locally. No critical finding remains.

FR-063 preimplementation review: user explicitly approves empty catalogs versus filtered no-results and persistent area navigation. No unresolved clarification or critical finding. Existing reads provide total counts; no new authority, schema or service rule is needed.

FR-063 final review: shared empty-state presentation distinguishes catalog absence from filtered no-results. Filter reset, kind-switch cleanup, no empty table headers, existing confirmations and real finance flows are verified. Identical tested assets are served locally; no critical finding remains. Broader roadmap markers are unchanged.


## Finance-only PR integration review

User explicitly requests a Finance-only PR. Isolate the delivered Finance services,
seven migrations, adapters, UI and tests on current main; exclude unmerged recorder,
ObjectGraph, graph-layout, pulse tests, shared graph styles and graph translations.
Retain main's PageActionBar and inline row previews while adding Finance actions.
Retarget browser journeys to visible row disclosure and the shared page action menu.
Correct UI requirement identifiers from the conflicting FR-035–039 to FR-059–063;
original settlement requirements keep FR-035–039. This is traceability correction,
not a product change. No new scope or schema beyond the approved Finance slices.
