# Contract: Application Reference

`GET /api/tenants/{tenant_id}/application-reference`

Authorization uses existing active tenant membership. Success returns `version`,
`principle`, four counts, and `commands`, `events`, `projections`, and
`fact_predicates`. Commands contain enriched service contracts; Projections contain
derived `invalidated_by` Events. No tenant rows are returned. Invalid configuration
fails closed instead of serving partial data.

