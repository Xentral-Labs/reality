# Implementation Plan: Company Time Zone

**Branch**: `349-company-time-zone` | **Spec**: [spec.md](spec.md)

## Summary

`domain/calendar.business_day(value, zone)` is the one rule that turns a stated day or an instant
into a business day. `services/company_time_zone.py` keeps the company's stated zone (table
`company_time_zone`, migration `0138`, versioned source stream as for the company currency) and
offers `company_zone`, `company_day` and `company_today`, memoised per session. Operational day
derivations route through it:

- `core`: shop order dates (`_source_document_day`), invoice, credit, payment and refund document
  dates, the aging register and overdue days, expired lots, the payment run's today;
- `credit_actions`, `payment_actions` (evidence checks mirror creation), `invoice_actions`,
  `down_payments`, `payment_intake`, `finance/settlement`, `finance/deposits`,
  `delivery_failures`, `finance/balances`, `finance/opening`, `payouts`, `credit_exposure`,
  `operational_previews`, `analytics/finance_relation`;
- `exceptions`: expiry, open items, discount deadlines and `next_clock_moment` (local midnight;
  an item due or expiring today is now a candidate, which the UTC version missed under the
  24-hour floor);
- `web/read_models`: register day filters in SQL with the same stated-day rule.

Not routed (limitations): analysis report grouping, cost/contribution economic dates, demo and
storyline fixtures, display-only formatting.

## Constitution Check

- Storage stays UTC; stated days are never recomputed (VIII).
- One typed table justified by use on every day derivation (III); tenant-scoped.
- The statement is reviewed and versioned; the tool is shared by all surfaces.
- No document status.

## Tests

Service tests, a migration test, the Q05 story and pinned catalog counts.
