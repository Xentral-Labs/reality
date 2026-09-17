# Declaration Coverage Audit

Date: 2026-09-17. Generated and re-runnable with [check_coverage.py](check_coverage.py):

    REALITY_DATABASE_URL=... PYTHONPATH=packages/reality-core/src \
      .venv/bin/python specs/224-native-reporting-platform/check_coverage.py

This audit exists because a manual read found a missing return path by accident. An
accident is not a method. T002 turns this script into a test so the question is answered
on every change instead of whenever somebody remembers to ask.

## Method: four axes, because one misses half the gaps

| Axis | Question |
|---|---|
| 1. Structure | Is every business table a node, every foreign key an edge? |
| 2. Vocabulary | Is every value of a discriminating column covered by some node? |
| 3. Measures | Does every node carry at least one measure, or is it filter-only? |
| 4. Catalog | Does the declaration agree with `config/data_model.yaml`? |

**Axis 2 is the one that matters most here, and it is the one that is easy to forget.**
The purchase side lives in the *same tables* as the sales side under different `type`
values. A foreign-key audit reports `document` as fully covered and is wrong.

## Findings

### 1. Structure — 11 of 43 business tables are nodes

67 foreign keys have no declared edge. Most point at tables that are deliberately out of
the first slice. Twelve are more interesting, because both ends are already nodes:

| Open edge | Judgement |
|---|---|
| `commitment.document_id → document` | **Add.** The document-level link beside the line-level one. |
| `commitment.location_id → location` | **Add.** Fulfilment location of a promise. |
| `ledger_entry.account_id → subledger_account` | Needs a `subledger_account` node first. Finance slice. |
| `movement.resolves_movement_id → movement` | **Resolved and declared.** Not a correction: an outbound movement settling a customer return. See below. |
| `movement.handling_unit_id`, `.lot_id`, `.serial_unit_id`, `.shipment_package_id` | Traceability slice. Deliberately deferred. |
| `document.payment_term_id`, `party.payment_term_id` | Needed for aging. Deferred with it. |
| `document_line.price_list_entry_id` | Pricing slice. Deferred. |
| `item.default_location_id` | Master-data convenience. Low value. |

### 2. Vocabulary — the purchase side is not declared

| Column | Value | In code | Declared |
|---|---|---|---|
| `document.type` | `sales_order` | 30× | yes |
| | `sales_invoice` | 44× | yes |
| | `credit_note` | 33× | yes |
| | `purchase_order` | 14× | **no** |
| | `supplier_invoice` | 35× | **no** |
| | `supplier_credit_note` | 13× | **no** |
| `commitment.type` | `customer_delivery`, `supplier_delivery` | | both — the node has no `where` |
| `movement.type` | `opening_stock`, `receipt`, `shipment`, `return`, `supplier_return`, `transfer`, `adjustment`, `correction` | | all — the node has no `where` |

**Traced against the chain that was asked about — product to goods receipt to supplier
return — this is exactly where it breaks:**

| Step | Record | Declared |
|---|---|---|
| Product | `item` | yes |
| Purchase order | `document` type `purchase_order` | **no** |
| Promise to receive | `commitment` type `supplier_delivery` | yes |
| Goods receipt | `movement` type `receipt` | yes |
| Return to supplier | `movement` type `supplier_return` | yes |
| Supplier invoice | `document` type `supplier_invoice` | **no** |
| Supplier credit note | `document` type `supplier_credit_note` | **no** |

The physical side is complete. The document side is missing three type values. So today
one can ask what was physically received and returned, but not what it was ordered
against or whether it was credited — which is precisely the question
`supplier_return_not_credited` exists for as an exception class.

This is a **deliberate deferral** under the specification's sales-first scope, not an
oversight — but it was not named anywhere, and an unnamed deferral is indistinguishable
from a gap. It is named here. Cost to close: four node definitions that differ from the
sales ones only in their `where`, plus their edges. Roughly 90 lines, no new mechanism.

### 3. Measures — six nodes are filter-only

`item`, `invoice_line`, `shipment`, `location`, `return_announcement` and `campaign`
carry no measure. That is legitimate — they are traversed and filtered, not summed — but
it should be a stated property rather than an omission, because "no measure" and
"measure forgotten" look identical in a YAML file. The declaration gains an explicit
`measures: none` acknowledgement for those, so the loader can tell the two apart.

Missing measures worth adding in this slice: `returned_quantity` on `return_announcement`
and `invoiced_quantity` on `invoice_line`.

### 4. Catalog drift — `data_model.yaml` is 13 tables behind

`config/data_model.yaml` documents 74 tables; the schema has 87. Undocumented:

    analytics_report, analytics_report_draft, commitment_revision, demo_data_connection,
    movement_correction, ordinary_company_creation, return_announcement, scheduled_job,
    scheduled_job_run, shipment, shipment_event, shipment_event_supersession,
    shipment_package

Two of them — `shipment` and `return_announcement` — are nodes in this declaration. So
the reporting graph currently declares business concepts that the repository's own data
model catalog does not describe. **This is an existing drift, independent of this
feature**, but this feature is the first thing that makes it visible, and it should be
fixed where it belongs rather than worked around here.

Separately, `data_model.yaml` has a small formatting defect: unquoted commas inside flow
mappings turn a description into garbage keys, for example `document.type` parsing as
`{'description': 'Evidence type such as sales_order', 'invoice': None, 'or payment.': None}`.

## Where this is systematically recorded — and where it is not

| What | Where it lives today | Verdict |
|---|---|---|
| Tables and columns | `config/data_model.yaml`, 74 tables in 8 sections with descriptions | The right place. 13 tables behind. |
| Foreign keys | The SQLAlchemy models, authoritative | Fine; this audit reads them directly. |
| Tenant isolation | `config/tenant_isolation_catalog.yaml`, with a pinned count | Exemplary — the model to copy. |
| Commands, resources, events, projections, exceptions, references, connectors | Seven further catalogs under `config/` | Each systematic within its purpose. |
| **Value vocabularies** — what `document.type` may be | **Nowhere.** String literals in the code; partial appearances in five catalogs written for other purposes; prose in `data_model.yaml` ("such as sales_order, invoice or payment") | **The gap.** It is why the purchase side was invisible. |

### Recommendation

Value vocabularies belong in `data_model.yaml`, beside the column they constrain:

    document:
      columns:
        type:
          description: Evidence type.
          values: [sales_order, purchase_order, sales_invoice, supplier_invoice,
                   credit_note, supplier_credit_note]

Then this audit reads them from there instead of carrying its own copy, a node that
discriminates on an uncatalogued value fails to load, and a new type value added in code
without a catalog entry fails a test. That is the same shape as the isolation catalog's
pinned count, which is the existing thing in this repository that works best.

Until that exists, the vocabulary lives in `check_coverage.py` with the occurrence count
of each value as evidence that it is real.

### 5. `movement.resolves_movement_id` — resolved

Read in `services/core.py` and `services/exceptions.py`. It records that an outbound
movement **settles a customer return**: goods that came back are put away, scrapped or
sent on. The service enforces that the target is a movement of type `return`, that it
concerns the same item, that the goods leave the location the return arrived in, and
that resolutions never exceed what came back.

It is therefore a business relationship, not a correction. It does not interact with
`movement_correction`, which fixes a movement that was recorded wrongly, and it raises
no double-counting question — both movements are real physical events that belong in a
quantity sum. It is declared as the edge `resolves`, `n:1`, with the target restricted
to returns.

It also earns its place: it is what the `return_unresolved` exception class judges — a
return still sitting on the dock with nobody deciding what happens to it.

## What this changes in the plan

- T002 gains this script as a test, with an explicit exemption list: a table or type
  value may be undeclared only if it is named as deferred, with a reason.
- T003 gains `measures: none` as an explicit node acknowledgement.
- Two edges to add now: `commitment.document_id` and `commitment.location_id`.
- Two measures to add now: `returned_quantity`, `invoiced_quantity`.
- `movement.resolves_movement_id` is clarified and declared as the edge `resolves`. It
  is not a correction mechanism, so it does not interact with `movement_correction` and
  raises no double-counting question. The open item is closed.
- The purchase slice is named as deferred, with its cost, rather than being absent.
- `data_model.yaml` drift and its formatting defect are raised as their own work,
  outside this feature.
