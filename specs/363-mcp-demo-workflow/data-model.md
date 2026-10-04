# Data Model

No new fields, tables, migrations or persisted derived states. Company context reads
Tenant. Pending pages read ChangeProposal metadata. Exact review reads the same retained
proposal input/preview and decision policy as Web. The delivery review fingerprint is
scoped to exact retained intent/state, not an authentication credential. DocumentLine
discovery follows its existing Document foreign key. All queries enforce tenant scope.
