# Data Model

No new tables/columns. SourceRecord stores unmodified original data.order as shopify/order_graphql and exact external numeric ID; source_version_at is updatedAt. ImportJob context retains only explicit mapping and acquisition metadata. Existing ChangeProposal binds original source ID/hash/version and reviewed interpretation. Missing mapping remains review_required plus InterpretationOutcome, with no fabricated proposal.
