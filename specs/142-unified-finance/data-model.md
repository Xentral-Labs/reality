# Data model

No new model. Open items are observations over Document evidence, LedgerEntry and SettlementAllocation. Payments are existing recorded cash entries with allocation observations and reversal roles. Journal rows are LedgerEntries. All business reads are tenant-scoped; amounts retain Decimal strings and currency. Source-stated totals remain received values. No state transitions, effects or new foreign keys.
