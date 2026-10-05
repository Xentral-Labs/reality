# Data model
No stored entities, fields or relationships are added.
Order → DocumentLine → Commitment; document fallback applies only when commitment has no line. Reservation/Movement → Commitment. BusinessEvent subject_type/subject_id identifies an exact member and action_id identifies the ChangeProposal. Executed status is retained lifecycle evidence, not proof every external effect succeeded; exact execution status owns verification.
Transient record fields: id, proposal_id, tool, status, created_at, decided_at, review_read, verification_read, association_scope. Page metadata adds decision_coverage. No input/output, human decider claim, review token or approval authority is exposed.
