# Data Model
No persistence change. Fact keeps tenant, subject type/ID, predicate, stored value, observed_at and optional source/rule identity. SourceRecord version metadata and InterpretationRule name/version are projected through scoped joins. Repeated observations remain distinct by opaque Fact ID. URL context is not business state. Subject/source scope clearing does not mutate any record.
