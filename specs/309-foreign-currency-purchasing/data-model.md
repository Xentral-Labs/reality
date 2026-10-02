# Data Model: Foreign-Currency Purchasing

## `company_currency` (new)

| Column | Type | Notes |
|---|---|---|
| tenant_id | String, PK, FK tenant | One row per company; absent means EUR |
| currency | String(3) | Upper-case ISO code |
| source_record_id | String, FK source_record (tenant) | The statement in force, a version of `internal_company_currency` |
| created_at, updated_at | DateTime(tz) | |

Checks: `currency ~ '^[A-Z]{3}$'`.

## `ledger_entry` (two new columns)

| Column | Type | Notes |
|---|---|---|
| company_amount | Numeric(18,4), nullable | Amount in the company currency; null means an unconverted foreign entry from before spec 309 |
| exchange_rate | Numeric(18,8), nullable | Company units per document unit; 1 for company-currency entries |

Checks:
- `company_amount IS NULL OR company_amount >= 0`;
- `exchange_rate IS NULL OR exchange_rate > 0`.

A document-currency `amount` of 0 is allowed only on an `exchange_difference` entry with a positive company amount. The service enforces this, because the account role is derived.

Backfill: `company_amount = amount` and `exchange_rate = 1` where `currency = 'EUR'`.

## Account role `exchange_difference` (new)

Debit is a realised loss and credit a realised gain. It gets a default destination like the other roles.

## Events

- `company_currency.set` (subject `company_currency`).
- `ledger.posted` entries gain `company_amount` and `exchange_rate`. The group payload gains `company_currency`.
