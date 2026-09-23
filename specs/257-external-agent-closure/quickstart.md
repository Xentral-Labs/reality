# Quickstart: External Agent Audit Closure Validation

## Purpose

Validate the completed feature against a fresh company using only public MCP reads/proposals and
authenticated Web review. Do not use direct database or ORM access for business setup or proof.

## Prerequisites

1. Run API, MCP, Web, PostgreSQL and required shared background roles from one revision.
2. Apply migrations once through the deployment migration role. This feature itself expects no
   new migration.
3. Create a fresh uniquely named tenant and one temporary least-privilege MCP credential.
4. Keep the historical CanisPro tenant unchanged as comparison evidence.
5. Generate and verify public reference output before the live run:

```bash
make docs-generate
make docs-catalog-check
make spec-check
```

## Validation sequence

### 1. Schema and capability discovery

- Capture deployed `tools/list` without secrets.
- Compare tool names, required fields, enums and nested shapes with generated Tool Usage data.
- Describe reservation, shipment, settlement, credit, dunning, free supplier invoice, rejection
  and costing guidance without invalid-value probes.
- Expected: no unexplained schema/reference difference and every capability names its review and
  verification path.

### 2. Exact-location reservation effects

- Put stock in a child location and demand at its parent; confirm a reservation.
- Expected: exact-location rule is explained and receipt reports `none`, full shortage and no
  reservation/event.
- Move some stock explicitly to the commitment location and repeat partial then complete cases.
- Expected: effect classification and quantities reconcile in each case.

### 3. Owner-confirmed finance

- Through MCP prepare exact payment, early-payment discount, accepted small remainder,
  overpayment and dunning with fee.
- Through Web review and approve/reject as an authenticated owner.
- Through MCP reconcile proposal and read invoice, payment, available credit, adjustment and
  notice.
- Expected: agent confirmation is refused, owner confirmation succeeds, amounts remain separate
  and every effect is explainable.

### 4. Free supplier invoice

- Record one service/freight supplier invoice without a purchase-order line through its canonical
  action.
- Expected: one source-backed supplier invoice and balanced payable, with no invented commitment
  or stock movement and no generic-document workaround.

### 5. Credit and return

- Read invoice-credit context, use returned opaque position identities to record and optionally
  allocate a partial credit.
- Receive a tracked return into quarantine and split it between restock and scrap/loss.
- Expected: credit and physical disposition remain separate, tracking/location are exact and the
  linked returned-not-credited observation reconciles.

### 6. Operational validation and proposal cleanup

- Attempt an unsupported movement/document type and an unsupported payment filter.
- Expected: actionable refusal before durable proposal/document creation.
- Prepare a harmless proposal and reject it through MCP; replay rejection.
- Expected: no business effect, stable rejected lifecycle and no pending queue entry.

### 7. Ordinary-company costing

- Start from received goods, supplier invoice and separately stated freight with no cost review.
- Read guidance, prepare each named existing cost action and confirm through owner Web review.
- Read inventory value, DB1 and DB2 after completion; repeat with one evidence component missing.
- Expected: complete fixture is explainable; incomplete results remain unavailable with exact
  missing basis. No purchase/list price is promoted to actual cost.

### 8. Full CanisPro qualification

- Repeat this numbered required coverage on the fresh tenant:

  1. create fresh company, parties, items, locations and tracked opening stock;
  2. record the sales and purchase orders and verify their commitments;
  3. record partial supplier supply and receipt, then exact-location none/partial/complete
     reservations;
  4. dispatch partial and remaining customer quantities and verify stock movements;
  5. record/post sales and supplier invoices, including one free supplier invoice;
  6. settle exact, partial, reduced and overpaid receivables/payables and verify reusable credit;
  7. announce/receive tracked returns, apply every supported disposition and record an
     invoice-linked customer credit;
  8. record and reverse a manual dunning notice with a source-stated fee;
  9. reach or truthfully refuse inventory value, DB1 and DB2 from named evidence; and
  10. reject an unwanted pending proposal through the controlled human-decision surface.
- Record every mutation receipt and independent read-back.
- Produce an F1–F13 closure matrix with terminal status and evidence.
- Expected: no undocumented-value probes, direct persistence, generic-document workarounds or
  unresolved unwanted proposals for in-scope operations.

## Required automated gates

Run focused tests first, then the repository's complete required suite:

```bash
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

Also run PostgreSQL concurrency suites selected by tasks, catalog generation/checks and the
fresh public-surface qualification above. Red required checks mean the feature is not complete.

## Recorded incremental evidence

### 2026-09-23 — clean-client discovery and exact-location reservation

- Command: `PYTHONPATH=src ../../.venv/bin/pytest -q` with
  `test_capability_discovery_accepts_public_or_unique_application_name`,
  `test_reservation_receipts_classify_none_partial_and_complete`, and
  `test_capability_lookup_resolves_public_and_unique_application_names`.
- Expected: canonical public and unique application identities resolve without fuzzy probing;
  exact-location zero, partial and complete reservations expose distinct effect and remaining
  work while preserving the no-parent/child-aggregation rule.
- Actual: `3 passed in 6.91s` against PostgreSQL. The zero case retained no Reservation, the
  partial case retained its exact shortage and the complete case reported no remaining work.
- Verification basis: shared capability read plus current Reservation/Commitment records used by
  the focused tests. This is incremental automated evidence, not the final deployed CanisPro
  qualification required by sections 1 and 8.

### 2026-09-23 — strict public payment filters

- Command: `.venv/bin/pytest -q packages/reality-core/tests/finance/test_payment_reads.py`
  plus the adjacent `packages/reality-core/tests/finance/test_credit_reads.py` regression suite.
- Expected: `finance_payments` accepts only `incoming` and `outgoing`, filters matching rows,
  rejects the legacy `side` field and rejects every unsupported direction at the shared
  application boundary.
- Actual: `10 passed in 2.32s` against PostgreSQL. The public MCP schema and application read use
  the same closed vocabulary; `customer`, `supplier`, `inbound`, an explicit empty direction and
  `side` all produced actionable refusals.
- Verification basis: current committed payment Documents and LedgerEntries read through the
  shared `finance.payments.list` application tool. No proposal or business record is created by
  this read-only acceptance story.

### 2026-09-23 — invoice-linked credit and tracked return resolution

- Command: `.venv/bin/pytest -q` over the operational-exception, return-domain and public
  return-adapter suites, selected with `returned_not_credited or invoice_linked_credit or
  return_disposition`.
- Expected: an invoice-linked credit follows CreditLine → InvoiceLine → OrderLine and clears only
  the matching returned-not-credited quantity; all four physical dispositions use the shared
  proposal path and preserve the arrived return's applicable tracking identity.
- Actual: `14 passed, 219 deselected in 5.26s` against PostgreSQL. The linked credit cleared the
  observation through the two shortest line links. `restock`, `quarantine_repair`, `scrap_loss`
  and `return_to_supplier` reconciled through Web and the shared read, and the lot-tracked case
  retained item, lot and arrival-location identity in its resolving Movement.
- Boundary evidence: unknown returns are unavailable; missing commitment or destination and
  incompatible lot identity are refused explicitly before a resolving Movement is retained.
  Credit and physical disposition remain separate decisions.

### 2026-09-23 — owner-governed finance closure

- Command: `.venv/bin/pytest -q` over `test_owner_handoff.py`,
  `test_settlement_flows.py`, `test_commercial_edges.py`,
  `test_free_supplier_invoice.py`, and `test_payment_reads.py`.
- Expected: agents prepare supported finance work without effect; an unauthenticated or agent
  confirmation is refused; an authenticated owner decides owner-governed settlement and dunning;
  an ordinary authorized human may confirm the free supplier invoice; every proposal reconciles
  by its original identity and independent reads expose the result.
- Actual: `47 passed in 24.61s` against PostgreSQL. Exact/partial payment, explicit reduction,
  accepted remainder, overpayment credit, credit allocation/refund, dunning fee/reversal and the
  atomic source-backed free supplier invoice all retained their existing authority boundaries.
  Strict payment directions remained `incoming` or `outgoing`.
- Web evidence: proposal review labels the authenticated-owner boundary and reconciliation read;
  dunning review names the retained-notice verification and states that no email is sent.
  Four Web contract tests, the production Web build and the `de`, `nl`, and `es` localization
  audit passed.

### 2026-09-23 — bounded costing guidance and demo readiness

- Command: `.venv/bin/pytest -q` over `test_cost_query.py`, `test_costing_tools.py`,
  `test_inventory_costing_services.py`, `test_contribution_reviews.py`,
  `test_selling_costs.py`, `test_demo_costing_profile.py`, and
  `test_demo_data_intake.py`.
- Expected: ordinary-company reads distinguish uninitialized, pending, stale, failed and
  complete guidance without inventing cost; actual, estimated, unavailable DB1 and incomplete
  DB2 remain independent; an agent or company token may prepare an effect-free proposal, while
  only an authenticated active owner may confirm it. The canonical demo must reach the same
  shared services through Company Setup and normal intake, including a pending-approval setup
  actor, without an ordinary-company shortcut.
- Actual: `129 passed in 294.54s` against PostgreSQL. Complete and incomplete cost scopes kept
  their bounded missing-basis and explanation links; tenant scope remained enforced; proposal
  preparation created no CostAttribution; owner confirmation created exactly one and reconciled
  through the shared read. Canonical demo calculation readiness, exact source lineage, Web/tool/MCP
  parity and synthetic intake all passed through the existing profile and setup services.
- Web evidence: the cost explanation contract passed five checks, the `de`, `nl`, and `es`
  localization audit passed, and `npm run build` completed successfully. The build retained the
  existing large-chunk warning but produced a valid production bundle.
- Boundary evidence: preparation requires tenant membership when a human principal is present,
  but not owner authority or active-user confirmation authority. Confirmation independently
  requires the authenticated active owner. No changes were made to `demo_profile.py` or
  `company_setup.py` to obtain these results.

### 2026-09-23 — clean public proposal and read boundaries

- Command: `.venv/bin/pytest -q` over the proposal lifecycle, reporting vocabulary,
  invoice-credit context, payment reads and provenance suites, selected for public manual types,
  invalid movements, rejection lifecycle, independent invoice context, payment filters and
  unknown upstream labels.
- Expected: public manual document creation exposes exactly six operational types; unsupported
  document or movement values fail before a proposal or business record exists. An authorized
  human may reject a pending proposal without business effect, stable replay or cross-tenant
  disclosure. Invoice positions remain discoverable through an independent read, payment
  directions accept only `incoming` and `outgoing`, and an unknown upstream label remains
  lossless source evidence rather than becoming an operational type.
- Actual: `19 passed, 104 deselected in 2.77s` against PostgreSQL. The six-value schema was exact
  and duplicate-free; invalid document and movement probes left proposal, Document and Movement
  counts unchanged. Pending rejection, replay, executing/executed refusal and tenant scope all
  held. Invoice context and strict payment filtering returned or refused the documented values,
  while the unknown upstream label remained confined to its SourceRecord payload.
- Verification basis: proposal lifecycle reads, tenant-scoped invoice context and payment reads
  were used independently of mutation receipts. Reporting-only document kinds were explicitly
  proven not to expand the manual document creation vocabulary.

## Evidence handling

- Store no passwords, cookies, bearer tokens or raw secret-bearing proposal input.
- Use opaque IDs in the protocol and include human numbers only as display/search context.
- Record expected and actual results, error codes, verification reads and release revision.
- Do not mark a finding closed from a mutation response alone; use the named authoritative read.

## Redacted terminal result

Write the final qualification result as one JSON-compatible object. Redact credentials and raw
secret-bearing payloads before persistence. Opaque tenant, proposal and record identities may be
retained because they are required for reconciliation; human numbers are display context only.

```json
{
  "schema_version": "external-agent-closure/v1",
  "release_revision": "<git-revision>",
  "company": {"name": "<unique-name>", "tenant_id": "<opaque-tenant-id>"},
  "started_at": "<UTC timestamp>",
  "finished_at": "<UTC timestamp>",
  "overall_status": "passed|failed|blocked",
  "findings": [
    {
      "id": "F1",
      "expected_disposition": "<retained disposition from spec.md>",
      "terminal_status": "closed|expected_boundary|failed|blocked",
      "expected_result": "<redacted expectation>",
      "actual_result": "<redacted observation>",
      "mutation_receipts": ["<proposal or effect identity>"],
      "verification_reads": [
        {"tool": "<canonical public read>", "record_ids": ["<opaque-id>"], "result": "<redacted summary>"}
      ],
      "error_codes": [],
      "evidence_files": ["<repository-relative path>"],
      "notes": "<no secrets or raw credential-bearing input>"
    }
  ],
  "gates": [
    {"command": "<required gate>", "status": "passed|failed", "evidence_file": "<path>"}
  ]
}
```

The `findings` array MUST contain exactly one entry for every identifier F1 through F13. A
`closed` status requires at least one authoritative verification read. `expected_boundary` must
name the retained authority or domain boundary and its public guidance. `failed` records the
observed mismatch and error code. `blocked` names the external prerequisite and may not be used
for a reproducible product failure. `overall_status` is `passed` only when every finding is
`closed` or `expected_boundary` and every required gate passed.
