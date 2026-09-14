# Data model

No schema change. CommitmentHold keeps its shortest link to Commitment. PartyDeliveryHold remains separate. Existing BusinessEvent.action_id/correlation_id attributes hold effects to the existing ChangeProposal. Release updates released_at on every active own hold and emits existing commitment.hold_released with hold_ids. Review metadata snapshots identities and recorded content, not a new operational authority.
