# Public Site Privacy Interface Contract

## Routes

| Locale | Imprint | Privacy |
|---|---|---|
| English | /imprint/ | /privacy/ |
| German | /de/imprint/ | /de/privacy/ |
| Dutch | /nl/imprint/ | /nl/privacy/ |
| Spanish | /es/imprint/ | /es/privacy/ |

These URLs return complete legal HTML without scripts. Slashless forms normalize to the
same document. A `www` redirect preserves path/query. Locale path owns legal-page language;
links return to marketing with explicit lang. Every legal page has locale switching and
both legal footer links. Unknown legal URLs must not pretend to be legal documents by
serving the marketing shell. Static HTML must not load the React localization observer.

## Visitor behavior

No account, consent or API is needed to read legal information. Core navigation uses
native links. Text remains usable at mobile sizes, keyboard focus is visible, headings
are ordered and assistive technology can identify the document language. No external
font/image/embedded-service requests or speculative external connections are allowed.
Ordinary destination links load only upon activation.

The essential-only version has no banner or nonfunctional settings control. Footer legal
labels are localized. Legal text describes actual host/provider processing rather than
claiming that no data is collected solely because tracking is absent.

## Language handoff

Explicit lang survives Site internal navigation, Docs fallback/internal navigation, App
entry redirects and outgoing links, including English. Other query parameters and hashes
survive changes. Invalid values fall back safely. Choosing nl/es displays English Docs
without converting the remembered-in-URL preference to en. Deliberate Docs en/de selection
replaces the choice. Account loading cannot override explicit URL language and must not
write an account preference. Explicit profile save continues through the existing service.
A new anonymous direct visit without lang uses defaults; no cross-session recall is promised.

## Release checks

Preview fixtures are test inputs, not valid operator facts. Public release builds require
complete approved content for four locales, a resolved inventory with no optional services,
applicable provider evidence, operator and legal review references bound to current inputs,
and candidate test evidence. A digest mismatch or missing input fails with a named blocker.
Public Docker/deploy paths cannot quietly select preview mode. A preview artifact is marked
non-publishable and rejected by the public publication check.

Input review is checked before candidate generation; candidate tests and digest-bound
approval are checked after generation and before promotion. Keep the candidate approval
outside the hashed artifact and promote the tested artifact without rebuilding it.

Candidate evidence can precede publication; deployed smoke evidence necessarily follows it.
The dossier distinguishes these phases and records disable/rollback ownership if actual
processing differs. Review evidence is auditable; automatic validation is not legal review.

## Conditional extension

Any future retained optional service must first update plan/tasks/analysis. Its interface
must meet spec FR-009–FR-012, including one-action equal-prominence initial rejection,
purpose-level choice, persistent access to withdrawal, no collection before valid permission,
expiry/version invalidation, removal of controlled storage and multi-page withdrawal.
Until that design is approved and verified, a nonempty optional-service configuration is an error.

## Hosting baseline

FR-016–FR-018 require dedicated private SSE-S3 ALB logs in eu-central-1 with 30-day
expiration and administrator-only non-service access. AWS template/overlay values are
planned inputs until deployment is verified. Error/application collectors must be
inventoried separately. A successful infrastructure check does not approve legal texts.

## Draft review mode

Explicit `draft` mode uses real operator inputs, localized unreviewed banners and
noindex/disallow indexing. `draft: true` is rejected by candidate validation. Blockers
may remain only for draft rendering; no release or review state is fabricated.
