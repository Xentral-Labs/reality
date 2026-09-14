# Data Model
No business schema change. UI layout v1: density normal/compact, hidden optional column IDs, bounded width map. Keyed by authenticated user ID and stable register variant. Corrupt/unknown values ignored. No records stored.
URL table query: table identifier, size25/50/100, sort allowlisted string, direction asc/desc. Incompatible variant sort resets. Tenant switch clears selected records/filter/page as before.
