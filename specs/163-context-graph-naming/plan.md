# Plan: Context Graph naming

Rename the first Inspector section label in `inspectorSections.ts`, add the invariant term
to both localization catalogs and audits, and rewrite the public-site copy in
`LandingPage.tsx` and `WhyRealityPage.tsx` where it describes connected facts, with the
matching German, Dutch and Spanish catalog entries. Update the site contract that asserted
the old wording and add one that fixes the term. Adapters only; no domain, service, API or
persistence change.

## Constitution Check
All principles PASS. Naming only; no schema, authority, mutation, read or link change.

## Verification and rollback
Web: inspector navigation contract, four-language audit, TypeScript build. Site: contract,
appearance, localization and audit suites, TypeScript/Vite build. Prettier and spec policy.
Rollback reverts this commit.
