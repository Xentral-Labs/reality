# Quickstart: Graph-Native Reporting

Status: planned. Nothing below executes yet; it describes the intended first slice so the
shape can be judged before implementation.

## Ask a question

Chat and the API author a typed query object. People who prefer to read the path use the
Cypher-near text surface. Both compile to the same internal query.

    MATCH (c:party {id: $customer})<-[:ordered_by]-(o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN month(o.ordered_at), o.currency, sum(stated_order_amount)

`ordered_by` is declared `n:1`, so nothing fans out and each order is counted once.

## Watch it refuse

    MATCH (c:party {id: $customer})<-[:ordered_by]-(o:order)
          -[:contains]->(l:order_line)-[:of_item]->(i:item)
    RETURN i.name, sum(stated_order_amount)

`contains` is declared `1:n`. A EUR 1,000 order with four lines would be counted four
times. The compiler refuses, names `contains` as the edge that fanned out, and offers
`line_amount`, which lives at line grain. Hand-written SQL and literal Cypher both return
4,000 here without complaint.

## Compare across domains

Order value, invoiced amount and allocated settlement are three separate aggregates
joined on party and currency — never one join chain, which would multiply all three
against each other. Each branch keeps its own date basis.

## Traverse to variable depth

    MATCH (l:location {id: $warehouse})<-[:within*1..6]-(sub)<-[:stored_in]-(m:movement)
    RETURN m.item, sum(quantity)

`within` is the only recursive edge declared today. It compiles to a recursive common
table expression with the declared depth bound and a cycle guard. An unbounded request is
refused. When bills of material arrive, `consists_of` is declared the same way and every
existing capability applies to it with no compiler change.

## Save it

Prepare, review, confirm and save are unchanged from spec 222. The stored definition is
the typed traversal plus the model version that interpreted it — no SQL, no dialect.

## What you will not find

No view to create, no role to provision, no grant to audit, no second database, no
materialised projection, and no place to type raw SQL in the primary path.
