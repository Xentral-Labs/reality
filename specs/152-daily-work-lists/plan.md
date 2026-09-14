# Plan: Daily work lists

Reuse existing tenant-scoped delivery and attention reads. Add pending proposal tool filtering and oldest-first order to shared core read/count services and API; preserve history order. No persistence change. Frontend: shared WorkList primitives, bounded incremental page loader, side dialog; new CommitmentsPage selected by ordersView=commitments. Existing OrdersPage/DeliveryCase and action confirmation remain canonical. Refactor AttentionPage and DecisionsPage presentation, retaining Inspector and action dispatch. Four-language UI text in localization.tsx.

## Constitution Check
All principles PASS: no schema, new authority, direct writes or browser calculations of business quantities. Existing shortest evidence links and tenant-scoped shared services remain. Exception engine remains existing derived authority; inherited full-set evaluation is explicitly a limitation, not a new scalable backend claim.

## Verification and rollback
Tests first: pending proposal filter/count/order, frontend routing/open-only contracts and browser fixture coverage for 120-row load-more, filter reset, drawer focus/Escape and no mutation on inspection. Then domain (none), services, API, UI. Run required backend suite, frontend contracts/build/i18n, spec and browser checks. Build matching local images if backend changes; no migrations. Rollback restores code/images without data operations.

Decision search matches existing tool type and received input text in SQL; the type
filter uses the canonical stored tool: prefix. Quantity/amount context is displayed
only when explicitly present in the proposal, never inferred from opaque references.

Icon refinement: reuse the existing PackageCheck icon for both sides in CommitmentsPage.tsx. Constitution PASS; no behavioral or schema change beyond visual affordance. Verify frontend contracts, production build and spec gate; no new test for this reversible icon replacement. Analysis: FR-002 and T006 are consistent; no unresolved finding.

Presentation refinement: add a title metadata portal beside PageActions and render WorkHeader totals into it. Move only the header underline using a background, retaining 40px hit targets. Constitution PASS; no data/service changes. Review: requirements clear; no critical findings. Verify build, contracts and daily-work browser fixtures.
