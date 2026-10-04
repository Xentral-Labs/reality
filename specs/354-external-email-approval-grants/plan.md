# Implementation Plan 354

## Reviewed approach

Product scope authorized in chat: propose a format if Tobi has not published one
and implement in PR #332. Discussion reviewed; no concrete format supplied.
Ed25519 compact JWS and server-configured per-company subject mandates are the
smallest verifiable contract that does not require external people to have Reality
accounts. No token permission is interpreted as human authority.

Domain: closed input/claim/trust models in domain/email_approval_grants.py.
Services: email_approval_grants.py verifies signature and current mandate, owns
atomic acceptance; emails.py supplies exact normalized digest and rechecks grant
on claim; decision_attribution.py resolves recorded Source proof in a bounded
batch. Tools/MCP/API route to that service. UI renders shared attribution and
provides original Source navigation. Generated catalogs document input schemas.

## Constitution Check

| Principle | Result | Proof |
|---|---|---|
| Immutable Source → Evidence | PASS | Original compact signed proof stored losslessly; no Facts inferred |
| Reality authority | PASS | Existing Decision/EmailDispatch with canonical authorization service |
| Proven schema | PASS | No new table/column; extend existing channel constraint to external_grant; source identity indexes and existing company lock prevent replay |
| Tenant/shared services | PASS | Every query scoped; trust mandates require exact tenant; adapters delegate |
| Spec/test first | PASS | Spec, plan and tasks precede implementation; adversarial tests planned first |
| Explainable UI | PASS | Shared decider result and grant Source link; no browser trust calculation |
| Simplicity | PASS | Existing cryptography dependency, one algorithm, no network/key-fetch infrastructure |
| Received evidence | PASS | Original JWS plus verified actor provenance; no fabricated direct human observation |

## Persistence and rollback

Use SourceRecord source_system=email_approval, source_type=email_approval_grant,
external_id=SHA256([iss,jti]); payload contains original JWS and verified claims,
configured person label, proposal ID, verified public key/kid and acceptance mandate/time. These are public audit material, never private signing keys. Acceptance checks existing identity before
writes under shared company delivery lock; altered proof cannot make versions.
Decision output retains grant_source_id, decision channel external_grant. The existing channel check currently permits only Chat; extending that enum is necessary for shared attribution and current claim authority. No new column/table is needed.
Existing source/company deletion includes proof. Deployment rollback refuses new
grant acceptance/claims when verifier is removed; historical Source evidence stays.
Migration 0140 extends the existing decision-channel check constraint only. A guarded downgrade refuses to erase populated external attribution; no synthetic backfill or default registry. Old email proposals can use
a freshly read normalized digest, but executed mail cannot receive retroactive proof.

## Review risks and analysis

Configured issuer is an authority attesting human interaction; malicious issuer
can lie. Pinning keys and explicit subject/company authorization constrain that
trust; UI states external verification honestly. Deployment consistency is required
for revocation. Proof is not a claim capability and cannot skip operation permission.
Expired proof must be refreshed through a new person approval before unclaimed send;
no automatic validity extension. Exact grant replay checks current validity.

Manual Spec Kit-equivalent consistency/coverage analysis: no unresolved ambiguity,
no constitutional exception, no critical finding. Spec Kit commands are not
available in this session; do not claim those tools were run. Every FR maps to tasks
and planned executable tests. Final current-head CI remains the completion gate.
