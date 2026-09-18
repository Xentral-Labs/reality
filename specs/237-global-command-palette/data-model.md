# Data Model: Global Command Palette

## Business persistence

No business table, typed business field, foreign key or source payload changes. Search reads existing identity and held display fields. Operational amounts/status remain observations from canonical readers. No stored search documents, background index, denormalized balance or document fulfillment state.

## Read contracts

### SearchRequest

- `tenant_id`: server route scope, never inferred from a target or cursor.
- `principal`: authenticated/trusted-local execution context, with existing membership and lesson policy enforced.
- `query`: trimmed text, 0–500 characters; nonempty input searches records, while empty input returns no record candidates and is handled by metadata/preferences.
- `provider`: allowlisted provider enum from the search contract.
- `family`: optional allowlisted refinement belonging to that provider.
- `language`: `en | de | nl | es`; original business names stay unchanged.
- `limit`: 1–50, default 4 for palette provider requests.
- `cursor`: optional opaque continuation; includes version, query/scope fingerprint, tier and last ordering tuple. It is not authority; validation never removes tenant/owner predicates.
- `context` and `recent_keys`: optional bounded allowlisted identities for same-tier tie-breaking, at most twenty keys. They grant no permission and do not add candidates.

### SearchHit

- `key`: canonical physical record kind plus opaque ID, or stable capability/destination/template key. Tenant scope is part of the enclosing request.
- `family`: record refinement distinct from its visible result group.
- `group`: one of the eleven stable visible-group keys in `contracts/search.md`; provider boundaries do not create new groups.
- `label`, `secondary`: business-facing context drawn only from held/authorized values.
- `roles`: existing partner roles when relevant.
- `reference`, `recorded_date`, `source_label`: optional held distinguishing metadata, no guessed values.
- `state`: optional canonical observation with its freshness metadata; omit rather than compute in search.
- `match`: tier plus match reason (`identifier`, `reference`, `label`, `prefix`, `tokens`, `typo`). Raw values are not overwritten by normalized strings.
- `target`: discriminated launch descriptor from `contracts/ui.md`; no arbitrary URL or form input map.
- `sort_key`: deterministic comparable tuple used for merging; does not expose inaccessible identities.

### SearchPage

`items`, `has_more`, `next_cursor`, `provider`, `scope`, `evaluated_at`. No exact global count. A provider failure is a typed error response; the client retains other providers' successful pages. Search completion reflects only requested/healthy providers.

### ResolvedTarget

A client-supplied allowlisted reference resolves to a current authorized SearchHit, or a generic unavailable result without old labels. Transport/network failure is distinct from unavailable. Resolve max forty references (twenty recents plus twenty favorites); deduplicate first. Result targets are rechecked again by the real reader/command when opened or executed.

## Transient Palette View State

Broad filter, optional record-family refinement and optional Show all visible-group key are separate values. Store the preceding filter/refinement for Return. Each paged group tracks its source cursors and unconsumed hits; Reports combines local calculated views/templates with private-report pages before its fifty-hit cap. This state is memory-only, bound to user/company/query/ranking context, and cleared on scope change. It is not part of browser-local preferences or business persistence.

## Browser-local navigation preferences

Key: `reality.command-palette.v1:<user_id>:<tenant_id>`.

Value: schema version, up to twenty ordered recent target references and twenty ordered favorite target references. Each reference contains only a discriminated target kind, necessary opaque IDs/stable metadata keys and last-open/pin time. No names, amounts, customer text, source data, query history or authentication secrets. Untrusted stored values undergo enum/shape/length validation and are never execution authority.

Transitions:

1. Successful authorized open -> move reference to recent head; keep max twenty.
2. Pin -> add unique reference; reject a twenty-first pin with a clear limit message, never evict another favorite silently.
3. Unpin/clear recents -> remove corresponding references.
4. Open palette -> resolve references before rendering labels; transient failure retains hidden references for retry.
5. Explicit not-found/forbidden -> remove the affected reference without disclosing a reason that distinguishes another tenant's object.
6. Company/user change -> abort old requests, clear rendered labels and activate a distinct collection.
7. Successful logout/authentication loss -> clear feature-local keys and notify other tabs. Storage denial falls back to in-memory behavior with a quiet persistence-unavailable hint.

No browser preference needs an Alembic table or a service write.

## Database search support migration

The implementation revision is `packages/reality-core/migrations/versions/0066_global_search_support.py`, following the inspected `0065_requested_analysis` head.

- `reality_search_normalize_v1(text)` is immutable and uses explicit versioned normalization rules rather than deployment-dependent locale folding.
- `reality_search_edit_one_v1(text, text)` is immutable, bounded to one insertion/deletion/substitution/adjacent transposition; matching eligibility and tokenization remain explicit query rules.
- `reality_search_tier_v1(text, text[], text[])` composes normalization, tokenization and matching into one reusable immutable SQL predicate, so queries apply the same ranking before LIMIT. This support function adds no business field or authority.
- PostgreSQL UTF8 is required for normalization. Deployment/test preflight verifies this; no production startup runs DDL.
- Add only justified nonunique indexes over existing fields: tenant plus normalized names/reference fields (Party.name/accounting_code; Item.name/sku; Location.name; Document.number/customer_reference; SourceRecord.external_id; ShipmentPackage.tracking_number), and owner/tenant plus normalized report name if absent. Inventory existing indexes first; reuse equivalent ones. Opaque primary-key equality needs no redundant index.
- Indexes are rebuildable access paths, not persisted business authority. Query and index expressions must use the exact versioned function. Normalization changes require a new function version and index rebuild, not an in-place semantic change to an immutable indexed function.
- Downgrade drops only this revision's indexes, then its functions, after the old application release is restored. Never drop an extension or another feature's index.
- Existing metadata-created PostgreSQL test fixtures need the same support installer explicitly; migration tests separately prove installation/upgrades/downgrades. Application startup never installs support functions.

## Relationships preserved

Partner roles -> Party; Document -> Party/SourceRecord; ShipmentPackage -> Shipment -> counterparty/SourceRecord; payment cash LedgerEntry -> its held Document/Party; Reservation -> Commitment. Matching through these links does not create new FKs. Return source versions separately and use provenance readers for details rather than adding redundant search relationships.

Measured refinement: normalized ID/reference B-tree indexes and human-label `pg_trgm` GIN expression indexes are declared in `db/search_indexes.py` and installed by migration 0063. A complete edit-distance regex superset narrows evaluation without dropping possible matches. The extension is retained on downgrade because other features may share it. The ASCII normalization fast path is mathematically equivalent to the version-one mapping, not a new identity rule.

The equivalent frozen Latin-1 normalization path is exhaustively checked against
Python for code points 1–255. Direct label-family candidates retain ordered index
execution; joined evidence candidates materialize the complete matching set before
bounded ordering. Materialization is never a sampled candidate cap.
