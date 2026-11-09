# Existing records only

- Action/ChangeProposal: dedicated type shopify_source_buyer_mapping/1, frozen review input, proposed then mapping-only executed output, external attribution remains truthful.
- Approval SourceRecord/SourceStream: tuesday/shopify_buyer_mapping_approval/original_source_id; raw proof plus exact review and one immutable current mapping choice. No ImportJob for proof evidence.
- Original Source/SourceStream untouched. Original ImportJob.input untouched; error/status/outcome may record buyer_mapping_recorded_intake_pending while still needs_review.
- Party/PartyRole read and locked only. No customer/order/commitment/movement/ledger/fulfillment rows created.
