# Unified app completion plan

**Language**: English
**Date**: 2026-09-08
**Status**: Completion direction accepted by the owner; initial dependency/data audit complete. Functional closure and retirement remain open.
**Spec impact**: None. This records approved prioritization and read-only audit evidence. It does not change application behavior, business records, permissions or route admission. Each implementation increment follows Spec Kit before code changes.

## Accepted finish line

The owner accepted this sequence: close necessary legacy dependencies, preserve existing
data/practice continuity, accept the retained operational workflows, make the owner's
UI changes, then perform the final switch and remove obsolete presentation. Freeze
feature expansion at Specs 107–134 plus necessary closure fixes. Legacy feature parity
and a complete new technical Explorer are not completion requirements.

This document supersedes the open-ended proposed delivery order in
[the capability inventory](unified-capability-inventory.md). That inventory remains
historical evidence; its unimplemented candidates are not automatically release blockers.

## Read-only evidence collected

Inspected the unified and legacy route/component boundaries and existing shared-service
reads. Authenticated to the existing local API on port 8007 using the already authorized
owner account. Read all five bootstrap-visible companies (four ordinary, one practice),
all owned practice-entry pages, all returned run details and execution-status reads for
the eleven executing steps. Company queries used their explicit tenant IDs. Authentication
created normal session state; no business mutation, proposal execution/rejection, rule
activation/deactivation, reconciliation write or provider request was performed.

| Observation | Result | Completion implication |
| --- | --- | --- |
| Ordinary-company stock configuration | One stocked, untracked item across four companies; no nondefault item settings detected in those returned records | No current local need demonstrated for a tracked-stock editor or broader item-settings migration |
| Commercial references | No payment terms, price lists or pricing groups; no returned party linked to a payment term | Defer broad commercial maintenance; preserve existing reference fields when editing and recheck before deployment |
| Tracked inventory | No returned handling units, lots or serial units in any of the five companies | Defer separate tracked-inventory workflows for this local target; this is not evidence about other deployments |
| Missing-information/rules | Two implemented cases; three rule versions: one active, one disabled, one draft | Preserve rule/case inspection and a confirmed disable path for the active rule; no need to rebuild recommendation/authoring/simulation |
| Pending ordinary-company decisions | One proposed reality_gap_create and one proposed location_create | Preserve inspection and legitimate dismissal/recovery. location_create uses records input already supported by master-data review; reality_gap_create currently falls back to legacy |
| Owned practice history | 34 runs: 2 active, 32 archived; 110 executed, 3 rejected, 11 executing steps | Preserve active entry, archived history and original proposal identity in the common app |
| Executing practice steps | All eleven belong to archived runs: eight movement_create, three order_create. All status reads report execution unknown and business outcome not_proven; none returns a receipt. Ten have operational_state not_checked, one unresolved | Retain honest unknown-result inspection. Do not retry, mark successful, delete, or reopen archived runs to make migration appear clean |
| AI configuration | Managed provider metadata reports available for all four ordinary companies; practice AI-settings access returns 403 | Metadata is not proof of a working provider request. Keep the practice boundary; run a separate isolated provider acceptance check |

No HTTP errors occurred in these inventory reads apart from the expected practice
AI-settings denial. Item/party list services are unpaginated tenant-scoped reads;
pending reviews and cases were paged to completion. Practice history was paged to the
reported total. Rule counts cover versions linked to the returned cases; they are not
a database-wide orphan-rule integrity claim. Other users' private practice runs and
companies outside these memberships were not inspected. Repeat the audit for the actual
deployment scope before deleting presentation. The local execution record is
`/private/tmp/reality-cutover-audit.json`; no credentials, business payloads or user names
are included in this committed plan.

## Remaining dependency map

| Entry in the new app | Current old destination | Bounded closure treatment |
| --- | --- | --- |
| Shell: More workspaces | /app/orders | Remove after retained navigation acceptance; no replacement view launcher |
| Shell: Playground; UnifiedApp practice-company guard | /playground; /app/orders with sandbox tenant | Replace with common-shell practice entry and isolated history/actions; preserve backend admission boundaries |
| DataSourcesPage: Technical Explorer | /app/explorer | Keep necessary source/evidence inspection in existing registers/Inspector; add only a demonstrated missing record access |
| MasterDataPage: Advanced settings | /app/parties, /app/items, /app/locations | Current records already have full-detail inspection. Verify updates preserve untouched fields; remove the legacy escape for the accepted basic scope |
| MasterDataCard: non-customer/supplier receipt fallback | /app/parties | Provide exact record inspection for other party roles without pretending they are customers |
| OrdersPage: advanced operations | /app/orders | Remove after supplier acceptance and explicit deferral of remaining experimental operations |
| DeliveryCase: existing workspace | /app/commitments | Existing case/Inspector must retain supported context and hold/correction access |
| WarehousePage: advanced operations | /app/inventory, /app/reservations, /app/movements | Retained stock/reservation/movement actions are covered; verify selected records and remove duplicate-register escape |
| FinancePage: advanced operations | /app/open-items, /app/payments, /app/journal | Retained finance controls are covered; verify records/receipts and remove duplicate-register escape |
| DecisionsPage and ChatPage: unsupported proposal | /app/exceptions | Add common proposal inspection, permissible explicit rejection and honest execution-status handling; do not invent generic execution for excluded tools |
| App.tsx default routing | Legacy fallback plus separate PracticeEntry and VITE_UNIFIED_APP | Final compatibility route map and sole new default, after functional/UI acceptance |

Search covered literal and interpolated old-route exits in `apps/web/src/unified/`,
plus `App.tsx`, unified routing and the legacy Route union. Final route acceptance
must also cover bookmarked legacy URLs, Site/Docs/account-return links and unknown URLs;
removing visible buttons alone is insufficient.

## Three bounded functional closure packages

### F1 — Existing controls and records remain reachable

- [x] C01 Inventory remaining legacy exits and existing local use; record approved scope freeze.
- [ ] C02 Provide a unified fallback for existing unsupported decisions and historical outcomes, including the observed reality_gap_create proposal. Preserve explicit rejection and read-only unknown-state inspection; no generic auto-confirm or automatic replay.
- [ ] C03 Preserve inspection of the observed missing-information cases and all rule versions; add a reviewed disable control for active rules through the existing shared service. Leave the real active rule unchanged during verification.
- [ ] C04 Close the mapped ordinary-company legacy exits with existing registers/Inspector or the smallest demonstrated replacement. Verify full-detail/reference preservation and nonstandard party receipt access. Avoid a second technical dashboard.

Done when all retained ordinary-company jobs and controls have tested destinations in
the unified app, including the actual audit findings. This does not require every old
mutation to receive a new form.

### F2 — Practice continuity in the common app

- [ ] C05 Make practice entry/history use the common shell with a clear isolated-company boundary. Preserve active/archived runs, receipts and unknown-status reads. Existing backend practice-only restrictions remain authoritative; no ordinary-company write endpoint is enabled for sandbox data.
- [ ] C06 Prove archived unknown-result continuity using isolated representative fixtures. The eleven observed archived unknown results may remain unknown; preserving their evidence and status is the requirement, not forcing their resolution. No replay or deletion of the owner's runs.

Keep the useful existing practice flows and reuse their reviewed services. Do not add
lessons or rebuild every experimental editor. No separate Playground shell remains at
final cutover.

### F3 — Functional acceptance

- [ ] C07 Prove the supplier flow through the real browser and an isolated migrated database: purchase order, receipt, supplier invoice, payment and an appropriate correction/reversal path. Retain the already proved customer flow from Spec 127.
- [ ] C08 Recheck the retained item-import path and make one controlled provider read acceptance request with synthetic company data if the configured provider is available. Record actual external prerequisites/failures distinctly from UI or service defects. No new connector/provider project.
- [ ] C09 Complete cross-company, role, signed-out/no-company and interrupted-action acceptance plus required CI. Refresh the dataset-aware retirement audit for the deployment scope.

**Gate for the owner's UI work:** F1–F3 pass for the accepted scope, or an external-only
limitation is explicitly recorded and accepted. UI work must not wait on deferred
feature ideas.

## After functional closure

- [ ] U01 Apply the owner's requested UI changes and perform visual acceptance.
- [ ] R01 Verify old-route/account-return/Site/Docs compatibility, sole new entry and rollback artifact. No redirects may replay an action.
- [ ] R02 Perform the authorized rollout and retire obsolete UI, styles and temporary migration switch after the agreed rollback window. Preserve data and supported service/API contracts; code retirement is not database deletion.

Rollout authorization is separate from local implementation. The owner has accepted
the direction and sequence, not an unreviewed deployment or deletion of business data.

## Deferred from this completion scope

Additional providers/connectors/CSV profiles; broad commercial/pricing editors; large
rule recommendation/authoring/simulation/replay UI; new analytics; tracked opening,
transfers and general stock operations; physical returns and supplier credits;
existing-payment multi-invoice allocation; document-wide hold and document-line
correction editors; parallel specialized dashboards. Promote one only if a specific
retained job or deployment dataset proves that its absence prevents safe operation.
A deferred editor does not imply deletion of its records or disabling its API/tool.

## Verification of this audit increment

Documentation and read-only inspection only. `make spec-check` and `git diff --check`
are the required checks; no new runtime test suite is claimed. The most recent runtime
baseline remains Spec 134: 1750 backend tests passed with 7 existing skips, plus the
recorded browser/frontend gates. Functional closure checkboxes remain open until their
own implementation and acceptance evidence exists.


## Owner sequencing update — Spec 135

The owner subsequently requested four specific UI changes immediately: compact left
navigation, a slim sticky header, a toggleable persistent right chat and Analytics
before Settings with Reports beneath it. This explicitly brings that bounded UI work
forward. F1–F3 and final retirement remain open; implementing this layout does not mark
functional closure complete or exhaust the owner's potential later UI requests.

## PR integration note

Current main independently used feature numbers 107–110. The unified foundation, analytics/master-data, warehouse/attention and finance specifications were renumbered to 139–142 for integration. Historical references to unified Specs 107–110 describe these same increments. Later unified Specs 111–138 retain their numbers.

Rule editing and simulation exist inside expandable rule versions and require company-owner access. The owner reported that these controls are difficult to discover; an explicit edit/simulate entry remains a UX follow-up. Rules support deactivation rather than destructive deletion. The reported account/company role has not been independently verified. This draft PR does not claim final functional closure or legacy retirement.

PR integration verification: full PostgreSQL suite on the merged branch passed with 1789 tests and 7 skips (`pytest -n 4`, isolated test databases). Ruff, spec policy and diff check against current main passed. Fresh frontend run passed 133 contracts, four-language localization audit and production build. These checks do not close the separately tracked deployment/provider/practice acceptance items.

## Owner retirement instruction — Spec 143

After merging PR #152, the owner explicitly requested a new PR removing Playground
and the old app. Spec 143 supersedes the temporary dual-presentation arrangement:
the unified app becomes the sole browser product, with bookmark compatibility and
retirement messaging. This authorizes source removal, not deployment or data deletion.
The earlier broad functional-closure checklist is not claimed complete. Existing
sandbox services, historical runs and authorization remain intact; no experimental
workflow parity or sandbox-to-production conversion is introduced.
