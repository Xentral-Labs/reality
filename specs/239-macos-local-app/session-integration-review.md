# Approved shared session integration

## Concrete change

Extract issuance/revocation of existing UserSession records from web/auth.py into
services/account_sessions.py. Preserve SHA-256 token hashing, 48-byte random tokens,
30-day expiration and existing hosted cookie attributes. Web auth retains its cookie
transport and transaction ownership. The desktop adapter uses the same service and
sends the raw token only through its native private pipe, then sets the already-proven
HttpOnly/SameSite=Strict cookie. No anonymous HTTP bootstrap or auth-disabled mode.

The service must reject local_os identities unless the trusted session context names
the exact installation owner. Existing email identities retain their prior hosted
admission/session semantics. Sessions remain persisted, revocable and tenant access
continues to require membership. Never write a fake email verification timestamp.

## Risk and validation

This touches shared hosted authentication. Incorrect extraction could break login,
logout or session rejection. Required checks: hosted login/logout/admission regressions,
local/hosted session rejection, revocation, exact-owner mismatch, migration upgrade and
safe-downgrade tests, then full backend suite before declaring integration complete.
No existing user database is migrated by the development tests.

## Automatic approval review

The attempted extraction command was rejected before execution. The stated reason
was that onboarding authorization did not explicitly cover this shared authentication
boundary and its wider effects. Before owner approval the extraction was not retried; account_sessions.py did not
exist and issuance/revocation remained in web/auth.py. The already-written
local-identity foundation is under isolated regression testing. Explicit owner approval
is required before continuing this shared-session change and desktop integration.

## Owner approval

The owner explicitly answered "ja" to the shared-session integration request on
2026-09-19. Proceed with the described service extraction, hosted regressions and
local setup integration. Release/signing requirements remain unchanged.

## Execution after approval

The approved service extraction is implemented. Focused session/access tests pass,
as do the actual packaged native session and real browser company-creation journey.
The broader suite is being verified; release approval is neither requested nor inferred.
