# Implementation Plan: Separate Public Site and Product Web App

**Branch**: `022-public-site` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

### ERP Lite increment (2026-09-12, FR-028)

Attribute-strip refinement: reuse Lucide icons and semantic surface/border/text
tokens. Five equal desktop cells collapse into two columns, then one on small
screens. Decorative icons are hidden from assistive technology. No copy or
behavior changes; existing Site gates and visual review cover T115.
Constitution and scope review PASS; no critical analysis findings.

Final copy trim: shorten three paragraphs and update existing catalog entries and
contract expectations. Retain all FR-028 semantics and layout. T114 maps to the
existing contract and full Site gate; Constitution PASS, no analysis findings.

Graph emphasis refinement: move whole JSX sections, retaining anchors and renumbering
04/05; add one translated explanation above the graphic. Use normal surface/text
tokens inside the diagram, reserve the dark section for framing, enlarge record and
event labels, remove the redundant current-context label that collides with NOW.
At tablet widths use the existing stacked-card layout earlier; keep mobile rows
readable. Update existing graph contract before implementation; run Site gates,
spec policy and review CSS/section ordering. Constitution PASS; acceptance and T113
cover the change, no unresolved or critical analysis findings.

Context Graph clarification: update the existing introduction and its three catalog
entries, naming the shared foundation and five Reality record types. Update the
FR-028 assertion first; verify Site gates and spec policy. No layout or business
change. Requirement, T112 and contract align; Constitution PASS, no open findings.

Dashboard-teaser removal: owner approved deleting the sentence without replacement.
Update the existing section contract first, remove its JSX, three catalog entries
and unused CSS rule, then run the Site gate and spec policy. FR-028 acceptance and
T111 align; Constitution PASS, no unresolved or critical analysis findings.

ERP-optional refinement: replace the two approved copy blocks in `LandingPage.tsx`
and their translations in `localization.tsx`; add one attribute in the existing
wrapping list. No new layout, dependency, schema, service, or tool. Update the
existing FR-028 contract before implementation; run Site gates and spec policy.
Scope review is the owner's "ja mach" acceptance of the exact proposed copy.
Analysis: FR-028 acceptance, T110 and the existing contract align; all Constitution
principles PASS and no unresolved or critical findings remain.

Follow-up approved by the owner: delete only the Connections readiness paragraph
and link. Update the existing source-section assertion first, then remove the JSX.
Constitution check PASS; requirement, assertion and T109 align with no critical
analysis findings. Verify the complete Site gate and spec policy; no new layout.

Approved presentation-only extension of US4. Add one numbered section in
`provider-site/src/LandingPage.tsx` between Connections and Context, using six compact
capability cells and two explanatory blocks. Reuse semantic color tokens in
`landing.css`; collapse the grid from three to two to one column. Update all three
translation dictionaries in `localization.tsx`, retaining English component copy.
Correct the source paragraph and provenance caption and renumber later sections.
No domain, service, tool, schema, migration, dependency, or hosting changes.

Research: inventory, order-to-cash, procure-to-pay, ledger and source-ingestion
contracts support these capability summaries. README establishes MIT licensing.
Custom views reuse existing interfaces; dashboard publishing is future scope.
Use a compact model description rather than a table count or speed claim.

Constitution Check: principles I–VIII PASS; source values remain authoritative,
operational states are described as derived, and this static adapter adds no rules.
The existing data model and interface contracts remain unchanged. Rollback is limited
to this section, related copy, styles and catalog entries.

Validation order: update the existing source/numbering contracts and add FR-028
placement/content checks first, observe failure, implement, then run the complete
Site format/tests/localization/build gate, spec policy, and desktop/mobile visual
review. Backend, migration and Product Web execution are not required for this
static-copy-only increment because none of their files or contracts change.
Record evidence in `quickstart.md`. Review final diff for claims and source lineage.

### Account-first hero increment (2026-09-06, FR-027)

Owner-approved scope: simplify only the homepage hero to one existing signup link.
Reuse the translated Create account label and configured-origin/language helper.
Remove the operating-model and Playground buttons and Playground-specific footnote;
retain the ordinary navigation and system-safety note. No new component, CSS layout,
API, authentication, onboarding, business logic, or schema is required.
Update the superseded discovery wording in Spec 095. First replace the old
three-way discovery contract with a failing single-action and routing assertion in
`provider-site/scripts/site-contract.test.mjs`; then edit `LandingPage.tsx` and verify
Site tests, all four locale audits, production build, rendered desktop/mobile hero,
Spec policy and diff. Rollback restores these presentation changes through Git.
Constitution Check: all existing rows PASS. Analysis: requirement, acceptance,
T104–T105 and contract align; no unresolved clarification or critical finding.

Extract the current landing-page presentation into a second locked Vite/React
application at `provider-site`. Keep authentication, onboarding, and the tenant product in
`apps/web`, whose root becomes its authentication/application entry. Give both browser
applications independent Docker/Nginx definitions, CI gates, Compose services, and
documented domains. Account links use a build-time public app-origin contract.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: Two small static browser bundles; no backend, schema, or business-data change

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Static presentation split; the business chain is unchanged | PASS |
| Reality owns operational state | No document or operational state changes | PASS |
| Proven schema only | No schema or migration change | PASS |
| Tenant + shared service boundaries | Site has no service access; Web retains API-only tenant access | PASS |
| Spec/test traceability | FR/DR map to three stories and browser/deployment proofs | PASS |
| Explainable web behavior | Product Cockpit/Inspector is moved unchanged | PASS |
| Smallest coherent design | Two explicit apps; no CMS, workspace framework, or premature shared UI package | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/       # pure rules, if needed
packages/reality-core/src/reality/services/     # application behavior
packages/reality-core/src/reality/tools/        # shared agent/CLI tools
packages/reality-core/src/reality/web/          # transport only
packages/reality-core/tests/                    # unit, service, story, adapter proof
apps/web/src/                     # presentation only
provider-site/src/                    # public presentation only
```

**Files/layers affected**: `provider-site/`, `apps/web/`, `compose.yml`, `.env.example`,
`.dockerignore`, `.github/workflows/quality.yml`, `Makefile`, `README.md`,
`docs/ARCHITECTURE.md`, `docs/WEB_SPEC.md`, ADR 0005, and repository-layout tests.

## Design

### Reality flow

N/A for the site. Product Web keeps the existing API → shared services →
Source/Evidence/Reality flow without changes.

### Service and adapter flow

The public site is static and performs no application call. Its account links cross to
the configured product origin. Product Web continues to proxy `/api/*` to `apps/api`
and uses the existing authentication and operational service paths.

### Data and migration impact

No schema, migration, persistence, or business-data impact.

### Failure, security, and tenant behavior

The public site has no credentials or tenant state. Product cookies remain scoped by
the application deployment/hosting configuration. Unknown site paths return the site
shell; unknown product paths return the product SPA shell. Production `www` redirect
is an edge contract preserving path and query and is not implemented as application logic.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003, FR-007–FR-008 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Site does not exist and links are relative |
| FR-004–FR-006 | browser contract | `apps/web/scripts/product-boundary.test.mjs` | Product root currently renders landing page |
| FR-009–FR-012 | repository contract | `packages/reality-core/tests/test_repository_layout.py` | Site service, paths, commands, and docs are absent |
| DR-001–DR-003 | regression | Full backend and browser gates | Must prove no business/runtime regression |
| FR-015 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Shared agentic-core proposition and bilingual agent connection model are absent |
| FR-016 | browser contract | `provider-site/scripts/site-contract.test.mjs` | `/platform` regresses to speculative tiers or omits build-time Cloud price, admission capacity, waitlist behavior, and the Cloud versus self-hosted operating choice |
| FR-017 | browser contract | `provider-site/scripts/site-contract.test.mjs` | `/why-reality` category education, focused fulfillment and Finance scenarios, durable fact sequence, and landing/package links are absent |
| FR-018 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Public routes regress to duplicated headers, inconsistent language controls, or visually offset desktop navigation |
| FR-019 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Education regresses to abstract terminology, more than two competing scenarios, or lacks a plain-language analogy and agent outcomes |
| FR-020 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Education lacks definitions, a worked reasoning example, correction semantics, or clear category boundaries |
| FR-021 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Education fails to demonstrate how linked commitments, reservations, movements, constraints, and lineage become a bounded agent context packet |
| FR-022 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Fulfillment context regresses to disconnected cards without chronology, typed records, shortest true links, missing-event semantics, or context selection |
| FR-023 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Fulfillment regresses to a flat timeline without plan-versus-actual branches, bounded subgraph selection, simultaneous interpretation, or ERP-log distinction |
| FR-024 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Finance example regresses to prose cards without a traceable refund Commitment, Ledger Entry/open item, expected Settlement, missing Payment, and safe agent outcome |
| FR-025 | browser contract | `provider-site/scripts/site-contract.test.mjs` | Navigation regresses to an example-library label or education omits the selective, lossless intake and deliberately small typed relationship model |

## Rollout and Rollback

Deploy site and Web artifacts before switching host routing. Point `runreality.ai` to
site, permanently redirect `www`, and point `app.runreality.ai` to Web. Existing
sessions remain product-origin concerns. Rollback restores the prior combined Web
artifact and host mapping atomically; no database rollback exists.

## Review Risks

- Account links accidentally remaining relative and opening on the public origin.
- Product root continuing to expose marketing or site importing application/API code.
- CI validating only one browser app after the split.
- Provider-specific `www` routing cannot be proven by Compose; it is documented and
  contract-tested, then must be configured at the hosting edge.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
