# Data model

No schema change. MovementCorrection retains original_movement_id, compensating_movement_id and optional replacement_movement_id, reason and request_fingerprint. Existing BusinessEvent action_id/correlation_id attributes the correction to ChangeProposal. Review snapshots are proposal metadata only, not business authority. Signed pool effects are derived reads. Original/replacement return references remain explicit and cannot silently vanish in the quantity form.
