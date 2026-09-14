# Implementation Plan: A Lot Can Expire

**Branch**: `109-a-lot-can-expire` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One nullable date on the lot record, one operation to state it, one operational exception class
over stock a company holds past its best-before, and one cause saying that stock is reserved for a
customer. No threshold, no horizon, no learned statistic.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, PyYAML
**Storage**: PostgreSQL; one revision adding one nullable `Date` column
**Testing**: pytest, `tests/test_inventory_tracking_reservations.py` and the derivation suite
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Nothing computed, nothing blocked, nothing chosen; strict tenant scope
**Scale/Scope**: One column, one operation, one class, one cause

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The date is printed on the goods and stated on the delivery note; the lot is the Reality record it belongs to, and the source record it came from is already linked | PASS |
| Reality owns operational state | Expiry is a stated fact; whether stock is expired is derived per read from that date and the day the queue is asked | PASS |
| Proven schema only | One nullable column on an existing record, for a value that has nowhere to live, justified in Complexity Tracking | PASS |
| Tenant + shared service boundaries | Every read and write filters `tenant_id`; the quantity held comes from the one tracked-identity stock rule the product already uses | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The entry names the stated date, how long ago it passed, the quantity held, and whether a customer is waiting for it | PASS |
| Received values not recomputed | **The centre of this feature.** No shelf life is multiplied out from a production date, no horizon is invented, and re-stating a different date is refused rather than adjusted | PASS |
| Smallest coherent design | Five alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Store a shelf life in days on the item and compute the date.** This is how most systems do it
  and it is the exact thing Principle VIII forbids: the date a company acts on would be one the
  product multiplied out rather than one the supplier stated, and a lot that left the factory late
  would carry a date nobody printed. The date is read off the goods.
- **An "expiring soon" class.** The one a reader will expect, and refused deliberately. It needs a
  horizon, and no horizon exists: nothing on an item states a shelf life and no term states a
  minimum remaining life. Learning it from this company's own turnover would work and would put an
  **eleventh** class on the Spec 080 helper, whose numbers have never been checked against a real
  business — the largest standing risk in this queue. Reporting what has actually expired needs no
  invented number at all. What would unblock it is named in the specification.
- **A second class for expired-and-reserved.** Same record, same owner, same clearing path; only
  the urgency differs, which is what a cause is for. Two classes would have meant two ids for one
  lot and an operator reconciling them.
- **Refusing to ship expired stock.** It would stop a company recording something that already
  happened, which is the opposite of what this product is for. The customer has the goods either
  way.
- **A `String` or a timestamp for the date.** The repository stores business dates as strings
  (`document_date`) because a source may state a free-form period label, and instants as
  `DateTime(timezone=True)`. A best-before is neither: it is a calendar day, and an instant would
  invent a time of day nobody stated. This is the first `Date` column in the schema, which is a
  novelty worth naming and still the honest type.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/00xx_lot_expiry.py
packages/reality-core/src/reality/db/core.py                     # the column
packages/reality-core/src/reality/services/core.py               # create_lot, state_lot_expiry
packages/reality-core/src/reality/services/exceptions.py         # one class, one cause
packages/reality-core/src/reality/catalogs.py                    # the class id and cause id
packages/reality-core/config/operational_exception_catalog.yaml
packages/reality-core/config/command_catalog.yaml                # one command
packages/reality-core/config/tenant_isolation_catalog.yaml
packages/reality-core/config/business_event_catalog.yaml          # lot.expiry_stated
packages/reality-core/src/reality/tools/application.py, mcp/catalog.py, web/api.py
packages/reality-core/tests/test_inventory_tracking_reservations.py
packages/reality-core/tests/operational_exceptions/test_derivation.py
docs/features/inventory.md, docs/features/operational_exceptions.md
apps/docs/content/catalogs/ (+ de/), docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### The date

`lot.expires_at`, a nullable `Date`. Stated at creation, or once afterwards through
`state_lot_expiry` — because goods arrive before somebody reads the label, and the alternative
would be recreating the lot.

**Re-stating a different date is refused.** A best-before read off the goods is a received value,
and two different dates for one lot means one of them is wrong in a way this product cannot
adjudicate. Re-stating the *same* date is accepted and changes nothing, so a retry is safe. Doing
corrections properly needs the append-only shape Spec 093 built for a counterparty's restatement,
and that is separable work rather than a corner of this one.

A lot with no date asserts nothing in either direction. There is no way to tell an item with no
shelf life from one whose label nobody read, and inventing that distinction would be worse than
the silence.

### The class, and the number that is not in it

`stock_expired` reports every lot whose stated best-before has passed and which still has stock on
hand. Two measurements, both real: the date somebody stated, and the day the queue is read. **No
threshold, no horizon, no learned statistic.**

That absence is the design decision most likely to be questioned, so the reasoning is here rather
than implied. "Expiring soon" is the more useful report and it needs a horizon. Nothing on an item
states a shelf life, no term states a minimum remaining life, and the one mechanism that could
produce a number — Spec 080's learned rule — already governs **ten of thirty-four classes** on
figures nobody has checked against a real business. Adding an eleventh would grow the largest
standing risk in this queue to buy a report whose threshold nobody could defend. Expired is
unambiguous and costs nothing invented.

The quantity held comes from `stock_by_identity`, the rule the product already uses for a tracked
identity, so this can never disagree with what the inventory register shows. A lot with nothing
left is not reported: nothing is held, so there is nothing for anybody to do.

Ordering is by the day each lot expired and then by identity, so two identical reads of an
unchanged tenant return an identical answer.

### The cause

`reserved_for_delivery` says the expired stock has an active reservation naming its lot, and names
how much. Same record, same owner, same clearing path — only the urgency differs, which is exactly
what a cause is for. Releasing the reservation removes the cause and leaves the entry, because the
stock is still expired.

Both `Reservation` and `Movement` already name a lot, so the cause and the quantity held need no
new relation at all.

### Nothing is blocked and nothing is chosen

No movement is refused, no reservation is released, no lot is picked. Refusing a shipment of
expired stock would stop a company recording something that already happened — the customer has
the goods — and choosing which lot ships is an allocation policy this product has never had.

### Data and migration impact

One revision adding one nullable `Date` column. No backfill: no lot states a date before this
ships, so the class reports nothing and every existing behaviour is untouched. The downgrade drops
the column.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_inventory_tracking_reservations.py::test_a_lot_carries_the_stated_best_before` | nothing can hold it |
| FR-002 | service | `test_inventory_tracking_reservations.py::test_a_best_before_can_be_stated_afterwards` | it cannot |
| FR-003 | service | `test_inventory_tracking_reservations.py::test_a_different_best_before_is_refused` | it is overwritten |
| FR-004 | service | `test_a_different_best_before_is_refused` | an unreadable date is accepted |
| FR-005 | service | `test_a_lot_carries_the_stated_best_before` | an undated lot asserts something |
| FR-006 | story | `test_derivation.py::test_stock_expired` | no entry |
| FR-007 | story | `test_stock_expired` | a lot with nothing held is reported |
| FR-008 | story | `test_derivation.py::test_expired_stock_reserved_for_a_customer` | no cause |
| FR-009 | story | `test_derivation.py::test_expired_lots_are_ordered_by_the_day_they_expired` | order varies |
| FR-010 | service | `test_inventory_tracking_reservations.py::test_expiry_blocks_nothing` | a movement is refused |
| FR-011 | story | every existing suite, unchanged | an existing behaviour moved |
| DR-001 | review | one migration, one nullable column, no backfill | — |
| DR-002 | unit | `test_coverage.py` closed registry and cause vocabulary tests | catalog drift |
| DR-003 | review | no threshold or learned helper in the diff | — |
| DR-004 | story | `test_derivation.py::test_the_quantity_held_is_the_one_stock_rule` | a second count appears |
| DR-005 | service | `test_inventory_tracking_reservations.py::test_lot_expiry_is_tenant_scoped` | another tenant is reachable |
| DR-006 | service | `test_a_different_best_before_is_refused` | a date was adjusted |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

One migration adding a nullable column. No lot states a date on deploy, so the class reports
nothing and every register, projection and class behaves exactly as today. Rollback drops the
column; the lots and movements already recorded are untouched.

The demo month states no best-before and its pinned queue is unchanged.

## Review Risks

- **The absent "expiring soon" class is the thing a reviewer will ask for**, and it is the most
  useful report shelf life could produce. Refusing it is a judgement about evidence, not about
  value: the horizon would be invented, and the one mechanism for producing it is already carrying
  ten classes on unverified numbers. If a real tenant supplies a turnover figure, or a customer
  term states a minimum remaining life, this becomes buildable on stated ground.
- **Expired stock stays sellable.** Nothing is blocked, so a picker can still ship it and the
  entry only reports afterwards. That is deliberate — refusing the movement would stop a company
  recording what happened — and it means this feature reduces surprise rather than preventing
  loss.
- **A stated date cannot be corrected.** A typo is stuck until somebody builds the append-only
  restatement this deliberately leaves out. The alternative — silently overwriting a received
  value — is worse, and refusing at least makes the typo visible.
- **The first `Date` column.** Every other business date here is a string or a timestamp. A
  reviewer may prefer consistency with `document_date`; the argument for the type is that a
  best-before is a calendar day and both alternatives misrepresent it, one as free-form text and
  the other with a time of day nobody stated.
- **A lot with no date is silent, and most lots will have no date.** So the class fires only for
  companies that record the field, and there is no way to nag the ones that do not — nothing
  states which items have a shelf life. That is a real limit of a model that only knows what it
  was told.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| Schema change: one nullable date on `lot` | The value has nowhere to live; nothing in the schema can express a best-before, and it decides whether stock may be sold | A shelf life on the item with the date computed, rejected under Principle VIII; a string or a timestamp, rejected as misrepresenting a calendar day | Recorded here; one revision, no backfill |
