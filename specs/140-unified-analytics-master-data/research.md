# Research decisions

- Existing dashboard trends are scripted previews, so they cannot support live historical promises. Use actual dated Commitment and Movement records and label their different units as record counts.
- MovementCorrection explicitly links original, compensation and replacement. Effective shipment activity excludes original/compensation IDs, allowing an uncorrected replacement to contribute on its own occurrence day. This is corrected retained history, not an immutable as-of snapshot.
- Existing core preview_master_data_updates supplies expected_revision and update_* batch tools preserve optional fields. Reuse them; narrow the new form to basic fields. In particular location update defaults would clear parent if omitted, so retain it explicitly from the snapshot.
- Customer/supplier classification follows PartyRole, not duplicated identities or only the single legacy type. Similar labels never identify a record.
- Durable creation retries use existing ChangeProposal identities. An uncertain execution is looked up, not submitted again. Editing creates a new reviewed proposal after rejecting the old one.
- Human continuation already authorizes this product increment. There is no unresolved owner decision, new schema or removal to approve again.
