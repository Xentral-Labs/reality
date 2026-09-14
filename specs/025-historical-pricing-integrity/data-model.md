# Data Model: Historical Pricing Integrity

## Persistence decision

No migration and no new field. Existing records are sufficient.

## PriceList

Commercial configuration for one direction and currency, with lifecycle/default and
optional validity behavior. Changes affect future resolution only.

## PriceListEntry

One item/unit/quantity-tier price option with optional validity. An entry selected for
an agreement remains readable by opaque identity. This feature does not add destructive
delete or in-place price mutation.

## Applicability relationships

`PartyPriceList`, `PartyGroup`, `PartyGroupMember`, and `PartyGroupPriceList` determine
which list participates in a new decision. They are not copied onto DocumentLine and
their later state does not reinterpret an existing agreement.

## DocumentLine

Historical Evidence fields used by this feature:

- `id`, `tenant_id`, `document_id`: opaque ownership and Evidence identity;
- `item_id`, `sku`, `description`: agreed subject/display context;
- `quantity`, `unit_price`, `gross_amount`, `unit`: agreed commercial values;
- `price_list_entry_id`: optional shortest link to the selected pricing entry.

The optional relationship means:

- present: the resolver-selected entry explains the agreed price;
- absent: the price was agreed manually or came from Evidence without a supported
  pricing decision; no provenance is manufactured.

## Selected-entry attachment validation

No new relationship is introduced. The existing optional FK may be set by the shared
DocumentLine creation service only when the existing price resolver returns the same
opaque entry for the Document party/direction/currency/effective time and the line
item/quantity/unit, and its price equals the agreed unit price. A mismatch, foreign
identity, unsupported Document direction, or incomplete context rejects the entire
Document creation. A missing ID remains the explicit manual-price path.

## Derived historical explanation

The explanation is read-only and is not persisted. It contains two explicitly separate
parts:

1. `agreed`: the stored DocumentLine values and retained entry/list identity;
2. `current_resolution`: a new resolution for the requested comparison time, or an
   explicit unavailable reason.

Equality of amounts does not imply equality of identity or decision context.

## Reality independence

Existing Commitment, Reservation, Movement, and LedgerEntry records are not changed by
price configuration or explanation. They retain their established shortest links to
Document/DocumentLine where applicable.

## Validation and tenant rules

- Every traversal includes the same `tenant_id` as the line.
- A retained entry must belong to the line's tenant.
- Entry → PriceList traversal must remain inside that tenant.
- Foreign identities behave as not found and visible values are never used to repair a
  missing relationship.
- No cascade or destructive removal of referenced entries is introduced.

## State transitions

DocumentLine has no pricing state transition in this feature. Price configuration may
become active, inactive, applicable, expired, replaced, or lower priority for new work;
the agreed line snapshot remains unchanged across all transitions.
