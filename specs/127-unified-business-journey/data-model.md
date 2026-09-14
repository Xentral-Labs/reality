# Data model
No new entities or fields. Order SourceRecord→Document→DocumentLine→Commitment; Reservation→Commitment; shipment Movement→Commitment. Invoice line→order line; credit line→invoice line. Refund postings are linked to credit postings through SettlementAllocation. LedgerReversal preserves original entries. Verify derived quantities and balances with no source amount recomputation.
