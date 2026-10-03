# Credit and Delivery Reference Boundary

**Feature**: [Spec 343](../spec.md)
**Created**: 2026-10-03
**Purpose**: Define the initial acceptance denominator and source anchors before implementation (T002).
**Authority**: Design-time boundary inventory only. This file is not a generated product explanation, is never served as a current blueprint, and makes no claim about the running deployment or passed tests.

## Registered roots and relationships

| Public entry | Actual application/source root | Relationship |
|---|---|---|
| `credit_exposure` tool/command | `tools.application._credit_exposure` → `services.credit_exposure.credit_exposure` → `credit_exposures` | Read current customer exposure |
| `fulfillment_readiness` tool/view dependency | `tools.application._fulfillment_readiness` → `services.fulfillment_readiness.fulfillment_readiness` | Read current delivery commitment readiness |
| `credit_hold_release_propose` MCP tool | Canonical `credit_hold_release` → `delivery_actions.review_delivery` → `credit_hold_actions.review_credit_release` | Prepare the exact hold release |
| `proposal_approve_and_execute` MCP tool | Shared proposal decision boundary → `tools.application.approve_and_execute_proposal` → `tools.application._credit_hold_release` → `credit_hold_actions.release_credit_holds` | Confirm and execute; owner policy precedes replay |
| Sales-order intake/revision consumers | `core.create_manual_order`, `core._shopify_interpretation`, `core.revise_commitment` → `credit_exposure.hold_if_over_credit_limit` | Record source/order evidence and place holds; do not refuse over-limit intake |
| Reviewed/manual shipment recording | `delivery_actions.review_delivery`, `tools.application._movement_create` → `fulfillment_readiness.require_paid_prepayment` | Payment-only gate for recording physical goods; distinct from operational ship readiness |
| Recorded execution reconciliation | `proposal_execution_status` → `delivery_actions.delivery_execution_detail` → `credit_hold_actions.credit_release_detail` | Inspect the recorded release receipt and lifecycle |
| Generic hold release | `core.release_document_holds` → `core.release_commitment_hold` | Retain owner-released credit hold reasons |

Public identifiers and actual callable roots are resolved dynamically in the implemented service. The source table below is the planning baseline, not a resolver that overrides executable registrations.

## Business outcome denominator

Each B-series row is an acceptance obligation. Both included/excluded (or allowed/refused) outcomes must be represented where the predicate permits them; absence of a matching executable test is an explicit test gap, never evidence of coverage. Numeric boundaries include exact equality, zero and strictly greater/less where applicable. Composite guards must preserve their operands and short-circuit meaning.

| ID | Outcome-affecting rule family | Required distinction | Source anchor |
|---|---|---|---|
| B001 | Customer identity and evaluation time | Tenant-scoped customer lookup; unknown/foreign record; UTC as-of versus current time | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B002 | Open-item eligibility | Positive open amount and supported receivable/payable type; other records omitted | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B003 | Open-item currency | Customer currency counts; other currency named without conversion | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B004 | Payable treatment | Payables are named separately and never subtracted from exposure | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B005 | Credits and payments | Only positive available customer credit counts; other currency excluded | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B006 | Held down payments | Offsettable received down payments count in customer currency; foreign ones named | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B007 | Order-line basis | Current non-cancelled commitment terms versus unpromised source line; fully cancelled order contributes zero | [`_order_rows`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L87) |
| B008 | Invoice quantity exclusion | An invoice whose every posted group is reversed does not reduce uninvoiced quantity | [`_invoiced_quantities`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L27) |
| B009 | Remaining quantity | Clamp uninvoiced quantity to zero; omit nonpositive lines | [`_order_rows`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L87) |
| B010 | Unpriced and foreign order lines | Other currency excluded; missing unit price contributes zero and is identified | [`_order_rows`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L87) |
| B011 | Stated order value | Prorate the stated gross line amount for uninvoiced quantity at existing amount scale; zero source quantity yields zero; never substitute quantity × unit price | [`_order_rows`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L87) |
| B012 | Exposure arithmetic | Open invoices + uninvoiced open order amounts − available credits; no stored second authority | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B013 | Limit boundary | Limit > 0 AND exposure > limit; equality is not over limit; zero denotes no configured limit | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B014 | Overdue context | Only days-overdue > 0 among receivables; report independently of limit decision | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) |
| B015 | Hold intake eligibility | Sales order with customer, positive configured limit, matching currency and customer-delivery commitments | [`hold_if_over_credit_limit`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L477) |
| B016 | Order contribution gate | This order contributes positive counted value AND total exposure is over limit | [`hold_if_over_credit_limit`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L477) |
| B017 | Hold idempotency and cancellation | Skip already actively credit-held or cancelled commitments; add beside other holds | [`place_credit_holds`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L430) |
| B018 | Hold evidence | Active credit holds require reason credit_check, creator credit_limit, correct tenant/commitment and no released timestamp | [`active_credit_holds`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L407) |
| B019 | Hold effects | Append hold and commitment.held event with exposure facts; order/source stays recorded | [`place_credit_holds`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L430) |
| B020 | Readiness target and quantity | Unknown/foreign or non-customer commitment refused; proposed quantity must be positive and not exceed open quantity | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B021 | Physical and reserved cover | Active reservations and unblocked physical stock; single selected warehouse versus combined cover | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B022 | Cross-warehouse cover | Own location stock versus min(reserved, physical) from other locations; no double count | [`stock_cover`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L178) |
| B023 | Active execution holds | Any active commitment hold and current party delivery hold contribute distinct blockers | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B024 | Reservation and stock shortage | Insufficient reservation; physical shortage or reservation physically split beyond ready quantity | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B025 | No evidence order | Commitment without order evidence has operational readiness only; positive open quantity still required | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B026 | Order and payment-term selection | Wrong/missing sales order refused; missing term or requires_prepayment false bypasses payment gate, not operational blockers | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B027 | Prepayment authority | Required amount is stated order gross; candidate invoices linked to order lines or order down-payment invoices | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B028 | Invoice attribution | Different party/currency is ambiguous; same-party/currency other-order billing is consolidated | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B029 | Qualifying settlements | Active invoice/payment allocations with correct party and currency; exclude consolidated entries from direct received sum | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B030 | Consolidated invoices | Open consolidated invoice blocks; fully settled one contributes stated order-related line amounts | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B031 | Down-payment double counting | Subtract existing live offsets already counted as received down payments | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B032 | Prepayment blockers | Missing posted invoice, ambiguous attribution, open consolidated invoice and remaining amount > 0 are independent reasons | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B033 | Final readiness | Open quantity > 0 AND no combined operational/payment blockers | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) |
| B034 | Manual movement distinction | Only customer shipment uses payment blockers; generic movement recording must not be described as enforcing all operational readiness blockers | [`require_paid_prepayment`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L590) |
| B035 | Release target | Tenant-scoped sales order and active credit holds required; missing or non-sales order refused | [`_order_holds`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L30) |
| B036 | Release reason | Trimmed nonempty reason required; blank or missing reason refused | [`preview_credit_release`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L47) |
| B037 | Reviewed fields and context | Exactly document_id and reason; pin hold identities/order, show current exposure without pinning it | [`review_credit_release`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L127) |
| B038 | Overlapping release | Another executing release for same order prevents conflicting action; excluded current proposal does not conflict | [`assert_no_unresolved_credit_release`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L155) |
| B039 | Review confirmation and freshness | Exact review token and explicit confirmation; re-read pinned hold state and reject changed review | [`validate_review`](../../../packages/reality-core/src/reality/services/delivery_actions.py#L575) |
| B040 | Owner authority | Credit release selects company-owner policy; owner check precedes executed replay | [`resolve_decision_policy`](../../../packages/reality-core/src/reality/services/proposal_decisions.py#L20) |
| B041 | Identity exception | Existing principal requires owner; identity-free path only when existing authentication mode is disabled | [`require_decision_authority`](../../../packages/reality-core/src/reality/services/proposal_decisions.py#L80) |
| B042 | Current company access | Active company membership and user admission, with existing trusted-local/admin exceptions; never infer authority from review text | [`require_delivery_principal`](../../../packages/reality-core/src/reality/services/delivery_actions.py#L1153) |
| B043 | Actual owner role | Current active membership required and role must equal owner | [`require_owner`](../../../packages/reality-core/src/reality/services/memberships.py#L71) |
| B044 | Release effects | Lift only selected active credit holds; retain other holds; emit per-commitment release event with reason | [`release_credit_holds`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L79) |
| B045 | Generic release preservation | Generic releases keep OWNER_RELEASED_HOLD_REASONS; closure can explicitly supply empty kept set | [`release_commitment_hold`](../../../packages/reality-core/src/reality/services/core.py#L6403) |
| B046 | Recorded release verification | Only matching action/order/reason events and exact receipt verify result; pending/unsettled/unresolved remain distinct | [`credit_release_detail`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L173) |
| B047 | Proposal lifecycle | Missing, executing, rejected, unsupported and stale reviewed proposals do not execute; executed replay retains authority checks | [`approve_and_execute_proposal`](../../../packages/reality-core/src/reality/tools/application.py#L3816) |
| B048 | Effective credit consumption | Reversed control groups excluded; active allocations reduce available credit; paid/outstanding state follows exact amounts | [`available_credit_rows`](../../../packages/reality-core/src/reality/services/finance/credits.py#L16) |
| B049 | Effective settlement authority | Own ledger balance and active allocations define open amount; reversal role changes result | [`settlement_positions`](../../../packages/reality-core/src/reality/services/core.py#L11230) |
| B050 | Reversed payment/invoice evidence | Reversed allocation groups and either reversed posting endpoint do not contribute | [`active_settlement_allocations`](../../../packages/reality-core/src/reality/services/core.py#L11953) |
| B051 | Down-payment receipt authority | Cash-backed allocations count as paid; credits/write-offs are not received cash; live offsets consume offsettable amount | [`down_payment_invoices`](../../../packages/reality-core/src/reality/services/down_payments.py#L254) |
| B052 | Effective commitment revisions | Use the current applicable stated revision and correction-aware movement quantities | [`commitment_terms`](../../../packages/reality-core/src/reality/services/core.py#L3432) |
| B053 | Due-date context | Opening debt retains original due date; other items use effective term/document date; aging is context, not a new credit policy | [`with_invoice_aging`](../../../packages/reality-core/src/reality/services/core.py#L14099) |

## Input and helper obligations

All helper symbols below are in scope when they contribute to an above result. `financial_open_items`/settlement/reversal reads, commitment revisions, blocked stock, active allocations, available credits, received down payments and due-date helpers are **not** opaque exemptions: dynamic analysis must follow their relevant predicates and calculations, or mark the affected blueprint partial. The AST site inventory records the baseline for these functions as well.

Functions invoked deeper than this table remain dynamically discoverable dependencies. A newly discovered outcome-affecting condition is included in the completeness denominator automatically. T043 must reject completeness while any such condition is unresolved. The 64-function limit applies per detail request, not to the combined acceptance journey; related roots may be inspected separately, with shared-rule links preserving their dependency.

Generic persistence mechanics (SQLAlchemy flush/commit, object construction mechanics, UID generation and event serialization) and framework transport machinery do not need independent business blueprints. Their business selection/effect and failure boundaries still need source-cited nodes. Authentication credentials/cryptography are excluded from public source inspection; company-role and authorization predicates remain explained from their approved shared policy code.

## Source symbol inventory

These paths/spans identify the checkout used for boundary review only. Product responses must inspect the installed running function and expose its own evidence digest. This inventory may not be used as a pre-generated blueprint or test description.

| Source | Qualified symbol | Planning span |
|---|---|---|
| `services/credit_exposure.py` | [`credit_exposure`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L332) | 314–322 |
| `services/credit_exposure.py` | [`credit_exposures`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L195) | 185–311 |
| `services/credit_exposure.py` | [`_order_rows`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L87) | 84–182 |
| `services/credit_exposure.py` | [`_invoiced_quantities`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L27) | 27–81 |
| `services/credit_exposure.py` | [`active_credit_holds`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L407) | 381–400 |
| `services/credit_exposure.py` | [`place_credit_holds`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L430) | 403–446 |
| `services/credit_exposure.py` | [`hold_if_over_credit_limit`](../../../packages/reality-core/src/reality/services/credit_exposure.py#L477) | 449–485 |
| `services/credit_hold_actions.py` | [`_order_holds`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L30) | 30–43 |
| `services/credit_hold_actions.py` | [`preview_credit_release`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L47) | 46–73 |
| `services/credit_hold_actions.py` | [`review_credit_release`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L127) | 123–147 |
| `services/credit_hold_actions.py` | [`release_credit_holds`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L79) | 76–120 |
| `services/credit_hold_actions.py` | [`assert_no_unresolved_credit_release`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L155) | 150–164 |
| `services/credit_hold_actions.py` | [`credit_release_detail`](../../../packages/reality-core/src/reality/services/credit_hold_actions.py#L173) | 167–243 |
| `services/fulfillment_readiness.py` | [`stock_cover`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L178) | 172–197 |
| `services/fulfillment_readiness.py` | [`fulfillment_readiness`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L225) | 218–553 |
| `services/fulfillment_readiness.py` | [`require_paid_prepayment`](../../../packages/reality-core/src/reality/services/fulfillment_readiness.py#L590) | 564–603 |
| `services/proposal_decisions.py` | [`resolve_decision_policy`](../../../packages/reality-core/src/reality/services/proposal_decisions.py#L20) | 20–77 |
| `services/proposal_decisions.py` | [`require_decision_authority`](../../../packages/reality-core/src/reality/services/proposal_decisions.py#L80) | 80–123 |
| `services/delivery_actions.py` | [`validate_review`](../../../packages/reality-core/src/reality/services/delivery_actions.py#L575) | 575–608 |
| `services/delivery_actions.py` | [`require_delivery_principal`](../../../packages/reality-core/src/reality/services/delivery_actions.py#L1153) | 1153–1173 |
| `services/core.py` | [`financial_open_items`](../../../packages/reality-core/src/reality/services/core.py#L11623) | 11623–11637 |
| `services/core.py` | [`_financial_open_items`](../../../packages/reality-core/src/reality/services/core.py#L11640) | 11640–11754 |
| `services/core.py` | [`settlement_positions`](../../../packages/reality-core/src/reality/services/core.py#L11230) | 11230–11281 |
| `services/core.py` | [`active_settlement_allocations`](../../../packages/reality-core/src/reality/services/core.py#L11953) | 11953–12026 |
| `services/core.py` | [`open_invoice_amount`](../../../packages/reality-core/src/reality/services/core.py#L11565) | 11565–11601 |
| `services/core.py` | [`open_invoice_amounts`](../../../packages/reality-core/src/reality/services/core.py#L11284) | 11284–11293 |
| `services/core.py` | [`_settlement_control_entries`](../../../packages/reality-core/src/reality/services/core.py#L11102) | 11102–11132 |
| `services/core.py` | [`_ledger_reversal_roles`](../../../packages/reality-core/src/reality/services/core.py#L11135) | 11135–11172 |
| `services/core.py` | [`_document_account_balances`](../../../packages/reality-core/src/reality/services/core.py#L11175) | 11175–11208 |
| `services/core.py` | [`_allocated_per_entry`](../../../packages/reality-core/src/reality/services/core.py#L11211) | 11211–11217 |
| `services/core.py` | [`_open_amount`](../../../packages/reality-core/src/reality/services/core.py#L11296) | 11296–11303 |
| `services/core.py` | [`commitment_terms`](../../../packages/reality-core/src/reality/services/core.py#L3432) | 3432–3486 |
| `services/core.py` | [`commitment_quantity`](../../../packages/reality-core/src/reality/services/core.py#L3489) | 3489–3509 |
| `services/core.py` | [`movement_quantity`](../../../packages/reality-core/src/reality/services/core.py#L3224) | 3224–3235 |
| `services/core.py` | [`_movement_quantities`](../../../packages/reality-core/src/reality/services/core.py#L3238) | 3238–3267 |
| `services/core.py` | [`_effective_commitment_value`](../../../packages/reality-core/src/reality/services/core.py#L3383) | 3383–3391 |
| `services/core.py` | [`stock_at`](../../../packages/reality-core/src/reality/services/core.py#L3772) | 3772–3793 |
| `services/core.py` | [`blocked_quantity`](../../../packages/reality-core/src/reality/services/core.py#L3907) | 3907–3939 |
| `services/core.py` | [`active_party_delivery_hold`](../../../packages/reality-core/src/reality/services/core.py#L6515) | 6515–6528 |
| `services/core.py` | [`release_commitment_hold`](../../../packages/reality-core/src/reality/services/core.py#L6403) | 6403–6458 |
| `services/core.py` | [`release_document_holds`](../../../packages/reality-core/src/reality/services/core.py#L6496) | 6496–6512 |
| `services/core.py` | [`with_invoice_aging`](../../../packages/reality-core/src/reality/services/core.py#L14099) | 14099–14126 |
| `services/core.py` | [`_payment_terms_by_id`](../../../packages/reality-core/src/reality/services/core.py#L14090) | 14090–14096 |
| `services/core.py` | [`effective_payment_term`](../../../packages/reality-core/src/reality/services/core.py#L14041) | 14041–14052 |
| `services/core.py` | [`invoice_due_date`](../../../packages/reality-core/src/reality/services/core.py#L14055) | 14055–14064 |
| `services/core.py` | [`invoice_discount_date`](../../../packages/reality-core/src/reality/services/core.py#L14067) | 14067–14080 |
| `services/core.py` | [`invoice_days_overdue`](../../../packages/reality-core/src/reality/services/core.py#L14083) | 14083–14087 |
| `services/finance/credits.py` | [`available_credit_rows`](../../../packages/reality-core/src/reality/services/finance/credits.py#L16) | 16–169 |
| `services/down_payments.py` | [`held_down_payments`](../../../packages/reality-core/src/reality/services/down_payments.py#L606) | 606–633 |
| `services/down_payments.py` | [`down_payment_invoices`](../../../packages/reality-core/src/reality/services/down_payments.py#L254) | 254–300 |
| `services/down_payments.py` | [`_reversed`](../../../packages/reality-core/src/reality/services/down_payments.py#L68) | 68–87 |
| `services/down_payments.py` | [`_cash_received`](../../../packages/reality-core/src/reality/services/down_payments.py#L90) | 90–139 |
| `services/down_payments.py` | [`live_offsets`](../../../packages/reality-core/src/reality/services/down_payments.py#L175) | 175–200 |
| `services/down_payments.py` | [`_offset_groups`](../../../packages/reality-core/src/reality/services/down_payments.py#L142) | 142–172 |
| `services/down_payments.py` | [`order_down_payment_invoice_ids`](../../../packages/reality-core/src/reality/services/down_payments.py#L636) | 636–648 |
| `services/memberships.py` | [`require_owner`](../../../packages/reality-core/src/reality/services/memberships.py#L71) | 71–80 |
| `services/memberships.py` | [`_active_membership`](../../../packages/reality-core/src/reality/services/memberships.py#L59) | 59–68 |
| `tools/application.py` | [`_credit_exposure`](../../../packages/reality-core/src/reality/tools/application.py#L326) | 326–338 |
| `tools/application.py` | [`_fulfillment_readiness`](../../../packages/reality-core/src/reality/tools/application.py#L398) | 398–405 |
| `tools/application.py` | [`_credit_hold_release`](../../../packages/reality-core/src/reality/tools/application.py#L1341) | 1341–1347 |
| `tools/application.py` | [`_movement_create`](../../../packages/reality-core/src/reality/tools/application.py#L1005) | 1005–1069 |
| `tools/application.py` | [`approve_and_execute_proposal`](../../../packages/reality-core/src/reality/tools/application.py#L3816) | 3788–4103 |

## Baseline decision-site inventory

The denominator counts decision **sites**, not all combinations of possible execution paths or measured coverage. Site kinds are `if`, conditional expression, comprehension filter, and SQLAlchemy `where`/`filter` predicate lists. Every boolean operand/comparison inside a site remains part of its expression; true/false or included/excluded diagram outcomes are required where applicable. Loops, effects and arithmetic without a predicate remain covered by the B-series obligations and graph nodes. General proposal/policy functions contain branches for other tools; only credit-release-reachable branches belong to the initial journey, and their unfiltered sites below must not be misrepresented as credit-only rules.

| Site | Source symbol | Line | Kind | Exact source predicate |
|---|---|---|---|---|
| S001 | `services/credit_exposure.py:credit_exposures` | 201 | if | `not parties` |
| S002 | `services/credit_exposure.py:credit_exposures` | 210 | if | `party is None or open_amount <= ZERO` |
| S003 | `services/credit_exposure.py:credit_exposures` | 212 | if | `document.type not in RECEIVABLE_TYPES &#124; PAYABLE_TYPES` |
| S004 | `services/credit_exposure.py:credit_exposures` | 223 | if | `document.currency != party.default_currency` |
| S005 | `services/credit_exposure.py:credit_exposures` | 225 | if | `document.type in RECEIVABLE_TYPES` |
| S006 | `services/credit_exposure.py:credit_exposures` | 239 | if | `party is None or available <= ZERO` |
| S007 | `services/credit_exposure.py:credit_exposures` | 248 | if | `item['currency'] != party.default_currency` |
| S008 | `services/credit_exposure.py:credit_exposures` | 264 | if | `row['currency'] != party.default_currency` |
| S009 | `services/credit_exposure.py:credit_exposures` | 274 | comprehension | `row['days_overdue'] > 0` |
| S010 | `services/credit_exposure.py:credit_exposures` | 290 | conditional | `over_limit` |
| S011 | `services/credit_exposure.py:_order_rows` | 98 | query | `Document.tenant_id == tenant_id, Document.party_id.in_(list(parties)), Document.type == 'sales_order'` |
| S012 | `services/credit_exposure.py:_order_rows` | 107 | if | `not orders` |
| S013 | `services/credit_exposure.py:_order_rows` | 111 | query | `DocumentLine.tenant_id == tenant_id, DocumentLine.document_id.in_([order.id for order in orders])` |
| S014 | `services/credit_exposure.py:_order_rows` | 122 | query | `Commitment.tenant_id == tenant_id, Commitment.document_id.in_([order.id for order in orders]), Commitment.type == 'customer_delivery'` |
| S015 | `services/credit_exposure.py:_order_rows` | 129 | if | `commitment.document_line_id` |
| S016 | `services/credit_exposure.py:_order_rows` | 135 | comprehension | `commitment.status != 'cancelled'` |
| S017 | `services/credit_exposure.py:_order_rows` | 146 | if | `rows` |
| S018 | `services/credit_exposure.py:_order_rows` | 149 | comprehension | `c.status != 'cancelled'` |
| S019 | `services/credit_exposure.py:_order_rows` | 151 | if | `order_promises and all((c.status == 'cancelled' for c in order_promises))` |
| S020 | `services/credit_exposure.py:_order_rows` | 158 | if | `uninvoiced <= ZERO` |
| S021 | `services/credit_exposure.py:_order_rows` | 166 | conditional | `line.unit_price is not None` |
| S022 | `services/credit_exposure.py:_order_rows` | 170 | if | `order.currency != party.default_currency` |
| S023 | `services/credit_exposure.py:_order_rows` | 172 | if | `line.unit_price is None` |
| S024 | `services/credit_exposure.py:_order_rows` | 177 | conditional | `Decimal(line.quantity) > ZERO` |
| S025 | `services/credit_exposure.py:_invoiced_quantities` | 37 | if | `not line_ids` |
| S026 | `services/credit_exposure.py:_invoiced_quantities` | 40 | query | `DocumentLine.tenant_id == tenant_id, DocumentLine.billed_document_line_id.in_(line_ids), Document.type == 'sales_invoice'` |
| S027 | `services/credit_exposure.py:_invoiced_quantities` | 54 | if | `invoice_ids` |
| S028 | `services/credit_exposure.py:_invoiced_quantities` | 56 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.document_id.in_(invoice_ids)` |
| S029 | `services/credit_exposure.py:_invoiced_quantities` | 64 | conditional | `all_groups` |
| S030 | `services/credit_exposure.py:_invoiced_quantities` | 66 | query | `LedgerReversal.tenant_id == tenant_id, LedgerReversal.original_posting_group_id.in_(all_groups)` |
| S031 | `services/credit_exposure.py:_invoiced_quantities` | 78 | if | `posted and posted <= reversed_groups` |
| S032 | `services/credit_exposure.py:active_credit_holds` | 386 | if | `not commitment_ids` |
| S033 | `services/credit_exposure.py:active_credit_holds` | 390 | query | `CommitmentHold.tenant_id == tenant_id, CommitmentHold.commitment_id.in_(commitment_ids), CommitmentHold.reason_code == 'credit_check', CommitmentHold.created_by == 'credit_limit', CommitmentHold.released_at.is_(None)` |
| S034 | `services/credit_exposure.py:place_credit_holds` | 423 | if | `commitment.id in held or commitment.status == 'cancelled'` |
| S035 | `services/credit_exposure.py:hold_if_over_credit_limit` | 463 | if | `order.type != 'sales_order' or not order.party_id` |
| S036 | `services/credit_exposure.py:hold_if_over_credit_limit` | 466 | if | `Decimal(party.credit_limit) <= ZERO or order.currency != party.default_currency` |
| S037 | `services/credit_exposure.py:hold_if_over_credit_limit` | 468 | comprehension | `c.type == 'customer_delivery'` |
| S038 | `services/credit_exposure.py:hold_if_over_credit_limit` | 469 | if | `not promises` |
| S039 | `services/credit_exposure.py:hold_if_over_credit_limit` | 477 | comprehension | `row['document_id'] == order.id` |
| S040 | `services/credit_exposure.py:hold_if_over_credit_limit` | 481 | if | `order_value <= ZERO or not exposure['over_limit']` |
| S041 | `services/credit_hold_actions.py:_order_holds` | 34 | if | `order.type != 'sales_order'` |
| S042 | `services/credit_hold_actions.py:_order_holds` | 38 | query | `Commitment.tenant_id == tenant_id, Commitment.document_id == order.id` |
| S043 | `services/credit_hold_actions.py:preview_credit_release` | 51 | if | `not holds` |
| S044 | `services/credit_hold_actions.py:preview_credit_release` | 54 | if | `not stated` |
| S045 | `services/credit_hold_actions.py:review_credit_release` | 126 | if | `set(arguments) != FIELDS` |
| S046 | `services/credit_hold_actions.py:release_credit_holds` | 112 | if | `_commit` |
| S047 | `services/credit_hold_actions.py:assert_no_unresolved_credit_release` | 154 | query | `ChangeProposal.tenant_id == tenant_id, ChangeProposal.type == 'tool:credit_hold_release', ChangeProposal.status == 'executing'` |
| S048 | `services/credit_hold_actions.py:assert_no_unresolved_credit_release` | 161 | if | `proposal.id != exclude and saved.get('document_id') == arguments.get('document_id')` |
| S049 | `services/credit_hold_actions.py:credit_release_detail` | 176 | conditional | `proposal.status == 'executed'` |
| S050 | `services/credit_hold_actions.py:credit_release_detail` | 179 | conditional | `proposal.status == 'proposed'` |
| S051 | `services/credit_hold_actions.py:credit_release_detail` | 184 | conditional | `review` |
| S052 | `services/credit_hold_actions.py:credit_release_detail` | 187 | query | `BusinessEvent.tenant_id == tenant_id, BusinessEvent.event_type == 'commitment.hold_released', BusinessEvent.action_id == proposal.id` |
| S053 | `services/credit_hold_actions.py:credit_release_detail` | 197 | if | `payloads and all((payload.get('document_id') == intent.get('document_id') and payload.get('reason_code') == 'credit_check' for payload in payloads))` |
| S054 | `services/credit_hold_actions.py:credit_release_detail` | 209 | if | `proposal.status != 'executed' or result['receipt'] == receipt` |
| S055 | `services/credit_hold_actions.py:credit_release_detail` | 211 | conditional | `proposal.status == 'executed'` |
| S056 | `services/credit_hold_actions.py:credit_release_detail` | 227 | if | `proposal.status == 'proposed'` |
| S057 | `services/credit_hold_actions.py:credit_release_detail` | 230 | if | `result['verification'] == 'recorded_unsettled'` |
| S058 | `services/credit_hold_actions.py:credit_release_detail` | 235 | if | `result['verification'] == 'verified'` |
| S059 | `services/fulfillment_readiness.py:stock_cover` | 192 | if | `location_id == own_location_id` |
| S060 | `services/fulfillment_readiness.py:fulfillment_readiness` | 232 | query | `Commitment.tenant_id == tenant_id, Commitment.id == commitment_id` |
| S061 | `services/fulfillment_readiness.py:fulfillment_readiness` | 237 | if | `commitment is None` |
| S062 | `services/fulfillment_readiness.py:fulfillment_readiness` | 239 | if | `commitment.type != 'customer_delivery'` |
| S063 | `services/fulfillment_readiness.py:fulfillment_readiness` | 248 | conditional | `proposed_quantity is None` |
| S064 | `services/fulfillment_readiness.py:fulfillment_readiness` | 249 | if | `proposed_quantity is not None and (checked_quantity <= ZERO or checked_quantity > open_quantity)` |
| S065 | `services/fulfillment_readiness.py:fulfillment_readiness` | 256 | query | `Reservation.tenant_id == tenant_id, Reservation.commitment_id == commitment.id, Reservation.status == 'active'` |
| S066 | `services/fulfillment_readiness.py:fulfillment_readiness` | 270 | conditional | `commitment.item_id` |
| S067 | `services/fulfillment_readiness.py:fulfillment_readiness` | 276 | if | `from_location_id` |
| S068 | `services/fulfillment_readiness.py:fulfillment_readiness` | 289 | query | `CommitmentHold.tenant_id == tenant_id, CommitmentHold.commitment_id == commitment.id, CommitmentHold.released_at.is_(None)` |
| S069 | `services/fulfillment_readiness.py:fulfillment_readiness` | 299 | conditional | `commitment.to_party_id` |
| S070 | `services/fulfillment_readiness.py:fulfillment_readiness` | 303 | conditional | `party_hold` |
| S071 | `services/fulfillment_readiness.py:fulfillment_readiness` | 305 | if | `commitment_hold_ids` |
| S072 | `services/fulfillment_readiness.py:fulfillment_readiness` | 307 | if | `party_hold_ids` |
| S073 | `services/fulfillment_readiness.py:fulfillment_readiness` | 309 | if | `reserved_quantity < checked_quantity` |
| S074 | `services/fulfillment_readiness.py:fulfillment_readiness` | 311 | if | `physical_quantity < checked_quantity or reserved_quantity >= checked_quantity > ready_quantity` |
| S075 | `services/fulfillment_readiness.py:fulfillment_readiness` | 315 | if | `not commitment.document_id` |
| S076 | `services/fulfillment_readiness.py:fulfillment_readiness` | 336 | query | `Document.tenant_id == tenant_id, Document.id == commitment.document_id` |
| S077 | `services/fulfillment_readiness.py:fulfillment_readiness` | 341 | if | `order is None or order.type != 'sales_order'` |
| S078 | `services/fulfillment_readiness.py:fulfillment_readiness` | 344 | conditional | `order.payment_term_id` |
| S079 | `services/fulfillment_readiness.py:fulfillment_readiness` | 345 | query | `PaymentTerm.tenant_id == tenant_id, PaymentTerm.id == order.payment_term_id` |
| S080 | `services/fulfillment_readiness.py:fulfillment_readiness` | 354 | if | `term is None or not term.requires_prepayment` |
| S081 | `services/fulfillment_readiness.py:fulfillment_readiness` | 377 | query | `DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == order.id` |
| S082 | `services/fulfillment_readiness.py:fulfillment_readiness` | 385 | query | `DocumentLine.tenant_id == tenant_id, Document.type == 'sales_invoice', Document.party_id == order.party_id, Document.currency == order.currency, DocumentLine.billed_document_line_id.in_(order_line_ids)` |
| S083 | `services/fulfillment_readiness.py:fulfillment_readiness` | 418 | query | `DocumentLine.tenant_id == tenant_id, DocumentLine.id.in_(select(DocumentLine.billed_document_line_id).where(DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == invoice_id, DocumentLine.billed_document_line_id.is_not(None)))` |
| S084 | `services/fulfillment_readiness.py:fulfillment_readiness` | 428 | query | `DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == invoice_id, DocumentLine.billed_document_line_id.is_not(None)` |
| S085 | `services/fulfillment_readiness.py:fulfillment_readiness` | 436 | if | `any(((party, currency) != (order.party_id, order.currency) for party, currency, _ in billed_orders))` |
| S086 | `services/fulfillment_readiness.py:fulfillment_readiness` | 441 | if | `any((document_id != order.id for _, _, document_id in billed_orders))` |
| S087 | `services/fulfillment_readiness.py:fulfillment_readiness` | 446 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.document_id.in_(candidate_invoice_ids), LedgerEntry.account == 'accounts_receivable', LedgerEntry.party_id == order.party_id, LedgerEntry.currency == order.currency` |
| S088 | `services/fulfillment_readiness.py:fulfillment_readiness` | 455 | comprehension | `entry.document_id` |
| S089 | `services/fulfillment_readiness.py:fulfillment_readiness` | 462 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.id.in_(payment_entry_ids), LedgerEntry.party_id == order.party_id, LedgerEntry.currency == order.currency` |
| S090 | `services/fulfillment_readiness.py:fulfillment_readiness` | 471 | comprehension | `entry.document_id in consolidated` |
| S091 | `services/fulfillment_readiness.py:fulfillment_readiness` | 474 | conditional | `ambiguous` |
| S092 | `services/fulfillment_readiness.py:fulfillment_readiness` | 479 | comprehension | `row.invoice_ledger_entry_id in entry_ids and row.invoice_ledger_entry_id not in consolidated_entries and (row.payment_ledger_entry_id in valid_payments) and (row.currency == order.currency)` |
| S093 | `services/fulfillment_readiness.py:fulfillment_readiness` | 487 | if | `not ambiguous` |
| S094 | `services/fulfillment_readiness.py:fulfillment_readiness` | 489 | query | `Document.tenant_id == tenant_id, Document.id.in_(consolidated)` |
| S095 | `services/fulfillment_readiness.py:fulfillment_readiness` | 494 | if | `open_amount > ZERO` |
| S096 | `services/fulfillment_readiness.py:fulfillment_readiness` | 501 | query | `DocumentLine.tenant_id == tenant_id, DocumentLine.document_id == invoice.id, DocumentLine.billed_document_line_id.in_(order_line_ids)` |
| S097 | `services/fulfillment_readiness.py:fulfillment_readiness` | 526 | if | `not invoice_ids` |
| S098 | `services/fulfillment_readiness.py:fulfillment_readiness` | 528 | if | `ambiguous` |
| S099 | `services/fulfillment_readiness.py:fulfillment_readiness` | 530 | if | `consolidated_open` |
| S100 | `services/fulfillment_readiness.py:fulfillment_readiness` | 532 | if | `remaining > ZERO` |
| S101 | `services/fulfillment_readiness.py:require_paid_prepayment` | 580 | if | `movement_type != 'shipment' or not commitment_id` |
| S102 | `services/fulfillment_readiness.py:require_paid_prepayment` | 583 | query | `Commitment.tenant_id == tenant_id, Commitment.id == commitment_id` |
| S103 | `services/fulfillment_readiness.py:require_paid_prepayment` | 587 | if | `kind != 'customer_delivery'` |
| S104 | `services/fulfillment_readiness.py:require_paid_prepayment` | 592 | comprehension | `code in PAYMENT_BLOCKERS` |
| S105 | `services/fulfillment_readiness.py:require_paid_prepayment` | 593 | if | `payment` |
| S106 | `services/proposal_decisions.py:resolve_decision_policy` | 35 | if | `tool in FINANCE_COMMANDS or tool == 'credit_hold_release'` |
| S107 | `services/proposal_decisions.py:resolve_decision_policy` | 38 | conditional | `tool == 'credit_hold_release'` |
| S108 | `services/proposal_decisions.py:resolve_decision_policy` | 41 | if | `tool == 'cost.change'` |
| S109 | `services/proposal_decisions.py:resolve_decision_policy` | 44 | if | `tool in {'graph.reports.change', 'graph.requests.create'}` |
| S110 | `services/proposal_decisions.py:resolve_decision_policy` | 47 | conditional | `tool == 'graph.reports.change'` |
| S111 | `services/proposal_decisions.py:resolve_decision_policy` | 49 | if | `tool in MEMBERSHIP_MUTATION_TOOLS` |
| S112 | `services/proposal_decisions.py:resolve_decision_policy` | 53 | if | `tool in ACCOUNT_MUTATION_TOOLS` |
| S113 | `services/proposal_decisions.py:resolve_decision_policy` | 56 | if | `'_delivery_review' in arguments` |
| S114 | `services/proposal_decisions.py:resolve_decision_policy` | 58 | if | `authority == 'action_context'` |
| S115 | `services/proposal_decisions.py:resolve_decision_policy` | 61 | if | `tool in REFERENCE_MUTATION_TOOLS` |
| S116 | `services/proposal_decisions.py:resolve_decision_policy` | 74 | conditional | `approval_available` |
| S117 | `services/proposal_decisions.py:require_decision_authority` | 98 | if | `phase == 'preflight'` |
| S118 | `services/proposal_decisions.py:require_decision_authority` | 99 | if | `'cost_owner' in policy.checks` |
| S119 | `services/proposal_decisions.py:require_decision_authority` | 102 | if | `not confirmed` |
| S120 | `services/proposal_decisions.py:require_decision_authority` | 105 | if | `'credit_owner' in policy.checks` |
| S121 | `services/proposal_decisions.py:require_decision_authority` | 106 | if | `principal is not None` |
| S122 | `services/proposal_decisions.py:require_decision_authority` | 108 | if | `os.environ.get('REALITY_AUTH_MODE') != 'disabled'` |
| S123 | `services/proposal_decisions.py:require_decision_authority` | 110 | if | `phase == 'identity'` |
| S124 | `services/proposal_decisions.py:require_decision_authority` | 111 | if | `'membership_identity' in policy.checks and principal is None` |
| S125 | `services/proposal_decisions.py:require_decision_authority` | 113 | if | `'account_identity' in policy.checks and principal is None` |
| S126 | `services/proposal_decisions.py:require_decision_authority` | 115 | if | `phase == 'execution' and 'finance_owner' in policy.checks` |
| S127 | `services/proposal_decisions.py:require_decision_authority` | 116 | if | `principal is not None` |
| S128 | `services/proposal_decisions.py:require_decision_authority` | 118 | if | `os.environ.get('REALITY_AUTH_MODE') != 'disabled'` |
| S129 | `services/proposal_decisions.py:require_decision_authority` | 120 | if | `phase == 'locked' and 'reviewed_member' in policy.checks` |
| S130 | `services/proposal_decisions.py:require_decision_authority` | 122 | if | `phase == 'reference' and 'reference_member' in policy.checks` |
| S131 | `services/delivery_actions.py:validate_review` | 584 | if | `not review or not confirmed or token != review['token']` |
| S132 | `services/delivery_actions.py:validate_review` | 586 | comprehension | `key != REVIEW_KEY` |
| S133 | `services/delivery_actions.py:validate_review` | 588 | if | `current['token'] != review['token']` |
| S134 | `services/delivery_actions.py:validate_review` | 590 | conditional | `tool in PAYMENT_TOOLS` |
| S135 | `services/delivery_actions.py:validate_review` | 592 | conditional | `tool == 'ledger_reverse'` |
| S136 | `services/delivery_actions.py:validate_review` | 594 | conditional | `tool == 'item_create'` |
| S137 | `services/delivery_actions.py:validate_review` | 596 | conditional | `is_opening(tool, arguments)` |
| S138 | `services/delivery_actions.py:validate_review` | 598 | conditional | `tool in CUSTOMER_HOLD_TOOLS` |
| S139 | `services/delivery_actions.py:validate_review` | 602 | if | `tool == 'commitment_revise' and current['effect'].get('selection_required') and (not current['intent'].get('retained_allocations'))` |
| S140 | `services/delivery_actions.py:require_delivery_principal` | 1155 | if | `principal is None` |
| S141 | `services/delivery_actions.py:require_delivery_principal` | 1160 | query | `AppUser.id == principal.user_id` |
| S142 | `services/delivery_actions.py:require_delivery_principal` | 1164 | if | `user is None or (user.status != 'active' and (not user.is_platform_admin))` |
| S143 | `services/delivery_actions.py:require_delivery_principal` | 1166 | if | `not user.is_platform_admin and (not session.scalar(select(TenantMembership.id).where(TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == principal.user_id, TenantMembership.status == 'active')))` |
| S144 | `services/delivery_actions.py:require_delivery_principal` | 1167 | query | `TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == principal.user_id, TenantMembership.status == 'active'` |
| S145 | `services/core.py:_financial_open_items` | 11658 | query | `Document.id.in_(document_ids) if document_ids is not None else True` |
| S146 | `services/core.py:_financial_open_items` | 11658 | query | `Document.party_id.in_(party_ids) if party_ids is not None else True` |
| S147 | `services/core.py:_financial_open_items` | 11658 | query | `Document.tenant_id == tenant_id, Document.type.in_(('sales_invoice', 'supplier_invoice', 'opening_customer_debt', 'opening_supplier_debt', 'down_payment_invoice'))` |
| S148 | `services/core.py:_financial_open_items` | 11672 | conditional | `document_ids is not None` |
| S149 | `services/core.py:_financial_open_items` | 11673 | conditional | `party_ids is not None` |
| S150 | `services/core.py:_financial_open_items` | 11680 | query | `Party.tenant_id == tenant_id, Party.id.in_({document.party_id for document in documents})` |
| S151 | `services/core.py:_financial_open_items` | 11691 | query | `OpeningItem.tenant_id == tenant_id, OpeningItem.document_id.in_([d.id for d in documents])` |
| S152 | `services/core.py:_financial_open_items` | 11698 | conditional | `opening_details` |
| S153 | `services/core.py:_financial_open_items` | 11700 | query | `OpeningItem.tenant_id == tenant_id, OpeningItem.document_id.in_(opening_details)` |
| S154 | `services/core.py:_financial_open_items` | 11724 | if | `position is None` |
| S155 | `services/core.py:_financial_open_items` | 11729 | conditional | `effective_before` |
| S156 | `services/core.py:_financial_open_items` | 11733 | conditional | `document.id in opening_details` |
| S157 | `services/core.py:_financial_open_items` | 11735 | conditional | `document.id in opening_details` |
| S158 | `services/core.py:_financial_open_items` | 11738 | conditional | `party` |
| S159 | `services/core.py:_financial_open_items` | 11739 | conditional | `party` |
| S160 | `services/core.py:_financial_open_items` | 11744 | conditional | `relation and role == 'reversed_original'` |
| S161 | `services/core.py:_financial_open_items` | 11746 | conditional | `open_amount == ZERO` |
| S162 | `services/core.py:_financial_open_items` | 11748 | conditional | `open_amount < gross` |
| S163 | `services/core.py:active_settlement_allocations` | 11971 | if | `entry_ids is not None and (not entry_ids)` |
| S164 | `services/core.py:active_settlement_allocations` | 11973 | query | `SettlementAllocation.tenant_id == tenant_id` |
| S165 | `services/core.py:active_settlement_allocations` | 11976 | if | `entry_ids is not None` |
| S166 | `services/core.py:active_settlement_allocations` | 11977 | query | `or_(SettlementAllocation.payment_ledger_entry_id.in_(entry_ids), SettlementAllocation.invoice_ledger_entry_id.in_(entry_ids))` |
| S167 | `services/core.py:active_settlement_allocations` | 11984 | if | `not allocations` |
| S168 | `services/core.py:active_settlement_allocations` | 11997 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.effective_at < effective_before if effective_before else True, LedgerEntry.id.in_(entry_ids)` |
| S169 | `services/core.py:active_settlement_allocations` | 11999 | conditional | `effective_before` |
| S170 | `services/core.py:active_settlement_allocations` | 12008 | query | `LedgerReversal.tenant_id == tenant_id, LedgerReversal.reversed_at < effective_before if effective_before else True, LedgerReversal.original_posting_group_id.in_({entry.posting_group_id for entry in entries.values()})` |
| S171 | `services/core.py:active_settlement_allocations` | 12010 | conditional | `effective_before` |
| S172 | `services/core.py:active_settlement_allocations` | 12022 | comprehension | `entries.get(row.payment_ledger_entry_id) is not None and entries.get(row.invoice_ledger_entry_id) is not None and (entries[row.payment_ledger_entry_id].posting_group_id not in reversed_groups) and (entries[row.invoice_ledger_entry_id].posting_group_id not in reversed_groups)` |
| S173 | `services/core.py:open_invoice_amount` | 11592 | if | `allocations is None` |
| S174 | `services/core.py:_settlement_control_entries` | 11117 | comprehension | `document.type in SETTLEMENT_CONTROL` |
| S175 | `services/core.py:_settlement_control_entries` | 11119 | if | `not wanted` |
| S176 | `services/core.py:_settlement_control_entries` | 11123 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.effective_at < effective_before if effective_before else True, LedgerEntry.document_id.in_(list(wanted)), LedgerEntry.account.in_({account for account, _ in wanted.values()})` |
| S177 | `services/core.py:_settlement_control_entries` | 11125 | conditional | `effective_before` |
| S178 | `services/core.py:_settlement_control_entries` | 11130 | if | `(entry.account, entry.debit_credit) == wanted[entry.document_id]` |
| S179 | `services/core.py:_ledger_reversal_roles` | 11147 | if | `not posting_group_ids` |
| S180 | `services/core.py:_ledger_reversal_roles` | 11151 | query | `LedgerReversal.tenant_id == tenant_id, LedgerReversal.reversed_at < effective_before if effective_before else True, or_(LedgerReversal.original_posting_group_id.in_(posting_group_ids), LedgerReversal.reversing_posting_group_id.in_(posting_group_ids))` |
| S181 | `services/core.py:_ledger_reversal_roles` | 11153 | conditional | `effective_before` |
| S182 | `services/core.py:_ledger_reversal_roles` | 11165 | if | `relation.reversing_posting_group_id in posting_group_ids` |
| S183 | `services/core.py:_ledger_reversal_roles` | 11170 | if | `relation.original_posting_group_id in posting_group_ids` |
| S184 | `services/core.py:_document_account_balances` | 11184 | if | `not accounts or not document_ids` |
| S185 | `services/core.py:_document_account_balances` | 11188 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.effective_at < effective_before if effective_before else True, LedgerEntry.account.in_(accounts), LedgerEntry.document_id.in_(document_ids)` |
| S186 | `services/core.py:_document_account_balances` | 11196 | conditional | `effective_before` |
| S187 | `services/core.py:_document_account_balances` | 11204 | conditional | `side == 'debit'` |
| S188 | `services/core.py:_open_amount` | 11300 | if | `role == 'reversed_original'` |
| S189 | `services/core.py:_open_amount` | 11302 | conditional | `control.debit_credit == 'debit'` |
| S190 | `services/core.py:commitment_terms` | 3444 | conditional | `commitment_ids is None` |
| S191 | `services/core.py:commitment_terms` | 3445 | if | `ids is not None and (not ids)` |
| S192 | `services/core.py:commitment_terms` | 3447 | query | `Commitment.tenant_id == tenant_id` |
| S193 | `services/core.py:commitment_terms` | 3449 | query | `CommitmentRevision.tenant_id == tenant_id` |
| S194 | `services/core.py:commitment_terms` | 3454 | query | `Reservation.tenant_id == tenant_id, Reservation.status == 'active'` |
| S195 | `services/core.py:commitment_terms` | 3458 | if | `ids is not None` |
| S196 | `services/core.py:commitment_terms` | 3459 | query | `Commitment.id.in_(ids)` |
| S197 | `services/core.py:commitment_terms` | 3460 | query | `CommitmentRevision.commitment_id.in_(ids)` |
| S198 | `services/core.py:commitment_terms` | 3463 | query | `Reservation.commitment_id.in_(ids)` |
| S199 | `services/core.py:commitment_terms` | 3476 | conditional | `commitment.type == 'customer_delivery'` |
| S200 | `services/core.py:_movement_quantities` | 3243 | query | `Movement.tenant_id == tenant_id` |
| S201 | `services/core.py:_movement_quantities` | 3248 | query | `MovementCorrection.tenant_id == tenant_id, Movement.tenant_id == tenant_id` |
| S202 | `services/core.py:_movement_quantities` | 3257 | if | `commitment_id is not None` |
| S203 | `services/core.py:_movement_quantities` | 3258 | query | `Movement.commitment_id == commitment_id` |
| S204 | `services/core.py:_movement_quantities` | 3259 | query | `Movement.commitment_id == commitment_id` |
| S205 | `services/core.py:_effective_commitment_value` | 3389 | if | `value is not None` |
| S206 | `services/core.py:stock_at` | 3776 | if | `location_id` |
| S207 | `services/core.py:stock_at` | 3778 | query | `Movement.tenant_id == tenant_id, Movement.item_id == item_id, Movement.to_location_id.is_not(None)` |
| S208 | `services/core.py:stock_at` | 3783 | query | `Movement.tenant_id == tenant_id, Movement.item_id == item_id, Movement.from_location_id.is_not(None)` |
| S209 | `services/core.py:stock_at` | 3788 | if | `location_id` |
| S210 | `services/core.py:stock_at` | 3789 | query | `Movement.to_location_id == location_id` |
| S211 | `services/core.py:stock_at` | 3790 | query | `Movement.from_location_id == location_id` |
| S212 | `services/core.py:blocked_quantity` | 3925 | query | `StockBlock.tenant_id == tenant_id, StockBlock.item_id == item_id, StockBlock.status == 'active'` |
| S213 | `services/core.py:blocked_quantity` | 3930 | if | `location_id` |
| S214 | `services/core.py:blocked_quantity` | 3931 | query | `StockBlock.location_id == location_id` |
| S215 | `services/core.py:blocked_quantity` | 3937 | if | `value` |
| S216 | `services/core.py:blocked_quantity` | 3938 | query | `field == value` |
| S217 | `services/core.py:active_party_delivery_hold` | 6520 | query | `PartyHold.tenant_id == tenant_id, PartyHold.party_id == party_id, PartyHold.hold_type == 'delivery', PartyHold.released_at.is_(None)` |
| S218 | `services/core.py:release_commitment_hold` | 6425 | if | `action_id` |
| S219 | `services/core.py:release_commitment_hold` | 6429 | query | `CommitmentHold.tenant_id == tenant_id, CommitmentHold.commitment_id == commitment_id, CommitmentHold.released_at.is_(None), ~(CommitmentHold.reason_code.in_(_keep_reason_codes) & (CommitmentHold.created_by == CREDIT_CHECK_CREATOR))` |
| S220 | `services/core.py:release_commitment_hold` | 6445 | if | `holds` |
| S221 | `services/core.py:release_commitment_hold` | 6456 | if | `_commit` |
| S222 | `services/core.py:release_document_holds` | 6503 | query | `Commitment.tenant_id == tenant_id, Commitment.document_id == document_id` |
| S223 | `services/core.py:with_invoice_aging` | 14110 | if | `row.get('origin') == 'opening'` |
| S224 | `services/core.py:with_invoice_aging` | 14121 | conditional | `row.get('origin') == 'opening'` |
| S225 | `services/core.py:_payment_terms_by_id` | 14094 | query | `PaymentTerm.tenant_id == tenant_id` |
| S226 | `services/core.py:invoice_due_date` | 14062 | if | `document_day is None` |
| S227 | `services/core.py:invoice_due_date` | 14064 | conditional | `term` |
| S228 | `services/core.py:invoice_discount_date` | 14075 | if | `term is None or term.discount_percent is None or term.discount_days is None` |
| S229 | `services/core.py:invoice_discount_date` | 14078 | if | `document_day is None` |
| S230 | `services/core.py:invoice_days_overdue` | 14085 | if | `due_date is None` |
| S231 | `services/finance/credits.py:available_credit_rows` | 33 | if | `side not in {'customer', 'supplier'}` |
| S232 | `services/finance/credits.py:available_credit_rows` | 36 | conditional | `customer` |
| S233 | `services/finance/credits.py:available_credit_rows` | 37 | query | `LedgerReversal.tenant_id == tenant_id, LedgerReversal.reversed_at < effective_before if effective_before else True` |
| S234 | `services/finance/credits.py:available_credit_rows` | 39 | conditional | `effective_before` |
| S235 | `services/finance/credits.py:available_credit_rows` | 42 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.effective_at < effective_before if effective_before else True, LedgerEntry.account == role, LedgerEntry.debit_credit == ('credit' if customer else 'debit'), LedgerEntry.posting_group_id.not_in(reversal_groups), Document.type.in_((f'{side}_payment', f'{side}_deposit', f'opening_{side}_credit', 'credit_note' if customer else 'supplier_credit_note'))` |
| S236 | `services/finance/credits.py:available_credit_rows` | 54 | conditional | `effective_before` |
| S237 | `services/finance/credits.py:available_credit_rows` | 56 | conditional | `customer` |
| S238 | `services/finance/credits.py:available_credit_rows` | 63 | conditional | `customer` |
| S239 | `services/finance/credits.py:available_credit_rows` | 68 | if | `query.strip()` |
| S240 | `services/finance/credits.py:available_credit_rows` | 70 | query | `or_(Document.number.ilike(match), Document.id.ilike(match), Party.name.ilike(match))` |
| S241 | `services/finance/credits.py:available_credit_rows` | 77 | if | `party_id` |
| S242 | `services/finance/credits.py:available_credit_rows` | 78 | query | `LedgerEntry.party_id == party_id` |
| S243 | `services/finance/credits.py:available_credit_rows` | 79 | if | `party_ids is not None` |
| S244 | `services/finance/credits.py:available_credit_rows` | 80 | query | `LedgerEntry.party_id.in_(party_ids)` |
| S245 | `services/finance/credits.py:available_credit_rows` | 93 | comprehension | `document.type.startswith('opening_')` |
| S246 | `services/finance/credits.py:available_credit_rows` | 98 | conditional | `opening_ids` |
| S247 | `services/finance/credits.py:available_credit_rows` | 100 | query | `OpeningItem.tenant_id == tenant_id, OpeningItem.document_id.in_(opening_ids)` |
| S248 | `services/finance/credits.py:available_credit_rows` | 118 | conditional | `available == 0` |
| S249 | `services/finance/credits.py:available_credit_rows` | 118 | conditional | `used` |
| S250 | `services/finance/credits.py:available_credit_rows` | 119 | if | `status and (state not in {'open', 'partial'} if status == 'outstanding' else state != status)` |
| S251 | `services/finance/credits.py:available_credit_rows` | 120 | conditional | `status == 'outstanding'` |
| S252 | `services/finance/credits.py:available_credit_rows` | 130 | conditional | `document.type.startswith('opening_')` |
| S253 | `services/finance/credits.py:available_credit_rows` | 132 | conditional | `document.type.endswith('_deposit')` |
| S254 | `services/finance/credits.py:available_credit_rows` | 134 | conditional | `document.type.endswith('_payment')` |
| S255 | `services/down_payments.py:held_down_payments` | 614 | if | `not party_ids` |
| S256 | `services/down_payments.py:held_down_payments` | 619 | query | `Document.tenant_id == tenant_id, Document.type == 'down_payment_invoice', Document.party_id.in_(party_ids)` |
| S257 | `services/down_payments.py:held_down_payments` | 631 | if | `not row['reversed'] and row['offsettable'] > ZERO` |
| S258 | `services/down_payments.py:down_payment_invoices` | 260 | query | `Document.tenant_id == tenant_id, Document.type == 'down_payment_invoice', Document.order_document_id == order_id` |
| S259 | `services/down_payments.py:down_payment_invoices` | 271 | conditional | `reversed_` |
| S260 | `services/down_payments.py:down_payment_invoices` | 277 | conditional | `reversed_` |
| S261 | `services/down_payments.py:_reversed` | 71 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.document_id == document_id` |
| S262 | `services/down_payments.py:_reversed` | 77 | if | `not groups` |
| S263 | `services/down_payments.py:_reversed` | 81 | query | `LedgerReversal.tenant_id == tenant_id, LedgerReversal.original_posting_group_id.in_(groups)` |
| S264 | `services/down_payments.py:_cash_received` | 94 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.document_id == document_id, LedgerEntry.account == 'accounts_receivable', LedgerEntry.debit_credit == 'debit'` |
| S265 | `services/down_payments.py:_cash_received` | 102 | if | `not controls` |
| S266 | `services/down_payments.py:_cash_received` | 109 | comprehension | `row.invoice_ledger_entry_id in controls` |
| S267 | `services/down_payments.py:_cash_received` | 111 | if | `not allocations` |
| S268 | `services/down_payments.py:_cash_received` | 115 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.id.in_({row.payment_ledger_entry_id for row in allocations})` |
| S269 | `services/down_payments.py:_cash_received` | 125 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.account == 'cash', LedgerEntry.posting_group_id.in_(set(payment_groups.values()))` |
| S270 | `services/down_payments.py:_cash_received` | 136 | comprehension | `payment_groups.get(row.payment_ledger_entry_id) in cash_groups` |
| S271 | `services/down_payments.py:live_offsets` | 187 | query | `DownPaymentOffset.tenant_id == tenant_id` |
| S272 | `services/down_payments.py:live_offsets` | 188 | if | `down_payment_ids is not None` |
| S273 | `services/down_payments.py:live_offsets` | 189 | query | `DownPaymentOffset.down_payment_document_id.in_(down_payment_ids)` |
| S274 | `services/down_payments.py:live_offsets` | 192 | if | `final_invoice_ids is not None` |
| S275 | `services/down_payments.py:live_offsets` | 193 | query | `DownPaymentOffset.final_invoice_document_id.in_(final_invoice_ids)` |
| S276 | `services/down_payments.py:live_offsets` | 200 | comprehension | `row.final_invoice_document_id in live` |
| S277 | `services/down_payments.py:_offset_groups` | 146 | if | `not final_ids` |
| S278 | `services/down_payments.py:_offset_groups` | 150 | query | `LedgerEntry.tenant_id == tenant_id, LedgerEntry.document_id.in_(final_ids), LedgerEntry.account == 'customer_down_payments', LedgerEntry.debit_credit == 'debit'` |
| S279 | `services/down_payments.py:_offset_groups` | 160 | query | `LedgerReversal.tenant_id == tenant_id, LedgerReversal.original_posting_group_id.in_({group for values in groups.values() for group in values})` |
| S280 | `services/down_payments.py:_offset_groups` | 171 | comprehension | `(live := (values - reversed_groups))` |
| S281 | `services/down_payments.py:order_down_payment_invoice_ids` | 642 | query | `Document.tenant_id == tenant_id, Document.type == 'down_payment_invoice', Document.order_document_id == order_id` |
| S282 | `services/memberships.py:require_owner` | 76 | if | `membership is None` |
| S283 | `services/memberships.py:require_owner` | 78 | if | `membership.role != 'owner'` |
| S284 | `services/memberships.py:_active_membership` | 63 | query | `TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == user_id, TenantMembership.status == 'active'` |
| S285 | `tools/application.py:_movement_create` | 1011 | if | `arguments.get('occurred_at') is not None` |
| S286 | `tools/application.py:_movement_create` | 1013 | if | `opening_cost is not None` |
| S287 | `tools/application.py:_movement_create` | 1016 | if | `arguments.get('movement_type') != 'opening_stock' or not arguments['action_id']` |
| S288 | `tools/application.py:_movement_create` | 1042 | if | `not blocked` |
| S289 | `tools/application.py:_movement_create` | 1048 | if | `arguments.get('movement_type') != 'receipt'` |
| S290 | `tools/application.py:approve_and_execute_proposal` | 3800 | query | `ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id` |
| S291 | `tools/application.py:approve_and_execute_proposal` | 3805 | if | `candidate is None` |
| S292 | `tools/application.py:approve_and_execute_proposal` | 3814 | if | `'report_author' in authority_policy.checks` |
| S293 | `tools/application.py:approve_and_execute_proposal` | 3818 | if | `not confirmed` |
| S294 | `tools/application.py:approve_and_execute_proposal` | 3827 | if | `candidate.status == 'executed'` |
| S295 | `tools/application.py:approve_and_execute_proposal` | 3830 | if | `candidate.status == 'executing'` |
| S296 | `tools/application.py:approve_and_execute_proposal` | 3832 | if | `candidate.status == 'rejected'` |
| S297 | `tools/application.py:approve_and_execute_proposal` | 3834 | if | `candidate.status != 'proposed'` |
| S298 | `tools/application.py:approve_and_execute_proposal` | 3840 | if | `tool is None or not tool.mutating` |
| S299 | `tools/application.py:approve_and_execute_proposal` | 3850 | query | `Tenant.id == tenant_id` |
| S300 | `tools/application.py:approve_and_execute_proposal` | 3851 | if | `tenant and tenant.purpose != 'playground' and eligible(tool_name, arguments) and (REVIEW_KEY not in arguments) and (not (tool_name == 'movement_create' and arguments.get('movement_type') == 'opening_stock')) and (tool_name not in {'party_delivery_hold', 'party_delivery_hold_release'})` |
| S301 | `tools/application.py:approve_and_execute_proposal` | 3863 | if | `REVIEW_KEY in arguments and (not confirmed or review_token != arguments[REVIEW_KEY]['token'])` |
| S302 | `tools/application.py:approve_and_execute_proposal` | 3868 | if | `tool_name in FINANCE_COMMANDS` |
| S303 | `tools/application.py:approve_and_execute_proposal` | 3873 | if | `tool_name in {ADJUSTMENT_COMMAND, SETTLEMENT_COMMAND, OPENING_COMMAND, ASSIGNMENT_COMMAND, 'cost.change'}` |
| S304 | `tools/application.py:approve_and_execute_proposal` | 3885 | query | `ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id` |
| S305 | `tools/application.py:approve_and_execute_proposal` | 3893 | if | `proposal.status == 'executed'` |
| S306 | `tools/application.py:approve_and_execute_proposal` | 3895 | if | `proposal.status != 'proposed'` |
| S307 | `tools/application.py:approve_and_execute_proposal` | 3905 | conditional | `confirming_principal` |
| S308 | `tools/application.py:approve_and_execute_proposal` | 3923 | query | `ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id, ChangeProposal.status == 'proposed'` |
| S309 | `tools/application.py:approve_and_execute_proposal` | 3938 | if | `claimed_id is None` |
| S310 | `tools/application.py:approve_and_execute_proposal` | 3940 | query | `ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id` |
| S311 | `tools/application.py:approve_and_execute_proposal` | 3945 | if | `proposal is None` |
| S312 | `tools/application.py:approve_and_execute_proposal` | 3947 | if | `proposal.status == 'executed'` |
| S313 | `tools/application.py:approve_and_execute_proposal` | 3949 | if | `proposal.status == 'executing'` |
| S314 | `tools/application.py:approve_and_execute_proposal` | 3955 | if | `REVIEW_KEY in arguments` |
| S315 | `tools/application.py:approve_and_execute_proposal` | 3977 | if | `tool_name in REFERENCE_MUTATION_TOOLS` |
| S316 | `tools/application.py:approve_and_execute_proposal` | 3984 | if | `tenant and tenant.purpose != 'playground'` |
| S317 | `tools/application.py:approve_and_execute_proposal` | 3988 | if | `tool_name.endswith('_update')` |
| S318 | `tools/application.py:approve_and_execute_proposal` | 3999 | if | `tool_name in {'party_update', 'item_update', 'location_update', 'fact_observe', 'reserve', 'movement_create', 'movement_correct', 'reservation_release', 'party_delivery_hold', 'party_delivery_hold_release', 'commitment_hold', 'commitment_hold_release', 'party_create', 'item_create', 'location_create', 'order_create', 'customer_payment_post', 'sales_invoice_record', 'supplier_payment_post', 'supplier_invoice_record', 'supplier_invoice_free_record', 'supply_assign', 'return_disposition', 'customer_exchange_record', 'order_line_item_assign', 'credit_hold_release', 'reorder_point_set', 'reorder_point_remove', 'stock_block', 'stock_block_release', 'stock_block_scrap', 'down_payment_invoice_record', 'proforma_invoice_record', 'commitment_revise', 'commitment_cancel', 'sales_credit_record', 'customer_refund_post', 'ledger_reverse', 'shipment_notice_record', 'shipment_dispatch', 'shipment_receive', 'shipment_event_record', 'shipment_event_supersede'}` |
| S319 | `tools/application.py:approve_and_execute_proposal` | 4045 | if | `tool_name in ACCOUNT_MUTATION_TOOLS` |
| S320 | `tools/application.py:approve_and_execute_proposal` | 4050 | if | `'request_author' in authority_policy.checks` |
| S321 | `tools/application.py:approve_and_execute_proposal` | 4057 | if | `'report_author' in authority_policy.checks` |
| S322 | `tools/application.py:approve_and_execute_proposal` | 4072 | query | `ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id, ChangeProposal.status == 'executing'` |
| S323 | `tools/application.py:approve_and_execute_proposal` | 4082 | if | `tool_name in MASTER_TOOLS` |

Baseline totals: **53 business outcome obligations**, **62 source symbols**, **323 decision sites** ({'if': 161, 'comprehension': 17, 'conditional': 59, 'query': 86}). These are planning baseline counts, not a passing-test or complete-analysis claim.

## Integration call sites

The following callers add the hold inside existing order/revision transactions. Their full unrelated order-validation rules are not being redesigned, but every guard enclosing the listed invocation must be preserved by dynamic call resolution. Unsupported enclosing control flow must produce a partial result.

- [`core.revise_commitment`](../../../packages/reality-core/src/reality/services/core.py#L3733) invokes `hold_if_over_credit_limit` at line 3733; enclosing function starts at 3512.
- [`core.create_manual_order`](../../../packages/reality-core/src/reality/services/core.py#L8196) invokes `hold_if_over_credit_limit` at line 8196; enclosing function starts at 8036.
- [`core._shopify_interpretation`](../../../packages/reality-core/src/reality/services/core.py#L13180) invokes `hold_if_over_credit_limit` at line 13180; enclosing function starts at 12975.

## Existing executable test anchors

These are **candidate source files to inspect**, not claims that every branch is asserted or passed. Actual scenario setup, parameters, assertions and relationships are extracted on demand during implementation. Unasserted B/S obligations must show test gaps.

- `packages/reality-core/tests/test_credit_exposure.py`: exposure components, uninvoiced orders, other currencies, unpriced lines, over-limit and tenant scope.
- `packages/reality-core/tests/test_credit_hold.py`: record-and-hold intake, holds beside other holds, replay, owner reason, generic release preservation, cancellation/revision and stated amounts.
- `packages/reality-core/tests/test_credit_hold_adapters.py`: MCP schemas, Web/CLI shared entry points, cross-tenant rejection and inspector exposure.
- `packages/reality-core/tests/test_fulfillment_readiness.py`: stated prepayment, reversed/foreign evidence, attribution, consolidated invoices, stock/reservation/holds and tenant scope.
- `packages/reality-core/tests/test_proposal_decision_policy.py`: owner guidance/execution, membership and existing identity exceptions.
- `packages/reality-core/tests/finance/test_available_credits.py`: effective available credit; related down-payment, stock, movement-correction and settlement tests are discovered through the referenced helper sources.

## Completeness release gate

1. Resolve actual registered roots and all reachable outcome-affecting helper predicates for each reference request.
2. Compare extracted decisions with this baseline and include additional live decisions, never suppress changes to keep a count stable.
3. Represent prerequisites, calculations, selection filters, refusals, effects, authority and adapter distinctions, with exact source evidence and text/diagram equivalence.
4. Show actual assertion-linked tests or explicit test gaps for every declared outcome. Candidate discovery alone proves neither assertion coverage nor successful execution.
5. A business predicate left opaque, omitted due to bounds or based on a mismatched release makes the affected reference blueprint partial and fails FR-015's completed-blueprint gate.
6. Product comprehension still requires the documented ERP-professional exercise; agent/source-inventory review cannot substitute for it.

## Request-time business presentation (FR-020–FR-022)

Blueprint adds an optional BusinessPresentation with mode llm/unavailable/outdated,
language/model, source-cited overview, original-rule-linked business steps, contracted
original edges, original-scenario-linked Given/When/Then and an inference notice.
All channels obtain this response from the same explain service. Public input fields
are unchanged; callers cannot supply model prompts, provider URLs, keys, source paths
or company records. Interpretation is not cached or persisted. Short model request
aliases resolve to original server rule/source identities; unknown aliases reject the
entire answer. The model cannot supply edges or run results. Up to 12 assertion-linked
first test cases are sent; remaining definitions are available in technical evidence.
Source-only and case-comparison reads omit interpretation. Evidence is revalidated
after inference; drift discards prose and marks outdated.
