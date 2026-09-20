# Quickstart: Verify CEO Contribution Templates

1. Run focused declaration and traversal tests.
2. Run the focused web contract test and frontend build.
3. Start the normal stack and open Analytics → Templates.
4. Confirm the four localized contribution templates appear.
5. Adopt each and confirm it pauses at the contribution-basis selector.
6. Select the demo company's confirmed contribution basis and compare results with invoice-line explanations.
7. Verify currency/base-unit separation, monthly/channel grouping, leakage ordering, and incomplete DB2 coverage.

Required regression gates: `make spec-check`, focused backend tests, relevant web tests, `make lint`, `make test`, and `make web-build`.
