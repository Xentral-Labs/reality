# Implementation Plan: The Link Nothing Enforced

**Branch**: `100-the-link-nothing-enforced` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One configuration file saying which nullable references the operational exception queue leans on,
what depends on each and which way each fails; three gates composing it with facts discovered from
the mapper, the source and the command catalog; and the two things those gates find on their first
run.

## Technical Context

**Language/Version**: Python 3.12+, TypeScript for the web app
**Primary Dependencies**: SQLAlchemy 2, PyYAML, `ast` from the standard library
**Storage**: PostgreSQL; **no migration**
**Testing**: pytest, `tests/test_reference_integrity.py`, plus the web app's own build
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: No class changes; no reference becomes required; nothing is guessed
**Scale/Scope**: One config file, one loader, three gates, two surface fixes

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Nothing about the layers changes. The gate governs references between records that already exist | PASS |
| Reality owns operational state | The declaration is configuration about code, not tenant state; no derivation and no stored value changes | PASS |
| Proven schema only | No migration. Two surfaces gain the ability to carry a field that already exists | PASS |
| Tenant + shared service boundaries | The gates read the mapper, the source and the catalogs; the two recordings that prove the directions are tenant-scoped like every other | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | A person recording a manual line can finally say which order line it bills, which is what eleven classes read | PASS |
| Received values not recomputed | No reference is guessed, matched or generated. A missing one stays missing | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Make the references non-nullable.** The obvious fix and the wrong one: every one of the four
  records legitimately exists without its reference. A manual invoice for a service bills no order
  line; a transfer settles no return. Requiring the link would refuse honest records to protect a
  derivation, which inverts what the product is for.
- **Add a class reporting a line with no reference.** It would be a wall of entries, most of them
  correct, and nobody could clear them. Spec 088 already refused a class on exactly that ground —
  a condition nobody can end is a report, not an exception.
- **Guess the link.** Matching an invoice line to an order line by item and amount is the guess
  Spec 099 refused for announcements. It would be worse here: a wrong link makes five classes
  *confidently wrong* rather than blind, which is the only outcome worse than silence.
- **Hand-write the list of references that matter.** The version this replaces. A list beside the
  code is exactly what drifts, and the last three gates in this repository all worked because one
  side of them was complete by discovery.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/reference_catalog.yaml           # new: the declaration
packages/reality-core/src/reality/catalogs.py                 # its loader and validation
packages/reality-core/src/reality/mcp/catalog.py              # the schema names the field
packages/reality-core/tests/test_reference_integrity.py       # new: the three gates
packages/reality-core/tests/operational_exceptions/test_derivation.py  # the two directions
apps/web/src/api.ts, apps/web/src/App.tsx                     # the box a person can type in
docs/features/operational_exceptions.md, docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### What the gate is composed of

The same shape as Spec 094, and the reason it worked there: **one side is complete by discovery
and cannot be forgotten, the other is hand-maintained and must be argued.** Three pairs:

| Discovered, complete | Declared, reasoned | The gate |
|---|---|---|
| Every nullable foreign key on the four records, from the mapper | load-bearing or trace-only, with a reason | a new reference cannot arrive unclassified |
| Every derivation that reads a load-bearing reference, from the source | the classes declared for it | a class cannot start or stop depending on one quietly |
| Every construction of one of the four records, from the source | exemptions with reasons | a new writing path cannot drop a reference |
| Every adapter of a command whose service constructs one, from the command catalog | exemptions with reasons | a surface cannot be unable to carry one |

Every one fails in both directions. A stale entry is as much a failure as a missing one, because a
stale exemption hides the next real gap — the lesson Spec 094 wrote down.

### The declaration

`config/reference_catalog.yaml` lists each record's nullable references. A load-bearing entry
names what it means, the classes that depend on it, and each class's **direction**:

- `reports_absence` — the class concludes from the reference being missing, so a missing one
  reports work that was actually done. It cries wolf.
- `requires_presence` — the class starts from the reference, so a missing one means it never looks
  at that record. It goes blind.
- `traces_only` — the class names the reference in the evidence it reports and concludes nothing
  from it. Absence costs nothing.

The reading is the most useful thing in the file, and it is the one thing **only a person can
say**. Discovery can prove which classes *read* a reference; it cannot tell a conclusion from a
mention, because both are the same attribute access. So the gate keeps the list complete and the
reading is argued — and every `traces_only` entry is a claim a reviewer can disagree with.

Twenty-five pairs: six cry wolf, thirteen go blind, six only trace. `billed_not_received` going
blind means a company pays for goods that never arrived and nothing notices. And four classes are
in both directions at once — `shipped_not_billed` cries wolf when an invoice line does not say
what it bills and goes blind when the promise does not say which order line it came from.

Validation lives in the loader rather than only in the test, so anything that loads the catalog
gets the same refusal — the rule Spec 007 set for every other catalog here.

### Discovering the consumers

The derivation registry gives every class its function. Walking the module's syntax tree from
there — through the helpers it calls, following both attribute reads and string literals, because
`invoice_price_differs` names the column in a query while `shipped_not_billed` reads it through a
helper — gives the set of load-bearing references each class touches.

Only load-bearing references are walked. A trace-only reference like `source_record_id` is read by
almost every class to fill in its evidence, and walking those would report thirty-one of
thirty-two classes and mean nothing. That distinction is exactly what the first gate exists to
keep honest.

The walk is deliberately generous — it counts a string literal as well as an attribute access, so
a class that reaches a reference by name in a dictionary still counts. That over-reports on
purpose: it can never miss a real reader, and everything it names has to be classified, including
the six pairs that turn out to be evidence rather than reasoning.

### Discovering the writers

Every construction of `DocumentLine(`, `Movement(`, `Commitment(` or `ReturnAnnouncement(` in
`reality/**`, found by syntax tree rather than by grep so a keyword spread over several lines still
counts. For each, the load-bearing references of that record must appear among its keywords.

Passing the keyword is not the same as passing a value — `billed_document_line_id=row[...]` is
`None` when nobody supplied one, legitimately. So this gate proves the **plumbing** exists on every
path, not that a person filled it in, and the specification says so rather than implying more.

### Discovering the surfaces, and why MCP cannot be exempted

A command whose service constructs one of these records declares its adapters. Each adapter has one
module, and the reference must be named there.

A passthrough may be exempted for a human adapter: chat forwards whatever arguments it is given, so
a person who knows the field can use it. **MCP may never be exempted on that ground**, and this is
the point worth arguing. An agent knows only what a schema names. `document_create_propose`
declares `lines` as a free-form object array, so the field has always passed through if sent — and
no agent has ever sent it, because nothing told it the field exists. A passthrough is a capability
for a human and an absence for an agent.

### What the gates find on their first run

Written before anything was declared, as Spec 094's was, so the first run is evidence rather than
decoration:

- **MCP does not name `billed_document_line_id`.** Fixed by declaring the line schema properly
  instead of `{"type": "object"}`.
- **The web app cannot send it.** `ManualLine` has no such field, so the Cockpit's manual document
  form — the only human surface for a manual invoice — has no box for the thing eleven classes
  read. Fixed in both the recording form and the correction form.

The web app's field is a plain text input for an order line identity. There is no reference
combobox for document lines and inventing one is a separate piece of work; a labelled box a person
can paste an id into is honest, and better than the nothing that is there now.

### Data and migration impact

None. No table, no column, no revision.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `test_reference_integrity.py::test_every_nullable_reference_is_classified` | a reference is unclassified |
| FR-002 | unit | `test_reference_integrity.py::test_the_reference_catalog_fails_in_both_directions` | an empty reason is accepted |
| FR-003 | unit | `test_reference_integrity.py::test_declared_consumers_are_the_discovered_consumers` | the lists differ |
| FR-004 | story | `test_derivation.py::test_a_missing_billing_reference_makes_the_queue_cry_wolf` and `::test_a_missing_billing_reference_makes_the_queue_go_blind` | the direction is not what was declared |
| FR-005 | unit | `test_reference_integrity.py::test_every_writer_passes_the_reference_through` | a construction drops one |
| FR-006 | unit | `test_reference_integrity.py::test_every_adapter_can_carry_the_reference` | MCP cannot |
| FR-007 | unit | `test_reference_integrity.py::test_an_mcp_passthrough_is_not_an_exemption` | the exemption is accepted |
| FR-008 | unit | `test_the_reference_catalog_fails_in_both_directions` | a stale entry passes |
| FR-009 | unit | `test_every_adapter_can_carry_the_reference` | the schema is silent |
| FR-010 | review | the web app's line shape and its build | no field exists |
| FR-011 | story | every existing suite, unchanged | a class moved |
| DR-001 | review | no migration added | — |
| DR-002 | unit | `test_reference_integrity.py::test_the_loader_refuses_a_broken_catalog` | only the test validates |
| DR-003 | unit | the three discovery tests | a list is hand-maintained |
| DR-004 | unit | `test_coverage.py` closed registry test | passes unchanged |
| DR-005 | review | no matching or generation added | — |
| DR-006 | story | the existing isolation suites | — |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no behaviour change. The gates are tests; the two fixes add a field to a schema
and a box to a form. A tenant that never uses either behaves exactly as today. Rollback is deleting
the config file, its loader and the test module.

The demo month's pinned queue is unchanged.

## Review Risks

- **The gate proves the plumbing, not the value.** Every path can carry the reference; nobody is
  forced to set it. That is the honest limit of a gate that must not make an optional field
  required, and the specification states it rather than implying more. What it does buy is that
  the next writing path and the next surface cannot silently lack the ability.
- **The consumer discovery is a syntax-tree walk, not a proof.** It follows calls by name inside
  one module and would miss a reference reached through a dynamic lookup or another module. That is
  a real limit; against it, the walk is checked against a declaration a person wrote, so the two
  have to agree, and either being wrong alone fails the build.
- **A fourth reference joined the list during the work.** `Commitment.document_line_id` was not in
  the original three; the mapper-driven discovery found it, and eight classes turn out to conclude
  from it through a single inner join in `_order_line_promises`. That is the gate earning its keep
  before it shipped, and a warning that a hand-written list would have been wrong on day one.
- **`traces_only` is where the gate stops being mechanical.** Six pairs are declared as evidence
  rather than reasoning, and nothing but a person's reading says so. A wrong call there makes the
  map say a class is safe when it is not. The counter-argument is that the alternative — treating
  every read as a conclusion — would declare fourteen classes dependent on a reference where six
  of them are not, and a map that over-claims is trusted less than one that argues.
- **A plain identity box is poor interaction design.** Pasting an order line id into a text field
  is not what a good form does. The alternative is a reference picker for document lines, which is
  a separate feature; the box is chosen over continuing to have nothing.
- **The glossary entry is not rendered anywhere yet.** The generated reference describes
  top-level parameters, and `billed_document_line_id` is a field of a line inside `lines`. So the
  gate makes sure the reference is described in the one place this repository describes
  parameters, and a reader of the generated MCP page still will not see it. Rendering nested line
  fields is a separate piece of work; describing the field is worth doing first, and pretending
  otherwise would be the kind of overclaim this specification exists to avoid.
- **Trace-only is a judgement.** Classifying `source_record_id` as trace-only is a person's call,
  and if a class ever concludes from its absence the classification becomes wrong. The consumer
  gate does not walk trace-only references, so that mistake would not be caught — which is why
  every trace-only entry has to state a reason somebody can disagree with.

## Complexity Tracking

No Constitution exception is claimed. No schema change, no new entity, no new exception class, no
new derived value, and no change to any existing behaviour.
