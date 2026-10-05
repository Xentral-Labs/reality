# Take over an operational case

A case groups responsibility for accepted work. In the first version, an order's customer deliveries
share one case and each announced return has a separate related case. New products, warehouses and
raw source messages do not create cases.

Coordination is the default for every company. New accepted orders receive cases immediately;
existing open/partial orders and accepted open returns are included by bounded upgrade jobs.
Completed history remains closed. Read `operational_case_status` to verify migration and coverage
readiness; incomplete upgrade or job failure requires operator attention, not activation.

If the agent needs help, open the case and confirm **Take over manually / stop automation**. New
automated actions for this case stop immediately. Already started actions remain visible: stopping
automation does not cancel a shipment or other external action.

Repair the order in Shopify, then let the supported source/evidence workflow accept the changed
data. A raw message alone is not an accepted repair. The case shows current outstanding work, linked
Sources and any unresolved execution or source changes.

Choose **Review before returning to automation**. Reconcile outstanding uncertainty, inspect the
current state and confirm **Return to automation**. Changed data requires a fresh review. Old plans
do not resume; the agent must prepare current work.

The case ID identifies this responsibility boundary. A proposal ID identifies a decision. An
external correlation ID identifies the outside system's processing context. They are separate
references and none creates business permission.

Use `operational_case_object` to find cases from an existing order, commitment, return or proposal;
use `operational_case_explain` to inspect the same state as the Web UI. Reads do not create work.
MCP/Chat can propose responsibility controls; an authenticated human must confirm them.

Live Shopify transport and automatic refund intent/execution are not included in this version.
Supplier processes and other case families are planned separately.
[Tool reference](/tool-usage/commands) describes the available operations.

## Default coordination (spec 377)

Coordination applies to every company without activation. Apply migration 0145 and run matching
scheduler/worker services. Use `operational_case_status` to verify migration readiness, completed
historical coverage, platform provenance and actual job failure. Open/partial orders and open
accepted returns are backfilled; closed history and raw mail are excluded. Manual ownership and
exact handback remain intact. Old approvals require fresh review. This grants no supplier, Finance,
warehouse, refund, outgoing-mail or external-provider authority. Historical owner adoption and
executed receipts are preserved. Populated rollout downgrade is refused.
