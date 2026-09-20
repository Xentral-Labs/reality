# Data Model: Demo Contribution Portfolio

## Schema impact

No new table, column, foreign key, index, or migration is required. The feature composes existing tenant-scoped business records and stores only stable references in the existing JSON profile manifest.

## Existing records used

### SourceRecord

- Immutable `demo_profile` payload for acquisition evidence, orders, movements, sales invoices, and selling-cost supplier invoices.
- Stable external references make examples discoverable and initialization idempotent.
- Received quantities and amounts remain lossless source authority.

### Document and DocumentLine

- Ordinary order, sales-invoice, and supplier-invoice evidence.
- Invoice lines are the contribution scopes; human document numbers are labels, not relationships.

### Movement and inventory-cost review records

- One company-owned opening lot supplies exact acquisition value.
- Five issue movements consume non-overlapping quantities from that lot.
- One inventory review creates exact retained members for commercial matching.

### LedgerEntry and financial evidence

- Posted sales invoices provide received net revenue through existing finance components.
- Posted supplier invoice lines provide received selling-cost amounts.

### Commercial match and contribution review records

- Each invoice line matches its exact consumed inventory member.
- Selling assignments link evidenced direct and allocated costs to that line.
- A contribution review confirms revenue completeness and every selling-cost category disposition.
- DB1, DB2, and DB2 rate are derived observations and are not persisted as authority.

### Profile manifest

- `costing_cases` retains existing `fixture_a`, `missing_cost`, and `late_cost_return` entries.
- Five stable complete-case entries add invoice-line, inventory-review, commercial-match, and contribution-review references.
- Profile identity becomes `international_demo`, version 3.

## Invariants

- Every record is tenant-scoped.
- Five issue quantities exactly partition the portfolio acquisition quantity; no quantity is reused.
- Every complete invoice has exactly one admitted commercial match at the profile cutoff.
- Every non-zero selling cost originates in supplier-invoice evidence and an explicit selling assignment.
- Every absent selling-cost category is explicitly reviewed as zero before DB2 becomes complete.
- Replay creates no additional portfolio sources, reviews, matches, or assignments.
- Existing version-2 profiles and continuous Demo Data are not mutated.

## Lifecycle

1. Author immutable acquisition and sales sources.
2. Create ordinary documents, movements, and postings.
3. Review inventory ownership and acquisition cost.
4. Match each billed line to its exact consumed-cost member.
5. Author and post selling-cost evidence; assign its parts.
6. Review contribution completeness and category dispositions.
7. Store only opaque references in the profile manifest.
8. Derive DB1 and DB2 on read through the shared service.
