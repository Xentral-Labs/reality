# Quickstart: Ship-Complete and No-Backorder Rules

1. Seed a customer with an order of two lines: one in stock, one short.
2. In the web, state "Komplettlieferung" for the customer with a reason.
   - The order shows the blocker naming the short line.
   - Shipping the ready line is refused.
   - "Wartet auf Vollständigkeit" lists the order.
3. Lift the rule for this order from the finding. The ready line ships, and the customer's rule stays.
4. State "Keine Rückstände" for a second customer and ship part of an order.
   - "Rückstand gegen Kundenregel" offers the cancellation.
   - Confirm it; the finding clears.
