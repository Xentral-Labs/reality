# Research
Canonical aging_register -> financial_open_items -> settlement_positions handles
postings, allocation reversals and opening balances. No equivalent shared SQL exists.
Reuse it rather than duplicate finance calculations. party_balances is paginated and
includes unused credits, so it cannot be treated as invoice outstanding amounts.
Debit-positive/credit-negative is established by core.account_balance.
Document.document_date is lossless text; explicit semantic metadata and guarded
read-time parsing avoid a storage migration and preserve malformed originals.
Research agent finance_analysis_research reviewed canonical services read-only.
