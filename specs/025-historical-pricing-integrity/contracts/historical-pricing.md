# Contract: Historical Pricing Explanation

## Purpose

Expose the difference between agreed DocumentLine Evidence and a fresh pricing decision
without changing either.

## Shared read input

- tenant identity;
- document-line opaque identity;
- optional comparison effective time.

The line supplies its document party/direction/currency and its own item, quantity, and
unit when these values are sufficient for comparison.

## Shared DocumentLine creation input

The existing line input gains one optional field:

```text
price_list_entry_id?
```

When present, the shared service must reproduce the exact entry through the authoritative
resolver using the Document party, commercial direction, currency, and effective time
plus the line item, quantity, unit, and unit price. Mismatch, foreign identity,
unsupported direction, or incomplete context rejects the complete Document creation.
When absent, the line remains an explicitly agreed manual/Evidence price and no pricing
provenance is invented. Transport layers pass the ID but do not validate pricing.

## Shared read result

```text
line_id
document_id
agreed:
  quantity
  unit
  unit_price
  gross_amount
  currency
  price_list_entry_id?
  price_list_id?
  price_list_code?
current_resolution:
  available
  compared_at
  unit_price?
  currency?
  unit?
  source?
  price_list_id?
  price_list_entry_id?
  unavailable_reason?
changed_since_agreement
```

`changed_since_agreement` compares both commercial value and selected-entry identity.
It never changes the `agreed` result.

## Behavior

- Read-only; repeated calls with the same effective context return equivalent results.
- If the line has no retained entry, `agreed.price_list_entry_id` remains absent.
- If current resolution is impossible because required inputs are absent, the result
  explains that it is unavailable rather than inventing values.
- An inactive or expired retained entry remains available for historical explanation.
- A foreign tenant's line, entry, list, party, or item is not disclosed.

## Document Inspector

The Lines section leads with quantity and agreed money. When a retained entry exists,
the row exposes its opaque pricing identity and list context. A current comparison is
visually and textually labeled as current, never historical. Manual pricing is labeled
as an agreement without a selected pricing entry.

## Compatibility

Existing document and Inspector fields remain unchanged. Historical pricing details are
additive read fields; the optional selected-entry input is additive to Document creation.
No caller receives general permission to update an agreed DocumentLine through this
contract.
