# Source-backed selling costs and reviewed DB2

Approved continuation of commercial_v1 (FR-003/007/011–016/019/020/022).
Reuse CostComponentBasis and CostAttribution revisions: selling_assign admits an exact
received supplier net amount, explicit recoverable/not-applicable tax treatment and
owner-confirmed selling-expense scope. Preserve signed shares and explicit effects;
invoice charges increase cost, supplier credits decrease it regardless of upstream sign.
Reject missing net, unsupported tax, currency mismatch and more than 100 parts. Shares
must preserve source sign, be nonzero, and sum in magnitude to at most the received net.
An assignment replaces the entire previous selling revision, never adds to it. Reuse
withdraw for retirement. Replacement evidence/rematching and mixed acquisition/selling
components are unsupported: any component ever used for one family cannot enter the
other, even after withdrawal. Reject receipt replace against a selling predecessor.
This conservative boundary prevents inbound freight from entering both DB1 and DB2.

New cost_selling_attribution_part points to existing attribution revision and sold
sales-invoice DocumentLine, with category, signed source share, effect and direct/allocated
kind. Supplier documents remain protected by the existing admitted-component guard.
Targets must be exact same-tenant sales invoice lines; currency must match. No inferred
order/partner/date allocation, payment-net revenue or arbitrary overhead allocation.
Packaging/fulfilment expense confirmation explicitly excludes inventory purchases and
costs already in acquisition/manufacturing. Inventory consumption is a future input path.

The versioned commercial_v1 selling checklist comprises outbound_freight, fulfilment,
packaging, payment_fee, marketplace_commission, sales_commission and other_selling.
Extend contribution_review with optional selling_categories: all seven explicit
(evidenced/confirmed_zero/not_applicable/unresolved) decisions, each with a reason.
Omission preserves existing DB1-only behavior. Zero/not-applicable with active amounts
refuses; evidenced without an amount and unresolved produce an incomplete DB2 scope.
Every active part for that sold line is captured automatically, bounded to 100 parts;
latest revisions only, including withdrawals and reassignments away from the line.
Direct and allocated subtotals remain distinct; zero is authoritative only through the
scope review. DB2=DB1-direct-allocated selling cost; rate uses positive received revenue.
Fixture A: revenue1200, consumption630, direct90+allocated24 => DB1 570, DB2 456, rate38%.

New cost_selling_review_category and cost_selling_review_member retain exact decisions
and part membership for each contribution review. Composite tenant FKs, unique category
and part membership, integrity hash including retained revision/component amounts, and
bounded reads preserve historical replay. Extend the existing contribution digest only
when a selling checklist exists; pre-migration DB1 reviews keep their original digest.
Reads use frozen member IDs, not current assignments. Later events make current DB1/DB2
unavailable while labeled basis amounts and explicit review_id history remain readable.
New reviews still require a current inventory candidate; refresh is explicit, never
automatic. All mutations use existing owner/proposal/confirmation/tenant lock/rollback/
replay controls. No monetary result becomes stored authority.

Static migration0067 adds only these three tables and FK indexes; empty downgrade works,
any retained selling row blocks downgrade before dropping anything. No UI/scheduler/new
public command: cost.change and cost.contribution.get plus existing MCP expose the same
semantics. Update catalogs, German nested argument guidance, generated docs and graph
integration deferrals. General tax/FX, returns, partial revenue, broad reporting and
reference qualification remain outstanding; no full-product completion claim.
