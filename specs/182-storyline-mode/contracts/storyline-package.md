# Contract: Storyline package

**Spec**: FR-002, FR-014, FR-017, FR-019, FR-020, FR-021 | Implemented by
`reality.storyline.package` (Pydantic v2, `extra="forbid"`, byte bound 200 000).

## Document

```yaml
storyline: 1                       # format version, integer, required
key: order-to-close                # ^[a-z0-9][a-z0-9-]{1,78}$
version: 1                         # integer > 0
title:   { en: "…", de: "…", nl: "…", es: "…" }   # en required; others required for built-ins
summary: { en: "…", de: "…", nl: "…", es: "…" }
author:  { name: "…", contact: "…" }              # optional, free text, ≤ 200 chars each
seed:
  parties:
    nordlicht: { role: customer, name: "Nordlicht Handels GmbH", payment_term: $ref.terms.net14 }
    baltic:    { role: supplier, name: "Baltic Supply" }
  items:
    fjord: { sku: IT-FJORD, name: "Fjord Thermo-Becher", unit: piece, price: "24.50", currency: EUR }
  locations:
    hamburg: { name: "Hamburg" }
  terms:
    net14: { code: NET14, days: 14 }
  history:                         # ordered; each entry is an ordinary command
    - command: movement_create
      at: -60d
      input: { movement_type: opening_stock, item: $ref.items.fjord, location: $ref.locations.hamburg, quantity: 8 }
    - command: document_create
      at: -56d
      input: { document_type: sales_invoice, number: RE-0389, party_id: $ref.parties.nordlicht, gross_amount: "1180.00", document_date: -56d, payment_term_code: NET14,
               lines: [ { item_id: $ref.items.fjord, quantity: "40", unit: pcs, unit_price: "29.50", gross_amount: "1180.00" } ] }
      as: overdue_invoice          # names the result for $seed.overdue_invoice.output.document_id
    - command: sales_invoice_post
      at: -56d
      input: { document_id: $seed.overdue_invoice.output.document_id }
    - command: party_delivery_hold          # cannot be backdated; created as of today
      input: { party_id: $ref.parties.nordlicht, reason_code: credit_check, note: "RE-0389 overdue" }
    - command: order_create
      at: -14d
      input: { direction: purchase, number: BE-0107, counterparty_id: $ref.parties.baltic, requested_delivery_at: -7d, … }
      as: purchase_order
chapters:
  - key: order
    title:     { en: "Create the order", de: "Auftrag anlegen", nl: "…", es: "…" }
    situation: { en: "…", de: "…", nl: "…", es: "…" }
    explain:   { en: "…", de: "…", nl: "…", es: "…" }
    view: view:orders               # a key of workspace_catalog.yaml views
    kind: command                   # command | read; a refused preparation is a valid outcome of a command chapter
    command: order_create           # the proposal tool name (TOOLS key; ChangeProposal.type = tool:<name>)
    input:                          # validated against the tool's MCP input schema
      direction: sales
      number: AT-0041
      company_party_id: $company.party
      counterparty_id: $ref.parties.nordlicht
      location_id: $ref.locations.hamburg
      gross_amount: "294.00"
      requested_delivery_at: +5d
      lines: [ { item_id: $ref.items.fjord, quantity: "12", unit: pcs, unit_price: "24.50", gross_amount: "294.00" } ]
    primary: { record_type: commitment, from: output.commitment_ids[0] }
    expect: { raised: [outgoing_commitment_at_risk], cleared: [] }   # shown as expected vs observed, never blocking
    next: reference
  - key: overpayment
    …
    context:                        # reads performed at preparation, in order; results feed the input
      settlement: { tool: finance.settlement.context, input: { document_id: $seed.overdue_invoice.output.document_id } }
    command: finance.settlement.apply
    input: { expected_revision: $context.settlement.revision, document_id: $seed.overdue_invoice.output.document_id, mode: payment, amount: "1300.00", allocation_amount: "1180.00", reference: "…", effective_at: 0d }
  - key: explain-hold
    kind: read
    reads:                          # a read chapter lists one to eight reads and no command
      - { tool: exception_explain, input: { exception_id: $exception.overdue_receivable.$seed.overdue_invoice.output.document_id } }
      - { tool: finance.party_balances.list, input: { side: customer } }
    requires: { findings_present: [overdue_receivable] }   # preconditions beyond resolvable references
    next: overpayment
  - key: dispatch
    …
    branches:                        # exactly one default; each names a chapter
      - { key: explain, label: { en: "…", de: "…", nl: "…", es: "…" }, next: explain-hold, default: true }
      - { key: call,    label: { … },                                    next: call-customer }
```

## Reference kinds

| Form | Resolves to | Rule |
| --- | --- | --- |
| `$ref.<group>.<name>` | the opaque id of a seed party, item or location; for `terms` the payment term **code**, because commands take terms by code | group and name must exist in `seed` |
| `$company.party` | the practice company's own party | the only `$company` field today |
| `$seed.<as>.output.<path>` | a field of a named seed history result | `as` must be declared earlier in `history` |
| `$chapter.<key>.output.<path>` | a field of an earlier chapter's proposal output | the chapter must lie on every path from the first chapter to this one (a dominator), so no branch can skip it |
| `$context.<name>[.<path>]` | a value of the chapter's `context` block, read at preparation in declaration order and recorded in the trace | `name` must be declared in this chapter's `context`; a context read may reference earlier context names |
| `$exception.<class>.<reference>` | a finding id `exc__<class>__<record id>` composed from a class and any other reference | the class must exist in the exception catalog |
| `-42d`, `+3d`, `0d` | a UTC datetime relative to the run's start, or a calendar day for `document_date` and Fact `value` | only in `at` and in fields the command documents as dates (`effective_at`, `occurred_at`, `observed_at`, `requested_delivery_at`, `promised_at`, `ordered_at`, `document_date`, `due_before`, `value`) |

Any string in `input` that matches an opaque id pattern (`^[a-z]{3}_[0-9a-f]{10}$`) or that a
command's schema declares as an id field without being a reference is refused with
`raw identity is not allowed`.

## Validation passes

1. **Shape**: the Pydantic model; unknown fields, missing required fields, wrong types, bounds
   (≤ 60 chapters, ≤ 40 history entries, ≤ 4 branches per chapter, ≤ 200 000 bytes).
2. **Catalog**: every `command` and every history `command` is a mutating tool of the
   dispatcher (`TOOLS`); every `reads[].tool` and `context.*.tool` is a read tool; every
   `view:` is a workspace view; every id in `expect`, `requires` and `$exception` is an
   operational exception class; every predicate in `expect.facts` is a Fact predicate. Inputs
   are checked against the tool's MCP input schema (required keys, unknown keys, enum members,
   scalar types) with references and relative dates as placeholders; the proposal path
   validates the resolved arguments again at run time. No JSON Schema engine is added.
3. **References**: every reference resolves within its scope (seed names, earlier seed
   results, dominating chapters, declared context names, known classes); raw opaque ids and
   misplaced relative dates are refused; `next` and every branch `next` name a chapter;
   exactly one branch has `default: true`; every chapter is reachable from the first; no
   chapter is reachable from itself; `primary.from` starts with `output.`.
4. **Language**: `en` present for every text; built-ins must carry all four languages;
   imports may omit languages and the app falls back to `en` with a visible notice.

All failures are collected and returned as `{"errors": [{"path": "chapters[3].command",
"code": "unknown_command", "detail": "…"}, …]}`; nothing is stored on any error. Warnings
(`command_requires_confirmation_you_may_lack`) do not block the import.

## JSON Schema

`reality.storyline.package.json_schema()` returns the Pydantic-generated schema with `$id`
`https://docs.runreality.ai/storylines/storyline.schema.json`; the docs generator writes it to
`apps/docs/content/public/storylines/storyline.schema.json`. A built-in file starts with
`# yaml-language-server: $schema=…/storyline.schema.json` so editors complete it.

## Draft export (FR-021)

The draft has the same shape with two additions: `draft: true` at the top and
`missing: true` on every text object the exporter could not fill. An unsupported command is
emitted as `{ key: step-7, kind: unsupported, command: <name>, reason: "…" }` in place;
validation of a draft reports it as an error, so a draft must be edited before import.
