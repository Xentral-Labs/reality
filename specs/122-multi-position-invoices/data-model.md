# Data model
No migration. One SourceRecord contains submitted header and ordered lines. One Document holds the stated invoice total. N DocumentLines hold stated quantities/amounts and each points directly to its order line. Two LedgerEntries post the stated header total. Existing proposal and events bind review and exact created IDs. No payment or stock state is added.
