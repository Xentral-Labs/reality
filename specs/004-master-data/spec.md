# Feature Specification: Operational Master Data Baseline

**Baseline ID**: `004-master-data`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline existing Party, Item, Location, Payment Term, pricing, lifecycle, operational-field, and shared-adapter behavior."

## Context and Intent

### Problem

Operators need stable tenant-owned business identities and commercial settings that can
be reused by Evidence and Reality without making human labels or upstream payload fields
into identity. Contributors need one baseline that explains which master-data fields are
operationally proven, how lifecycle preserves history, and how price/payment decisions
are resolved.

### Scope

- Party identity, multiple roles, accounting/commercial fields, and source trace.
- Item identity, units, stock/service behavior, tracking, conversion, and purchasing
  defaults.
- Location identity, hierarchy, stock permission, lifecycle, and source trace.
- Payment terms and their use as opaque references from Party and Document.
- Sales and purchase price lists, quantity tiers, direct/group/default assignments, and
  deterministic price resolution.
- Create, read, update, deactivate, and reactivate behavior through shared services,
  CLI, API, and Web surfaces.
- Tenant-scoped suggestions and Inspector access to source provenance.

### Non-Goals

- Product variants, bills of materials, units-of-measure conversion graphs, or catalogs.
- Contact persons, postal addresses, bank accounts, or customer/supplier hierarchies.
- Percentage discounts, free goods, promotions, rebates, or tax calculation.
- Deleting master data that is linked to historical Evidence or Reality.
- Connector-specific master-data synchronization beyond immutable SourceRecord links.
- Defining party delivery holds, which belong to the commitments/holds baseline.

### Existing Contracts

- [`docs/features/master_data.md`](../../docs/features/master_data.md)
- [`docs/features/operational_fields.md`](../../docs/features/operational_fields.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

Party, Item, Location, PaymentTerm, PriceList, PriceListEntry, and pricing assignment
records are tenant-owned master data with opaque identities. Supported lifecycle
operations preserve inactive records for historical links. Source-backed Party, Item,
Location, and PaymentTerm records may point to the current immutable SourceRecord;
untyped external details remain in its payload.

Operational fields are included only where existing decisions repeatedly join, filter,
calculate, constrain, or act on them. Evidence such as an agreed document price remains
historical even when master pricing later changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain Operational References (Priority: P1)

As an operator, I can create and update Parties, Items, and Locations, deactivate them
for new work, and retain them for historical inspection.

**Why this priority**: These identities are prerequisites for commitments, inventory,
documents, finance, and explanation.

**Independent Test**: Perform create, list, update, deactivate, fetch, and reactivate
operations for all three record families through shared adapters and verify equivalent
tenant-scoped state.

**Acceptance Scenarios**:

1. **Given** valid Party, Item, or Location input, **When** it is created, **Then** it
   receives an opaque tenant-owned identity and begins active.
2. **Given** an active record, **When** it is deactivated, **Then** it remains readable
   and historically linked but unavailable for new operations requiring active data.
3. **Given** an inactive record, **When** it is reactivated, **Then** it becomes
   available for new operations without replacing its identity.
4. **Given** a foreign tenant's opaque ID, **When** an update or lifecycle change is
   attempted, **Then** the record is not found.

### User Story 2 - Preserve Source-Backed Master Data (Priority: P1)

As an operator, I can see where a master-data record came from and inspect its original
payload without promoting every upstream field into the operational schema.

**Why this priority**: Master data must remain traceable while the typed model stays
small and business-proven.

**Independent Test**: Create source-backed master data, update its external reference,
and verify that the current record links an immutable SourceRecord while prior source
truth remains unchanged.

**Acceptance Scenarios**:

1. **Given** a source system, external ID, and payload, **When** supported master data is
   created, **Then** the decoded payload is preserved in an immutable SourceRecord.
2. **Given** a changed source reference or payload, **When** the record is updated,
   **Then** new source truth is versioned rather than overwriting the previous payload.
3. **Given** a manual master-data record, **When** no source is supplied, **Then** the
   record remains valid without manufactured provenance.

### User Story 3 - Apply Proven Operational Fields (Priority: P1)

As an operator, I can classify Parties, Items, and Locations with the small set of typed
fields needed for operational decisions.

**Why this priority**: Incorrect or unbounded typing would either prevent core decisions
or turn Reality into a copy of upstream systems.

**Independent Test**: Create multi-role Parties, tracked and non-stock Items, and nested
Locations; verify normalization and operational constraints.

**Acceptance Scenarios**:

1. **Given** a Party with customer and supplier roles, **When** it is created, **Then**
   both roles reference one Party identity.
2. **Given** an Item with a non-positive conversion factor or negative lead time,
   **When** it is saved, **Then** validation rejects it.
3. **Given** a Location that disallows stock, **When** a physical movement references
   it, **Then** the movement is rejected.
4. **Given** a proposed parent that creates a Location cycle, **When** the hierarchy is
   updated, **Then** the change is rejected.

### User Story 4 - Resolve Commercial Terms (Priority: P2)

As a commercial operator, I can assign payment terms and resolve one applicable sales
or purchase price from direct, group, or default price lists and quantity tiers.

**Why this priority**: Repeatable commercial decisions need typed, explainable inputs
while agreed document values remain Evidence.

**Independent Test**: Configure default, group, and direct price lists with multiple
quantity tiers, then verify precedence, direction/currency separation, and the selected
price-list entry.

**Acceptance Scenarios**:

1. **Given** an active payment term code, **When** it is assigned to a Party or
   Document, **Then** the opaque PaymentTerm identity is stored.
2. **Given** an inactive payment term, **When** a new assignment is attempted, **Then**
   it is rejected while historical references remain valid.
3. **Given** applicable direct, group, and default lists, **When** a price is resolved,
   **Then** direct takes precedence over group, which takes precedence over default.
4. **Given** multiple applicable tiers in one list, **When** quantity is resolved,
   **Then** the highest minimum quantity not exceeding the requested quantity wins.
5. **Given** a purchase list, **When** a sales price is requested, **Then** it does not
   participate in resolution.

### Edge Cases

- Party roles include more than one role and role-specific default locations.
- The legacy Party type shadow differs from canonical PartyRole records.
- Source system is provided without external ID, or vice versa.
- Payment-term code differs only in case or surrounding whitespace.
- More than one default price list is proposed for a direction and currency.
- Pricing group membership or assignment is outside its validity interval.
- Two price tiers have the same minimum quantity.
- Item and Location defaults reference a foreign tenant.
- A Location becomes inactive while historical Movements still reference it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Party, Item, and Location create, update, list, read, deactivate, and
  reactivate operations MUST use shared tenant-scoped application services.
- **FR-002**: Deactivation MUST preserve opaque identity and all historical Evidence and
  Reality links; supported interfaces MUST NOT delete these records.
- **FR-003**: Blank required names, SKUs, units, or other core typed values MUST be
  rejected with a business-readable error.
- **FR-004**: Source-backed master data MUST retain immutable lossless SourceRecord
  provenance; manual records MUST remain valid without a source.
- **FR-005**: PartyRole MUST be the canonical source for company, customer, and supplier
  capabilities, including multiple roles per Party and an optional role default Location.
- **FR-006**: Party accounting code, payment term, default currency, credit limit, and
  tax identifier MUST be typed only as inputs to existing joins, constraints, or
  commercial decisions.
- **FR-007**: Item type, tracking type, default Location, purchase unit, conversion
  factor, and lead time MUST enforce their documented operational constraints.
- **FR-008**: Only stocked Items MAY participate in physical Movements; conversion
  factors MUST be positive and lead time MUST NOT be negative.
- **FR-009**: Location parent relationships MUST remain tenant-owned and acyclic, and a
  Location that disallows stock MUST NOT participate in physical Movements.
- **FR-010**: PaymentTerm code MUST be normalized and unique within one tenant, due days
  MUST be non-negative, and new assignments MUST require an active term.
- **FR-011**: Party and Document MUST reference PaymentTerm through its opaque ID rather
  than its human code.
- **FR-012**: Sales and purchase pricing MUST use separate direction/currency contexts
  and MUST NOT mix incompatible lists.
- **FR-013**: Price resolution MUST apply direct Party assignment before PartyGroup
  assignment before the default list, then select the highest applicable quantity tier.
- **FR-014**: A resolved document line MAY retain the PriceListEntry that explains its
  agreed price; later price-list changes MUST NOT rewrite Evidence.
- **FR-015**: Invalid or cross-tenant master-data mutations MUST return business errors
  without revealing foreign records.
- **FR-016**: CLI, JSON API, and Web master-data mutations MUST produce equivalent
  domain state through shared services.

### Domain and Traceability Requirements

- **DR-001**: Source-backed records link to immutable SourceRecord; master-data records
  are operational reference identities, while Documents remain Evidence and
  Commitment/Reservation/Movement/LedgerEntry remain Reality.
- **DR-002**: Master-data lifecycle and configuration are stored; inventory,
  fulfillment, open quantities, risk, and balances remain derived from Reality.
- **DR-003**: Every master-data lookup, mutation, suggestion, price resolution, and
  hierarchy validation MUST include tenant scope.
- **DR-004**: Relationships MUST use opaque IDs. Names, SKUs, codes, tax identifiers,
  and external IDs are business lookup/display values, not identity.
- **DR-005**: Operational screens MUST expose concise source identity and an Inspector
  path to raw source payload and related Evidence/Reality where applicable.

### Key Entities

- **Party**: Stable business actor identity with commercial defaults and source trace.
- **PartyRole**: Canonical capability performed by a Party.
- **Item**: Stable product/service identity and operational quantity defaults.
- **Location**: Hierarchical operational place with an explicit stock permission.
- **PaymentTerm**: Tenant-owned due-date agreement referenced through an opaque ID.
- **PriceList / PriceListEntry**: Direction/currency price context and item quantity tier.
- **PartyPriceList**: Direct commercial assignment with highest precedence.
- **PartyGroup / PartyGroupMember / PartyGroupPriceList**: Reusable grouped commercial
  assignment with precedence below direct Party assignment.

## Reality Applicability

- **Source**: Optional immutable SourceRecord supplies lossless upstream master-data
  truth. Unknown external fields remain in its payload.
- **Evidence**: Documents and lines capture agreed parties, items, terms, quantities,
  and prices; later master-data changes do not rewrite them.
- **Reality**: Commitments, Reservations, Movements, and LedgerEntries reference the
  operational Party, Item, and Location identities needed for action and calculation.
- **Shortest links**: Role → Party; PaymentTerm assignment → PaymentTerm; price entry →
  PriceList and Item; document line → selected PriceListEntry when explanation is needed.
- **Stored/derived**: Master-data configuration and lifecycle are stored. Stock,
  availability, fulfillment, risk, and financial balances are derived.
- **Shared boundary**: Domain validation and mutation live in shared application
  services called by CLI, API, Web, and tools.

## Success Criteria *(mandatory)*

- **SC-001**: Party, Item, and Location lifecycle operations produce equivalent domain
  state through CLI, API, and Web service paths.
- **SC-002**: Inactive records remain readable and retain 100% of historical links.
- **SC-003**: Cross-tenant master-data references and mutations are rejected without
  foreign-record disclosure.
- **SC-004**: Every typed operational field is linked to a documented repeated decision,
  constraint, join, filter, or calculation.
- **SC-005**: Price resolution deterministically returns the same tier and precedence
  source for identical Party, Item, quantity, direction, currency, unit, and date inputs.
- **SC-006**: Source-backed master data can be traced to the complete immutable payload;
  manual records do not claim artificial provenance.

## Assumptions and Dependencies

- PartyRole is canonical; the legacy Party type remains only a migration/compatibility
  shadow until a future spec proves its removal.
- ISO currency and established unit vocabularies are normalized by shared services.
- Price validity is evaluated against the documented business/effective date supplied
  to resolution, or the current effective time when the caller omits it.
- Party delivery holds are governed by `006-commitments-holds`, not this baseline.
- File import mappings are governed by `004-source-ingestion`; this baseline owns the
  resulting master-data behavior only.

## Open Questions

The owner approved this baseline on 2026-08-31. Discounts, promotions,
contact/address models, product structures, and advanced unit conversion remain
explicit non-goals.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-003 | Verified as-is | `docs/features/master_data.md` | master-data services + adapters | `tests/test_cli.py`; `tests/test_master_data_api.py` | — |
| FR-004 | Verified as-is | Master Data + Constitution | create/update services and SourceRecord service | `tests/test_master_data_api.py`; `tests/test_source_ingestion.py` | — |
| FR-005–FR-009 | Verified as-is | `docs/features/operational_fields.md` | Party/Item/Location services | `tests/test_operational_fields.py` | — |
| FR-010–FR-011 | Verified as-is | operational-fields Payment Terms section | payment-term services | `tests/test_payment_terms.py`; `tests/test_operational_fields.py` | — |
| FR-012–FR-013 | Verified as-is | operational-fields Pricing section | pricing services and `resolve_price` | `tests/test_pricing.py` | — |
| FR-014 | Verified as-is | operational-fields Pricing section; `specs/025-historical-pricing-integrity/spec.md` | shared selected-entry validation and historical-pricing explanation | `tests/test_pricing.py`; `tests/test_master_data_api.py`; `tests/test_migrations.py` | Spec 025 proves agreed Evidence remains immutable while current pricing resolves separately |
| FR-015 | Verified as-is | Master Data + Tenancy contracts | tenant-scoped service lookups | `tests/test_master_data_api.py`; `tests/test_tenancy.py` | — |
| FR-016 | Verified as-is | `docs/features/master_data.md`; `specs/026-master-data-adapter-parity/spec.md` | shared Party, Item, and Location services plus CLI/API/Web adapters | `tests/test_master_data_parity.py`; `tests/test_cli.py`; `tests/test_master_data_api.py`; `apps/web/scripts/master-data-parity.test.mjs` | Spec 026 proves the complete 36-cell lifecycle matrix and equivalent authoritative state |
| DR-001–DR-005 | Verified as-is | Constitution; Master Data; Operational Fields; Web Spec | models, services, API/CLI/Web paths | master-data, operational-field, source, and tenancy tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-004 | US1–US2 | CLI/API lifecycle and source-ingestion proofs |
| FR-005–FR-009 | US3 | Operational-field and constraint proofs |
| FR-010–FR-014 | US4 | Payment-term and pricing proofs plus documented gaps |
| FR-015–FR-016 | US1 | Tenant and adapter-equivalence evidence |
| DR-001–DR-005 | All stories | Constitution and cross-layer trace review |
