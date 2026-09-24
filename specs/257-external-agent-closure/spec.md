# Feature Specification: External Agent Audit Closure

**Feature Branch**: `257-external-agent-closure`
**Created**: 2026-09-23
**Status**: Draft — awaiting product/domain review
**Language**: English
**Input**: "Turn the independent CanisPro MCP audit findings F1 through F13 into one prioritized, executable specification that preserves intentional domain and authority boundaries while closing confirmed usability, coverage, validation and verification gaps."

## Context and Intent

### Problem

An independent agent created and operated a realistic B2B pet-food company through the
public MCP surface. The resulting quantities, documents and balances were largely
correct, but the run required extensive guessing, low-level workarounds and repeated
read-backs. It also classified several intentional product boundaries as defects and
missed capabilities that already exist through another product surface or in the current
catalog.

The product therefore has two distinct problems to solve. Confirmed gaps must be closed
so that a new external agent can discover, prepare, hand off, verify and recover the
supported business workflows. At the same time, Reality must not weaken exact-location
inventory, owner-only financial judgment, evidence-based costing or explicit human
confirmation merely to make an autonomous test complete without a person.

This specification is the single closure contract for audit findings F1 through F13. It
does not assume that every original finding requires new implementation. Each finding is
classified as a required product change, a discoverability or validation correction, a
regression proof for behavior already present, or an expectation that must be explicitly
rejected and explained.

### Scope

- Make the supported MCP workflow self-describing from discovery through verification,
  including closed value sets, confirmation prerequisites, receipts and next reads.
- Let an agent prepare every in-scope business action and let an authenticated owner
  review, approve or reject owner-governed actions through the shared proposal boundary.
- Close confirmed MCP coverage gaps for free supplier invoices, dunning, proposal
  rejection and the read context needed for invoice-linked customer credits.
- Make no-effect, partial-effect and refusal outcomes unambiguous without equating
  technical execution with business success.
- Validate closed business vocabularies before durable proposals or documents are
  created, with actionable errors that name missing or accepted input.
- Prove that current return dispositions, invoice-linked credits, overpayments,
  settlement reductions and filters work through their canonical paths.
- Give ordinary companies a guided evidence-based path from uninitialized costs to
  explainable inventory value and contribution observations, while reusing the demo
  readiness contract for canonical demo companies.
- Preserve one auditable disposition and regression proof for every original finding
  F1 through F13.

### Non-Goals

- Treating an MCP credential, API key, model output or prior approval as an authenticated
  company owner's confirmation.
- Automatic approval, automatic financial judgment or automatic cost-policy activation.
- Aggregating stock across parent and child locations for reservation; reservations
  remain exact-location allocations.
- Deriving historical acquisition cost from a price list, purchase order price or other
  merely plausible value when the required evidence has not been admitted and reviewed.
- Recomputing source-stated amounts, inventing missing taxes or presenting unavailable
  values as zero.
- Replacing the proposal lifecycle, introducing a second finance or costing path, or
  adding transport-specific business rules.
- Adding automatic dunning runs, sending reminders, executing bank transfers or
  performing external effects.
- Retaining probe documents, malformed proposals or workaround-created records as
  accepted business examples.
- Automatically rewriting historical tenants or silently repairing the CanisPro tenant.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Spec-driven workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Web product](../../docs/WEB_SPEC.md)
- [Safe proposal confirmation](../059-safe-proposal-confirmation/spec.md)
- [Credit-note posting](../084-credit-note-posts/spec.md)
- [Return fees and deductions](../095-a-fee-is-a-charge/spec.md)
- [Unified invoice-linked customer credit](../125-unified-invoice-credit/spec.md)
- [Accounting journal and settlement differences](../148-accounting-journal-cost-centers/spec.md)
- [Commercial edge workflows](../247-commercial-edge-workflows/spec.md)
- [B2B operational chain](../248-b2b-operational-chain/spec.md)
- [Web and MCP proposal review parity](../249-web-mcp-review-parity/spec.md)
- [Operational integrity](../250-operational-integrity/spec.md)
- [Live demo cost readiness](../251-live-demo-cost-readiness/spec.md)
- [Receipt costing](../../docs/features/receipt-costing.md)

## Audit Finding Disposition

| Finding | Verified disposition | Priority | Required closure |
|---|---|---:|---|
| F1 | Confirmation is intentionally separate, but the route to the current review token is insufficiently discoverable. | P1 | Describe and return the next review step without weakening explicit confirmation. |
| F2 | The business operation exists through a lower-level two-step path; direct MCP coverage is missing. | P2 | Support a free supplier invoice with stated supplier and positions through one reviewed action. |
| F3 | Exact-location reservation is intentional; parent/child aggregation is explicitly out of scope. A zero application can still be mistaken for success. | P1 | Preserve exact location and distinguish no effect, partial effect and complete application in the result and guidance. |
| F4 | Owner authorization for financial judgment is intentional. An MCP credential must not become an owner principal. | P1 | Provide a complete agent-prepare to owner-decide handoff and explain the boundary before confirmation. |
| F5 | Selected-invoice payment is intentionally bounded; overpayment belongs to settlement with separate cash and allocation amounts. | P1 | Make the canonical overpayment path discoverable and verifiable through the owner handoff. |
| F6 | Invoice-linked credit is implemented, but the exact valid shape and required invoice-line identities are not reliably discoverable to an independent agent. | P1 | Expose credit context and a complete valid input contract; prove the canonical tool works without a generic document workaround. |
| F7 | Current catalogs contain closed values that the audit did not receive or discover. | P1 | Enforce runtime, generated-reference and deployed-schema parity for every closed value set. |
| F8 | The return refusal did not identify the missing delivery commitment. | P2 | Name the missing or incompatible field and accepted relationship in the refusal. |
| F9 | Current return dispositions include quarantine/repair and scrap/loss. | P2 regression | Prove those dispositions through public surfaces and document their exact vocabulary. |
| F10 | Generic document creation can retain unsupported operational document types until a later action refuses them. | P2 | Validate the closed operational document vocabulary before proposal persistence while preserving lossless external payloads. |
| F11 | Manual dunning with an optional stated fee exists, but is not available through the public MCP proposal surface. | P1 | Publish the existing owner-confirmed dunning flow and its reversal/read context through MCP. |
| F12 | Missing inventory value and DB1/DB2 are truthful when cost evidence is unreviewed; automatic inference would violate the model. The ordinary-company setup path remains too difficult to discover and complete. | P1 | Guide an owner from named missing basis to reviewed, published and explainable results; retain unavailable where evidence is insufficient. |
| F13 | Mixed collection of schema, filter, read, proposal-lifecycle and exception-link findings. | P1–P3 | Close only independently reproduced subfindings and preserve explicit regression coverage for corrected or rejected claims. |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and verify the supported MCP path (Priority: P1)

An external agent with no repository knowledge can inspect a business capability, prepare
valid input, tell a human exactly what must be reviewed, and verify the observed effect
without guessing enumerations, internal document types or a hidden follow-up call.

**Why this priority**: An agent that must probe production state to learn closed values
creates noise, unsafe pending decisions and false defect reports. Schema-first discovery is
the foundation for every other workflow in this specification.

**Independent Test**: Give a clean client only the public MCP endpoint and credentials for
one test company. Require it to prepare one receipt, dispatch, reservation, supply
assignment, return disposition, settlement and invoice credit, then identify the exact
review and verification steps without an invalid-value probe.

**Acceptance Scenarios**:

1. **Given** a parameter with a closed business vocabulary, **When** the client reads the
   public tool definition, **Then** every accepted value and its business meaning are
   present and match the deployed validator and public reference.
2. **Given** a proposal that requires a state-bound review, **When** preparation succeeds,
   **Then** the response identifies the proposal, whether a fresh review is required, the
   read that supplies it, and the exact confirmation preconditions without claiming that
   the agent may approve it.
3. **Given** a reservation with no stock at the commitment's exact location, **When** it is
   confirmed, **Then** the receipt states zero applied quantity, full shortage, no created
   reservation and remaining work; it is not presented as a successful allocation.
4. **Given** some but not all requested stock at the exact location, **When** reservation is
   confirmed, **Then** the receipt distinguishes requested, applied and shortage quantities
   and names the authoritative verification reads.
5. **Given** a client asks for capability guidance using the public MCP tool identity or its
   application capability identity, **When** that identity is supported, **Then** guidance
   is returned or the response supplies the canonical discoverable identity; the client is
   not left to guess aliases.
6. **Given** generated public reference data and a deployed MCP service from the same
   release, **When** their tool names, required fields, closed values and nested inputs are
   compared, **Then** there are no unexplained differences.

---

### User Story 2 - Complete owner-governed finance without weakening authority (Priority: P1)

An agent can prepare a payment difference, overpayment, account prerequisite, dunning
notice or other supported financial action. An authenticated company owner can review and
decide the exact proposal in Web, after which the agent can reconcile the same proposal and
read the resulting balances or credit.

**Why this priority**: The audit correctly exposed an end-to-end usability gap but proposed
the unsafe remedy of treating a token as an owner. The product needs a complete human
handoff, not weaker authorization.

**Independent Test**: Through MCP, prepare an early-payment discount, an accepted small
remainder, a customer overpayment and a dunning notice with a stated fee. Through an
authenticated owner session, review and decide each proposal. Through MCP, reconcile each
result and verify the open invoice, payment, reusable credit, adjustment or fee.

**Acceptance Scenarios**:

1. **Given** an agent credential without a human user principal, **When** it attempts to
   confirm an owner-governed financial proposal, **Then** confirmation is refused before
   any financial effect and the response directs the proposal to owner review.
2. **Given** the same pending proposal, **When** an authenticated active owner opens it in
   Web, **Then** the owner sees its exact cash, allocation, reduction, account and balance
   consequences and can approve or reject it through the shared decision boundary.
3. **Given** a payment larger than the selected invoice's open amount, **When** the agent
   uses the documented settlement path with separate cash and allocation amounts and the
   owner confirms it, **Then** the invoice closes and the excess remains visible as reusable
   same-party credit.
4. **Given** a valid contractual discount or accepted small remainder and configured
   reduction account, **When** the owner confirms the reviewed settlement, **Then** cash,
   claim reduction, reason and resulting open amount remain separately explainable.
5. **Given** missing account configuration, **When** preparation or review occurs, **Then**
   the required account role and owner action are named; an ordinary payment with no
   reduction is not incorrectly described as needing a reduction account.
6. **Given** overdue invoices for one customer and currency, **When** an agent prepares a
   manual dunning notice and an owner confirms it, **Then** the notice and optional exact
   stated fee are recorded through the existing dunning semantics and can be read and
   reversed through the public workflow.
7. **Given** a free supplier invoice with no purchase-order line, **When** the agent states
   its supplier, currency, amount and supported free positions and an authorized human
   explicitly confirms it, **Then** one canonical supplier-invoice action records and posts
   it without requiring owner-only authority or a generic document workaround.

---

### User Story 3 - Credit and resolve a return through canonical records (Priority: P1)

An agent can read the creditable positions of a customer invoice, record a partial or full
invoice-linked credit, and separately resolve returned goods using the supported physical
dispositions. Financial and physical outcomes remain connected to their own evidence and
neither is inferred from the other.

**Why this priority**: The audit used a three-step generic-document workaround that lost
the shortest link to invoice and return evidence, leaving exceptions open despite plausible
ledger totals.

**Independent Test**: Start with a posted multi-line customer invoice and an arrived
lot-tracked return. Read the invoice-credit context, record and optionally allocate a
partial credit, then split the physical return between restock and scrap/loss. Verify the
credit, invoice, return, location, lot and exception results independently.

**Acceptance Scenarios**:

1. **Given** a posted customer invoice, **When** its credit context is read, **Then** every
   eligible invoice-line identity, credited and remaining quantity, amount capacity and
   blocking condition required for a valid proposal are returned.
2. **Given** valid invoice-linked positions, stated amounts, reason and explicit allocation,
   **When** the reviewed credit is confirmed, **Then** one credit note with position links,
   balanced postings and optional allocation is created without a return or stock effect.
3. **Given** a legacy order-line return credit, **When** it is prepared, **Then** its distinct
   valid shape remains supported and is not confused with invoice-linked financial credit.
4. **Given** a missing invoice, missing position, foreign position or incompatible
   position, **When** credit preparation is attempted, **Then** the refusal identifies the
   invalid relationship before a durable proposal is presented for approval.
5. **Given** an arrived tracked return in quarantine, **When** the operator chooses
   `scrap_loss`, **Then** the exact returned stock identity is removed from its actual
   location, the disposition remains linked to the return and unrelated stock is unchanged.
6. **Given** an arrived return and a supported disposition, **When** a required commitment,
   destination or relationship is absent, **Then** the error names the missing field and
   expected relationship rather than reporting an unrelated ownership conflict.
7. **Given** returned quantity credited through the canonical linked-credit path, **When**
   return exceptions are read, **Then** `returned_not_credited` reflects the linked credited
   quantity; an unlinked generic credit does not silently satisfy that conclusion.

---

### User Story 4 - Reach truthful cost and contribution results (Priority: P1)

An owner of an ordinary company can start from an uninitialized cost result, see the exact
missing evidence and decisions, complete the permitted reviews, publish the retained
context, and then inspect inventory value and contribution. If the evidence is insufficient,
the result remains unavailable with an actionable explanation.

**Why this priority**: Inventory value and contribution are essential for the target B2B
demonstration, but inventing them from agreed prices would violate the core authority model.

**Independent Test**: Receive purchased goods with a supplier invoice and separately stated
freight, begin from an uninitialized company, follow only the public guided actions, then
read acquisition cost, remaining inventory value, DB1 and DB2 with their coverage and
evidence. Repeat with one required value absent and verify that the final result stays
unavailable.

**Acceptance Scenarios**:

1. **Given** an uninitialized inventory or contribution query, **When** an owner inspects it,
   **Then** the result names the bounded scopes, missing evidence or decisions, why the
   current result is unavailable, and the next permitted review action.
2. **Given** only an agreed purchase price or price-list value, **When** actual acquisition
   cost is requested, **Then** actual cost remains incomplete and any estimate is separately
   labelled; no historical actual is invented.
3. **Given** complete received goods, invoice components and attributable freight evidence,
   **When** an owner admits and reviews the complete scope, **Then** the published result
   explains the exact acquisition amount, unit basis, remaining quantity and consumed cost.
4. **Given** matched sales revenue and reviewed consumed acquisition cost, **When** DB1 is
   read, **Then** the result is available only for the matched supported quantity and exposes
   its revenue and cost basis.
5. **Given** incomplete or unreviewed direct selling costs, **When** DB2 is read, **Then** DB1
   may remain available while DB2 remains explicitly unavailable or partial with its own
   coverage; missing cost is never treated as zero.
6. **Given** a canonical live-demo company, **When** setup reports calculation readiness,
   **Then** it satisfies the coverage and freshness requirements of spec 251 rather than
   creating a separate audit-only costing path.
7. **Given** a receipt has a completed cost review, **When** an unrelated tenant mutation occurs,
   **Then** the review remains current; only a change to the bounded evidence or decision scope
   can invalidate it, and the invalidating relationship is named.
8. **Given** owned stock is moved internally, **When** inventory value is reviewed, **Then** the
   transfer preserves the incoming value history rather than requiring independent acquisition
   evidence at the destination; any genuinely incomplete receipt is identified individually.
9. **Given** a source states sales net, tax and gross amounts, **When** the invoice is recorded and
   contribution is reviewed, **Then** those received values remain distinguishable and DB1/DB2
   consume the stated net basis without recomputing it from gross.

---

### User Story 5 - Keep public proposals and reads clean and recoverable (Priority: P2)

An external agent can filter public reads using the documented fields, reject proposals it
no longer wants a human to consider, and rely on validation to prevent exploratory garbage
from becoming durable business-looking records.

**Why this priority**: The audit left sixteen pending decisions and four probe documents.
Those artifacts are operational noise and can mislead later users even though the intended
business transactions remain correct.

**Independent Test**: Prepare invalid and valid proposals, filter customer and supplier
payments, reject selected proposals, retry rejection, and attempt unsupported operational
document types. Verify exact queue, read and persistence outcomes.

**Acceptance Scenarios**:

1. **Given** a pending proposal visible to the agent, **When** an authorized human explicitly
   requests rejection through the controlled MCP lifecycle surface, **Then** the proposal
   leaves the pending queue, records rejection attribution and creates no business effect;
   rejection is not available for default model selection.
2. **Given** an already rejected or executed proposal, **When** rejection is repeated, **Then**
   the outcome is stable and no business record changes.
3. **Given** customer, supplier, incoming or outgoing payment filters, **When** a documented
   filter is applied, **Then** every returned row satisfies it and unsupported filter names or
   values are rejected rather than ignored.
4. **Given** a closed operational field such as movement type or document type, **When** an
   unsupported value is proposed, **Then** preparation fails with accepted values before a
   pending proposal or operational document is persisted.
5. **Given** a caller needs invoice positions, **When** it uses the documented public read,
   **Then** it receives tenant-scoped opaque line identities and bounded position data without
   requiring access to the original creation receipt.
6. **Given** a low-level generic document action, **When** it receives external evidence with
   an unknown upstream label, **Then** the label may remain losslessly preserved in the source
   payload but is not accepted as a supported operational document type.
7. **Given** confirmation encounters a deterministic domain refusal and its transaction rolls
   back with no retained business effect, **When** the proposal is reconciled, **Then** it reaches
   terminal `failed`, reports `business_effect: none` and names a safe recovery; a timeout, lost
   response or otherwise unknown commit outcome remains `executing` and is never auto-replayed.

### Edge Cases

- A proposal becomes stale between agent preparation and owner review.
- A review token changes after a related reservation, movement, invoice, settlement or
  cost decision changes.
- Confirmation response is lost after an effect commits; reconciliation must not replay it.
- A valid action applies zero, a partial quantity or the full requested quantity.
- Parent location has no stock while one or more descendants do, or the reverse.
- A payment combines a supported reduction with an overpayment or uses mismatched currency.
- A credit references positions from multiple invoices, a reversed invoice or exhausted
  credit capacity.
- A tracked return is split across dispositions or has no applicable optional tracking
  identity.
- A dunning notice mixes parties or currencies, includes a settled invoice, or has no fee.
- Free supplier-invoice positions include charge items, quantities or source-stated amounts.
- Cost evidence arrives after a review or is corrected with an earlier effective date.
- Generated documentation is newer or older than the deployed MCP registry.
- A rejected proposal contains secrets or malformed legacy input; inspection and rejection
  must not disclose protected values.
- A deterministic execution refusal occurs after confirmation but before any business effect.
- An unrelated tenant event occurs after a cost review, or several independent receipts are
  reviewed without changing one another's evidence.
- An internal transfer creates an inbound movement at its destination without creating a second
  acquisition event or owner.
- A source states gross only, net only, tax separately, or an internally inconsistent combination;
  the product retains stated values and refuses unsupported completeness claims without deriving
  a replacement authority.
- Cross-tenant IDs in reads, proposals, confirmation, rejection or verification behave as
  unavailable and cause no partial effect.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every public MCP tool with a closed business vocabulary MUST expose the exact
  accepted values and concise meanings in its public input contract; runtime validation,
  capability guidance and generated reference MUST agree.
- **FR-002**: Nested MCP input fields, mutually exclusive shapes, conditional requirements,
  limits and timezone requirements MUST be machine-readable where the public schema can
  express them and MUST otherwise be stated in the tool's actionable guidance and refusal.
- **FR-003**: Proposal preparation MUST return or identify the opaque proposal, review state,
  next review read, confirmation authority and post-confirmation verification reads needed
  to finish the workflow safely.
- **FR-004**: Capability discovery MUST accept every documented public tool identity or
  deterministically return its canonical capability identity without requiring trial calls.
- **FR-005**: Reservation execution receipts MUST distinguish technical execution from
  applied operational effect and MUST state requested, applied, shortage, created record,
  current verification and remaining work, including the zero-effect case.
- **FR-006**: Reservation availability MUST remain scoped to the commitment's exact location;
  the product MUST explain that descendant stock requires an explicit physical or commitment
  decision and MUST NOT silently aggregate it.
- **FR-007**: Owner-governed finance and cost proposals prepared by an agent MUST be reviewable,
  approvable and rejectable by an authenticated active owner through the shared Web decision
  path, then reconcilable through the same proposal identity.
- **FR-008**: Agent credentials MUST NOT satisfy owner-principal requirements, and refusal of
  agent confirmation MUST create no financial, costing or account effect.
- **FR-009**: The canonical settlement workflow MUST support and document exact payment,
  partial payment, source-explained reduction, accepted small remainder, overpayment credit,
  existing-credit allocation and refund within their existing authority boundaries.
- **FR-010**: Overpayment MUST record actual cash separately from bounded invoice allocation
  and MUST expose the same-party, same-currency remainder as reusable credit.
- **FR-011**: The public finance context and review MUST name missing account roles and MUST
  not require or report an unrelated reduction account for a payment with no reduction.
- **FR-012**: MCP MUST expose the existing manual dunning notice, optional exact stated fee,
  read context and reversal as owner-confirmed proposals without adding automatic escalation
  or message delivery.
- **FR-013**: MCP MUST offer one explicitly human-confirmed free supplier-invoice action that
  accepts a supplier, currency, stated header amount and supported free positions without
  requiring owner-only authority, purchase-order lines or generic document creation.
- **FR-014**: The business invoice-credit context MUST derive every eligible invoice-line
  identity, credited and remaining quantity, amount capacity, invoice open amount and blocking
  reason needed to prepare a valid invoice-linked customer credit.
- **FR-015**: The customer-credit input contract MUST distinguish and completely describe the
  invoice-linked and legacy return-credit shapes, including required line fields, reason and
  explicit allocation amount.
- **FR-016**: A confirmed invoice-linked customer credit MUST preserve direct links from its
  credit positions to the credited invoice positions and their underlying order evidence so
  return and credit observations can derive correctly.
- **FR-017**: Return receipt and disposition refusals MUST identify missing or incompatible
  commitment, announcement, movement, location and tracking relationships in actionable terms.
- **FR-018**: Public contracts and regression proofs MUST cover `restock`,
  `quarantine_repair`, `scrap_loss` and `return_to_supplier`, preserving the arrived return's
  applicable location, lot, serial and handling-unit identity.
- **FR-019**: Closed operational document and movement types MUST be validated before a
  durable proposal or operational document is created. Public manual document creation supports
  exactly `sales_order`, `purchase_order`, `sales_invoice`, `supplier_invoice`, `credit_note`
  and `supplier_credit_note`; unknown upstream labels remain only in lossless source evidence
  unless separately mapped to a proven type.
- **FR-020**: An uninitialized, stale or incomplete cost result MUST identify its bounded
  scope, evidence gaps, review state and next authorized action without substituting a price,
  zero or generic error.
- **FR-021**: The ordinary-company cost journey MUST let an owner discover, review and retain
  supported acquisition, inventory, commercial-match, DB1 and DB2 bases through one coherent
  sequence with independent coverage for each result.
- **FR-022**: Actual acquisition cost, carrying value, DB1 and DB2 MUST remain unavailable when
  their required evidence or review is absent; an agreed purchase price MAY appear only as a
  separately labelled estimate where an existing contract permits it.
- **FR-023**: Canonical live-demo costing MUST reuse and satisfy spec 251; this feature MUST NOT
  create a second demo-only calculation or authority path.
- **FR-024**: MCP MUST permit explicit authorized-human rejection of a pending proposal through
  a controlled lifecycle surface that is excluded from default model-selectable tools,
  preserving attribution and creating no business effect; repeated or stale rejection MUST be
  safe.
- **FR-025**: A public tenant-scoped invoice read MUST make the FR-014 credit context, including
  opaque invoice-line identities and bounded follow-up values, accessible without depending on a
  past creation receipt.
- **FR-026**: Public payment filters MUST use one documented vocabulary and MUST either filter
  every row correctly or reject unsupported fields and values; they MUST NOT silently ignore
  a supplied filter.
- **FR-027**: The returned-not-credited observation MUST recognize only credit evidence with
  the required shortest true order/invoice-line relationship and MUST explain why an unlinked
  generic credit does not resolve the return.
- **FR-028**: The release verification MUST execute the original CanisPro workflow against a
  fresh tenant using only public schemas and supported Web review, record every invalid probe,
  and demonstrate that no undocumented-value probing, generic-document workaround or direct
  persistence access is required for in-scope operations.
- **FR-029**: Each original audit finding F1 through F13 MUST have a recorded terminal result:
  fixed behavior, improved guidance, regression proof of existing behavior, explicitly
  accepted limitation, or superseded claim with evidence.
- **FR-030**: Generated Tool Usage documentation MUST be regenerated and verified whenever a
  command, tool, read, projection, exception, event or MCP input contract changes.
- **FR-031**: The advertised customer-credit proposal MUST retain and validate every supplied
  argument for each supported credit shape; an empty or incomplete shape MUST be refused before a
  durable proposal exists, and a supported invoice-linked credit MUST complete without a generic
  document workaround.
- **FR-032**: Cost-review freshness MUST be derived from the bounded evidence and owner-decision
  scope of the reviewed receipt. Unrelated tenant activity MUST NOT invalidate the review, while
  a relevant change MUST invalidate it and identify the changed evidence relationship.
- **FR-033**: Relationship, required-input and closed-value validation that can be determined at
  preparation time MUST occur before proposal persistence; confirmation MUST NOT be the first
  point at which an invalid billed line or missing credit line is discovered.
- **FR-034**: A deterministic confirmation failure with no committed business effect MUST leave a
  terminal, inspectable failed outcome that states `business_effect: none` and permits safe
  recovery. It MUST NOT remain indefinitely in `executing` or be replayed as unknown execution.
- **FR-035**: Internal stock transfers MUST preserve the item's existing ownership and value
  history without treating the destination movement as a new acquisition receipt. Inventory
  review refusals MUST identify every exact movement or evidence scope that remains incomplete.
- **FR-036**: Every operation-specific public action MUST publish a machine-readable union of its
  accepted shapes, required fields, meanings and closed values. Cost amounts and sign semantics,
  review dispositions, tax treatments and shipment-purpose movement types MUST be discoverable
  without deliberate invalid calls.
- **FR-037**: Invoice evidence MUST retain source-stated net, tax and gross amounts when supplied,
  without deriving one received value from another. Contribution review MUST consume the stated
  net revenue basis and remain explicitly unavailable when the source did not state an accepted
  basis.

### Domain and Traceability Requirements

- **DR-001**: Every created business result MUST preserve the applicable
  SourceRecord → Document/DocumentLine → Reality chain and expose its shortest true links;
  generic workaround records MUST not be used to imitate a missing canonical relationship.
- **DR-002**: Documents MUST remain evidence rather than operational authority. Reservation,
  return, fulfilment, settlement and cost state MUST be derived from their Reality records.
- **DR-003**: Source-stated amounts, prices, dates, taxes, fees and quantities MUST be retained
  as received and MUST not be recomputed; missing evidence remains missing.
- **DR-004**: Proposal, document, line, commitment, movement, reservation, return, settlement,
  review and cost-scope relationships MUST use opaque tenant-scoped identities rather than
  human numbers or duplicated foreign keys.
- **DR-005**: Web, MCP, Chat, CLI and API MUST call the same application services and expose
  equivalent decisions and observations; transports MUST not implement alternate business
  rules or write business records directly.
- **DR-006**: Every read, proposal, confirmation, rejection and verification MUST enforce
  tenant scope; foreign identities behave as unavailable and no partial cross-tenant effect
  is permitted.
- **DR-007**: Financial account choice, settlement reduction, dunning fee, cost attribution,
  completeness, tax treatment, valuation and policy decisions MUST retain active-owner
  authority and explicit review.
- **DR-008**: No new stored field or relationship is justified by this umbrella specification
  alone; the plan MUST prove any proposed schema expansion against a concrete requirement and
  reject a read-time derivation or existing shortest relationship first.

### Key Entities

- **Change Proposal**: Existing tenant-scoped prepared intent with review, authority,
  lifecycle, rejection and stable execution receipt.
- **Capability Contract**: Public description of accepted input, authority, effect,
  limitations, verification and recovery for one supported action or read.
- **Financial Settlement**: Existing reviewed relationship between actual cash, bounded
  invoice allocation, explicit reduction or reusable credit.
- **Invoice Credit Context**: Read-time bounded view of one invoice and its eligible position
  capacity; it is not new financial authority.
- **Return Disposition**: Explicit physical decision over arrived return quantity, retaining
  the return movement's applicable identity and location.
- **Cost Scope and Review**: Existing evidence and owner decision that support an acquisition,
  inventory or contribution observation; the derived observation is not stored authority.
- **Audit Closure Record**: Version-controlled evidence mapping an original finding to its
  decision, requirement, proof and terminal status; it is documentation, not a business table.

## Success Criteria *(mandatory)*

- **SC-001**: A clean external client completes the in-scope CanisPro workflow with zero
  guesses of closed values and zero unsupported generic-document workarounds.
- **SC-002**: One hundred percent of public closed-value fields match across deployed schema,
  capability guidance, validation and generated Tool Usage reference.
- **SC-003**: Every confirmed reservation returns enough information for a client to distinguish
  refusal, no effect, partial effect, complete effect and indeterminate execution from one
  receipt plus its named verification reads.
- **SC-004**: All owner-governed audit cases can be prepared by an agent, decided by an
  authenticated owner and reconciled by proposal identity without granting owner authority to
  the agent credential.
- **SC-005**: Customer overpayment produces the exact expected invoice allocation and reusable
  credit; discounts and accepted residuals preserve separate cash and reduction evidence.
- **SC-006**: Invoice-linked credit and every supported return disposition complete through
  their canonical actions, and linked return-credit exceptions reconcile without manual
  document correction.
- **SC-007**: A complete ordinary-company costing fixture yields explainable inventory value,
  DB1 and DB2, while every incomplete fixture remains explicitly unavailable with the exact
  missing basis.
- **SC-008**: Invalid closed values, unsupported document types and malformed relationships
  create zero pending proposals and zero operational documents.
- **SC-009**: Every audit-created proposal can be approved, safely rejected or identified as
  indeterminate; no unwanted proposal remains pending solely because MCP lacks a lifecycle
  action.
- **SC-010**: F1 through F13 each map to at least one accepted scenario and executable proof or
  to an explicit approved non-goal with regression evidence.
- **SC-011**: Every FR and DR has an acceptance scenario and executable proof.
- **SC-012**: One unrelated tenant mutation leaves 100% of previously current receipt reviews
  current, while each relevant evidence mutation invalidates exactly the affected reviews.
- **SC-013**: A complete purchase, internal transfer and sale fixture yields the same explainable
  remaining inventory value before and after the transfer, and its invoice-linked DB1/DB2 result
  uses source-stated revenue evidence.
- **SC-014**: Every deterministic execution refusal in the qualification reaches a terminal
  inspectable state with no business effect; zero proposals remain indefinitely `executing`.

## Assumptions and Dependencies

- Specifications 249, 250 and 251 may still be implemented or completed independently;
  this feature treats their approved contracts as dependencies and does not duplicate their
  business rules.
- Existing shared proposal identity, Web decision routing and reconciliation remain the
  canonical handoff between agent preparation and human authority.
- Manual dunning, settlement differences, overpayment credit, invoice-linked customer credit
  and the four return dispositions remain existing domain capabilities to expose or verify,
  not redesign.
- The release qualification uses a fresh tenant. The historical CanisPro tenant is retained
  as audit evidence and is not silently cleaned or repaired by this feature.
- Any cleanup of the historical tenant's probe documents or pending proposals is a separately
  reviewed operational action.
- Product and domain review may lower the implementation priority of a finding, but every
  finding must retain a documented terminal disposition.

## Open Questions

None. Intentional authority, reservation-location and cost-evidence boundaries are fixed by
the Constitution and existing approved specifications; the remaining work is bounded by the
audit dispositions above.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-004, FR-030 | US1.1–US1.2, US1.5–US1.6 | Public catalog/runtime parity contract and clean-client discovery journey |
| FR-005–FR-006 | US1.3–US1.4 | Zero, partial and full exact-location reservation stories |
| FR-007–FR-008 | US2.1–US2.2 | Agent preparation, owner decision and MCP reconciliation story |
| FR-009–FR-011 | US2.3–US2.5 | Exact, partial, reduction, small-remainder and overpayment settlement stories |
| FR-012 | US2.6 | Dunning without fee, with fee and reversal through MCP/Web handoff |
| FR-013 | US2.7 | Free supplier-invoice business story with charge and ordinary positions |
| FR-014–FR-016, FR-025 | US3.1–US3.4, US5.5 | Invoice-credit context and canonical multi-position credit story |
| FR-017–FR-018 | US3.5–US3.6 | Tracked return disposition and actionable-refusal stories |
| FR-019 | US5.4, US5.6 | Closed document/movement validation and lossless source preservation |
| FR-020–FR-023, FR-032, FR-035, FR-037 | US4.1–US4.9 | Complete and incomplete ordinary costing, scoped freshness, transfer continuity, stated revenue and spec-251 demo regression |
| FR-024 | US5.1–US5.2 | Proposal rejection, replay and cross-tenant lifecycle tests |
| FR-026 | US5.3 | Customer/supplier and incoming/outgoing payment-filter contract tests |
| FR-027 | US3.7 | Canonical linked credit versus unlinked generic-credit exception story |
| FR-028–FR-029 | All stories | Fresh CanisPro qualification protocol and F1–F13 closure matrix |
| FR-031, FR-033–FR-034 | US3.1–US3.4, US5.4 | Credit input retention, propose-time relationship validation and terminal failure recovery |
| FR-036 | US1.1–US1.2, US1.5 | Operation-specific schema and guidance parity |
| DR-001–DR-004 | US2–US4 | Source/evidence/Reality and shortest-link review with business-story proofs |
| DR-005–DR-007 | All stories | Cross-surface parity, tenant-isolation and owner-authority tests |
| DR-008 | All stories | Plan Constitution Check and schema proof |

## Audit-to-Requirement Traceability

| Finding | Requirements | Primary evidence |
|---|---|---|
| F1 | FR-003–FR-004, FR-007 | Review discovery and owner handoff |
| F2 | FR-013 | Free supplier-invoice story |
| F3 | FR-005–FR-006 | Exact-location zero/partial/full reservation receipts |
| F4 | FR-007–FR-008, DR-007 | Agent refusal and authenticated-owner confirmation |
| F5 | FR-009–FR-011 | Overpayment and settlement-difference stories |
| F6 | FR-014–FR-016, FR-025, FR-031 | Invoice-line discovery, retained proposal input and canonical credit story |
| F7 | FR-001–FR-002, FR-030, FR-036 | Catalog/runtime/reference parity including operation-specific unions |
| F8 | FR-017 | Missing-relationship refusal tests |
| F9 | FR-018 | Four-disposition public regression |
| F10 | FR-019, FR-033–FR-034 | Early closed-type/relationship validation and terminal effect-free failure |
| F11 | FR-012 | MCP dunning and reversal story |
| F12 | FR-020–FR-023, FR-032, FR-035, FR-037, DR-003, DR-007 | Truthful guided costing, scoped freshness, transfer continuity, stated revenue and demo-readiness regression |
| F13 | FR-001–FR-005, FR-014, FR-019, FR-024–FR-036 | Schema, read, filtering, lifecycle, exception and release qualification |
