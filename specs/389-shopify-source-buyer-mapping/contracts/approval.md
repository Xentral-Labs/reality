# Exact Main human-review proof v1

Header: {alg:"EdDSA",typ:"tuesday-buyer-mapping+jwt",kid:TRUSTED_KEY_ID}.
Compact JWS, Ed25519 over the original ASCII base64url header.payload bytes.
No caller algorithm/key/url/jwk selection. Strict JSON duplicate keys rejected.

Claims (all required, no extra):
- iss: exact trusted Tuesday installation issuer
- aud: reality:shopify-source-buyer-mapping/1
- sub: opaque Tuesday person ID explicitly allowed by host policy, NOT a Reality user ID
- iat: integer Unix seconds; at most30seconds clock skew
- exp: integer Unix seconds, >now and <=iat+300
- jti: exact UUID of the retained Main human approval, not an independently minted runtime nonce
- tenant_id: exact Reality tenant
- review_id: exact retained mapping-only review
- review_digest: exact64lowercasehex digest returned by Realm prepare
- purpose: shopify_source_buyer_mapping_only/1

The frozen review digest binds original source/job/hash/integer version, external
order and shop, selected existing customer identity/current label/role digest,
review nonce/expiry and the mapping-only purpose. Main signs only after an
explicit authenticated human confirmation; model tools never sign or commit.
Root host must recheck current Main owner/session/source connection before HTTP.

Reality rechecks pinned issuer/key/subject/tenant/source policy and expiry after
acquiring current source/job/customer/review locks. Proof grants only recording
that exact mapping. It grants no order acceptance or further business action.
Raw compact proof and frozen review are retained as an immutable approval Source.
No Reality user ID is invented; submission token and external issuer/subject are
kept separately. No generic approve_and_execute permission is required or allowed.

Recorded commit/status returns approval.jti and approval.proof_digest (SHA256 of
the original compact JWS ASCII bytes). Unknown reconciliation must compare both
against its own retained human approval. A different proof never replays the same
accepted mapping, even from the same issuer and subject.
