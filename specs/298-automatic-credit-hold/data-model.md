# Data Model: Automatic Credit Hold

No schema change.

## Derived: credit exposure

Read at request time by `credit_exposure(party_id, as_of)`, and never stored.

| Field | Meaning |
|---|---|
| `currency` | The party's `default_currency`; only amounts in it are counted |
| `credit_limit` | As recorded on the party |
| `open_invoices` | Sum and rows (`document_id`, number, open, due date) |
| `overdue_invoices` | The open-invoice rows due before `as_of` |
| `open_orders` | Sum and rows (order, line, uninvoiced quantity, stated unit price, value); unpriced lines listed with value 0 |
| `available_credits` | Sum and rows (`document_id`, origin, available) |
| `exposure` | open invoices + open orders − available credits |
| `payables` | Sum and rows of open supplier invoices of the same party; not in `exposure` |
| `not_counted` | Documents in another currency |

## Reused: `commitment_hold`

A credit hold is a `commitment_hold` row. Only existing fields are used:
- `reason_code = "credit_check"`
- `created_by = "credit_limit"`
- `note` summarising the exposure

The facts at the moment of the decision are kept in the `commitment.held` event payload (`exposure` object above plus `order_value` and `limit`).

A release sets `released_at`. Its `commitment.hold_released` event names `reason_code` and the stated `reason`. The person comes from the decision trail of the confirming proposal.

## New refusal codes

- `credit_hold_release_reason_missing`: a credit hold is released only with a stated reason.
- `credit_hold_not_found`: the order has no active credit hold.
- `credit_hold_owner_release_required`: the generic release does not lift a credit hold.
- `company_owner_access_required` (existing): the confirming person is not an owner.
