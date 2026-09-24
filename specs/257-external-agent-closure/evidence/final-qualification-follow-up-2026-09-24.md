# Fresh CanisPro Final Qualification Follow-up — 2026-09-24

## Run identity

- Company: `CanisPro Tiernahrung Finalqualifikation 2026-09-24`
- Tenant: `ten_e19e802603`
- External protocol:
  `/Users/benediktsauter/Downloads/reality-mcp-testprotokoll-canispro-2026-09-24-finalqualifikation.md`
- Test interval: 2026-09-24 10:16–11:25 UTC
- Surfaces: public `reality-local` MCP tools and authenticated owner review in the Web product
- Prohibited paths observed: no database, ORM, SQL or backend correction access

The agent performed exactly one read-only tenant check before any business mutation. It returned
`ten_e19e802603`, matching the newly created company.

## Result

The qualification is **partially successful**. The operational core completed across master data,
purchase, receipt, costing, reservation, dispatch, sales invoicing, settlement, supplier and
customer credits, returns, opening balances and dunning. Public reads and Web views were used for
cross-checks. The run recorded 76 numbered steps and 18 finding groups.

### Qualified repairs from spec 257

- Complete `sales_credit_record_propose` arguments were retained and the invoice-linked customer
  credit completed, including settlement.
- Receipt reviews remained fresh after an unrelated payment-term event and more than 200 later
  events; relevant credit evidence invalidated only affected receipts and named the evidence IDs.
- Inventory review returned exact missing movement IDs.
- Source-stated net, tax and gross evidence was retained for order-backed purchase and sales invoice
  lines and used for net acquisition cost and DB1 candidates.

### Confirmed residual release/demo blockers

1. Four deterministic confirmation refusals remained permanently `executing`, effect unknown and
   invisible to the pending-decision Web list.
2. Owner confirmation of a complete contribution candidate returned HTTP 500; DB1 approval and DB2
   did not complete.
3. Shipment-level `occurred_at` did not reach created movements. An undocumented item-level value
   was accepted instead, and other unknown item fields were silently ignored.
4. Free supplier invoices, supplier credits and customer credits could not retain stated net/tax
   components, leaving freight-related receipt costs incomplete.
5. The deployed cost-operation schema remained empty at the top-level tool surface despite richer
   internal capability branches.
6. A posted dunning fee affected the ledger balance but did not appear in MCP or Web open items.

### Secondary confirmed gaps

- Generic public adapter errors for selected proposal-status and opening-context reads.
- Invoice previews omitted effective payment-term identity and shipment evidence.
- Expired-lot and return-announcement reads were too thin for action; expired stock had no receipt
  warning and remained ordinary available quantity.
- Return restock did not retain its stated reason.
- Settlement timestamp optionality, future-date validation, price guidance, reservation freshness,
  proposal deep-link loading and owner rules for rejection were inconsistent.
- Capability refusal examples for customer credit serialized as sentence fragments rather than
  structured guidance.

## Disposition

T101 is complete because the requested tests, builds, fresh-tenant qualification and evidence
capture were executed. The result is not represented as a fully green release qualification.
All reproducible residual findings are bounded by `specs/267-agent-qualification-gaps/spec.md`,
which preserves them for later planning and implementation without reopening completed spec 257
work.
