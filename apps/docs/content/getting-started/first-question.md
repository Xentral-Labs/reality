# Ask your first business question

Start with an everyday question: **What still needs to be delivered, and why?** Use your
[connected agent](./connect-agent) or the built-in Reality **Chat** with your demo company selected.

## 1. Find open work

```text
Use Reality to show me three open customer orders in my demo company. For each one,
show the customer and what remains to be delivered. Choose one and explain what was
ordered, what has already shipped and what is still open. Show the underlying records.
Do not change any data. State any missing data or limits of the result.
```

**You should see:** Concrete orders, their outstanding delivery quantities and references to the
records behind the answer. Payment and delivery are separate: a paid invoice does not prove that an
order has shipped.

Prefer a known example? Ask about **SO-006**: the unchanged baseline has five units ordered, three
shipped and two open. The agent should read its current position rather than repeat these example
quantities.

## 2. Understand one order

Continue in the same conversation:

```text
Stay with the order you selected. Explain why its remaining quantity is still open.
Distinguish what is already reserved, what stock is available at which location and
what prevents shipment, if anything. Show the evidence for each claim and say when
you cannot determine a cause. Do not change any data.
```

The useful answer separates outstanding demand, reservations and physical stock. An open quantity
alone does not prove a shortage. Available stock alone does not prove permission to ship.

## 3. Check one answer in Reality

Open the selected order in **Sales → Orders**. Compare the answer with its quantities and open an
underlying record in the Inspector. Follow its links to the supporting document and original source
payload where available.

**Business Facts** lets you inspect individual records. **Business Graph** shows their relationships
and recorded timeline. For a deeper explanation, [trace a result](./first-trace).

An empty list is not proof that everything is complete. Check the selected company, source coverage
and freshness before making a decision. Live simulation may add records between two reads.

**Next: [Prepare your first action →](./first-action)**
