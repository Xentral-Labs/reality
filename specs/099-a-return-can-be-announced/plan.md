# Implementation Plan: The Parcel That Has Not Left Yet

**Branch**: `099-a-return-can-be-announced` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One table for what a customer said they would send back, one nullable reference letting the goods
name the announcement they fulfil, one shared rule for what can still come back, and one class
for an announcement nothing arrived against.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, PyYAML
**Storage**: PostgreSQL; one revision — one table and one nullable column
**Testing**: pytest, `tests/test_return_announcements.py` and the derivation suite
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Append-only movement history; strict tenant scope; nothing generated
**Scale/Scope**: One table, one column, three operations, one class, one shared rule

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | A customer's statement arrives as Source or is recorded directly; the announcement is the promise the company then holds, and the goods that follow are the Movement they always were | PASS |
| Reality owns operational state | The announcement is settled by what arrives against it, derived per read, with one stored status transition — the same one `_append_movement` and `revise_commitment` already make | PASS |
| Proven schema only | One table for a record that does not exist, and one nullable reference, added exactly as Spec 082 added its own. No existing column changes | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; one rule answers what can still come back, for the movement path and the announcement alike | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The entry names the quantity announced, what has arrived, the day it was announced and which rule judged it | PASS |
| Received values not recomputed | Quantity, reference and reason are stored exactly as stated. No reference is generated, and the learned threshold shares a rule and never a history | PASS |
| Smallest coherent design | Four alternatives rejected below, one of them with a measurement | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **A third `Commitment.type`.** This is the semantically obvious answer: a Commitment *is* a
  directional promise and a customer promising to send goods back is one. It is rejected on a
  measurement rather than a feeling. `customer_delivery` appears **32 times across 8 modules**,
  and **17 of those are a two-way branch** — `"shipment" if commitment.type == "customer_delivery"
  else "receipt"`, `allowed = {...} if ... else {...}`, and so on — whose `else` silently means
  *supplier delivery*. A third type makes every one of those seventeen wrong, and most would go on
  passing their tests, because no test asks what happens to a type that does not exist yet. Spec
  093 faced the same choice for a counterparty's restatement and made the same call.
- **Matching arrivals to announcements by item and quantity.** Two open announcements against one
  delivery make it a guess, and a guess about which of a customer's returns arrived is worse than
  no link at all. One nullable reference, named by the caller, exactly as Spec 082 did.
- **Replacing the return's link to the delivery.** The return still names the customer delivery.
  That link bounds the return and four classes read it; the announcement is an additional
  statement about the same event, not a substitute.
- **Two classes, dated and undated, as Spec 080 did.** Spec 080 split because an undated order is
  a genuinely different operational situation from a late one. Here it is one condition with one
  owner and one clearing path, differing only in how the date was arrived at — so that belongs in
  the entry, not in the catalog.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0043_return_announcements.py
packages/reality-core/src/reality/db/core.py                      # the table, the column
packages/reality-core/src/reality/services/core.py                # the rule, three operations
packages/reality-core/src/reality/services/exceptions.py          # one class
packages/reality-core/config/operational_exception_catalog.yaml   # its guidance
packages/reality-core/config/command_catalog.yaml                 # three commands
packages/reality-core/config/tenant_isolation_catalog.yaml
packages/reality-core/config/business_event_catalog.yaml          # two events
packages/reality-core/src/reality/tools/application.py, mcp/catalog.py, web/api.py
packages/reality-core/tests/test_return_announcements.py          # new
docs/features/movements.md, docs/features/operational_exceptions.md
apps/docs/content/catalogs/ (+ de/), docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### One rule for what can still come back

`record_movement` already applies it inline for a returning movement: what was shipped against
the commitment, less what has already come back, read the correction-aware way so a voided
shipment protects nothing. That becomes `returnable_quantity(session, tenant_id, commitment_id)`
and the movement path becomes its first caller rather than its owner.

The announcement is its second caller, minus one more term: what other **open** announcements
against that delivery already claim. Without it a customer could announce the same five items
twice and the desk would expect ten.

This is the sixth derived figure in this line of work that had to be single-sourced — unit
comparability, learned thresholds, the date in force, the quantity in force, what is payable, and
now what can still come back. The rule is written before either caller uses it, and a test asserts
nothing else computes it.

### The announcement

A row holding the delivery it concerns, the quantity, the reference and the reason as the customer
stated them, the instant it was announced, the day the customer said the goods would go where they
said one, and a status of `open`, `fulfilled` or `withdrawn` — the same three-word vocabulary a
Commitment uses, because it is the same shape of thing.

It is **Reality rather than Evidence**: it is not a document somebody sent, it is the promise the
company now holds as a result. So it is settled or withdrawn, never corrected, and the statement
it was made from is whatever Source or operator produced it.

Nothing is generated. The reference in particular: a number this product invented would become the
number somebody has to tell the customer, and there is no notification path here.

### The parcel names its announcement

`Movement` gains a nullable `return_announcement_id`, added exactly as Spec 082 added
`resolves_movement_id` — nullable by design, because almost every movement fulfils no
announcement and the absence of a reference says exactly that.

Refused before anything is written: a movement that is not a return, an announcement that is not
open, and an announcement whose delivery is not the movement's own commitment. That last one is
the check that makes the link mean something.

The announcement is settled as fulfilled **at the moment** what has arrived against it reaches
what was announced — not at the next read, because there may not be a next event. That is the one
stored write this feature makes, and it is the same field for the same reason as Spec 097's
promise falling to what had already arrived.

More arriving than was announced is accepted, within what the delivery still allows. The customer
said two and sent three; both are true, the third item physically exists, and refusing would lose
a real movement.

### Nothing arrived

`announced_return_not_arrived` reports an open announcement with nothing, or not enough, arrived
against it. Two ways in:

- **The customer stated a day.** Report past it. Their word is the measurement and nothing needs
  learning.
- **They did not.** Report past this company's own rhythm, from the Spec 080 rule unchanged: the
  middle of the most recent twenty announcements that did arrive, three times over, never below a
  fortnight, and **silent below five** — because a company without history is not one with a
  lenient threshold, it is one this rule cannot speak about.

The entry says which rule judged it, so an operator reading it knows whether they are looking at
a promise the customer broke or a parcel that is simply slower than usual here. The floor is a
fortnight, matching `return_unresolved`, because a fortnight for a parcel to travel is ordinary
and the two halves of a return's life should not disagree about what ordinary means.

It clears when the goods arrive, with nothing stored. A withdrawn announcement is not reported at
all, because a withdrawal is the customer saying the parcel is not coming and there is nothing
left for anybody to do.

### Data and migration impact

One revision. A new table, and one nullable column with a foreign key on `movement`. No backfill:
no announcement exists before this ships, so every rule falls through and every class behaves
exactly as today. Downgrade drops both.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_return_announcements.py::test_what_the_customer_said_is_recorded` | nothing can hold it |
| FR-002 | unit | `test_return_announcements.py::test_one_rule_answers_what_can_come_back` | a second rule appears |
| FR-003 | service | `test_return_announcements.py::test_two_announcements_cannot_claim_the_same_goods` | it is accepted |
| FR-004 | service | `test_return_announcements.py::test_an_announcement_refuses` | a refusal is accepted |
| FR-005 | service | `test_return_announcements.py::test_the_parcel_names_its_announcement` | the link is not accepted |
| FR-006 | service | `test_return_announcements.py::test_a_movement_refuses_a_foreign_announcement` | a mismatch is accepted |
| FR-007 | service | `test_return_announcements.py::test_an_announcement_is_finished_when_the_goods_arrive` | it stays open |
| FR-008 | service | `test_return_announcements.py::test_more_may_arrive_than_was_announced` | it is refused |
| FR-009 | service | `test_return_announcements.py::test_an_announcement_can_be_withdrawn` | it cannot |
| FR-010 | story | the existing return suites, unchanged | an existing behaviour moves |
| FR-011 | story | `test_derivation.py::test_announced_return_not_arrived` | no entry |
| FR-012 | story | `test_derivation.py::test_an_announcement_without_a_date_or_a_history_is_not_judged` | it is judged |
| FR-013 | story | `test_derivation.py::test_announced_return_not_arrived` | the entry survives |
| FR-014 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | exactly one migration, one table, one column | — |
| DR-002 | review | the measurement in this plan | — |
| DR-003 | service | `test_one_rule_answers_what_can_come_back` | it is stored |
| DR-004 | story | `test_derivation.py::test_the_announcement_threshold_is_the_learned_rule` | a second rule appears |
| DR-005 | service | `test_return_announcements.py::test_announcements_are_tenant_scoped` | another tenant is reachable |
| DR-006 | unit | `test_coverage.py` closed registry test | catalog drift |
| DR-007 | service | `test_what_the_customer_said_is_recorded` | something was generated |
| DR-008 | unit | `test_application_catalog.py` reachability gate | an operation is undeclared |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

One migration adding a table and a nullable column. No announcement exists on deploy, so
`returnable_quantity` subtracts nothing, no movement carries a reference, and the new class
reports nothing. Rollback drops both; the returns and resolutions Specs 079 and 082 recorded are
untouched.

The demo month announces nothing and its pinned queue is unchanged.

## Review Risks

- **A third `Commitment.type` really is the more elegant model**, and a reviewer is entitled to
  prefer it. The argument against it is a measurement — seventeen two-way branches whose `else`
  means supplier delivery — and the honest cost of the choice made instead is one more entity in
  a model that prides itself on having few. If the commitment vocabulary is ever widened
  deliberately, this table is the first thing that should be folded into it.
- **One class judged two ways.** It reads as a shortcut and it is argued as a deliberate choice:
  one condition, one owner, one clearing path. If a reviewer disagrees, the split is mechanical —
  the derivation already branches — and the cost is a second catalog entry with the same
  guidance.
- **An announcement does not reserve or expect anything.** Nothing about supply changes, which
  means a company cannot plan around announced returns. That is deliberate: goods a customer has
  promised to send are not goods anybody can sell, and treating them as supply is how a
  warehouse ends up committing stock that never arrives.
- **The extra item.** Accepting three when two were announced means an announcement can be
  over-fulfilled. The alternative refuses a movement that physically happened, which is worse.
- **One stored status transition.** The announcement's status is set when the goods arrive rather
  than derived. It is the same trade Spec 097 made and for the same reason: without it a
  fulfilled announcement reads "open" until something else happens to it, and nothing else may.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| Schema change: one new table | Nothing in the model can hold what a customer said before the goods move; the announcement is a record that does not exist | A third `Commitment.type`, rejected on a measurement of seventeen two-way branches whose `else` means supplier delivery | Recorded here; one revision, no backfill |
| Schema change: one nullable column on `movement` | The goods must be able to say which announcement they fulfil, and matching would be a guess | Matching by item and quantity, rejected because two announcements against one delivery make it a guess | Recorded here; added exactly as Spec 082 added its own |
