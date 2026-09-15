# Review: Free Playground Trial

## Scope and boundaries

The owner approved implementation, then corrected the offer to “Try for free” without a permanent-free promise and explicitly chose no initial expiry. No expiration, billing conversion, card collection, anonymous account or deployment was introduced. Feature 189 open admission changes and the unrelated feature 188 work remain intact.

Canonical company setup and its durable receipt/live marker are reused. Signup consent is explicit, historic/invited accounts remain unchanged, initial deep links are not hijacked, archive never recreates a company, and partial setup recovers from Home reload. Shared source intake, operational readers and proposal confirmation remain authoritative. No schema change or new scheduling infrastructure.

Managed questions reserve an account slot under PostgreSQL row lock before provider work. Trial accounts cannot bypass the allowance through an ordinary company or by omitting optional demo-creation consent at public signup. The allowance marker is independent of the creation request. Existing non-trial business users and own providers preserve behavior. The legacy companion rebinds read-only authority after reservation commits; its existing provider-policy tests pass.

## Verification evidence

- New service/API and focused companion/default-policy regressions: PASS.
- New browser acceptance: PASS, including actual en/de/nl/es mobile text, source-backed destination rendering, no prompt on errors/uninitialized data, dismissal, exhaustion draft, reload and archive behavior.
- Web contracts: 155 PASS; localization: 1819 strings covered in all four languages; production build PASS.
- Site contracts: 63 PASS; localization: 480 strings covered in all four languages; production build PASS.
- Documentation contracts: 67 Node tests and existing Python checks PASS; catalog generation/build PASS.
- Lint, specification/traceability policy and whitespace diff checks: PASS.
- Isolated replay benchmark: 1 PASS in 10.83 seconds, with the original 60-second assertion unchanged.
- Remaining full backend suite: 2472 PASS, 9 existing skips in 403.65 seconds. Together with the separately passed benchmark: 2473 PASS, 9 skips, covering every collected test. The existing SQLAlchemy teardown warning remains.
- Existing manual company-setup browser acceptance: 16 creation/recovery/open combinations PASS. Its fixtures were aligned with the current company-list API and shared More actions menu; no production behavior was changed for those fixture updates.

An initial full regression found outdated disabled-by-default expectations and a real companion transaction-scope regression. The expectations now explicitly test false; the companion re-establishes read-only scope after quota reservation. Every backend test was subsequently verified in the isolated benchmark and parallel remainder partitions.

## Deployment

Local working-tree implementation only. Railway has not been changed. Deployment must publish the code and preserve deliberate environment overrides; open signup requires feature 189 admission settings, enabled Playground, email delivery and the existing scheduler/worker roles. Managed AI additionally requires the deployment provider key. Existing pending users are not retroactively admitted or enrolled in the new signup journey.

## Existing benchmark isolation

The second full run found one unrelated timing failure: the 10,000-source replay benchmark took 62.30 seconds against its unchanged 60-second limit while other checks ran. Its cleanup followed assertions, leaving 10,000 committed sources and one tenant behind and causing six later count/lifecycle failures. Cleanup now runs in `finally`, including rollback of pending work. Spec impact: none for this test-only cleanup; no product behavior or performance threshold changes. Final verification runs that benchmark without competing test workers, then the remaining suite in parallel, covering every test.

## Final result

All required checks are green. Final scope/Constitution/diff review found no schema expansion, cross-tenant disclosure, alternate business rule, unconfirmed business action, permanent-free promise, new expiry or external publication. Browser acceptance also covers keyboard activation. Existing feature 188 work was preserved. The local implementation is ready for review and a separate Railway rollout.

## Entry feedback refinement (2026-09-14)

The authorized real local signup completed email verification and canonical demo creation. Three starter links subsequently loaded actual company records with no browser errors. No account identifiers or credentials are recorded here.

The delayed HTTP regression initially failed because session loading had no visible status text. A second run found a real competing-navigation failure after verification: the state update triggered AuthGate's redirect alongside the submit handler's redirect. A single full navigation now owns that transition. Delayed session, signup, verification, bootstrap, entry-policy and demo responses all expose localized progress; verification refusal permits retry and the selected German language survives navigation.

Validation: 155 web contracts passed; en/de/nl/es localization and formatting passed; TypeScript/Vite build passed; existing free-playground browser journey passed, including four mobile locales; entry-progress browser regression passed; spec policy and diff whitespace passed. Existing backend verification remains applicable: this refinement changes only presentation and navigation, no service, schema or backend behavior. Local Docker web rebuilt; real account login and all three starter destinations passed. No Railway deployment.

Final deployed-local check: delayed entry regression also passed directly against Docker port 8080 after the final rebuild; the centered German progress view was visually inspected.

## Internal-repository PR integration

Rebased onto main at `27a606c`, preserving the merged public-site privacy and Railway legal changes. Additive conflicts in site translations and documentation were combined. Backend content is byte-for-byte unchanged from the fully verified trial commit. Rebased checks: 156 web contracts, 77 site contracts, web/site localization and production builds passed; spec policy covers all 80 changed files. Whitespace in newly added specs was normalized.

Both entry-progress and full free-playground browser suites passed against the rebased production build, including four mobile locales. Web formatting passed.

## Free-only offer correction

Owner confirmed there is currently no paid hosted account and requested removal of the capacity banner. FR-011 supersedes retained paid Cloud positioning. Contract assertions first failed on the old card; updated site contracts and locale checks pass (77 tests), along with the four-language audit and production build. Browser checks at 1440px and 390px in en/de/nl/es confirmed free trial signup, no monthly/usage price, no capacity banner and no horizontal overflow. German mobile screenshot visually inspected. Backend admission, quota and self-hosted behavior are unchanged.

## Packages page focus

Owner approved removing the architecture/agent ecosystem block. The page contract first failed on its presence; after removal, all 77 site tests, four-language audit and production build passed. No other public-page content or service behavior changed.

Local Docker verification passed at desktop and mobile widths in all four languages: both offers remain, architecture/capacity sections are absent and no horizontal overflow occurs.

## Shared header local design preview

FR-013 preview uses a 68px desktop header, 32px flat logo, single-line wordmark, neutral navigation and compact language control. The free trial CTA retains emphasis. Site contracts (77), localization, formatting and production build pass. Browser review at 1440px, 1130px and 390px in all four languages confirms no overlap or page overflow and a working mobile menu. Desktop and mobile screenshots inspected. The design was verified locally and the owner subsequently requested publication in the PR.

## Hero alignment correction

FR-014: removed the centered, narrower hero container. Browser geometry reproduced an 82px title/card offset at 1920px before the change. After local Docker rebuild, eyebrow/title/description/card left edges match at 1920, 1440, 900 and 390px, without horizontal overflow. Desktop screenshot inspected; formatting, production build and spec policy passed. The change is limited to three CSS declarations.

## First visual-polish round

FR-015 applies shared typography, spacing and trial CTA presentation across public pages. Site contracts (77), four-language audit, production build and formatting pass. Browser checks cover three routes in four languages at desktop/mobile widths (24 combinations): no horizontal overflow, h1 line-height above 1.05, identical primary CTA backgrounds and preserved platform alignment. German desktop/mobile screenshots inspected. The typography browser check first exposed a competing legacy selector; the scoped heading rule now takes effect. No new business behavior.

## ERP Lite product-led preview

FR-016 uses actual delivery detail captures from the canonical demo, with verified 5/3/0/2 quantities. Four desktop screenshots and four responsive mobile quantity-grid screenshots contain no account identity. Static HTML explains the values, exposes meaningful alt text and identifies demo data. Site tests (77), localization, production build and spec policy passed. Eight browser combinations verified the language-specific responsive image source, loaded assets and no overflow. German desktop/mobile screenshots visually reviewed. Preview only, pending owner feedback.

FR-017 verification: captured actual weekly order counts (1, 8, 1, 1) and matching tables in en/de/nl/es at desktop/mobile widths. Replaced illustrative artwork with localized static screenshots and meaningful text alternatives. Site tests: 77 passed. Localization: 434/434 in every language. Build, formatting, spec policy and diff whitespace checks passed. Local Docker preview rebuilt; eight language/viewport checks verified loaded responsive images and no horizontal overflow. German desktop and mobile compositions visually inspected. This is a local preview; no production deployment or PR update was performed for FR-016/FR-017.

FR-018 review: core flow moved before the worked delivery example; optional model relationships and five background topics use native disclosures. Existing education content, finance distinctions, immutable-source qualifications and MCP/signup links remain intact. German initial page height falls from 13,957 to 6,766 px at 1440 px (51.5%) and from 23,630 to 10,583 px at 390 px (55.2%). Eight language/viewport checks verified collapsed initial state, keyboard open/close, no horizontal overflow including expanded content and a unique how-it-works anchor. Desktop disclosure layout and mobile process flow visually inspected. All 77 site tests, localization (442 strings per language), build, formatting, spec policy and diff whitespace checks passed. Local Docker preview only.
