# Quickstart: Sold for Less Than It Costs to Buy

**Language**: English

One acceptance story with five silences, run against PostgreSQL as part of
`tests/operational_exceptions/test_derivation.py`.

## The story

Record a standing purchase price of 10 for an item and agree a sales line at 8. One entry, with
both prices and a shortfall of 2 — each figure exactly as somebody wrote it. Agree another at
exactly 10 and nothing appears. Correct the first to 11 and the entry is gone on the next read.

## The five silences, each with its positive control

- **No purchase price standing.** Nothing is reported, whatever the sales price. Record one and
  the same line reports at once.
- **A line agreed at zero.** A sample or a replacement is priced at nothing on purpose. A line
  at one cent is not, and reports.
- **A purchase order line, and a line with no item.** Buying cheaply is the point of buying, and
  freight has no purchase price of its own. A sales line for the same item reports.
- **A different currency or unit.** Two euro a piece against ten a box is not a comparison. The
  same figures in the price list's own unit report.
- **Selling at exactly the purchase price.** A thin deal is a decision.

**Result**: passes.

## The demo month

Unchanged, and it proves nothing: the demo keeps no purchase price list, so the class cannot
fire there in either direction. Recorded here rather than presented as evidence.

## What the story taught

**The blocker was an assumption, not a missing capability.** This feature sat in the project's
own notes as needing "a cost basis the model does not hold". It does not: a purchase price list
is a first-class concept with its own direction, and the price on it is a figure somebody
stated. Checking that took one grep. The lesson is not about pricing — it is that a note saying
"this needs X first" ages badly and should be re-checked before it is believed, especially when
X sounds like accounting.

**Refusing to compute is what made it small.** A cost model would have needed landed cost, a
valuation method, and a decision about which receipt a sale consumed — and would have ended with
Reality presenting its own arithmetic as fact. Comparing two received values needs none of that
and is the same shape as every other price class here.

**The honest version is worth less than the imagined one, and says so.** It understates, because
freight and handling are not in the figure. It is silent for any company that keeps no purchase
prices, which may be most of them. Both are in the class's own guidance, where an operator reads
it, rather than only in this specification.
