# Read-time model
No persistence changes. stock_position derives three Numeric columns on item identity.
The fixed derivation registry maps finance.aging→document and warehouse.inventory→item,
with validated column metadata and one bound typed JSON relation per used service.
Measures preserve the item's unit and disallow time-bucket trends. The stock→item
identity edge provides existing true links to evidence, movements and reservations.
