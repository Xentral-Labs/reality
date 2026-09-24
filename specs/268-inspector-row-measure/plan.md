# Plan: An Inspector row states one measure

The rows already exist and already carry typed presentation parts
(`services/inspector_presentation.py`). The work is to give a row one more field of the
same kind, render it as a column, and move twelve compounds into it.

## The contract

`InspectorRow` gains two optional fields beside the existing `value`/`display_parts`:

```
meta?: string            # the qualifier, as the producer's plain rendering
meta_parts?: InspectorPart[]   # the same typed parts the value uses
```

Both are emitted only when a qualifier exists, so a row without one is byte-identical to
the row before this change (FR-008). Two builders produce rows and both take the same
argument (FR-009): `_row(label, value, kind, id, *, meta=None)` in
`services/operational_previews.py` and `inspector_row(label, value, *, meta=None)` in
`web/api.py`. Each runs its qualifier through the `display_parts` the value already uses,
so a date, an instant, a number or a money amount is typed rather than stringified.

## When a clock carries nothing

`moment(value)` in `services/inspector_presentation.py` returns `value.date()` when the UTC
clock reads midnight and `value` otherwise (FR-004). It lives in the presentation module
rather than in either producer, because both layers build movement rows and a second copy
would drift. `display_parts` then types the result as `date` or `datetime` with no further
branching, and the client's existing `formatDate`/`formatDateTime` do the rest — no new
part type, no new client formatter.

## What moves and what does not

A qualifier answers when, which state, where, or which record (FR-003). By that test:
ten rows move, two stay.

Moving: the pair's movements and reservations
(`operational_previews.py`); the commitment inspector's reservations and movements; the
three commitment lists on the document, party and item inspectors; the item inspector's
recent movements; the location inspector's recent movements, whose qualifier is itself
composite (`item name · moment`); the document inspector's ledger rows, where the measure
is the amount and `debit`/`credit` qualifies it — the two swap places; the shipment's
physical contents; the payment's inactive allocations.

Staying: both document-line rows, which compose a quantity with a money amount. Two
measures are a missing third column, and `meta` renders muted and small — the wrong home
for an amount. Recorded in the spec's Non-Goals rather than left implicit.

## The three renderers

`InspectorContent` (`apps/web/src/unified/Inspector.tsx`) carries the change. A row becomes
a bordered wrapper holding either a button (linked) or a div (plain), so the divider is the
same width in both cases and the hover surface can extend past it. The value side is a flex
group: the measure with `tabular-nums`, then the qualifier in a `min-w-[9.5rem]`
right-aligned muted column. In `compact` the group stacks instead (FR-005) — the inline
preview's cards are roughly 300px inside the dialog grid, where two columns do not fit. The
link's accent and underline move from the whole value to the measure alone (FR-006).

New class strings are module constants next to the file's existing `compactGrid` and
`compactSection`: the i18n audit treats a multi-word string literal inside a ternary as UI
copy, and Tailwind classes with spaces fail `isNonCopyValue`.

`ContextExplorer.tsx` renders the same rows in a narrow aside; it gets the stacked form.
`ObjectGraph.tsx` draws rows as graph nodes with one line of text, so it takes
`inspectorRowText(row)`, which joins value and qualifier back with the middle dot (FR-007)
— the compound is right where there is no second column to put it in.

`inspectorFormat.ts` gains `inspectorMeta(row)` and `inspectorRowText(row)` so the joining
rule exists once.

## Constitution Check

PASS. No schema, migration, table, column or projection: rows stay read-time observations
(Hard rules 1, 11). No document status field (Hard rule 2). No new identity (Hard rule 6).
No business rule in a transport — no number, derivation or link changes (Hard rule 7, Web
UI invariant). Tenant scope untouched: no new query. Read-only, so no confirmation boundary
(Hard rule 10). No new MCP tool or catalog entry; agents read records, not Inspector rows.

## Verification and rollback

`packages/reality-core/tests/test_inspector_presentation.py`: `moment()` for the midnight,
real-clock and `None` cases; `inspector_row` emitting a typed qualifier and a plain row
emitting neither field.

`packages/reality-core/tests/test_stock_at_location.py`: the pair's movements and
reservations carry quantity and moment apart; an import without a clock states only its
day; the location inspector's movement rows keep their item name — now asserted in `meta`,
and asserted *not* to be in the value, so the split cannot silently regress.

`apps/web/scripts/inspector-row-shape.test.mjs`: the two parts never share an element;
tabular figures and the reserved column; the row is the click target and the qualifier is
not underlined; the compact preview stacks; a row without a qualifier keeps its old
classes; `inspectorRowText` recomposes.

Regression cover comes from the suites that already read these inspectors end to end:
`test_operational_previews`, `test_master_data_api`, `test_unified_invoice_credit`,
`test_unified_delivery_reads`, `test_shipment_api`, `test_partial_invoicing_rebilling`,
`test_unified_customer_refund`, and on the web side `cost-record-inspector.test.mjs` and
the 262 browser script.

Rollback is a revert: no data is written, no contract field is required, and consumers that
ignore `meta` behave as before.

## Known follow-up

The row markup is duplicated in three renderers and was kept in step by hand. A shared row
component would make the next such change a one-file change. Named here and in the spec's
Assumptions; not part of this feature.
