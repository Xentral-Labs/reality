# Implementation Plan: Automatic Credit Hold

**Branch**: `298-automatic-credit-hold-plan` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

A shared, read-time credit exposure, made up of open invoices plus open uninvoiced orders minus available credits, with overdue items and payables named. Every sales-order entry path calls a credit check that holds the new order's promises with `credit_check` when the exposure passes the limit. The check records the facts in the hold note and event. A new reviewed, owner-only `credit_hold_release` lifts only credit holds, with a mandatory reason. The credit-limit finding reads the same exposure. There is no schema change. See [research.md](research.md), [data-model.md](data-model.md) and [contracts/credit-hold.md](contracts/credit-hold.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Primary Dependencies**: SQLAlchemy 2, FastAPI, Typer, pytest, React/Vite

**Storage**: PostgreSQL; no migration

**Testing**:
- pytest service, adapter and business-story tests
- web `test:i18n`, build and prettier
- the full backend suite

**Target Platform**: Backend, Web, MCP, CLI

**Project Type**: Service feature with adapters

**Performance Goals**:
- The check at entry reads one party's open items, orders and credits, which is bounded by that customer.
- The finding computes the exposure only for parties with a positive limit.

**Constraints**: Tenant-scoped; derived at read time; the reviewed tool and owner confirmation match the finance pattern; nothing in another currency is converted.

**Scale/Scope**:
- One new service module and one reviewed tool with its three adapters
- One read tool, the entry hooks, the finding, the web action
- Catalogs, stories and the Guide

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Exposure is read from open items, order lines, promises and credits; the hold is Reality on the promise. |
| II. Reality is the operational authority | PASS | No document status; the hold is on the commitment. |
| III. Proven schema only | PASS | No schema change; existing hold fields and event payloads hold the record. |
| IV. Tenant and service boundaries | PASS | One shared check called from every entry path; the release is a reviewed tool shared by Web, MCP and CLI. |
| V. Specification and test evidence | PASS | Tests are planned before each phase; stories precede the Guide change. |
| VI. Explainable Web product | PASS | The hold names every fact; the exposure read backs the "why". |
| VII. Simplicity and storage discipline | PASS | One exposure function feeds the check, the finding and the read. |
| VIII. Received values are recorded, never recomputed | PASS | Stated prices and amounts are used as stated; unpriced lines count 0 and are named. |

## Design

### Exposure (`services/credit_exposure.py`)

`credit_exposure(session, tenant, party_id, *, as_of=None, extra_document_ids=())` returns the structure in the data model.
- Open invoices and payables come from `financial_open_items(party_ids={party})`.
- Credits come from `available_credit_items(side="customer")`, filtered to the party.
- Open orders: the party's sales orders in its currency. For each line, the base is the quantity of its promises that are not cancelled (the line quantity if it has none), less `_order_line_billing(line)["invoiced"]`, never below 0, times the stated `unit_price`. A null price counts 0 and is named.

### Check at entry

`hold_if_over_credit_limit(session, tenant, order, commitments, *, action_id=None)`:
- Returns the holds it placed.
- Does nothing without a positive limit, when the order is in another currency, or when the order adds no counted value.
- Otherwise compares `exposure` with the limit. When it is over, it adds one `credit_check` hold per promise that has none, with `created_by="credit_limit"`, a summary note and a `commitment.held` event carrying the facts.

Called at the end of `create_manual_order`, the Shopify interpretation and the file `sales_order` import, inside their transaction. `assign_line_item` holds the new promise when the order has an active credit hold.

`hold_commitment` keeps its "one active hold" return for people. The credit check adds its own hold directly through a shared internal helper that emits the same event.

### Release

- `credit_hold_release` is a delivery-review tool, added to `HOLD_TOOLS`. Its allowed fields are `document_id` and `reason`.
- `review_hold` gives it a preview listing the promises and holds.
- The executor checks the owner as `FINANCE_COMMANDS` do and releases the order's `credit_check` holds with the reason.
- `release_commitment_hold` gets `reason_codes` (None = all) and `reason`. The generic tool passes every code except `credit_check` and refuses when nothing else is active; closures keep releasing all.

### Finding

`_credit_limit_exceeded_exceptions` uses `credit_exposure`. Its impact text and causal values name the exposure parts and the overdue invoices.

### Adapters and catalogs

- MCP tools, the web pass-through plus the party exposure endpoint, and the CLI commands.
- Catalog entries:
  - `command_catalog.yaml`: command, coverage, capability guidance and parameters
  - `action_discovery.json` and the web fixture
  - `resource_catalog.yaml` labels
  - `service_refusals.json`, with de/nl/es translations
  - the refusal ratchet, when a new module raises
  - the tenant isolation catalog and its pinned counts
  - the MCP topic
- Web:
  - an owner-only "Release credit hold" action with a required reason on a held order (DeliveryCase and ActionCard)
  - the hold's note in the existing hold display
  - an exposure section in the party inspector

### Stories and Guide

C07, C08 and R08 stories go in `tests/scenarios/test_catalog_finance.py`, followed by the catalog promotion, coverage, roadmap and `make docs-generate`.

## Project Structure

```text
specs/298-automatic-credit-hold/{spec,plan,research,data-model,quickstart,tasks}.md, contracts/credit-hold.md

packages/reality-core/src/reality/
├── services/credit_exposure.py          # new: exposure + check + release
├── services/core.py                     # entry hooks, release_commitment_hold reason codes, Shopify hook
├── services/file_interpreters.py        # entry hook
├── services/order_line_items.py         # hold the assigned promise
├── services/hold_actions.py             # credit_hold_release review
├── services/exceptions.py               # finding on the shared exposure
├── tools/application.py, mcp/catalog.py, cli/app.py, web/api.py
└── config/{command_catalog,resource_catalog,tenant_isolation_catalog}.yaml, config/{action_discovery,service_refusals,refusal_ratchet}.json
packages/reality-core/tests/
├── test_credit_exposure.py              # new
├── test_credit_hold.py                  # new: entry paths, release, refusals
├── test_credit_hold_adapters.py         # new: MCP, Web, CLI
└── scenarios/test_catalog_finance.py    # C07, C08, R08
apps/web/src/unified/{DeliveryCase,ActionCard}.tsx, localization.tsx, scripts/fixtures/action-reference.json
```

## Rollback

Revert the commits. Existing `credit_check` holds stay as ordinary holds, released by the generic tool.

## Complexity Tracking

No Constitution violations.
