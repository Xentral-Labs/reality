# Implementation Plan: Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices

**Branch**: `299-invoiced-not-shipped-plan` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Three new pieces of evidence share one new link to their order:
- a down-payment invoice, posted against received down payments, settled by ordinary payments and counted towards prepayment;
- a final-invoice offset that posts the stated deduction on the final invoice and records it;
- a pro-forma, which posts nothing.

A sales-side `billed_not_shipped` class mirrors `billed_not_received`. A `month_end_billing` read lists it beside `shipped_not_billed` from the same findings. See [research.md](research.md), [data-model.md](data-model.md) and [contracts/billing-documents.md](contracts/billing-documents.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Primary Dependencies**: SQLAlchemy 2, Alembic, FastAPI, Typer, pytest

**Storage**: PostgreSQL; migration `0105_down_payments`

**Testing**:
- pytest service, adapter and business-story tests
- web `test:i18n`, build and prettier
- the full backend suite

**Target Platform**: Backend, Web, MCP, CLI

**Project Type**: Service feature with adapters

**Performance Goals**: The readiness and offset reads stay bounded per order. The new class reads the same order-line promises as its purchase mirror.

**Constraints**: Stated amounts only; tenant-scoped; reviewed tools; derived states at read time.

**Scale/Scope**:
- one migration and two document types
- one account role
- two reviewed tools plus one extended
- one class and one read
- web actions, stories and the Guide

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Each document is recorded from a confirmed source record; postings follow from it. |
| II. Reality is the operational authority | PASS | No status on documents; paid, offset and not-shipped are derived. |
| III. Proven schema only | PASS | `order_document_id` is joined by readiness, offers and the order evidence. `down_payment_offset` is summed on every proposal to refuse an over-offset. |
| IV. Tenant and service boundaries | PASS | Reviewed tools shared by Web, MCP and CLI; the readiness change is in the shared service. |
| V. Specification and test evidence | PASS | Tests are planned before each phase. |
| VI. Explainable Web product | PASS | The order shows its down-payment and pro-forma invoices; the final invoice review shows offers and offsets. |
| VII. Simplicity and storage discipline | PASS | Ordinary payments settle a down-payment invoice; the offset is an ordinary posting. |
| VIII. Received values are recorded, never recomputed | PASS | Amounts and tax are stated; offsets are stated and only bounded. |

## Design

### Schema and roles

Migration `0105_down_payments`:
- `document.order_document_id`, with a foreign key and an index
- the `down_payment_offset` table, with foreign-key indexes and an amount check
- `customer_down_payments` added to `ck_subledger_account_role`

Also:
- `ACCOUNT_ROLES` and the transaction matrix gain the role and its rows;
- `initialize_accounts` creates the default;
- `SETTLEMENT_CONTROL` and the open-item types gain `down_payment_invoice`.

### Services

`services/down_payments.py`:
- `preview_down_payment_invoice` / `record_down_payment_invoice`
- `down_payment_offers(order_id)`: paid, offset and offsettable amounts per down-payment invoice
- `preview_offsets` / `post_offsets(final_invoice, offsets)`
- `preview_proforma` / `record_proforma`
- `order_billing_documents(order_id)`, for the inspector

The `sales_invoice_record` preview and execution in `core._preview_order_invoice` / `_record_order_invoice` call the offer and offset functions.

### Readiness

The candidate receivables for a prepayment order add the order's down-payment invoices (via `order_document_id`). Their allocated payments count as received. Reversed ones are excluded, as today.

### Finding and list

- `_billed_not_shipped_exceptions` mirrors `_billed_not_received_exceptions` on `customer_delivery` with shipments. The class gates follow.
- `month_end_billing(as_of)` filters `operational_exceptions(as_of)` to the two classes.

### Adapters and Web

- MCP propose tools and the read; Web pass-through and the `month-end-billing` endpoint; CLI commands.
- Web:
  - "Down-payment invoice" and "Pro-forma" actions on a sales order;
  - the final-invoice dialog shows offers, prefills the offset and lets the person adjust it;
  - the order inspector lists down-payment and pro-forma invoices and offsets;
  - a month-end billing section on the finance page.
- Translations, with `test:i18n` run before every push.

### Stories and Guide

- E03 (pro-forma and invoice before shipment, reported until shipped)
- Q01 (both month-end lists)
- E11 (30 % down payment offset in the final invoice)
- C14 (down payment, rest before shipment)

Then the catalog promotion, coverage, roadmap and docs.

## Project Structure

```text
specs/299-invoiced-not-shipped/{spec,plan,research,data-model,quickstart,tasks}.md, contracts/billing-documents.md
packages/reality-core/
├── migrations/versions/0105_down_payments.py
├── src/reality/db/core.py, domain/finance.py
├── src/reality/services/{down_payments.py (new), core.py, fulfillment_readiness.py, exceptions.py, invoice_actions.py}
├── src/reality/tools/application.py, mcp/catalog.py, cli/app.py, web/api.py
└── tests/{test_down_payments.py, test_proforma_invoices.py, test_billed_not_shipped.py, test_billing_document_adapters.py}, scenarios/test_catalog_finance.py
apps/web/src/... (order actions, final invoice dialog, finance month-end section, localization)
```

## Rollback

The downgrade drops the table and the column, and refuses while down-payment invoices or offsets exist.

## Complexity Tracking

No Constitution violations.
