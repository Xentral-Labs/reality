# Finance Read and UI Contracts

Use the current application's shared design system and Inspector. [views.md](../views.md) defines the complete product states; this contract binds those screens to shared read models. No screen computes business balances, tax, settlement or readiness in JavaScript.

## Shared read envelope

Each `finance.*.list`/`.explain` read returns `scope`, `as_of` (read instant, finance revision, tenant event sequence), `rows`, `totals`, `coverage`, `issues`, `next_cursor`. Amounts are Decimal strings paired with currency and basis. Totals cover every filtered row before pagination and remain separated by currency/side/basis. Unknown/missing source values are nullable with a reason, not zero. Filters are normalized and included in the cursor scope hash.

Provenance nodes distinguish `source_assertion`, `internal_decision`, `reality_record`, `derived_observation`. Derived observations include input IDs, rule identity and coverage limitations. List rows may carry compact summaries with drill-down references; explanation must make all contributing inputs accessible through continuation, not silently truncate them. New writes/events invalidate continuation; return `snapshot_changed` and a restart instruction. This is current-state consistency, not an unlimited historical as-of service.

Queries run through a read-only transaction with one REPEATABLE READ snapshot, no materialized refresh/commit. Persisted catalog descriptions advertise these as live shared reads. Agent explanation and web totals use the same service result. Available actions include current permission, evidence and eligibility conditions; this does not grant authorization to execute them.

## Screen/service binding

| Screen | Planned shared reads | Mutations or navigation |
|---|---|---|
| V01 Finance review | `finance.review.list`, `finance.evidence.explain` | Separate local-recording and handoff issues; resolve supported review cases |
| V02 Journal/accounts | `finance.journal.list`, `finance.account.explain` | Trace posting group → evidence → source; existing inverse flow |
| V03 Open items/payments | `finance.open_items.list`, `finance.payments.list`, `finance.settlement.explain` | Actual payment, explicit adjustment, allocation/refund, holds |
| V04 Received detail | `finance.components.list`, `finance.component.explain` | Show received/internal separately; confirmed component assignment |
| V05 Accounting handoff | `finance.handoff.list`, `finance.handoff.preview` | Prepare confirmed selection, immutable download |
| V06 External feedback | `finance.receipts.list`, `finance.handoff.explain` | Unmatched/conflicting receipt review with exact versions |
| V07 Cost attribution | `finance.cost_assignments.list` | Assigned/unassigned/missing basis; component detail |
| V08 Finance settings | `finance.accounts.list`, `finance.references.list`, `finance.mappings.list`, `finance.authorities.list` | Owner setup/catalog/source-classification/target-mapping/authority commands |
| V09 Available credits | `finance.credits.list`, `finance.credit.explain` | Customers/Suppliers tabs; reuse/refund/earmark; see origin |
| V10 Opening import | `finance.opening.list`, `finance.opening.preview` | Cutover scope preview, conflict review, confirmed import |
| V11 Money accounts | `finance.money_accounts.list`, `finance.money_event.explain` | Bank/provider/restricted/disputed/in-transit separated; evidence matching |
| V12 Advances | `finance.advances.list`, `finance.advance.explain` | Earmark, release, apply, cancellation review |
| V13 Trade finance | `finance.trade.list`, `finance.trade.explain` | Goods/billing/credit/payment links, coverage and unknowns |

V08 source-classification editing works without an accounting target. Show source system/namespace/code, resolved local reference and revision separately from target destinations. Money-account reads partition balances and availability by currency even when the same account ID contains multiple currencies; no combined monetary total.

All names are planned tool contracts. Each is added to command/projection discovery, with source/Reality relationships in Inspector and tenant-isolation catalog cases. Existing screens can host these views as tabs or drawers; thirteen view IDs do not require thirteen unrelated top-level pages.

## Surface design

Mount modular finance components in the root application using existing `br-*` styling, table/header/filter/pagination/dialog components, indigo actions and neutral read states. Preserve shared navigation and keyboard behavior. Choose labels such as operational balance, available credit, stated fee and assigned net amount; do not present a statutory profit-and-loss statement or imply external posting from a local success.

For each view verify loading, empty, filtered-empty, populated, error, forbidden and stale-action states. Applicable additions: partial assignment, mixed currency, missing source basis, invalid account reference, unmatched receipt, conflicting evidence and unknown migrated coverage. Disabled actions explain the actual service refusal. Confirmation displays actual money separately from noncash adjustment and makes affected origin/target items clear.

Validate 390 px mobile, 1024 px tablet Safari, 1440 px desktop; light/dark themes; keyboard focus and screen-reader labels; en/de/nl/es strings. Avoid the overlapping title/date/action row shown in the supplied screenshot by wrapping shared toolbar groups at tablet widths. Exact screenshots are implementation evidence, not claimed by this plan.

## Agent action verification

Agent reads capability conditions → obtains preview → requests user confirmation through the existing proposal path → executes approved command → re-reads the returned authoritative IDs → reports observed outcome and remaining exceptions. It must distinguish local recording, prepared file and externally asserted posting. Failed/stale actions cannot be narrated as success. Facts do not become a second balance store.

## Available-credit register (implemented read slice)

`GET /api/tenants/{tenant_id}/finance/open-items` accepts
`flow=customer-balance` or `flow=supplier-balance`, using the shared
`services.finance.credits.available_credit_items` service. Existing pagination,
query, status and sort parameters apply. `gross`, `settled`, `open` retain the
register response shape and mean original credit, used credit and available credit
in these flows. Amounts are Decimal strings. Totals cover all filtered rows,
independently of the displayed page, and remain separated by currency.

Each row includes the original document and type, party, control-entry ID, concrete
account ID/code/state, posting group, source ID when held and effective allocation
IDs. Reversed credit groups are excluded; reversed allocation counterparts release
availability. A blocked account does not hide historical credit.

The UI preserves the credit-note-only customer-credit flow and adds two explicit
available-credit choices. Payment-origin rows expose Explain, without offering the
existing credit-note-only refund action. No new mutation endpoint is introduced.

### Company reference settings

Company settings shows cost centers, case codes and coding groups with server
search, state filter, pagination, history and owner-only create/edit actions.
A review shows before/after and reason before confirmation. History remains
available for blocked references. No assignment editor is exposed in this slice.

### Financial-detail attribution dialog

Invoice/credit rows expose Financial detail to members and owners. A native dialog
shows received document summary separately from paged eligible lines; line-less
documents have one document component. Received/source codes and internal attribution
are visibly separate. Select net/gross/base, optional active case/group and explicit
center amounts; share currency always comes from evidence. Server preview displays
assigned and remaining amount with reason, then separate owner confirmation. History
retains old reference labels and decision provenance; source/line/document links use
the existing Inspector navigation. Errors, empty reference sets, unknown basis, partial
assignment, pending reload and narrow light/dark layouts are covered.

`finance.matrix.read` / GET `/finance/matrix`: finance revision, fourteen operations
with transaction key, label, stated basis, debit/credit role and default account/status,
and explicit control-account/evidence limitations. No mutation or balance effect.


Source classification slice: shared `finance.source_mapping.set` confirmed proposal; `finance.source_mappings.list` and `.history` read tools. GET `/finance/source-mappings`, GET `/finance/source-mappings/{mapping_id}/history`, POST `/finance/source-mappings/proposals`. Component context adds a separate `source_resolution` observation per actual component; existing source codes and evidence hash stay unchanged. Scope/revision/actor/reason and reference snapshots are returned; reads do not materialize components.

Finance configuration is rendered at `/app/finance?finance_view=settings` with the
selected tenant. The URL survives reload/navigation; the same three shared editor
reads/proposals/history contracts apply. Company settings no longer mounts these
editors. Opening the settings view does not read open items, payments or the journal.

## External target mapping views

Finance Settings → Accounts & account mapping → External accounting provides target
selection, Rules, External accounts, Tax codes and Accounting targets. Selection and
pending reviews are scoped to tenant/target and survive reload. A tab only mounts its
form once the matching list response arrives; preceding responses cannot reset a new
form or expose another target's choices. Rule keys are fixed while editing; changes
to scope use a new rule and explicit blocking of any conflicting former mode.
Financial detail includes Mapping preview, original received amounts, source mapping
history, internal attribution context, destination revision and an evidence action.
Specific classification failures reuse the existing source-resolution vocabulary.
A settings link leads to the Finance target configuration without performing a write.
