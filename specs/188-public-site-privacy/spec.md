# Feature Specification: Public Site Privacy and Legal Information

**Feature Branch**: `188-public-site-privacy` (isolated worktree; specification originally prepared on `main`)
**Created**: 2026-09-13
**Status**: Technical implementation verified — operator/legal review and publication approval pending
**Scope Approval**: The product owner approved this specification on 2026-09-13. This approves the requirements and scope; FR-013 legal and release prerequisites remain outstanding.
**Language**: English
**Input**: "Specify homepage changes to reduce the risk of legal complaints, including cookie consent and legal information."

## Context and Intent

### Problem

Visitors need to identify the operator, understand processing and control optional
services before they run. The owner wants to reduce exposure to legal complaints.
No specification, banner or automated test can guarantee immunity from warning letters,
litigation or regulatory action. This feature defines a verifiable privacy baseline
and a release review; it does not certify the entire business as legally compliant.

Source inspection on 2026-09-13 found no consent interface or privacy/imprint links in
the public footer, externally loaded Google Fonts, a Graphassets image and automatic
language persistence in a cookie and local storage. No visitor tracking was identified
in the inspected public-site source. These are repository observations, not a deployed
network audit. Reality's business analytics is unrelated to website visitor tracking.

### Scope

- All public-site routes, currently `/`, `/platform` and `/why-reality`, new legal pages,
  canonical and `www` entry points, mobile/desktop and supported site languages.
- Operator information, privacy disclosures, browser storage, external resources and
  hosting/CDN processing that may not appear in the browser bundle.
- A default release without optional visitor analytics, marketing or third-party embeds.
- Consent controls only if the inventory identifies an optional service that the owner
  explicitly decides to retain. Otherwise remove that service; do not introduce tracking.
- Shared language behavior and the links to Docs and account entry. Inventory these as
  separate processing boundaries; record out-of-scope findings with owners and follow-ups.
- Evidence for the actual deployment and ongoing maintenance of disclosures.

### Non-Goals

- A guarantee against legal complaints or a comprehensive company/product legal audit.
- New tracking, marketing forms, newsletters, checkout, accounts or business capabilities.
- A generic consent platform or third-party consent subscription without a proven need.
- Changes to operational business records, authentication or tenant permissions.
- Invented operator information or automatically treating generated legal text as approved.
- Certifying consumer-law, accessibility-law, intellectual-property, marketing-claim or
  contract compliance; relevant findings must be referred for separate review.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Specification workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Public-site boundary](../022-public-site/spec.md)
- [Public-site localization](../034-public-site-localization/spec.md)
- [Shared language](../176-shared-language/spec.md)
- [Web product contract](../../docs/WEB_SPEC.md)

This feature qualifies spec 176 FR-002/FR-003: explicit language handoff remains
supported, but an inferred default must not cause durable storage. Retained preference
storage needs a documented purpose, necessity, scope and finite retention decision.
Update the shared contract and verify all affected surfaces when implementing this change.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Identify the operator and understand processing (Priority: P1)

A visitor can read truthful legal information without an account or consent.

**Why this priority**: A banner does not replace operator identification or disclosures.

**Independent Test**: Follow legal links from every public route and compare each
published language with approved operator facts and the processing inventory.

**Acceptance Scenarios**:

1. **Given** any public page, **When** a visitor opens its footer, **Then** clearly named
   imprint and privacy links each lead directly to a dedicated readable page.
2. **Given** a direct legal URL, refresh or `www` entry, **When** it loads without login,
   consent or working scripts, **Then** legal text is available and is not replaced by
   the homepage or hidden behind a banner.
3. **Given** approved operator facts and an actual processing inventory, **When** a
   reviewer compares all legal translations, **Then** required information agrees and
   no placeholders, invented facts or unapproved claims remain.
4. **Given** mobile, keyboard-only or screen-reader navigation, **When** reading legal
   pages or changing languages, **Then** links, focus and reading order remain usable
   and a reviewed translation appears.

### User Story 2 - Browse with minimum processing (Priority: P1)

A visitor can browse without optional tracking or unnecessary external asset requests.

**Why this priority**: Avoiding unnecessary processing reduces exposure and review work.

**Independent Test**: Observe network and storage during fresh visits, scrolling,
language selection, cross-surface navigation, reload and return visits.

**Acceptance Scenarios**:

1. **Given** a fresh browser, **When** each route loads and the visitor scrolls or waits,
   **Then** no optional tracking, external font/image request, speculative connection to
   an external asset provider or unapproved storage access occurs.
2. **Given** no explicit language choice, **When** the default is selected, **Then** it
   is not durably stored. **Given** an explicit selection or language link, **When**
   moving between Site, Docs and App, **Then** the choice survives through the existing
   handoff and only approved preference storage is used, without sharing account data.
3. **Given** blocked storage, expired preferences or legacy values, **When** returning
   or changing language, **Then** navigation works, invalid values are ignored and
   obsolete storage is cleaned up where accessible without resetting authentication.
4. **Given** only reviewed essential processing, **When** visiting the site, **Then**
   no accept/reject banner suggests a nonexistent choice and privacy disclosures remain accurate.

### User Story 3 - Control any retained optional processing (Priority: P1, conditional)

If an optional service is explicitly retained, a visitor can make and reverse a choice.

**Why this priority**: Processing cannot precede the permission on which it relies.

**Independent Test**: Observe each retained service across consent states. If none is
retained, prove the optional inventory is empty and no banner appears; no consent framework is required.

**Acceptance Scenarios**:

1. **Given** no valid decision, **When** loading, scrolling, navigating or closing the
   interface, **Then** optional processing stays off until an affirmative choice.
2. **Given** the first consent layer, **When** displayed, **Then** accept-all and reject-all
   each take one action with equivalent prominence, settings are accessible and optional
   purposes are not preselected. Rejection does not prevent ordinary browsing.
3. **Given** a saved subset of purposes, **When** reloading or opening another route,
   **Then** only that valid subset runs. Every footer reopens settings, where withdrawing
   all optional consent takes one action.
4. **Given** withdrawal, expiry, an invalid decision, control failure or a new purpose/provider,
   **When** processing would next occur, **Then** affected optional services stay off until
   valid permission exists. Withdrawal stops further collection and clears controlled
   optional storage, without claiming that already transmitted data has been erased.

### User Story 4 - Release with evidence and maintain it (Priority: P1)

The operator can distinguish verified behavior from missing legal or operational work.

**Why this priority**: Source inspection alone cannot prove the deployed site's processing.

**Independent Test**: Review a release dossier with deliberately missing facts or an
unknown request and verify that release approval is blocked.

**Acceptance Scenarios**:

1. **Given** missing operator facts, provider terms, retention decisions, legal review or
   technical evidence, **When** assessing readiness, **Then** it is blocked with an owner
   and the evidence needed to resolve each missing item.
2. **Given** a candidate and deployment, **When** comparing browser observations and host
   configuration with the inventory, **Then** every destination, storage item and server-side
   purpose is accounted for. Unknown processing blocks approval; a post-deploy failure
   triggers disabling the affected service or rollback with a remediation owner.
3. **Given** prior approval, **When** a provider, purpose, retention period, operator fact,
   legal text or relevant host setting changes, **Then** affected review and tests reopen
   before publication approval.

### Edge Cases

- Storage unavailable, corrupted, cleared or expired; browser back/forward and multiple tabs.
- Parent-domain legacy language cookies, local preferences and explicit language links disagree.
- Unrelated self-hosted deployments must not inherit the production operator's legal identity.
- External resources or consent controls fail; failures must never enable optional tracking.
- Pixels, frames, preloads, tag managers and cookieless tracking require inventory too.
- Missing or unreviewed legal translation blocks that locale's approval; do not silently
  substitute unreviewed machine-generated legal text.
- Hosting/CDN/security logs may process personal data even with empty browser storage.
- Legal pages remain available with scripts disabled and while a consent overlay is visible.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Every public route MUST link directly to dedicated imprint and privacy
  pages, reachable without authentication, consent or scripts. Direct loads, refreshes
  and canonical redirects MUST preserve access to the intended legal page.
- **FR-002**: The imprint MUST use approved operator name, legal form, service address,
  representative and contact details, plus applicable register, tax and other mandatory
  details. Applicability MUST be reviewed; missing facts MUST NOT be fabricated.
  See [§ 5 DDG](https://www.gesetze-im-internet.de/ddg/__5.html).
- **FR-003**: Privacy information MUST describe actual purposes, lawful bases, data,
  recipients, retention periods or criteria, applicable transfers and safeguards,
  controller/contact, applicable data-protection contact, rights and complaint channels.
  It MUST cover hosting/security logs and distinguish Docs/account processing boundaries.
  Collection-specific mandatory/optional information MUST be included where applicable.
  See [GDPR Articles 12–14](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng).
- **FR-004**: Legal pages and conditional consent controls MUST support keyboard and
  assistive technology on mobile/desktop. English, German, Dutch and Spanish MUST convey
  reviewed equivalent information; original legal names/identifiers MUST remain unchanged.
- **FR-005**: A deployment inventory MUST record each destination/provider, purpose,
  data involved, storage name/type/scope where applicable, retention, consent classification
  and justification, and owner. It MUST include hosting/CDN processing and label unknowns.
- **FR-006**: The default release MUST have no optional tracking or external embeds.
  Fonts and imagery MUST be delivered from the site origin with verified usage rights;
  external asset preconnections MUST be removed. Ordinary outbound links MUST NOT load
  destination resources before activation.
- **FR-007**: Default language detection MUST NOT cause durable persistence. Remembering
  an explicit choice requires a documented necessity assessment, minimal scope and finite
  retention; otherwise preserve handoff without durable storage. Repeated reads MUST NOT
  extend retention. Remove superseded preference storage where accessible without touching
  authentication or unrelated preferences. A preference is not essential merely because
  it exists. This qualifies spec 176 FR-002/FR-003. See [§ 25 TDDDG](https://www.gesetze-im-internet.de/ttdsg/__25.html).
- **FR-008**: An essential-only deployment MUST show disclosures without an accept/reject
  banner. Optional services MUST be removed unless explicitly retained by the owner and
  FR-009–FR-012 are satisfied before activation.
- **FR-009**: Retained optional processing MUST stay off before valid affirmative consent,
  after rejection and on control failure. Scrolling, continued browsing, closing the
  interface or unrelated account actions MUST NOT count as consent.
- **FR-010**: If needed, the first consent layer MUST offer equally prominent one-action
  accept-all/reject-all and accessible settings. Explain purposes, providers and durations;
  distinct optional purposes MUST be independently selectable and initially off. Core
  browsing MUST remain available after rejection.
- **FR-011**: Every public footer MUST reopen settings when optional services exist.
  Withdrawal of all optional consent MUST take one action inside settings, stop further
  collection, propagate to other open site pages before further optional collection,
  and remove optional storage under site control.
- **FR-012**: If used, consent evidence MUST identify the choice, purposes/providers,
  notice version, time and expiry without cross-site tracking identifiers. Its retention
  and justification require review. Invalid/expired choices MUST default to off; new
  purposes/providers MUST NOT inherit old permission. See [GDPR Article 7](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng).
- **FR-013**: Release approval MUST require complete operator facts, approved inventory
  and legal text, applicable provider agreements/transfer review, named operational owners
  and documented review by a qualified legal/privacy reviewer. Confirm operator jurisdiction
  and flag other applicable website duties for separate review. Unknowns MUST block approval.
- **FR-014**: Required technical evidence MUST cover all public routes/locales, fresh and
  returning visits, storage failure, language handoff and all applicable consent states
  through network/storage observations. Audit the actual deployment including `www`,
  host-injected behavior and logging settings. Failures MUST block approval or require
  post-deploy disabling/rollback and tracked remediation.
- **FR-015**: A release dossier MUST name deployment/version, review date, reviewer,
  evidence and blockers. Relevant changes MUST invalidate affected approval. Assign an
  owner to recheck the inventory and legal sources at least every six months; this is
  a project policy, not a claimed statutory interval.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality remains unaffected. Website privacy preferences
  MUST NOT create or change operational SourceRecords, Documents or Reality records.
- **DR-002**: No business schema, duplicated relationship or document status is justified.
  Consent MUST NOT become a business identity or cross-tenant identifier.
- **DR-003**: The public site MUST remain independent of tenant data and authentication.
  Preserve existing account-entry and language boundaries; introduce no direct business
  writes, alternative business rules or unconfirmed mutating chat actions.

### Key Entities

- **Operator information**: Verified legal identity and contacts for a deployment.
- **Processing inventory**: Services/storage, purposes, lifecycle and reviewed classification.
- **Consent decision (conditional)**: Limited, revocable permission for optional processing.
- **Release dossier**: Versioned technical evidence, operator facts and human reviews.

These are conceptual information needs, not authorization for new business tables.

## Success Criteria _(mandatory)_

- **SC-001**: Every public route/locale offers one-link access to either legal page,
  including direct reload, without account or consent requirements.
- **SC-002**: Default-release journeys produce zero optional tracking requests, external
  font/image requests or unapproved storage accesses.
- **SC-003**: Every observed processing item maps to an approved inventory entry; zero
  unknown classifications, invented operator facts or legal-text placeholders remain.
- **SC-004**: If optional services exist, all consent-state tests prove blocking before
  permission and after withdrawal, with one-action rejection on the first layer.
- **SC-005**: The dossier identifies operator approval, legal review and deployed evidence;
  no required check or review is unresolved at release approval.
- **SC-006**: Every FR/DR maps to evidence; technical tests pass and manual checks name
  reviewers. Completing this spec does not establish implementation or release success.

## Assumptions and Dependencies

- Germany/EU is the initial review baseline, not a verified operator domicile or a claim
  that no other laws apply. Establishment, legal entity and target markets require review.
- Before publication approval, the owner must supply identity/address/representative/contact,
  applicable register/tax details, hosts/providers/regions, retention settings, applicable
  agreements and transfer safeguards, privacy contact and review owner. Do not guess them.
- No optional service has been requested. Removal is the default; consent implementation
  depends on a documented decision to retain one after inventory review.
- Product/account and Docs processing require their own review. Surface boundary gaps
  with owners and follow-ups; this feature cannot certify those entire products.
- Local copies of assets require verified usage rights; replace assets if rights are unknown.
- Final legal copy and translations require qualified review before publication approval.
- No live deployment audit, implementation, operator approval or legal sign-off was
  performed as part of preparing this draft.

## Open Questions

No unresolved product-scope question remains after owner approval. Operator/provider
facts and jurisdiction-specific legal conclusions remain release dependencies under
FR-013, not assumed approvals. Product scope review is complete; planning may proceed.

## Requirement Traceability

| Requirement   | Scenario(s)  | Planned test/evidence                                                                    |
| ------------- | ------------ | ---------------------------------------------------------------------------------------- |
| FR-001        | US1.1–2      | Footer/route, no-script and canonical-host checks                                        |
| FR-002–FR-003 | US1.3, US4.1 | Operator approval, inventory comparison and manual legal review                          |
| FR-004        | US1.4        | Locale checks, mobile/keyboard/screen-reader review and translation approval             |
| FR-005        | US4.2        | Network/storage audit and hosting/provider review                                        |
| FR-006        | US2.1        | Fresh-visit network checks, asset and license evidence                                   |
| FR-007        | US2.2–3      | Default/explicit/expiry/legacy/blocked-storage tests and cross-surface handoff           |
| FR-008        | US2.4, US3.1 | Essential-only no-banner check and optional-service decision review                      |
| FR-009–FR-010 | US3.1–2      | Conditional pre-consent/reject/subset interaction and network checks                     |
| FR-011–FR-012 | US3.3–4      | Conditional withdrawal/multi-page/expiry/version-change tests and evidence review        |
| FR-013        | US4.1        | Incomplete-dossier rejection and qualified review; legal conclusions are not automatable |
| FR-014        | US4.2        | Route/locale/state matrix, deployed audit and remediation evidence                       |
| FR-015        | US4.3        | Change-trigger review and recorded recurring-review ownership                            |
| DR-001–DR-003 | US2.2, US4.2 | No-schema/business-write diff review, browser boundary and handoff regression checks     |

## Legal Reference Baseline

Consulted on 2026-09-13. Recheck current versions and applicability at release review.
Requirements include conservative project choices, not only statutory obligations.

- [§ 5 DDG — operator information](https://www.gesetze-im-internet.de/ddg/__5.html).
- [§ 25 TDDDG — terminal storage/access and exceptions](https://www.gesetze-im-internet.de/ttdsg/__25.html).
- [GDPR — principles, lawful bases, consent, transparency, processors and transfers](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng).
- [German supervisory authorities' digital-services guidance](https://www.bfdi.bund.de/SharedDocs/Downloads/DE/DSK/Orientierungshilfen/OH_Digitale-Dienste.pdf?__blob=publicationFile&v=1):
  consent interfaces should correspond to processing that actually requires consent.

## Approved hosting extension (2026-09-14)

The user explicitly approved implementation of the following hosting configuration.
Operator: Xentral ERP Software GmbH, confirmed by the user. No additional product
scope approval is required. Live credentials and administrator role identifiers are
deployment inputs, not unresolved product requirements.

- **FR-016**: Enable ALB access logging to a dedicated private S3 bucket in
  eu-central-1 with all four public-access blocks, bucket-owner-enforced ownership,
  SSE-S3 and TLS-only access. Permit ALB delivery only to this account's log prefix;
  restrict other bucket access to explicitly named infrastructure administrator roles.
- **FR-017**: Configure expiration after 30 days on the whole dedicated log bucket,
  without versioning, replication or Object Lock retaining additional copies. Document
  that lifecycle deletion is asynchronous, not a guarantee of exact deletion time.
  Disable duplicate Nginx and Uvicorn request access logs on the shared ALB surfaces;
  retain necessary error/application logs only with documented 30-day collector retention.
- **FR-018**: Record the actual bucket, prefix, ALB attributes, policy, encryption,
  lifecycle and deployed server logging configuration after read-only verification.
  Missing access, log delivery, collector inventory or deployment evidence MUST remain
  explicit blockers. Never describe a prepared template as deployed infrastructure.
  Keep FR-006's no-tracking baseline and FR-013's publication review gate unchanged.

Acceptance: provisioning precedes ALB enablement; a real delivery appears beneath the
expected prefix; public access and non-administrator bucket access are denied; new
request access logs are absent from site/docs/web/API/MCP containers; errors remain
available. Wrong region, versioning, wrong expiry, missing delivery and unknown error
log retention each fail verification. Changes are limited to deployment adapters and
operational evidence; no business schema or service behavior changes.

## Real-operator draft preview (approved 2026-09-14)

**FR-019**: Local review MUST support real operator details and working legal text
without calling them fictional or approved. An explicit draft input and build mode
MUST label every legal page in its language as unreviewed, prevent indexing, preserve
known unresolved facts and remain ineligible for public promotion. Existing fixture
tests and candidate approval requirements MUST remain unchanged. All four languages
must provide review drafts with equivalent scope; missing facts stay visible.
Acceptance: eight draft URLs show Xentral facts and localized draft notices, render
without scripts, and contain no fictional operator. Draft input cannot pass candidate
validation even if someone attaches approval-shaped records.

## Final Railway demo legal pages (approved 2026-09-14)

**FR-020**: The non-canonical Railway demo MUST show final, provider-specific imprint
and privacy pages without draft labels. They MUST identify Railway hosting, the
configured Hobby plan's seven-day log retention, relevant technical request data and
possible international processing with links to Railway's official privacy, DPA and
log-retention information. The pages MUST remain non-indexable and MUST NOT claim AWS
hosts the Railway URL. Demo mode MUST remain ineligible for canonical production
promotion; AWS candidate approval remains unchanged.

Acceptance: all eight Railway legal URLs contain localized Railway disclosures, contain
neither draft labels nor AWS hosting claims, work without scripts and remain covered by
robots `noindex` and `Disallow`. Missing Railway URLs or an unsupported mode fails the
build. The user's instruction to make the Railway legal pages final approves this
provider-specific presentation; it is not an external legal opinion.
