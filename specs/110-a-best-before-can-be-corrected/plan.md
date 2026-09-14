# Implementation Plan: A Best-Before Can Be Corrected

**Branch**: `110-a-best-before-can-be-corrected` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One operation that corrects a stated best-before against a confirmed current value and a reason,
with its audit carried by a business event. One refusal message that now says where to go. No
schema, no new record type, no new class.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML
**Storage**: PostgreSQL; **no migration**
**Testing**: pytest, `tests/test_inventory_tracking_reservations.py` and the derivation suite
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Nothing judged, nothing derived; a correction confirms what it replaces
**Scale/Scope**: One operation, one event type, one corrected refusal message

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The lot is Reality; correcting a misread value on it is the product keeping its own record true, and the correction's own audit is a Business Event | PASS |
| Reality owns operational state | Whether stock is expired stays derived per read. The only write is the date and, through the event, what it was before | PASS |
| Proven schema only | No migration, no field, no table. The audit is carried the way a manual document's line correction already carries its own | PASS |
| Tenant + shared service boundaries | Every read and write filters `tenant_id` | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The event says what the date was, what it is and why. The refusal from stating names the correction | PASS |
| Received values not recomputed | The new date is recorded exactly as stated. Nothing is derived, and the product does not judge which reading was right | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **An append-only statements table, like Spec 093's.** The obvious shape and the wrong one, because
  the two things are different: Spec 093's own docstring says its record is *not* a correction —
  *"a correction says the record was wrong; this says the record was right and the world moved."* A
  best-before does not move. It would also make this the first correction in the product with its
  own record type, which a typo does not justify.
- **Letting `state_lot_expiry` overwrite.** Then nothing here would be worth building, and the
  distinction that makes the record trustworthy — stating is what you read, correcting is admitting
  you read it wrong — would be gone. It goes on refusing; only its message changes.
- **Refusing a correction when the lot carries a source record**, as
  `correct_manual_document_lines` refuses for a document. Measured before rejecting: **no import
  path creates lots at all.** `create_lot` is reached only from the agent tool, the API and the
  command line, each of which may attach a source record itself, and the date is stated by whoever
  calls the operation in every case. So the lot's source record says where the *batch* came from,
  not where the *date* came from, and refusing on it would block a correction to a hand-typed date
  because the goods arrived by import.
- **Requiring only a reason, without a confirmation.** Cheaper and weaker. Three operations in this
  product already make a caller confirm what they are acting on — the confirmed count of Spec 085,
  the confirmed total of Spec 098, the expected revision of a document correction — and the reason
  is the same each time: an operation that changes something a person got wrong should not be
  reachable by somebody who has not looked at it.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py     # correct_lot_expiry, one refusal message
packages/reality-core/config/command_catalog.yaml      # one command, two glossary entries
packages/reality-core/config/tenant_isolation_catalog.yaml
packages/reality-core/config/business_event_catalog.yaml  # lot.expiry_corrected
packages/reality-core/src/reality/tools/application.py, mcp/catalog.py, web/api.py
packages/reality-core/tests/test_inventory_tracking_reservations.py
packages/reality-core/tests/operational_exceptions/test_derivation.py
docs/features/inventory.md, docs/SPEC_COVERAGE_MATRIX.md
apps/docs/content/catalogs/ (+ de/)
```

## Design

### A correction, not a restatement

The distinction is the design. A counterparty saying a delivery will now be later is the world
moving, and Spec 093 keeps every statement because each was true when it was made. A best-before
is printed on a box: it does not move, so a second date means the first reading was wrong. Keeping
both as equally valid statements would be recording a contradiction as though it were history.

So the value is corrected in place and the audit goes in the event — which is exactly what
`correct_manual_document_lines` does for a document's lines, before and after, in the payload.

### What a correction costs

`correct_lot_expiry(lot_id, expires_at, *, expected_expires_at, reason)`.

- **A reason**, refused when empty. This is somebody saying the record was wrong; the reason is the
  only part of that a reader can use later.
- **The date they believe is stored**, including `None` for "nothing is stated". Refused when it
  does not match. Three operations here already work this way and the argument is the same: an
  operation that overwrites what a person got wrong must not be reachable by somebody who has not
  looked at it. It also makes the intent legible — *"I saw the fifteenth, it is the sixteenth"* —
  which is more than a reason alone conveys.
- **An actual change.** Correcting a date to itself is refused, the same call Spec 097 made about a
  revision that restates nothing.

Both dates go through the one date rule Spec 109 added, so an unreadable value is refused in either
position rather than in one.

### Correcting to nothing

Allowed, with a reason. A date read off the wrong label, on an item that has no shelf life, can
only honestly be fixed by saying the lot has no date.

The cost is stated rather than hidden: afterwards the record looks exactly like a lot nobody ever
stated a date for. The event history is the only place that distinction survives. That is
acceptable for the same reason the absent date is ambiguous in the first place — the product cannot
tell "no shelf life" from "nobody wrote it down" — and pretending otherwise would need a second
column to say why the field is empty.

### The refusal that sends people here

`state_lot_expiry` goes on refusing a different date, and its message now names the correction. A
refusal without a way forward is how the stuck typo stayed stuck for a whole specification, and
one sentence fixes it.

### The queue needs nothing

`stock_expired` derives from the stated date per read, so a correction changes what it reports on
the next read with nothing stored and no manual step. Both directions are recorded: an entry that
goes when the date moves forward, and one that appears when it moves back.

### Data and migration impact

None. No field, no table, no revision.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_inventory_tracking_reservations.py::test_a_misread_best_before_can_be_corrected` | nothing can correct it |
| FR-002 | service | `test_inventory_tracking_reservations.py::test_a_correction_refuses` | an empty reason is accepted |
| FR-003 | service | `test_a_correction_refuses` | a mismatched confirmation is accepted |
| FR-004 | service | `test_a_correction_refuses` | a no-op correction is accepted |
| FR-005 | service | `test_a_correction_refuses` | an unreadable date is accepted |
| FR-006 | service | `test_inventory_tracking_reservations.py::test_a_correction_records_what_it_replaced` | no event, or no before |
| FR-007 | service | `test_inventory_tracking_reservations.py::test_stating_a_different_date_names_the_correction` | the refusal says nothing |
| FR-008 | story | `test_derivation.py::test_the_queue_follows_a_corrected_best_before` | the entry does not move |
| FR-009 | review | the operation's own signature | — |
| FR-010 | story | every existing suite, unchanged | an existing behaviour moved |
| DR-001 | review | no migration in the diff | — |
| DR-002 | service | `test_a_correction_records_what_it_replaced` | a new record type appears |
| DR-003 | unit | `test_coverage.py` closed registry test | catalog drift |
| DR-004 | service | `test_a_misread_best_before_can_be_corrected` | the product judged a date |
| DR-005 | service | `test_inventory_tracking_reservations.py::test_correcting_expiry_is_tenant_scoped` | another tenant is reachable |
| DR-006 | service | `test_a_misread_best_before_can_be_corrected` | a date was adjusted |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no schema. The operation is additive; a tenant that corrects nothing behaves
exactly as today, and the only change to an existing operation is the wording of one refusal.
Rollback removes one command.

The demo month states no best-before and its pinned queue is unchanged.

## Review Risks

- **Correcting to nothing is lossy in the record.** Afterwards a lot looks like one nobody ever
  dated, and only the event history says otherwise. The alternative is a second column recording
  why the field is empty, which is more schema than the case deserves; the limit is stated in the
  specification rather than discovered later.
- **A correction confirms a value rather than a revision number.** Two corrections in the same
  instant could in principle both pass their confirmation if they read the same value first, and
  the second would win. A revision counter would close that; a lot's best-before is not a field two
  people race on, and adding a counter for it would be schema for a hypothetical.
- **The product does not judge which reading was right.** A correction records that somebody says
  the first one was wrong. Nothing stops a second correction back again, and nothing should:
  Reality is not the arbiter of what is printed on a box.
- **This makes `stock_expired` movable by hand.** Somebody who wants an entry to go away can
  correct the date forward. That is true of every corrected value in the product, the reason is
  recorded, and the alternative — an uncorrectable field — is the bug this specification fixes.

## Complexity Tracking

No Constitution exception is claimed. No schema change, no new entity, no new record type, no new
class, no new cause.
