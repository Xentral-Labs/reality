# Quickstart: Business Journey Guide

## Focused validation

1. Run catalog parity tests; expect exactly 228 unique baseline IDs and no broken/status-evidence references.
2. Run generation and freshness checks; expect English/German content, public JSON and contributor Markdown to be idempotent.
3. Run grounded-answer tests for supplier under-delivery, partial/out-of-scope cases, ambiguity, German, adversarial content and provider failure.
4. Run PostgreSQL proposal/vote stories for confirmation, duplicates, retry, concurrency, withdrawal, lifecycle and privacy.
5. Run Docs and Product Web browser contracts for filters, citations, static fallback, sign-in handoff and voting.
6. Open an ordinary English and German Docs page and verify the closed Ask Reality launcher uses the matching language and Guide route; verify the Business Journey Guide and standalone Journey Chat routes show no duplicate launcher.

## Required gates

```bash
make spec-check
make docs-generate
make docs-catalog-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

Also run the focused Docs build/browser suite and migration upgrade/downgrade proof named in `tasks.md`. Completion requires a public-artifact leakage scan and curated bilingual answer matrix.

## Expected result

The guide accounts for every canonical journey; supplier under-delivery produces a cited status-bounded explanation; insufficient evidence never becomes a capability claim; internal evidence remains authorized; and one account contributes at most one reversible active vote per proposal.

## Evidence recorded 2026-09-27

- Focused catalog/question/API/normal-Chat/proposal suite: 15 passed.
- Docs contract suite including the public chatbot: 91 passed.
- Production Docs build: passed; only the pre-existing bundle-size warning remains.
- Product Web TypeScript/Vite build and four-language localization audit: passed; only the pre-existing bundle-size warning remains.
- Spec policy and coverage-matrix gate: passed.
- Shared application/MCP read tool, normal Chat parity and authorized internal-evidence suite: 29 passed with the capability-catalog regressions.
- Generated bilingual Tool Usage reference includes the Business Journey Guide read tool.
- Proposal moderation requires Platform Admin authority, explicit confirmation, a public rationale and a valid journey link for `available`.
- Additive proposal/vote migration upgrade-downgrade and a real two-session concurrent vote race: 2 passed; one active relationship remains.
- Focused end-to-end backend regression set (catalog, questions, public/internal HTTP, proposal lifecycle, migration/concurrency and capability catalog): 38 passed from the repository root.
- Account HTTP mutation contract: anonymous access is refused; proposal and vote previews have no effect until the same account explicitly confirms.
- Ruff on the changed backend surface, spec policy and whitespace validation: passed.
- Curated proposal similarity accepts English paraphrases, a German/English supplier-shortage pair and a payment paraphrase while rejecting an unrelated receiving/payment pair. The preview exposes ranked open proposals and published journeys before confirmation.
- Updated focused backend regression set after similarity acceptance: 42 passed. Product Web production build and the English/German/Dutch/Spanish localization audit passed with zero missing translations.
- Normal Chat/MCP now exposes `business_journey_suggest_propose` and `business_journey_vote_propose`; both create the standard effect-free `ChangeProposal` preview and require the verified account principal at confirmation before calling the shared journey services.
- Journey mutation tool contract: 2 passed; existing membership proposal reauthorization regression: 2 passed; generated Docs contracts for the catalog, Guide and public widget: 54 passed.
- Tool Usage generation is deterministic and includes both new commands/tools. `make docs-catalog-check` remains intentionally open because its final `git diff --exit-code` compares the generated feature changes with uncommitted `HEAD`.
- Bilingual and multi-journey questions plus provider timeout, invalid citation and adversarial API fallbacks: 19 passed. Provider citations remain publication-bounded; the server derives the final evidence status and adds valid published IDs mentioned in prose to the visible citations.
- Local current-source stack rebuilt and restarted with API/MCP healthy, Product Web on 8080 and Docs on 8083. A temporary, explicitly labelled external-site simulation on 8082 loads the real public widget from 8083 and successfully calls the anonymous API on 8000 with allowed CORS.
- Public marketing-site embed: artifact and contract are ready; private operations-repository rollout and deployed smoke evidence remain pending.
- Catalog-bounded Anthropic semantic answering uses the existing managed `claude-haiku-4-5-20251001` configuration and workspace header. The server validates published IDs, completes explicitly named citations, derives the most conservative cited status and falls back deterministically on timeout or invalid output.
- Updated provider, typo, off-topic, status-ceiling, citation and EN/DE/NL/ES API regressions: 28 passed with Ruff clean. Local live acceptance returned `outcome: provider` for misspelled English, Dutch and Spanish return questions; a German poetry request was refused as outside Reality scope.
- Capability Advisor follow-up, broad overview, B2B solution and ephemeral-history regressions: 32 targeted service/API tests and 7 widget contracts passed with Ruff clean. Local live acceptance returned grounded provider answers for `Wie mache ich B2B mit Reality?` and the contextual follow-up `Und Wareneingang in mehreren Schritten?`.
- Public widget UX refresh: 6 contracts passed for new-tab Guide citations, readable 640 px desktop panel, fixed header/composer, independently scrolling ephemeral turns, mobile bottom sheet and safe text-node formatting. Docs production build and the rebuilt 8083 artifact passed; the current 8082 marketing-site embed loads that shared artifact.
- Docs Guide UX convergence: the embedded Ask Reality form now calls the same configured `/api/journey-guide/questions` endpoint as the website widget and renders its status, prose and citations. Local matching is only a labeled outage fallback. Asking and browsing are separate sections with examples, loading state, plain-language labels and a catalog count. Combined Guide/widget contracts: 11 passed; production build and local 8083 page returned HTTP 200 with the localhost API URL compiled in.
- Global Docs Ask Reality launcher (2026-09-28): the VitePress layout loads the existing public widget with the configured API URL and English/German Guide route, keeps it closed by default and suppresses it on the localized Business Journey Guide and standalone Journey Chat routes. The test was observed failing before the host component existed; afterward the focused widget suite passed 14/14, the complete Docs contract suite passed 108/108, Prettier passed and the production Docs build passed with only the existing bundle-size warning.
