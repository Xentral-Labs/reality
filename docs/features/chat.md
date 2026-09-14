# Feature: Chat

Chat is a natural-language shell over a registered application-tool layer. The provider
returns text plus structured tool calls; it never receives an ORM Session.

- Read tools may execute immediately and remain tenant-scoped.
- Mutation tools first produce a typed proposal containing arguments and human summary.
- Only an explicit confirmation executes a proposal; rejection records no business mutation.
- A proposal cannot be replayed after execution, tenant change, or argument tampering.
- A deterministic dummy provider covers reads, proposals, confirmation, rejection, and errors.
- OpenAI/Anthropic are future provider adapters, not alternate business logic.

Party, Item, and Location are operational references and may be created manually through
typed Chat proposals. Party requires name and roles; Item requires SKU and name and
defaults unit to `pcs`; Location requires name and defaults type to `warehouse`. Source
provenance remains optional and is never replaced by a synthetic manual source. A single
request may prepare an atomic same-family batch, but no record is written until explicit
confirmation executes the proposal through the shared master-data service.
New Location hierarchies use proposal-local `ref` and `parent_ref` values that the
service resolves to generated opaque Location IDs in input order. `parent_location_id`
remains reserved for an already-existing opaque Location ID and never accepts a name.

Existing Parties, Items, and Locations may also be changed through typed update
proposals. Chat may use names or SKUs to help a user find a record, but the proposal
targets only its opaque tenant-scoped ID and contains the complete intended update.
The reviewed current-state revision is checked again at confirmation, and same-family
batches are atomic. Every effective change emits an immutable Business Event whose
`changes` member contains normalized `before` and `after` values per changed field;
the event links to the executing proposal when applicable. Equal normalized updates
do not emit a false business-change event.

Chat sessions/messages are tenant-scoped and persistent. Application mutations and their
resulting IDs are captured as Actions for auditability.

New assistant answers use the authenticated user's saved UI language, number/date locale,
and display timezone. Providers receive this server-owned presentation context consistently:
prose and business labels follow language; numbers, quantities, money and calendar dates follow
locale; instants additionally follow timezone. Exact values, currencies, units, opaque IDs,
technical keys and source-stated content remain unchanged, and date-only values never shift by
timezone. Stored message bodies remain the presentation snapshot originally shown and are not
rewritten after a preference change.

Fact observations use the same proposal boundary. An agent may call
`fact_observe_propose` only for an explicit statement supported by an existing
same-tenant SourceRecord and about an existing opaque Reality subject. Its preview
shows source, subject, predicate, canonical value, and observation time. Confirmation
executes the shared `fact_observe` application tool. Model output, a repeated guess,
or a domain mutation is not itself a Fact, and typed Reality state is never copied into
Facts.

Removing a conversation from daily work archives it instead of deleting it. Archiving
retains every message, can be reversed, and never changes a pending or decided Change
Proposal. Tenant-wide proposals are reviewed in the Exceptions workspace under Pending
approvals and Decision history; the empty Chat state does not display orphaned proposals.

## Demo library

The Chat page shows a small contextual prompt library. Suggestions are real messages,
not a separate demo execution path. An empty tenant offers a confirmed `demo_seed`
proposal. A populated tenant offers read ideas for inventory/risk and, when relevant,
a reservation proposal containing the real opaque Commitment ID. Clicking an idea
creates a session when necessary and runs it through the normal chat/tool flow.

For an empty tenant, the library also offers the deterministic September 2026 business
month. Confirmation calls the exact same `run_normal_month` service as
`reality scenario run normal-month --tenant TENANT_ID`; Chat has no scenario-only write path.

## Complete business command coverage

The canonical application command catalog is also the Chat/MCP coverage contract.
Every tenant business command maps to strict public schemas; validation fails for
missing, stale, duplicate, or unjustified mappings. Read-only discovery runs directly.
Every mutation creates an exact durable proposal and calls the existing application
service only after explicit approval.

`business_records_discover` returns bounded tenant-scoped master-data, order,
commitment, warehouse, finance/pricing, and source records with opaque IDs and current
mutation-relevant fields. Human references may filter discovery but never replace
opaque relationship IDs.

`capability_describe` is the shared read-only semantic lookup for explicitly adopted
public proposal tools. It explains when a capability applies, when it must not be used,
its context and preconditions, expected refusals and events, retry guidance, and which
registered projections must be re-read before an outcome is called verified. Guidance
is validated catalog metadata, not authority or an alternative implementation of
service rules. The first complete descriptions cover Fact observation, manual order
creation, reservation creation, and Movement recording.

Sales and purchase order proposals atomically record immutable manual Source evidence,
Document/DocumentLine evidence, and derived outgoing or incoming Commitments. Documents
gain no fulfillment state. Mutation proposals also cover master-data lifecycle,
document evidence, warehouse identities/movements, reservations/holds, payments and
pricing, source configuration/ingestion, and membership. Membership execution still
requires a current human owner; an MCP token grant alone is insufficient.

## MCP read response contracts

See [MCP read contracts](mcp_reads.md) for currency-separated balances, quantity
and location semantics, retained-order evidence, cursor traversal, and the page
response migration. It also distinguishes diagnostic reads from legacy cache
refreshes and authentication telemetry.

## Sandbox practice companies

Since feature 169 the App copilot is admitted for active practice companies exactly like every
other reviewed practice operation (spec 155): the provider loop offers read and propose tools,
mutations stay behind the proposal boundary, and eligibility is read from persisted run, owner
and membership state. Lesson runs keep the read-only companion of spec 106. A policy refusal
is reported as "The Copilot is not available for this company: <reason>", never as a
transient failure. The same feature added two public reads the copilot lacked,
`finance_credits` (available customer or supplier credit) and `finance_payments` (recorded
payments with allocated and unallocated amounts), so questions about overpayments and
unmatched money are answered from records.
