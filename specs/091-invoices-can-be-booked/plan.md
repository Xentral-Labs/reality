# Implementation Plan: An Invoice Somebody Can Actually Book

**Branch**: `091-invoices-can-be-booked` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Three operations that already exist, proven and tenant-scoped, wired to the surfaces that already
reach their credit-note counterparts. No schema, no service logic, no new class.

The whole diff is declaration and transport. That is what makes it a defect rather than a
feature: the capability was built and nobody could call it.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI, SQLAlchemy 2, PyYAML for the closed catalogs
**Storage**: PostgreSQL; no schema change
**Testing**: pytest, API through `TestClient`, catalog drift gates
**Project Type**: backend service consumed by Web, MCP, Chat and CLI adapters
**Constraints**: Recording and booking stay two acts; opaque IDs; strict tenant scope
**Scale/Scope**: Three commands, three agent tools, three MCP schemas, two endpoints

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Recording produces Evidence and booking produces Reality; the two stay separate acts, which is what makes the gap between them representable | PASS |
| Reality owns operational state | Nothing gains a status; posting produces ledger entries exactly as it does today | PASS |
| Proven schema only | No schema change and no service change. Only reachability | PASS |
| Tenant + shared service boundaries | Every surface calls the one shared service; the isolation catalog gains the new tools and stays complete by discovery | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each endpoint returns the ledger entry identities it produced, as the credit-note endpoint does | PASS |
| Received values not recomputed | Every posted figure is the document's own gross amount; no surface introduces a number | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Post automatically when a document is recorded.** One fewer call and it destroys a
  distinction the product depends on: `credit_note_unposted` exists because recording and booking
  are two acts, and an invoice is no different. It would also post figures nobody asked to post.
- **Expose posting only over HTTP.** Half the gap. An agent could then create an order, record an
  invoice and be unable to book it, which is the same discontinuity one layer down.
- **Fix the whole declaration gap at once.** Measured, it is 18 services reached by a mutating
  endpoint and not declared — mostly reads that shape a response, plus tenant administration and
  chat. Only one of them is a business operation, and that one is in scope here. Doing the rest,
  and building the gate that would keep it done, would bury the capability this specification is
  about.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/command_catalog.yaml          # three commands, parameters, coverage, guidance
packages/reality-core/config/tenant_isolation_catalog.yaml # three tools
packages/reality-core/src/reality/tools/application.py     # three agent tools
packages/reality-core/src/reality/mcp/catalog.py           # three proposal schemas
packages/reality-core/src/reality/web/api.py               # two posting endpoints
docs/features/ledger.md, order_to_cash.md, procure_to_pay.md
apps/docs/content/catalogs/ (+ de/)                         # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                # specification row
```

## Design

### The credit note is the yardstick

Every decision here is "whatever the credit note does". The endpoint shape, the tool shape, the
proposal schema, the isolation family, the command's reads and writes. That is deliberate: the
two documents drifted apart precisely because nobody was comparing them, and the cheapest
protection against drifting again is that the shapes are identical enough to diff.

| Credit note | Invoice |
|---|---|
| `POST /finance/credit-notes/postings` | `POST /finance/sales-invoices/postings` |
| — | `POST /finance/supplier-invoices/postings` |
| `credit_note_post` | `sales_invoice_post`, `supplier_invoice_post` |
| `credit_note_post_propose` | `sales_invoice_post_propose`, `supplier_invoice_post_propose` |
| "Post credit note" | "Post sales invoice", "Post supplier invoice" |

Recording gains the same treatment: `POST /documents` already exists, so it needs a command
entry, a `document_create` tool and a proposal schema — the same three declarations `order_create`
has.

### Nothing in the service layer moves

`post_sales_invoice` and `post_supplier_invoice` already refuse the wrong type, an unknown
document, another tenant's document and a second posting. Every one of those refusals is proven
by existing tests calling the services directly. What this feature adds is a caller, so the
endpoint tests assert the refusals arrive as API errors rather than re-proving the rules.

That is also why DR-001 is worth reading as a review instruction: **a service-layer change in
this diff would mean the scope was misjudged.**

### What becomes reachable

Five conditions could not fire outside the demo, because each needs a posted invoice:
`overdue_receivable`, `overdue_payable`, `credit_limit_exceeded`, `purchase_discount_available`
and the `early_payment_discount_taken` reason. A test drives two of them end to end through the
API alone — record, book, read the queue — because that is the claim worth proving, and it is
the claim nobody made when those classes shipped.

### Data and migration impact

None.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | adapter | `test_master_data_api.py::test_a_sales_invoice_can_be_booked_over_the_api` | 404, the endpoint does not exist |
| FR-002 | adapter | `test_master_data_api.py::test_a_supplier_invoice_can_be_booked_over_the_api` | 404 |
| FR-003 | adapter | both tests, covering wrong type, unknown, foreign tenant, second posting | a refusal is not an API error |
| FR-004 | unit | `test_application_tools.py` / `test_ai_mcp.py` tool presence tests | the tools do not exist |
| FR-005 | unit | `test_application_tools.py::test_a_document_can_be_recorded_by_an_agent` | the tool does not exist |
| FR-006 | unit | `test_application_catalog.py`, `test_capability_guidance.py` | catalog drift |
| FR-007 | unit | `tests/tenant_isolation/` drift gate | isolation drift |
| FR-008 | adapter | `test_a_sales_invoice_can_be_booked_over_the_api` | recording alone leaves it owing nothing |
| FR-009 | adapter | `test_master_data_api.py::test_booking_makes_the_money_classes_reachable` | the classes stay silent |
| FR-010 | adapter | `test_a_sales_invoice_can_be_booked_over_the_api` | a credit cannot be netted |
| FR-011 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | no diff under `services/` and none under `migrations/versions/` | — |
| DR-002 | adapter | `test_a_sales_invoice_can_be_booked_over_the_api` | a surface introduces a figure |
| DR-003 | adapter | foreign-tenant cases in both endpoint tests | another tenant is reachable |
| DR-004 | unit | `test_coverage.py` closed registry test | passes unchanged |
| DR-005 | story | `test_normal_month.py` pinned queue | the demo queue moves |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no behaviour change to anything that already worked. The deploy adds three
callable operations. Rollback is a plain revert.

The demo month is unchanged: it calls the services directly and always did.

## Review Risks

- **This is mostly YAML and transport, and it is the most valuable thing in a while.** The risk
  at review is treating a small diff as a small change. What it fixes is that five shipped
  classes were unreachable on every real tenant.
- **The declaration gap stays open.** Seventeen services remain reachable from a mutating
  endpoint and undeclared after this feature, and nothing gates the difference — the isolation
  catalog is complete by discovery while the command catalog is hand-maintained. Another
  operation can ship tenant-safe and unreachable tomorrow. The measurement says a gate would be
  cheap, which makes its absence the more interesting fact.
- **Giving an agent the ability to record and book invoices widens what an agent can do to
  money.** Both are confirmation-required proposals like every other mutation, and the credit
  note has had exactly this since 084 — but it is a real widening and should be read as one.
- **`POST /documents` accepts any document type.** That is pre-existing and unchanged here; this
  feature declares the operation rather than narrowing it. Whether that endpoint should be
  narrower is a separate question this specification does not answer.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
