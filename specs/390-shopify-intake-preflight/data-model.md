# Data model

No persistent additions or updates. Read immutable SourceRecord, latest SourceStream,
ImportJob association/input, spec389 Action/approval Source relationship, Party and
PartyRole, Location and Item. A report is an ephemeral typed observation, not an
intake proposal, mapping grant, order, stock/payment fact or readiness authority.
Digest only semantic returned fields; observation time is outside the digest.

Reference fingerprints cover observed stable fields only, using purpose
shopify_intake_reference/1 plus kind and state. Common state is record ID, label,
active and source ID. Company adds type/roles; location adds type/stock permission/
parent; item adds SKU/unit/item type/tracking. These common schema99/current fields
avoid importing the newer reviewed-intake subsystem or treating irrelevant future
columns as read authority. No value is persisted as a new master-data version.
