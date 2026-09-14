# Feature Specification: Historical Pricing Integrity

**Feature Branch**: `025-historical-pricing-integrity`
**Created**: 2026-09-02
**Status**: Implemented and final-review approved
**Language**: English
**Input**: "Close `004/FR-014` by proving that later pricing changes never rewrite agreed DocumentLine Evidence and that new commercial work uses the pricing valid for its own effective context."

## Context and Intent

### Problem

Reality can resolve sales and purchase prices from direct party, party-group, and
default price lists with quantity tiers and validity windows. A DocumentLine may retain
the selected pricing entry, but the repository lacks focused proof that later pricing
configuration changes cannot alter an already agreed line.

Without that proof, historical documents may appear to change when a list is replaced,
deactivated, reprioritized, or no longer valid. Operators would then be unable to
reproduce what was agreed, explain margin or invoice differences, or trust Evidence as
the stable boundary between commercial configuration and business history.

### Scope

- Preserve the agreed unit price, quantity, gross amount, currency, unit, and optional
  selected pricing-entry identity on an existing DocumentLine.
- Allow an existing shared DocumentLine creation path to retain an optional
  server-validated selected pricing-entry identity without automatically pricing every
  line.
- Prove that subsequent price-list, assignment, group-membership, tier, validity, or
  lifecycle changes do not rewrite existing Document or DocumentLine Evidence.
- Resolve new commercial work using only the pricing configuration applicable to its
  own party, item, quantity, direction, currency, unit, and effective time.
- Keep the historical line explainable through its retained pricing-entry identity
  when one was selected, even when that pricing configuration is no longer active for
  new work.
- Cover both sales and purchase pricing and enforce tenant isolation.
- Close only the documented `004/FR-014` historical non-rewrite gap.

### Non-Goals

- Adding discounts, promotions, rebates, tax calculation, FX conversion, or margin
  management.
- Introducing price approval, price-version authoring, scheduled publication, or bulk
  price import workflows.
- Repricing, amending, or correcting an agreed DocumentLine. Document correction remains
  governed by the Evidence correction workflow.
- Automatically resolving a price for every document creation path where callers
  currently provide an explicit agreed price.
- Closing the separate `004/FR-016` adapter-equivalence gap.
- Adding schema fields solely for this proof.

### Existing Contracts

- [`specs/004-master-data/spec.md`](../004-master-data/spec.md)
- [`docs/features/master_data.md`](../../docs/features/master_data.md)
- [`docs/features/operational_fields.md`](../../docs/features/operational_fields.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve an Agreed Price (Priority: P1)

As a commercial or finance operator, I can rely on an agreed document line remaining
unchanged after its underlying pricing configuration changes.

**Why this priority**: Documents are Evidence. If master-data changes can rewrite an
agreed price, historical reporting, reconciliation, and explanation are unreliable.

**Independent Test**: Create a line from a resolved price, capture all agreed and
explanation values, change every applicable pricing input, and prove that the existing
Document and DocumentLine retain exactly the captured values and identity.

**Acceptance Scenarios**:

1. **Given** a price is resolved for a party, item, quantity, direction, currency, unit,
   and effective time, **When** a DocumentLine records the agreed result, **Then** its
   unit price, gross amount, currency, unit, quantity, and selected pricing-entry
   identity equal the agreed values.
2. **Given** a caller proposes a selected pricing-entry identity while creating an
   agreed line, **When** the server cannot reproduce that selection from the line and
   document's commercial context, **Then** the line is rejected without partial
   Evidence.
3. **Given** an agreed line references a selected pricing entry, **When** its price list
   is renamed, deactivated, ceases to be default, or falls outside validity for new
   work, **Then** every stored value and relationship on the existing line remains
   unchanged.
4. **Given** an agreed line was created from direct or group pricing, **When** assignment
   priority, membership, or applicability later changes, **Then** the existing line
   remains unchanged.
5. **Given** an agreed line has produced downstream commitments or ledger postings,
   **When** pricing configuration changes, **Then** those Reality records and their
   derived operational or financial results remain unchanged.

---

### User Story 2 - Apply New Pricing Only to New Work (Priority: P1)

As a commercial operator, I can change future pricing without affecting prior
agreements, and new work uses the configuration applicable to its own effective
context.

**Why this priority**: Pricing maintenance must support new business while preserving
historical truth.

**Independent Test**: Agree one line under an earlier pricing context, introduce a new
applicable tier or assignment, resolve a later transaction, and verify old and new
results independently.

**Acceptance Scenarios**:

1. **Given** an earlier line retains price A, **When** a later applicable pricing entry
   yields price B, **Then** new work receives B while the earlier line remains A.
2. **Given** pricing entries have non-overlapping validity periods, **When** prices are
   resolved at each effective time, **Then** each resolution selects the entry valid at
   that time and neither result changes afterward.
3. **Given** direct, group, and default applicability changes between two agreements,
   **When** each is resolved in its own effective context, **Then** each records its own
   selected precedence source without retroactive repricing.
4. **Given** a caller explicitly supplies an agreed line price without a selected
   pricing entry, **When** master pricing later changes, **Then** that line remains valid
   and unchanged without manufactured provenance.

---

### User Story 3 - Explain Historical Pricing Safely (Priority: P2)

As an operator or auditor, I can distinguish the price agreed on a historical line from
the price that would be resolved for new work today.

**Why this priority**: A price difference must be explainable without presenting current
master data as if it were historical Evidence.

**Independent Test**: Inspect an older line after pricing changes and compare its agreed
values and retained pricing identity with a fresh resolution for the same commercial
inputs.

**Acceptance Scenarios**:

1. **Given** an existing line and changed current pricing, **When** the line is read or
   inspected, **Then** the agreed line values lead and current pricing does not replace
   them.
2. **Given** the line retains a pricing-entry identity, **When** it is explained, **Then**
   the explanation uses that opaque relationship and does not infer identity from list
   codes, item SKUs, names, or amounts.
3. **Given** a pricing-entry or line identity from another tenant, **When** historical
   pricing is read, resolved, or linked, **Then** the foreign record is not disclosed or
   attached.

### Edge Cases

- A price list is inactive now but was valid when the line was agreed.
- A former default list is replaced by another default for the same direction and
  currency.
- Direct, group, or default precedence changes after agreement.
- Party-group membership starts or ends between two effective times.
- Quantity crosses a tier boundary for later work.
- Sales and purchase lists contain the same item and numeric price.
- A later price has the same amount but a different opaque pricing-entry identity.
- A line was entered manually and has no pricing-entry relationship.
- An agreed line references inactive Party, Item, or pricing configuration.
- A cross-tenant pricing entry has matching human codes, item SKU, currency, unit, and
  amount.
- A pricing change fails partway through; existing Evidence must still be unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An agreed DocumentLine MUST retain its stored quantity, unit price, gross
  amount, currency, unit, and optional selected pricing-entry identity unless an
  explicit Evidence correction workflow changes the line.
- **FR-002**: Any supported creation, update, lifecycle, assignment, membership,
  priority, or validity change to pricing configuration MUST NOT rewrite an existing
  Document or DocumentLine.
- **FR-003**: A retained pricing-entry relationship MUST remain readable for historical
  explanation even when that entry or its list is no longer applicable to new work.
- **FR-004**: New price resolution MUST evaluate the party, item, quantity, direction,
  currency, unit, precedence, lifecycle, and validity applicable to the requested
  effective time.
- **FR-005**: A later pricing result MUST affect only new work that explicitly records
  it; it MUST NOT trigger retroactive repricing of prior Evidence or Reality.
- **FR-006**: A manually agreed DocumentLine MAY have no selected pricing-entry
  relationship and MUST remain historical Evidence without manufactured pricing
  provenance.
- **FR-007**: Historical explanation MUST distinguish agreed line values from a current
  or newly resolved price and MUST NOT label current configuration as the historical
  agreement.
- **FR-008**: Pricing-entry relationships MUST use opaque tenant-owned identity; human
  codes, SKUs, names, dates, units, currencies, and amounts MUST NOT be used to recreate
  or infer the relationship.
- **FR-009**: Sales and purchase pricing histories MUST remain separate even when their
  visible values match.
- **FR-010**: Invalid and cross-tenant pricing references, resolutions, or attempts to
  attach a pricing entry to Evidence MUST fail without disclosing or mutating foreign
  records.
- **FR-011**: Failed pricing changes or resolutions MUST leave all pre-existing
  Document, DocumentLine, Commitment, Movement, and LedgerEntry records unchanged.
- **FR-012**: The historical non-rewrite rule MUST be shared by every supported caller;
  no interface may calculate or persist a competing historical price.
- **FR-013**: A supported DocumentLine creation path MUST accept an optional opaque
  selected pricing-entry identity only when the shared price resolver reproduces that
  exact entry, unit price, unit, currency, direction, party, item, quantity, and
  business-effective context; rejection MUST leave no partial Document or DocumentLine.

### Domain and Traceability Requirements

- **DR-001**: Price lists, entries, assignments, and memberships are current or
  time-bounded commercial configuration; Document and DocumentLine remain the Evidence
  of what was agreed.
- **DR-002**: The shortest true historical pricing relationship is DocumentLine to the
  selected pricing entry. The line MUST NOT duplicate list, assignment, group, or source
  relationships solely for convenience.
- **DR-003**: Commitments, Reservations, Movements, and LedgerEntries MUST continue to
  derive from or link through their established Evidence/Reality relationships; price
  maintenance MUST NOT rewrite them.
- **DR-004**: Every pricing lookup and historical relationship MUST be tenant-scoped and
  foreign identities MUST behave as not found.
- **DR-005**: The proof MUST not require new typed fields or a parallel price-history
  aggregate when immutable agreed line values and the optional selected-entry link are
  sufficient.

### Key Entities

- **PriceList**: A sales or purchase pricing context for one currency and validity
  interval.
- **PriceListEntry**: An item, unit, quantity-tier, price, and validity option considered
  during resolution.
- **PartyPriceList / PartyGroup pricing relationships**: Time-bounded applicability and
  precedence configuration for new price decisions.
- **DocumentLine**: Immutable Evidence of the agreed quantity and price, optionally
  linked to the selected pricing entry through its opaque identity.
- **Commitment / Movement / LedgerEntry**: Reality records that must remain unaffected
  by later price maintenance except through a separate explicit business correction.

## Success Criteria *(mandatory)*

- **SC-001**: In every covered pricing-change scenario, 100% of captured historical
  Document and DocumentLine values and identities remain byte-for-byte or numerically
  equivalent to their pre-change state.
- **SC-002**: Earlier and later effective contexts resolve their expected price and
  selected-entry identity in 100% of direct, group, default, tier, sales, and purchase
  acceptance cases.
- **SC-003**: Historical inspection always presents the agreed line value separately
  from any newly resolved value, with zero cases of current pricing replacing Evidence.
- **SC-004**: Cross-tenant and invalid pricing-reference cases produce no foreign
  disclosure and zero mutations to either tenant.
- **SC-005**: Failed pricing changes leave 100% of pre-existing Evidence and Reality
  records unchanged.
- **SC-006**: Every FR and DR maps to an acceptance scenario and executable proof or an
  explicitly owner-approved reason why automation is inappropriate.
- **SC-007**: The focused regression closes `004/FR-014` without adding a database field,
  a second pricing engine, or a retroactive repricing operation.

## Assumptions and Dependencies

- A DocumentLine becomes historical Evidence when the business operation records the
  agreed line; price lists remain configuration for new resolution decisions.
- Existing explicit Document correction semantics are the only supported way to change
  an agreed line after creation.
- Price validity uses the business-effective time supplied for the decision; callers
  that omit it intentionally request the current effective context.
- For a DocumentLine attachment, the business-effective time is the Document's ordered
  time when present, otherwise its document date at the start of that UTC day, otherwise
  the service's current time. Direction comes from the existing Document type
  vocabulary. A type without a supported commercial direction cannot retain a selected
  pricing entry.
- Price entries are retained while historically referenced. Removing or destructively
  overwriting referenced pricing entries is outside this feature and remains
  unsupported.
- Existing Decimal money and quantity behavior, UTC effective times, PostgreSQL storage,
  and tenant boundaries remain authoritative implementation constraints but do not
  change the product scope.
- Spec 025 closes only `004/FR-014`; all other documented gaps remain open.

## Open Questions

No unresolved product-scope questions. The smallest safe baseline is to prove and expose
the existing Evidence boundary without adding price-version authoring or automatic
repricing behavior.

The product owner approved this specification on 2026-09-02.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003, FR-013 | US1 scenarios 1–5; US3 scenarios 1–2 | Validated selected-entry attachment plus historical line snapshot before/after every pricing lifecycle and assignment change |
| FR-004–FR-005 | US2 scenarios 1–3 | Effective-time, tier, precedence, sales, and purchase comparison stories |
| FR-006–FR-009 | US2 scenario 4; US3 scenarios 1–2 | Manual-price, opaque-link, and direction-separation stories |
| FR-010–FR-012 | US1 scenario 4; US3 scenario 3 | Two-tenant, failure-atomicity, downstream non-mutation, and shared-boundary evidence |
| DR-001–DR-005 | All stories | Constitution, schema-diff, shortest-link, and Evidence-versus-configuration review |
| SC-001–SC-007 | All stories | Focused PostgreSQL regression, policy audit, and final owner review |
