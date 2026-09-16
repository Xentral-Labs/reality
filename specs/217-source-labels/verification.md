# Verification

2026-09-16. Approved scope, three requirements and three mapped tasks; no unresolved clarifications, critical findings or Constitution exceptions.

- Existing provenance-label tests first failed with translated Source/Origin labels; after implementation all nine provenance tests pass. The origin metadata and links remain unchanged.
- `gmake spec-check web-build`: passed, including formatting, 215 frontend tests, all four language audits, TypeScript and production build. Existing bundle-size advisory only.
- Provenance browser suite passed in en/de/nl/es, asserting the visible Source column caption, nonempty origin badges, link presence/absence, target host disclosure, Source Record inspection, contributing systems, 390px overflow and GET-only reads. Updated script formatting passed.
- Runtime regression found during review: mapping multiple keys to Source made reverse localization show Provenance in English. Fixed by changing related callers to the single Source key; legacy Provenance/Data source translations stay unchanged. Original source captions retain a local adjective around Source Record to avoid an alias with the canonical record name. Browser caption assertions protect this behavior.
- Reviewed 60 effective locale/key changes plus source-related UI heading/column keys. RecordOrigin fields, source_record identifiers, URLs, original names/external IDs and stock/source-code vocabulary remain unchanged. Review table is in review.md.
- No backend tests or catalog generation needed for UI-label-only changes. No schema or application-service modifications.
