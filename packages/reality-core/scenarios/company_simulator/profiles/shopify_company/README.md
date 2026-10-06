# Synthetic Shopify company

`scenario.yaml` is an explicitly synthetic month. `shopify.py` preserves the original authored order/refund shapes and uses existing production reviewed Shopify intake. Generic provider payout statements use the normal payout_statement authority; they are not mislabeled as native Shopify Payments data.

The profile distinguishes order demand, invoice, provider charge/refund, actual physical return, credit note, fees and bank payout. Three provider statements total charges90, refunds10, fees4 and net deposits76 EUR; clearing is independently checked at -10 EUR due to an intentionally unmatched charge. Statements arrive even when an operator creates no invoices: known payments are held/unallocated, while the unknown reference remains unmatched. Replaying a statement must not duplicate accepted records/postings.

No authentic customer export/API payout example exists in this repository. Real native-format mapping remains pending such evidence. Run with `--profile shopify`; see the parent README for setup, evidence and coverage boundaries.
