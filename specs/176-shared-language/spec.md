# Shared language across product surfaces

**Language**: English
**Status**: Approved user request

## Context and Intent
A user who chooses a language must retain it when moving between the public website, documentation and application. Today some links omit language, and account loading can overwrite a language carried by a link.

### Non-Goals
No translation expansion, shared authentication, business changes, cross-device synchronization, automatic account preference writes, number-format or timezone changes.

## User Scenarios & Testing
1. Choose German on the website, open Docs, open the app with an English account preference: all three display German. Returning to the website remains German.
2. Choose English after German: links explicitly carry English so old destination storage cannot win.
3. Choose Dutch or Spanish, open Docs: the English documentation is displayed, but returning to the site/app restores Dutch/Spanish. Explicitly choosing English or German in Docs replaces the preference.
4. Reopen a surface on the standard runreality.ai domains or localhost: the browser preference remains available. Separate unrelated deployment hosts carry it via links and remember it locally after arrival.
5. Block storage or supply an invalid language: navigation still works with supported fallback; existing paths, unrelated query parameters and fragments survive.

## Requirements
- **FR-001**: Cross-surface product links carry the current preference explicitly, including English; Docs uses its supported page language while preserving the original preference.
- **FR-002**: Remember validated en/de/nl/es preferences locally; share the preference across standard product subdomains and localhost without account/session data.
- **FR-003**: Explicit URL language takes priority, then browser preference, then saved account language or English. Auth loading must not overwrite a carried preference. Explicit profile language saves publish the new browser preference without changing number format/timezone.
- **FR-004**: Docs selects the equivalent localized topic on entry and remembers explicit language switches; no redirect loops or loss of anchors/search parameters.
- **FR-005**: Preserve deployable builds, configurable origins, safe blocked-storage behavior, and existing auth return destinations.

## Assumptions and Dependencies
The owner requests language continuity in the same browser. Docs supports en/de; site/app support en/de/nl/es. A non-sensitive preference cookie is shared only on the known runreality.ai parent domain; unrelated deployment hosts exchange the value through links. No third-party storage or speculative public-suffix inference.

## Success Criteria
All five scenarios pass with browser proofs and regression tests; all three builds and applicable localization audits pass. No business API mutation occurs merely because a language link is followed.

## Requirement Traceability

| Requirement | Tasks | Proof |
| --- | --- | --- |
| FR-001 | T001–T004 | shared-language unit and browser handoff tests |
| FR-002 | T001–T004 | scoped cookie, blocked storage and direct reopen tests |
| FR-003 | T001, T003 | conflicting account language and explicit profile save browser proofs |
| FR-004 | T001, T004 | Docs fallback, explicit switch, deep topic/query/hash/reload proofs |
| FR-005 | T001, T005 | blocked storage, URL tests, production builds and existing auth contracts |

## Privacy qualification (spec 188)

[Spec 188](../188-public-site-privacy/spec.md) supersedes FR-002's durable browser
retention and scenario 4's anonymous bare-URL recall. Explicit choices are carried by
URL across Site/Docs/App, including internal Docs navigation and English fallback for
nl/es. A fresh anonymous bare URL uses the surface default; an authenticated App visit
can use its existing saved account preference. No cookie/localStorage preference is
read or newly persisted. Only obsolete language storage is removed where accessible.
Explicit account profile saves continue through existing services. See spec 188 verification.
