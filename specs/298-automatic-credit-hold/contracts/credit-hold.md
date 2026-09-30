# Contract: Credit Exposure and Credit Hold Release

## Read `credit_exposure`

- Arguments: `party_id` (required) and `as_of` (optional ISO timestamp).
- Returns the derived exposure described in `data-model.md`, with amounts as decimal strings.
- Surfaces:
  - MCP `credit_exposure`
  - Web `GET /api/tenants/{tenant}/parties/{party_id}/credit-exposure`
  - CLI `credit-exposure --party-id`
- Refusals: `party_not_found`.

## Reviewed tool `credit_hold_release`

- Arguments: `document_id` (the sales order) and `reason` (required, non-blank).
- Review: prepared with `prepare_delivery_action`. It names:
  - the order
  - its promises with active `credit_check` holds
  - the exposure now
  - the reason
- Execution:
  - confirmed with the review token by an owner;
  - releases only the order's `credit_check` holds;
  - emits one `commitment.hold_released` event per promise with `reason_code` and `reason`.
- Surfaces:
  - MCP `credit_hold_release_propose` (strict schema)
  - Web through the delivery-action endpoints, plus an owner-only "Release credit hold" action on a held order
  - CLI `credit-hold-release-propose` and the existing confirm
- Refusals:
  - `credit_hold_release_reason_missing`
  - `credit_hold_not_found`
  - `company_owner_access_required`
  - `delivery_review_required`

## Changed: `commitment_hold_release`

- It leaves `credit_check` holds in place, and its review lists them.
- With only credit holds active, it refuses with `credit_hold_owner_release_required`.

## Changed: order entry

Each of these paths ends with the credit check for a new sales order:
- `order_create` / `create_manual_order`
- the Shopify interpretation
- the file `sales_order` import

The check adds the `credit_check` holds and the `commitment.held` events described in `data-model.md`. It never refuses the order.
