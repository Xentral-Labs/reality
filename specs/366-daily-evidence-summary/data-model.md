# Transient read data

No persisted entity or migration changes.

`summary` on discovery pages: scope=shown_records; shown_record_count; counts_by_type
for movements; omitted_before (cursor present); omitted_after (has_more);
complete_matching_selection (no cursor and no more); observation (deterministic English
text explicitly about retained records). The input records remain the traceability basis.
Counts are record counts, never quantities, customers or orders. Empty reads preserve
upstream freshness unknown. Legacy list output unchanged.

`unfulfilled_cause` on each order fulfillment line: status unknown for an open line
with positive open quantity; otherwise not_applicable. Notice states current blockers
are readiness observations, not evidence of historical nonexecution cause. The shortest
links remain commitment_id to existing order/movement/reservation evidence.

Quantity-reference records (Movement/Commitment/Reservation) include item_name and item_sku
from the same scoped Item reference used for unit. They are transient reference labels,
not identity; absent labels remain null. Source quantities are unchanged.
