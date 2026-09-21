# Explainable B2B Operational Chain

Specification 248 extends the canonical international demo with two compact end-to-end reference
chains. Both begin as ordinary dated documents, use shared application services and expose exact
human references plus UI paths in the profile manifest. They do not create a parallel demo model.

## Customer-specific procurement and replenishment

Search Sales for `SO-040` and Purchasing for `PO-010`. The purchase promises ten units of
`ITEM-011`: six are explicitly assigned to the customer commitment, two to stock replenishment and
two remain unassigned. Four units have arrived. Assignment describes commercial intent only;
receipt, physical stock and reservation remain separate facts.

Expected reconciliation: ordered 10 = customer-assigned 6 + stock 2 + unassigned 2. Received 4 and
open 6 are an independent fulfilment dimension. The profile manifest case is `b2b_supply_chain`.

## Mixed returned-goods disposition

Search Sales for `SO-041`, then open `ITEM-012` movements in Warehouse. Five shipped units return
to the Singapore location. Two are returned to normal Rotterdam stock, one remains in the
quarantine/repair location, one is scrapped with a stated reason and one is returned to the
supplier with a stated reason.

Expected reconciliation: arrived 5 = restocked 2 + quarantined 1 + scrapped 1 + supplier-returned
1 + unresolved 0. Customer credit and refund remain independent commercial evidence. The profile
manifest case is `b2b_return_disposition`.

## Traceability and replay

Every movement in these chains is linked to a commitment, return, source or explicit disposition
reason. The movement explanation read follows those shortest true links and does not persist a
derived authority. Company setup and assignment request identities are deterministic; replaying
the same confirmed setup request returns the same company instead of duplicating records.
