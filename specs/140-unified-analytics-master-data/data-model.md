# Data model

No new table, column or migration. Current metrics derive from Commitment and existing Reservation/Movement correction-aware helpers. Daily activity uses Commitment.created_at and Movement.occurred_at, with MovementCorrection links. Contributor identities retain the shortest existing trace paths.

Reference views use Party + PartyRole, Item and Location. Detail snapshots and expected revisions use existing core helpers. SourceRecord links remain unchanged by basic edits. ChangeProposal stores one-record canonical create/update intent, revision checks and the existing execution receipt. A deterministic ID is request identity, never business identity; actor and tenant participate in its hash.
