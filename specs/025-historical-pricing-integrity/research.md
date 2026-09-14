# Research: Historical Pricing Integrity

## Decision 1: DocumentLine is the immutable agreement snapshot

**Decision**: Treat the line's stored quantity, unit price, gross amount, unit, and
optional selected-entry identity as the historical agreement.

**Rationale**: DocumentLine is already Evidence and downstream records already use its
agreed values. This proves the Constitution's existing boundary without introducing a
second history model.

**Alternatives considered**: Re-resolve prices whenever a document is read was rejected
because it rewrites history semantically. Copying the complete price list onto each line
was rejected as duplicated configuration and provenance.

## Decision 2: Retain one shortest explanation link

**Decision**: Use `DocumentLine.price_list_entry_id` when a resolver selected an entry;
do not add direct links to PriceList, PartyPriceList, PartyGroup, or assignment records.

**Rationale**: The selected entry identifies the price and leads directly to its parent
list. Assignment and membership describe applicability at decision time but are not the
agreed value itself.

**Alternatives considered**: A pricing-decision aggregate was rejected because the
current gap asks for non-rewrite proof, not a new legal audit object. Human-value lookup
was rejected because codes and amounts are not identity.

## Decision 3: Price configuration is append-oriented around referenced entries

**Decision**: New commercial prices use new entries or validity/applicability changes;
historically referenced entries remain readable and are not overwritten or deleted.

**Rationale**: Existing creation and validity semantics already support time-bounded
resolution. Preserving the selected entry makes historical explanation stable.

**Alternatives considered**: Adding an in-place entry update was rejected because it
would make the retained identity point to changed commercial meaning. Full bitemporal
price authoring was rejected as unproven scope.

## Decision 4: Compare agreed and current values through one read-only service

**Decision**: Provide one tenant-scoped explanation read that returns agreed Evidence
and, when inputs are sufficient, a separately labeled fresh resolution at a supplied
comparison time.

**Rationale**: Operators can understand a difference without the UI implementing price
logic or confusing current configuration with historical truth.

**Alternatives considered**: Showing only the entry ID was rejected as insufficiently
useful. Repricing and persisting the current result was rejected as a direct violation
of the feature.

## Decision 5: No new event or mutation

**Decision**: Reuse current pricing mutation events; historical explanation emits no
event and writes no data.

**Rationale**: The business change already occurs in the existing price configuration
services. This feature proves isolation of historical Evidence and adds a read model.

**Alternatives considered**: A `document_line.price_preserved` event was rejected
because absence of mutation is not a business event.

## Decision 6: Close only the pricing-history gap

**Decision**: Spec 025 may close `004/FR-014` only. Adapter equivalence and all other
coverage gaps remain unchanged.

**Rationale**: The work is independently testable and avoids mixing unrelated lifecycle
surface coverage into a historical-integrity proof.

**Alternatives considered**: Combining `004/FR-016` was rejected because it introduces
a much wider UI/CLI/API matrix and obscures the Evidence invariant.
