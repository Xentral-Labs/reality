# Shared language implementation plan

## Design
Use a small dependency-free browser module under apps/shared for validation, URL generation and best-effort persistence. Store only the language in localStorage and a SameSite=Lax preference cookie; set Domain=runreality.ai only for that exact host or its subdomains. URL handoff works for independent Railway/custom hosts. Preserve existing deployment origins.

React site pages resolve the shared preference and publish it through their existing provider. All site documentation/auth links explicitly include language. AuthGate resolves the effective presentation language before mounting the app; explicit account preference callbacks publish their returned language. Existing account APIs and authorization remain unchanged.

VitePress initializes locale from explicit query, explicit German path or remembered preference, retaining topic/query/hash. Locale switches publish the selected en/de; English fallback from nl/es does not erase the original preference. Configured website/app anchors carry that preference, including navigation, footer, hero and ProductLink.

Docker contexts include the shared module for all three independent builds. No new dependency.

## Constitution Check
PASS: Source/Evidence/Reality, tenant boundaries, shared services and explainability unchanged. PASS: no schema or business authority added. PASS: presentation language remains independent of number locale/timezone. PASS: spec precedes implementation; tests precede fixes. No exceptions.

## Verification plan
Unit tests exercise all languages, stale English/German storage, explicit URL precedence, malformed values, blocked storage, cookie scope and URL preservation. Browser proofs cover website → Docs → logged-in app → website, conflicting account preference, language switches, fallback retention and direct return. Run site/web contracts and localization audits, docs contracts, three production builds, lint/spec checks.

## Review
The owner has requested same-browser continuity. Scope is bounded by FR-001–005; account synchronization across devices and translations are explicitly excluded. No unresolved clarification or critical issue.
