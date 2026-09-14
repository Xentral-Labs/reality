# Question coverage contract

This is the implemented acceptance scope for spec 185. Deterministic cases in
`test_analytics_questions.py`, `test_analytics_execution.py`, contributor/export
tests and canonical service regressions cover the supported meanings below. The
executable catalog publishes the seven restricted meanings (Q13, Q14, Q15, Q20,
Q21, Q24 and Q27) with the named narrower alternative. IDs correspond to the
[assessment](../../docs/analytics-question-assessment.md). Supported means the stated
descriptive meaning, never complete upstream knowledge.

| # | Question | Required answer in this feature |
|---|---|---|
| 1 | Customers ordering X in week 7 | Supported: distinct customers, product identity, ISO year/week and explicit timezone/date field. |
| 2 | Customers inactive for three months | Supported: previously observed buyers with no retained order in the resolved window; history scope disclosed. |
| 3 | First-time customers this month | Supported as first observed order in retained history, not first-ever purchase. |
| 4 | Largest quarter-over-quarter customer changes | Supported: comparable stated order values per currency, absolute/relative change, explicit dates and zero-baseline handling. |
| 5 | Customers buying A but not B | Supported: existence/absence in an explicit retained-history window. |
| 6 | Most ordered products this month | Supported: rank by selected order count, distinct buyers or comparable quantity. |
| 7 | Weekly quantity/value by product | Supported: recorded quantities and stated line amounts by ISO week, separated by unit/currency. |
| 8 | Products ordered together | Supported: distinct unordered product pairs per retained order, co-order count; repeated lines cannot multiply pairs. |
| 9 | Agreed selling prices by customer | Supported: recorded line prices with currency/unit/basis; no substitution of current price lists. |
| 10 | Frequently cancelled/returned products | Supported as separate operational cancellation counts and received-return quantities. No undefined combined rate; announced returns and source cancellation remain distinct. |
| 11 | Incompletely shipped customer orders | Supported: canonical open delivery commitments grouped by existing order evidence, including explicit documentless cases. |
| 12 | Overdue delivery promises and customers | Supported: current canonical overdue outgoing promises and affected parties. |
| 13 | Orders feasible from stock | Restricted: offer current reservation/hold readiness with explicit meaning. No simultaneous feasibility or allocation optimization. |
| 14 | Missing products for open orders | Restricted ambiguous wording: offer reservation gaps or current company-wide physical-stock versus open-demand comparison as separate definitions. Neither allocates future supply. |
| 15 | Order-to-delivery duration | Restricted: explain that dispatch completion, customer receipt and revision baseline differ. Existing dated shipment records may be shown; no new universal completion KPI. |
| 16 | Stock and reservations by location | Supported: current canonical physical/reserved/available quantities by item/location. |
| 17 | Stock with no outflow for 90 days | Supported: positive current stock with no effective movement of selected outbound types in the window. Corrected originals do not establish activity. |
| 18 | Stock not covering promised demand | Supported: current company-wide physical quantity against open customer demand, unit-safe; no time-phased allocation or location feasibility claim. |
| 19 | Supplier orders due next week | Supported: current effective due dates and remaining supplier promises; not an arrival forecast. |
| 20 | Customer orders affected by supplier delay | Restricted: offer candidate open customer demand sharing the late supplier promise's item. No causal or exact allocation assertion. |
| 21 | Supplier historical punctuality | Restricted: offer current overdue supplier commitments and original/revised dates; no undefined historical reliability rate. |
| 22 | Purchase-price trends | Supported: historical stated purchase-line prices grouped by product/currency/unit and date. |
| 23 | Historical suppliers, quantities and prices for X | Supported: retained purchase evidence by supplier with explicit ordered versus received quantities. |
| 24 | Single-supplier dependence | Restricted: offer exactly one observed supplier per product in the selected purchase history, not lack of available alternatives. |
| 25 | Partially received/invoiced purchase orders | Supported: compose canonical received/open quantities and line billing observations, including corrections/reversals and comparability limits. |
| 26 | Open/overdue customer invoices | Supported: complete invoice-level canonical open-item and aging results. Unposted evidence is separately identified, not included as a booked receivable. |
| 27 | Average customer payment lateness | Restricted: show recorded payments/allocations and current due-date context, without an invented historical weighted lateness KPI or using allocation time as payment time. |
| 28 | Shipped lines not fully billed | Supported: canonical shipment/billing discrepancy interpretation, returns/reversals/unit handling and exact contributing links. Dispatch is not confirmed receipt. |
| 29 | Payments with unallocated amounts | Supported: canonical allocated/unallocated recorded payments with complete result scope. |
| 30 | Due receivables/payables by week/currency | Supported: current open items grouped by ISO due year/week, side and currency; unknown dates stay separate. No cash forecast. |

## Default metric meanings

- Descriptive order measures use stated order/line evidence, not commitment creation time or current remaining quantity. Fully operationally cancelled orders can be excluded explicitly; partially cancelled order evidence retains its original stated values.
- Order totals and line amounts are distinct measures. A header amount must never be multiplied by joining its lines. Product-filtered value uses matching stated line amounts.
- Quantities are never combined across incompatible units. Money is separated by currency. No FX or new conversion policy is introduced.
- Compare periods using exact resolved boundaries. An incomplete current quarter is not silently treated as a completed quarter; explicit unequal periods remain visibly unequal.
- No matching records, unknown source values and numeric zero are different results. Aggregate bounds never silently omit matching contributors.
- A query requiring unavailable evidence reports its limitation; a narrower alternative is separately named and is never substituted silently.
