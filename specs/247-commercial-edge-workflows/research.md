# Research: Commercial Edge Workflows

## Separate dunning notice from its fee

**Decision**: Persist notice identity/membership separately; post an optional fee as its own charge.

**Rationale**: A reminder exists without a fee, while a fee changes receivables and needs ledger reversal.

**Alternatives considered**: Mutating the invoice destroys its stated value. Treating every notice as an invoice gives a zero-fee notice false financial meaning.

## Extend settlement adjustment for bad debt

**Decision**: Reuse the confirmed noncash-reduction service with a customer-only reason and dedicated account.

**Rationale**: It already preserves evidence, posts balanced entries, allocates one invoice and reverses cleanly.

**Alternatives considered**: A new balance table is a second authority; `accepted_small_remainder` misstates reason and account.

## Express deposits over ledger allocations

**Decision**: Use explicit deposit document types, normal cash/control postings and existing settlement allocations.

**Rationale**: The money is real; only its stated pre-invoice meaning differs. Availability remains a derivation.

**Alternatives considered**: A deposit balance table duplicates allocations. An ordinary payment hides the business meaning. Statutory deposit tax accounting is deferred.

## Reuse commitment revision for overdelivery

**Decision**: Expose and demonstrate a higher existing immutable revision before movement.

**Rationale**: Spec 097 accepts any positive quantity and fulfilment reads quantity in force.

**Alternatives considered**: Bypassing movement guards is inconsistent; mutating the order erases history.

## Manual first

**Decision**: No scheduled dunning or delivery channel.

**Rationale**: Recording and explaining the decision proves the core. Automation introduces separate policy and failure contracts.
