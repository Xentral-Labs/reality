# Tasks: The demo company also buys and gets paid

1. Scenario tests first: customer payment states and the receivable, the six purchase
   states, received quantities and stock, and identical settlement across companies.
2. Author `SETTLEMENT` and `PURCHASES` in `demo/international.py`.
3. Seed customer payments in the history loop.
4. Seed the purchase chain: orders, receipts, supplier invoices, supplier payments.
5. Widen the profile authority by exactly the operations these need.
6. Update the profile contract and the feature documentation with the new baseline.
7. Run the focused suites and the full PostgreSQL suite; record verification.
