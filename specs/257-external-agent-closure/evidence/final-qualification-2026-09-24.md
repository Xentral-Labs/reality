# Fresh CanisPro Qualification — 2026-09-24

## Run identity

- Company: `CanisPro Tiernahrung Abschlusslauf 2026-09-24 0905`
- Tenant: `ten_69eaf899ad`
- External protocol: `/Users/benediktsauter/Downloads/reality-mcp-testprotokoll-canispro-2026-09-24-abschlusslauf.md`
- Surfaces: public `reality-local` MCP tools plus authenticated owner review in the Web product
- Prohibited paths observed: no direct database access, ORM write, SQL, backend correction or OAuth dependency

The local stack was rebuilt from `origin/main` at `9c942d18` plus the audit-closure change at
`2a1725cd`. The running API and MCP containers were healthy. The installed API package contained
the stock-at-location domain module and route, and the running Web image contained the associated
stock-at-location UI artifact.

## Outcome

The qualification is **partially successful**. The operational order-to-cash,
purchase-to-pay, inventory, return, settlement, dunning and opening-balance journeys completed
through public proposals and owner review. Acquisition-cost attribution and review also completed
for goods, inbound freight and a purchase reduction. Inventory value and DB1/DB2 did not complete.

Confirmed improvements:

- capability discovery resolves public proposal tools;
- proposals return review tokens and owner confirmation reconciles by proposal identity;
- exact-location reservations explain available descendant stock without silently aggregating it;
- the owner can initialize all required finance-account roles;
- exact, partial, reduced and overpaid customer and supplier settlements work;
- manual dunning with a stated fee works;
- MCP and Web open items reconcile after the Web projection is refreshed;
- acquisition-cost attribution retains exact invoice-line and receipt evidence.

## Release-blocking observations

1. Receipt cost reviews use the global tenant event sequence as freshness. An unrelated payment
   term mutation changed a freshly reviewed receipt to `stale`, removed its actual cost and made
   a stable live-operating result impossible.
2. Inventory review refused a fully cost-reviewed item after an internal transfer with the
   undifferentiated message `Every receipt requires exact cost and ownership evidence.` The
   refusal did not identify the movement that lacked evidence; the observed evidence suggests
   the transfer destination was treated as a new value-bearing receipt.
3. A regular sales invoice did not retain a source-stated net revenue basis. Contribution review
   therefore returned `received_net_missing` with no candidate hash, so DB1 and DB2 were
   unreachable without replacing a complete posted line snapshot.
4. `sales_credit_record_propose` discarded every supplied argument, retained `{}` as the proposal
   input and failed only during confirmation. The supported lower-level credit-note sequence
   completed the business case but does not make the advertised action valid.
5. Deterministic confirmation errors left two proposals permanently in `executing`, with unknown
   execution and no permitted rejection or recovery path.
6. The deployed `cost_change_propose` schema exposed no properties even though the action accepted
   multiple operation-specific shapes. The external client had to infer fields and enums from
   validation failures. Shipment-purpose-specific movement types were also incomplete in
   capability guidance.

## Secondary observations

- A stated dunning fee appears in the ledger balance but not in party balances or the Web open-item
  list.
- The Web open-item projection lagged nine events until an explicit refresh.
- Invoice previews showed `payment_term_id: null` although derived due dates and discounts were
  correct.
- Future movement and finance timestamps were accepted without warning, while inventory review
  rejected a future cutoff with a combined unit-or-cutoff message.
- A received lot whose expiry date equalled the receipt date produced no preview warning.
- Restock disposition did not retain its stated reason on the resulting movement.

## Qualification decision

This run satisfies the evidence collection required by T075 but does not satisfy FR-028, SC-001,
SC-006, SC-007, SC-008 or SC-009. The final closure matrix must retain the unresolved findings and
link them to the follow-up requirements and tasks introduced from this evidence.
