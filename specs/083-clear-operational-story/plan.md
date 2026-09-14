# Implementation Plan: Clear Operational Story

**Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)
**Language**: English canonical content; existing public translations retained.

## Summary
Restore the original technology-led presentation and refine examples and boundaries selectively.
Reuse React/Vite, VitePress, existing styles and localization. No new dependencies.

Owner follow-up (FR-010): the final CTA now ends the landing page's main content. Remove the
plain open-source paragraph, the separate autonomy disclaimer box and the repeated
product-walkthrough card while retaining the agent-context timeline and four-step autonomy
progression. Assert all absences, then implement and run site, localization, build and spec gates.

## Technical Context
Agent recap: Spec impact: none. Add a bilingual explanatory closing chapter and navigation,
not an agent feature or promised timeline UI. Reconcile the existing inventory sequence and
finance example, explicitly label the assumed invoice-to-Huber evidence link, and separate
alternative corrections/cancellations from the base sequence. Distinguish stored records,
derived answers and source coverage. Test discoverability, numbers and limitations first;
then write the chapter and run docs gates. Owner approved scope; Constitution Check PASS.

Inventory chapter clarification: Spec impact: none. Explain existing write/derive boundaries
under FR-005 without changing business behavior. Retain sections 13–19 in both editions.
Show explicit Reservation creation, automatic consumption during shipment, separate receipt
and reservation actions, and calculated balances. Verify against reserve/_consume_reservations
and shipment/receipt services. Add a failing bilingual contract before copy edits; run docs gates.
Owner scope is explicit; Constitution Check PASS; no unresolved clarification or schema change.

Docs owner revision: Spec impact: none. Restore the original documentation home and first
journey/trace structure in English and German, including the 15/30/60-minute learning paths.
This clarifies existing FR-003 through FR-008 without changing behavior. Preserve model,
Fact-rule and action-boundary corrections elsewhere. Keep the lamp case as a small example
within the original journey; qualify timing as learning guidance, not a live ERP setup promise.
Review: explicit owner scope, Constitution Check PASS, no unresolved clarification.
Test the restored paths first, restore baseline copy with narrow corrections, run docs gates.

Glossary follow-up: Spec impact: none. Copy-only clarification of existing FR-005,
FR-006 and FR-008; no new behavior or model claims. Preserve the eight terms and layout.
Clarify evidence as Document/DocumentLine, obligations in both directions, source-backed
Facts, physical versus financial records, derived views and governed decisions.
Review: scope approved by owner; Constitution Check PASS; no unresolved clarification.
Add a focused glossary regression contract first, update all locales, then run site gates.

TypeScript/React public site and Markdown/VitePress docs; Node content-contract tests.
No storage, backend, API or business-rule changes.

## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Correct public chain and financial examples | PASS |
| Reality owns operational state | Open delivery is derived, not a document flag | PASS |
| Proven schema only | No schema change | PASS |
| Tenant + shared services | Static content only; no business calls | PASS |
| Spec/test traceability | Requirements mapped below; tests first | PASS |
| Explainable web behavior | Case traces answer through records and evidence | PASS |
| Received values not recomputed | Sample quantities only; no received amount recomputation | PASS |
| Smallest coherent design | Existing routes, styles, tools and catalogs | PASS |

## Repository Structure and Layer Changes
- provider-site/src/LandingPage.tsx and WhyRealityPage.tsx: original technology positioning and
  visuals, refined order example, domain labels and readiness.
- Remove provider-site/src/components/OperationalStory.tsx from the superseded redesign; integrate
  its simple example into the original landing narrative without changing the page structure.
- provider-site/src/PlatformPage.tsx: readiness beside access offers, unchanged prices.
- provider-site/src/localization.tsx: maintain all advertised languages.
- provider-site/src/landing.css: restore original layout; retain minimal readiness-note styling.
- apps/docs/content/{index.md,getting-started/,product-guides/,concepts/,integrations/}:
  English guidance and matching de/ editions; new missing-information guide.
- apps/docs/.vitepress/config.mts: expose the operator's extension guide.
- provider-site/scripts/site-contract.test.mjs and apps/docs/scripts/docs-contract.test.mjs:
  replace superseded copy assertions, preserve independent routing/locale/style tests.
- docs/WEB_SPEC.md: durable public presentation expectations.

## Design
No domain/service/tool changes; presentation follows existing contracts.
Sample order: ten lamps promised, four shipped, six open, two active reservations, four
unreserved; invoice settled through payment allocation. No implied shortage or lateness.
Source updates require review; a hypothetical case is not a preloaded demo.
Existing anchors and original technology-led visuals remain. Deeper explanation graphs stay,
with conceptual behavior labelled and incorrect domain labels corrected.
No credentials or external calls. Existing origins and language selection are preserved.

## Test Strategy and Traceability
| Requirements | Test | Initial failure |
|---|---|---|
| FR-001, FR-002, FR-004 | Site original-presentation and refined-example contracts | Missing original hero and graphics in the first rewrite |
| FR-003, FR-006 | Site readiness/action contract; docs entry contract | Turnkey and autonomy implications |
| FR-005 | Site model contract; docs semantic contract | Fact-only chain and Movement labels |
| FR-007, FR-008 | Docs entry and missing-information contract | No business path or Fact-rule guide |
| FR-009 | Existing locale, link, route and appearance tests; builds | New strings need translations |

Run site tests, i18n audit, build; docs tests and build; spec check and lint.
Backend/migration suites are not required: no runtime backend, schema or dependencies change.
Attempt desktop/mobile browser verification; report unavailable environment rather than claim a pass.

## Rollout and Rollback
Independent static site/docs deployment by owner; revert content changes to roll back.
No migration or account/pricing change. No deployment in this task.

## Review Risks
Avoid semantic drift between sample and translations, stale tests preserving obsolete claims,
and docs frontmatter links changing destinations accidentally.

## Complexity Tracking
No constitutional exceptions. Language catalogs and translated editions retain their existing
public-presentation role; technical artifacts remain English.
