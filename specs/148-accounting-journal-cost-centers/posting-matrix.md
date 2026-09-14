# Transaction Matrix and Declared Case Mapping

**Status**: Operational read matrix implemented (14 operations including opening positions and accepted reductions). Declared source/case and external target-account mapping are implemented and verified. Immutable handoff packages and delivery receipts remain planned.
**Feature**: [148](spec.md)

## Operational transaction matrix

The eight base operations below plus the explicitly confirmed [customer and supplier settlement adjustments](payment-differences.md) are fixed supported application behavior. Tenants configure concrete eligible accounts for its roles; they cannot program alternative debit/credit or amount-calculation rules. Display role names below do not mandate new technical identifiers or reinterpret existing gross counterpart semantics.

| Transaction | Debit role | Credit role | Received amount basis |
|---|---|---|---|
| Sales invoice | Receivable | Gross sales counterpart | Stated invoice gross |
| Customer credit note | Gross sales counterpart | Receivable | Stated credit total |
| Customer payment | Cash/payment | Receivable | Stated payment amount |
| Customer refund | Receivable | Cash/payment | Stated refund amount |
| Supplier invoice | Gross purchase counterpart | Payable | Stated invoice gross |
| Supplier credit note | Payable | Gross purchase counterpart | Stated credit total |
| Supplier payment | Payable | Cash/payment | Stated payment amount |
| Supplier refund | Cash/payment | Payable | Stated refund amount |

A draft or incomplete evidence object alone does not trigger recording. The shared service must recognize supported final financial evidence with its required identity, party, amount and currency. Automatic recording additionally requires the approved source/type authority. Merely creating/importing a document is not unconditional permission to post it. An explicit recording action uses the same validation and confirmation boundary.

Orders, purchase orders, reservations and physical movements create no financial posting under this matrix. Allocation links existing control entries; it does not duplicate a payment or invoice. Exact reversal uses the original group, original accounts and inverse directions, including the existing blocked-account reversal exception. A new replacement uses normal current eligibility rules. Zero-effect evidence creates no zero-amount ledger lines.

Normal invoice/credit/payment/refund actions may explicitly select a compatible account per required role; omitted selections use the uniquely configured role destinations except that invoice-bound control legs resolve the existing invoice account first. Different-account settlement requires the explicit reclassification contract, not an arbitrary replacement default. Preview shows resolved accounts, direction, received amount and provenance. Selection cannot change side or amount basis. The later plan inventories and adapts existing service signatures consistently across all adapters.

Source-stated signed credit/refund values retain their original representation; the supported operation normalizes the received magnitude and direction without recalculating the financial amount. Ambiguous document direction is a review case. No case code or customer country modifies this gross operational matrix.

## Declared case codes

CaseCode is a tenant-owned reference with stable ID, unique code, name/description and active/retired state. It describes an already declared business/tax case, not a determination of which tax law applies. Codes are extensible; the following are illustrative names only, not mandatory seeded legal classifications:

| Example code | Descriptive label |
|---|---|
| DOMESTIC_STANDARD | Domestic standard case |
| DOMESTIC_REDUCED | Domestic alternative stated treatment |
| EU_GOODS_B2B | Declared intra-EU business goods case |
| EXPORT_GOODS | Declared goods export case |
| US_SALES_TAX | Sale with stated sales tax |
| NO_TAX_STATED | Source explicitly states no tax applies |

Missing tax information is unknown and MUST NOT resolve to NO_TAX_STATED. Zero rate alone likewise does not identify exemption or any other treatment. Country, address, party type, rate and free-text descriptions cannot determine a case automatically in V1.

Retain original source case/tax codes losslessly. Resolve a declared source code through an explicit reviewed source-namespace-to-local-case mapping, or record a confirmed internal case assignment with author/reason. A source declaration and internal assignment remain separately inspectable. If they conflict, handoff requires explicit review rather than silently preferring one. A manual assignment does not supply absent tax/net amounts.

Assignment belongs to the actual received component or tax group, not blindly to the entire invoice. A document-level declaration stays document-level unless the source explicitly says it applies to the complete breakdown. One invoice may carry multiple cases. No line allocation is invented from a document summary.

## Optional coding groups

CodingGroup is a separate small tenant reference with stable ID, code/name and active/retired state, such as Goods, Freight or Software. It is used only when the same transaction/case needs different external account destinations. It is not a cost center and has no financial balance.

A group is supplied and mapped from an explicit source reference or confirmed internally on a received component. No guessing from descriptions, item names or country is permitted. Missing required coding group is a handoff review issue; it does not invalidate an otherwise valid operational claim.

## Exact mapping per target

Mapping revisions select external account/tax-code references by tenant, accounting target, transaction kind, declared CaseCode and optionally CodingGroup. Different targets may use different external references. Every reference is validated within its tenant/target namespace; no external account number becomes a local identity.

| Transaction | Declared case | Optional group | External account reference | External tax-code reference |
|---|---|---|---|---|
| Sales invoice | DOMESTIC_STANDARD | Goods | User-selected destination | User-selected target code |
| Sales invoice | EU_GOODS_B2B | Goods | User-selected destination | User-selected target code |
| Sales invoice | EXPORT_GOODS | Goods | User-selected destination | User-selected target code |
| Supplier invoice | DOMESTIC_STANDARD | Software | User-selected destination | User-selected target code |

These are examples of configuration shape, not valid accounting instructions. A mapping hands off the exact supplied net/tax/gross components with their basis. It does not turn the local gross counterpart into a net journal entry.

V1 uses exact resolution without priorities, country rules or arbitrary predicates:

- A case mapping declares either no group discrimination or exact group discrimination for one target/transaction/case scope.
- Without group discrimination, exactly one active approved destination exists for that scope and any supplied group is retained as annotation.
- With group discrimination, an explicit valid group and exactly one active approved mapping are required. A missing-group default cannot coexist as an implicit fallback.
- Duplicate/overlapping active mappings are rejected on activation. Runtime still requires exactly one match; zero or multiple matches create a precise review reason.
- Case/group-based mappings are authoritative for destination components covered by the selected profile. Simple local-account reference mappings cover only other explicitly declared profile roles; competing mapping mechanisms never silently override each other.

Invoice, credit and refund kinds are distinct mapping keys. Do not automatically reuse invoice tax coding for a credit. Payments and other profile components that require no case mapping use their declared account-reference handoff path; they do not inherit invoice tax codes or rebook invoice net/tax amounts. The neutral profile may carry unmapped evidence with explicit omissions; a case-coded profile or selected case-coded handoff requires exact resolution for every required component.

Versions are immutable once approved/used. Draft/save does not activate a mapping. Activation and changes require owner confirmation; changed evidence, assignment, profile or mapping revision invalidates a pending preview. Retired cases/groups remain visible in old packages but cannot be newly assigned. Correcting a case after preparation creates a new reviewed assignment/package revision; it never alters the original or silently resends it.

## Commands, views and shared reads

Commands/capabilities: maintain case/group references; preview/confirm source-code mappings and internal assignments; draft/test/activate/retire target mapping revisions. These are shared application tools with existing tenant/owner and confirmation boundaries; exact command names are a later technical-plan decision.

Finance settings adds a read-only Transaction matrix showing the eight base operations plus both settlement-adjustment directions and resolved local defaults. It links to account configuration and does not offer a debit/credit editor. Additional tabs/registers show Case codes, Coding groups, Source code mappings and Target case mappings.

Target mapping editor fields: target, transaction, case, group mode/optional group, external account, external tax code, revision and activation state. Preview against selected real evidence shows received components, source versus internal assignment, zero/one/multiple matches, selected destinations and omissions. No map-by-country or calculate-tax action exists.

Document/component Inspector shows declared case, optional group and their provenance. Finance review lists missing, retired, conflicting and unmapped codes separately from local recording readiness. Handoff preview freezes the chosen assignment/mapping revisions per component. Shared readiness/projection builders use the same resolver; browser code never runs a second rule engine.

## Planned proof

The acceptance suite covers all eight matrix directions and non-posting triggers; explicit/default account selection; two cases in one invoice; same case with Goods versus Software; distinct tenant/target mappings; no country-only inference; explicit no-tax versus unknown; group discrimination and overlap rejection; payment without an inherited invoice case; conflict between source/internal assignments; stale/retired revisions; and unchanged local gross balances and prior package versions after mapping changes.

## Explicit settlement-adjustment extension

The additional `customer_settlement_adjustment` operation debits Accepted settlement reduction counterpart and credits Receivable for the explicitly approved stated reduction amount. It is separate from cash and is never automatically authorized by invoice/payment recording or a matching discount rate. [payment-differences.md](payment-differences.md) owns acceptance, evidence, limits and reversal rules. Overpayment itself is an ordinary actual payment with a partially allocated credit, not another financial transaction type. Refund of excess uses the base customer refund direction and allocates against the original payment credit.

Supplier parity adds `supplier_settlement_adjustment`: debit Payable / credit Supplier settlement reduction counterpart for a stated documented supplier-agreed reduction. The customer counterpart role is separately named Customer settlement reduction counterpart. Supplier overpayment remains an ordinary payment with available unallocated payable debit; supplier refund receipt uses debit Cash/payment / credit Payable and settles that debit. [payment-differences.md](payment-differences.md) governs documented agreement, current bounds and correction rules for both directions. Neither case matching nor a payment-run proposal automatically authorizes an adjustment or proves actual cash movement.

## Opening-item extension

[opening-items.md](opening-items.md) supplies four separately confirmed migration operations: customer receivable (debit Receivable / credit Opening counterpart), customer credit (debit Opening counterpart / credit Receivable), supplier payable (debit Opening counterpart / credit Payable), and supplier credit (debit Payable / credit Opening counterpart). Amounts are stated outstanding positions at cutover. No sales/purchase invoice or payment is invented. Include these directions in the read-only matrix with a distinct Opening items section; source financial-event automation cannot silently create opening batches.

## Money-path and control-transfer extension

[trade-finance-controls.md](trade-finance-controls.md) adds bounded explicit provider capture/fee/retention/dispute/payout and bank-transfer meanings with their evidence requirements. A completed customer payment may debit its actual provider-clearing account rather than bank cash; pending authorization never posts as settled cash. The base customer/supplier claim directions remain unchanged. Account purpose must distinguish provider claims from cash, not merely relabel one generic bank balance.

The same contract defines conservative cross-account control reclassification with paired same-account allocations. Earmarking and payable holds create operational decision records, not ledger entries. Its shared trade/coverage controls and [agent contract](agent-finance-contract.md) apply to the complete transaction matrix, including opening and adjustment operations.
