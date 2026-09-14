# Quickstart: Say When the Units Do Not Meet

**Language**: English

Two acceptance stories, run against PostgreSQL as part of
`tests/operational_exceptions/test_derivation.py`.

## Story one — compare what the company has explained

Order ten boxes, ship them, invoice a hundred and eight pieces. Nothing on the item relates a
box to a piece, so the comparison cannot be made — and instead of the silence that used to
follow, one entry appears against the item saying so.

State that the item is bought in boxes of twelve. The same figures are now enough: the shortfall
reports as one box, in the unit the promise and every movement against it were recorded in.
Invoice the last twelve pieces and it clears with no manual step.

**Result**: passes.

## Story two — see what could not be judged

Two order lines for one item, three invoice lines in the wrong unit, **one** entry — because the
statement that is missing belongs to the item, and so does the fix. A fourth line whose units
already match is not counted.

The entry says which of two things went wrong, because their exits are different:

- **No conversion is stated.** State it once on the item.
- **One is stated and does not divide evenly.** A hundred and seven pieces are not a number of
  boxes. The exit is to record the line in a unit that comes out, and telling this company to
  state the relation would be advice it has already taken.

**Result**: passes.

## The four declines, each with its positive control

- **No stated relation.** Stating it reports the same pair at once.
- **A factor of zero or less.** No service will record one, so this is defence against a figure
  that arrived some other way. Restoring twelve reports at once.
- **A third unit.** Kilograms on an item stocked in pieces and bought in boxes are not in
  anything this company said. The item's own purchase unit converts on a second line.
- **A remainder.** One more piece makes the total come out, and the comparison happens
  immediately — because it is the total carried against the agreement that is converted, not
  each invoice on its own.

## Prices

A hundred and eight pieces convert to nine boxes exactly, and the prices are still not compared.
Nine euro per box and nine euro per piece are different figures; dividing one by twelve produces
money nobody agreed. That decline is also not reported, because no statement anybody could make
would resolve it — an entry offering one would be a lie. A price difference in a matching unit
still reports, on the very next line.

## The demo month

Unchanged, and the pinning test proves it. Every demo item is stocked and bought in pieces and
every line is recorded in pieces, so there is nothing here to decline. That is evidence the
class is quiet where units match, and evidence of nothing at all about how loud it is where they
do not.

## What the story taught

**Three copies of one rule is how two of them come to disagree.** `_billed_quantity`,
`_credited_quantity` and `_invoice_price_differs_exceptions` each decided comparability inline,
identically, by accident. Making the rule interesting was the moment that stopped being
survivable, so it became one decision — and the class that reports the declines reads them out
of that same decision rather than working them out a second time, which is the only way it can
be guaranteed never to report a pair the classes are in fact comparing.

**Converting is not computing, and the difference is worth stating precisely.** Recomputing
means producing a second authority for a figure a source stated. Multiplying a stated quantity
by a stated factor, at read time, storing nothing, is an observation over facts held. Prices are
excluded by the same principle read the other way: the division produces a figure nobody wrote
down, and where it does not come out it is the rounding this product exists to avoid.

**A silence was the actual defect.** Every decline was the right answer and every one of them
was invisible, so an operator could not tell a line nobody needs to look at from one the rules
refused to look at. Nothing was wrong with any of those decisions; what was wrong was that they
were never said out loud.

**This class will be loud, and that is the condition.** A tenant that has never maintained
conversion factors and records lines in mixed units now sees an entry per affected item. It is
bounded by items rather than by lines for exactly that reason, and it is the first class in this
catalog whose subject is the company's own master data rather than a transaction.
