# Contract: Foreign-Currency Purchasing

## Company currency

- `company_currency_set` (reviewed): `{currency}`.
  - The review shows the current currency and the stated one.
  - Refusals:
    - `company_currency_invalid`;
    - `company_currency_has_postings`;
    - `company_currency_changed_since_review`.
- `company_currency` (read): `{currency, source_record_id | null}`.
- Web:
  - `GET /api/tenants/{t}/finance/company-currency`;
  - `POST /api/tenants/{t}/finance/company-currency/proposals`, confirmed by the shared approve.
- CLI: `finance company-currency show|set CUR`.

## Supplier invoice

`supplier_invoice_record` and `supplier_invoice_post` take an optional `exchange_rate` (a decimal string, company units per invoice unit).
- It is required when the invoice currency differs from the company currency (`exchange_rate_required`).
- It is refused when the currencies are the same (`exchange_rate_not_applicable`).
- It must be positive (`exchange_rate_invalid`).
- The review shows `{currency, gross_amount, exchange_rate, company_amount}`.

## Supplier payment

`supplier_payment_post` takes an optional `paid_amount` (a decimal string, company currency).
- It is required for an invoice in a foreign currency (`paid_amount_required`).
- It is refused for an invoice in the company currency (`paid_amount_not_applicable`).
- It is refused for an unconverted foreign invoice (`invoice_not_converted`).
- It must be positive (`paid_amount_invalid`).
- The review shows:
  - `amount` and `currency`, the settled amount in the invoice currency;
  - `paid_amount` and `payment_rate`;
  - `invoice_rate` and `invoice_value`, the company-currency value of the settled part;
  - `exchange_difference` (`gain` | `loss` | `none`, and the amount).
- A change of the invoice's remainder since the review makes the confirmation stale.

## Ledger reads

Ledger entries and posting groups gain `company_amount` and `exchange_rate`, and posting groups gain `company_currency`. Account balances gain `company_balance`.
